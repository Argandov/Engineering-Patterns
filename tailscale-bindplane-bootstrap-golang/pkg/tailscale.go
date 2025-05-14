package pkg

import (
	"fmt"
	"siem-collector-bootstrap/helpers"
)

// InstallTailscale streams the official installer, enables the service, and runs `tailscale up`.
func InstallTailscale(ts_key, hostname string) error {

	fmt.Println("[+] Installing TS")

	// 1. Install via curl|sh
	cmd := fmt.Sprintf("curl -fsSL https://tailscale.com/install.sh | sh")
	if err := helpers.Run("bash", "-c", cmd); err != nil {
		return fmt.Errorf("install tailscale: %w", err)
	}
	// 2. Enable service
	if err := helpers.Run("systemctl", "enable", "--now", "tailscaled"); err != nil {
		return fmt.Errorf("enable tailscaled: %w", err)
	}
	// 3. Up
	if err := helpers.Run("tailscale", "up", "--authkey", ts_key, "--hostname", hostname); err != nil {
		return fmt.Errorf("tailscale up: %w", err)
	} else {
		fmt.Println("[+] OK - TS installed")
	}
	return nil
}
