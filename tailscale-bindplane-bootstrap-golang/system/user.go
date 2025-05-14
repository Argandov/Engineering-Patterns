package system

import (
	"encoding/base64"
	"fmt"
	"io"
	"os/exec"
	"strings"

	"siem-collector-bootstrap/helpers"
)

func CreateUser(username, b64pass string) error {
	exists := exec.Command("id", username).Run() == nil

	if !exists {
		if err := helpers.Run("useradd", "-m", "-s", "/bin/bash", username); err != nil {
			return fmt.Errorf("creating user %q: %w", username, err)
		}
	}

	if err := SetUserPassword(username, b64pass); err != nil {
		return fmt.Errorf("setting password for %q: %w", username, err)
	}

	if err := helpers.Run("usermod", "-aG", "sudo", username); err != nil {
		return fmt.Errorf("adding %q to sudo group: %w", username, err)
	}

	return nil
}

func SetUserPassword(username, b64pass string) error {
	raw, err := base64.StdEncoding.DecodeString(b64pass)
	if err != nil {
		return fmt.Errorf("invalid base64 password: %w", err)
	}

	password := strings.TrimRight(string(raw), "\r\n")

	if strings.ContainsAny(password, ":\n") {
		return fmt.Errorf("password contains unsupported character ':' or newline")
	}

	cmd := exec.Command("chpasswd")
	stdin, err := cmd.StdinPipe()
	if err != nil {
		return fmt.Errorf("failed to open stdin for chpasswd: %w", err)
	}

	go func() {
		defer stdin.Close()
		io.WriteString(stdin, fmt.Sprintf("%s:%s\n", username, password))
	}()

	if out, err := cmd.CombinedOutput(); err != nil {
		return fmt.Errorf("chpasswd failed: %s – %w", strings.TrimSpace(string(out)), err)
	}
	return nil
}
