package helpers

import (
	"bytes"
	"fmt"
	"net/http"
	"time"
)

func NotifySlack(webhookID, text, hostname string) error {

	slack_url := "https://hooks.slack.com/services/"
	webhookURL := fmt.Sprintf("%s/%s", slack_url, webhookID)

	payload := fmt.Sprintf(`{"text":"[%s] %s"}`, hostname, text)
	client := &http.Client{Timeout: 5 * time.Second}
	resp, err := client.Post(webhookURL, "application/json", bytes.NewBufferString(payload))
	if err != nil {
		return fmt.Errorf("Slack POST failed: %w", err)
	}
	defer resp.Body.Close()
	if resp.StatusCode >= 300 {
		return fmt.Errorf("Slack returned status %d", resp.StatusCode)
	}
	return nil
}
