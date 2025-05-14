package system

import (
	"fmt"

	"tailscale-bindplane-bootstrap/helpers"
)

func EnsureSSH() error {
	// 1) Check if openssh-server is installed
	if err := helpers.Run("dpkg", "-s", "openssh-server"); err != nil {
		if err := helpers.Run("apt-get", "update", "-qq"); err != nil {
			return fmt.Errorf("failed to apt-get update: %w", err)
		}
		if err := helpers.Run("apt-get", "install", "-y", "openssh-server"); err != nil {
			return fmt.Errorf("failed to install openssh-server: %w", err)
		}
	}

	// 2) Enable & start SSH server
	if err := helpers.Run("systemctl", "enable", "--now", "ssh"); err != nil {
		return fmt.Errorf("failed to enable/start ssh: %w", err)
	}

	return nil
}
