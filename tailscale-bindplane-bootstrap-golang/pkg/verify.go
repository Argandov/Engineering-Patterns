package pkg

import (
	"fmt"

	"tailscale-bindplane-bootstrap/helpers"
)

// VerifyServices ensures tailscaled and observiq-collector are active.
func VerifyServices() error {
	fmt.Println("[+] Final Step: Verifying services...")
	svcs := []string{"tailscaled", "observiq-otel-collector"}
	for i, svc := range svcs {
		if err := helpers.Run("systemctl", "is-active", "--quiet", svc); err != nil {
			return fmt.Errorf("service %s not active: %w", svc, err)
		} else {
			fmt.Printf("\t- Verification %v/2 passed\n", i+1)
		}
	}
	return nil
}
