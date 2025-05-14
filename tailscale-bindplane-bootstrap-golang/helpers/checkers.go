package helpers

import (
	"context"
	"errors"
	"fmt"
	"net/http"
	"os"
	"os/exec"
	"strings"
	"time"
)

type SystemChecker struct{}

func (c *SystemChecker) CheckAll() error {
	fmt.Println("[i] Checking system...")
	if err := c.checkRootOrSudo(); err != nil {
		return fmt.Errorf("sudo/root test failed: %w", err)
	}
	if err := c.checkDebian(); err != nil {
		return fmt.Errorf("OS test failed: %w", err)
	}
	if err := c.checkInternet(); err != nil {
		return fmt.Errorf("network test failed: %w", err)
	}

	fmt.Println("[+] All checks passed")
	return nil
}
func (c *SystemChecker) checkRootOrSudo() error {
	if os.Geteuid() == 0 {
		return nil
	}
	if err := exec.Command("sudo", "-n", "true").Run(); err != nil {
		return errors.New("\n\tMust be run as root or have passwordless sudo")
	}
	return nil
}

func (c *SystemChecker) checkDebian() error {
	data, err := os.ReadFile("/etc/os-release")
	if err != nil {
		return fmt.Errorf("cannot read os-release: %w", err)
	}
	for _, line := range strings.Split(string(data), "\n") {
		if (strings.HasPrefix(line, "ID=") && strings.Contains(line, "debian")) ||
			(strings.HasPrefix(line, "ID_LIKE=") && strings.Contains(line, "debian")) {
			return nil
		}
	}
	return errors.New("\n\tunsupported OS; only Debian-based distros allowed")
}

func (c *SystemChecker) checkInternet() error {
	client := &http.Client{Timeout: 5 * time.Second}
	urls := []string{
		"https://tailscale.com",
		"https://github.com",
	}
	for _, u := range urls {
		ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
		defer cancel()
		req, _ := http.NewRequestWithContext(ctx, http.MethodHead, u, nil)
		resp, err := client.Do(req)
		if err != nil {
			return fmt.Errorf("cannot reach %s: %w", u, err)
		}
		resp.Body.Close()
		if resp.StatusCode < 200 || resp.StatusCode >= 400 {
			return fmt.Errorf("unexpected status from %s: %d", u, resp.StatusCode)
		}
	}
	return nil
}
