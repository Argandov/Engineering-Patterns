package pkg

import (
	"fmt"

	"siem-collector-bootstrap/helpers"
)

func InstallBindplane(
	version string,
	websocket string,
	key string,
	config string,
) error {
	fmt.Println("[+] Installing Bindplane")
	scriptURL := fmt.Sprintf(
		"https://github.com/observIQ/bindplane-agent/releases/download/v%s/install_unix.sh",
		version,
	)

	tmpScript := "/tmp/install-bindplane.sh"
	if err := helpers.Download(scriptURL, tmpScript); err != nil {
		return fmt.Errorf("download bindplane script: %w", err)
	}

	websocket_full := fmt.Sprintf("wss://%s", websocket)

	args := []string{
		tmpScript,
		"-e", websocket_full,
		"-s", key,
		"-v", version,
		"-k", config,
	}
	if err := helpers.Run("sh", args...); err != nil {
		return fmt.Errorf("run bindplane installer: %w", err)
	} else {
		fmt.Println("[+] OK - Bindplane installed")
	}

	return nil
}
