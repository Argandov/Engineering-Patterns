package helpers

import (
	"fmt"
	"io"
	"net/http"
	"os"
	"time"
)

func Download(srcURL, destPath string) error {
	out, err := os.Create(destPath)
	if err != nil {
		return fmt.Errorf("creating %q: %w", destPath, err)
	}
	defer out.Close()

	client := &http.Client{Timeout: 30 * time.Second}
	resp, err := client.Get(srcURL)
	if err != nil {
		return fmt.Errorf("GET %q: %w", srcURL, err)
	}
	defer resp.Body.Close()

	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("bad HTTP status %d for %q", resp.StatusCode, srcURL)
	}
	if _, err := io.Copy(out, resp.Body); err != nil {
		return fmt.Errorf("writing to %q: %w", destPath, err)
	}
	return nil
}
