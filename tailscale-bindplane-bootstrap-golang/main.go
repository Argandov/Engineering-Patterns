package main

import (
	"fmt"
	"os"
	"siem-collector-bootstrap/helpers"
	"siem-collector-bootstrap/pkg"
	"siem-collector-bootstrap/system"

	"github.com/spf13/cobra"
)

var (
	// SYSTEM
	user      string
	b64pass   string
	client_id string

	// TS
	ts_key string

	// BP
	bp_websocket string
	bp_key       string
	bp_ver       string
	bp_config    string

	// SLACK
	webhook string
)

func newRootCmd() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "Bootstrap Installer",
		Short: "Installs and configures Tailscale and Bindplane",

		RunE: func(cmd *cobra.Command, args []string) error {
			host, err := os.Hostname()
			hostname := fmt.Sprintf("%s-%s", client_id, host)
			if err != nil {
				hostname = client_id
			} else {
				fmt.Printf("[+] Initializing installer on [%s]\n", hostname)
			}
			// CHECKED
			if err := system.EnsureSSH(); err != nil {
				fmt.Printf("[!!] SSH install failed: %v\n", err)
				helpers.NotifySlack(webhook, "[!!] SSH install failed: "+err.Error(), hostname)
				return err
			}
			if err := system.CreateUser(user, b64pass); err != nil {
				fmt.Printf("[!!] User creation failed: %v\n", err)
				helpers.NotifySlack(webhook, "[!!] User creation failed: "+err.Error(), hostname)
				return err
			}

			if err := pkg.InstallTailscale(ts_key, hostname); err != nil {
				fmt.Printf("[!!] Tailscale install failed: %v\n", err)
				helpers.NotifySlack(webhook, "[!!] Tailscale install failed: "+err.Error(), hostname)
				return err
			}
			if err := pkg.InstallBindplane(bp_ver, bp_websocket, bp_key, bp_config); err != nil {
				fmt.Printf("[!!] Bindplane install failed: %v\n", err)
				helpers.NotifySlack(webhook, "[!!] Bindplane install failed: "+err.Error(), hostname)
				return err
			}
			if err := pkg.VerifyServices(); err != nil {
				fmt.Printf("[!!] Service verification failed: %v\n", err)
				helpers.NotifySlack(webhook, "[!!] Service verification failed: "+err.Error(), hostname)
				return err
			}
			fmt.Printf("[+] Bootstrap complete for %s\n", hostname)
			helpers.NotifySlack(webhook, fmt.Sprintf("[SUCCESS] Bootstrap complete for [%s]", hostname), hostname)
			return nil
		},
	}

	// Bind  flags
	f := cmd.Flags()
	// System
	f.StringVarP(&client_id, "id", "i", "", "unique identifier")
	f.StringVarP(&user, "user", "u", "", "username to create")
	f.StringVarP(&b64pass, "p64-pass", "p", "", "Base64 password for user")
	// BP
	f.StringVarP(&bp_websocket, "websocket-endpoint", "w", "", "BP websocket URL")
	f.StringVarP(&bp_key, "bp-key", "k", "", "BP auth key")
	f.StringVarP(&bp_ver, "bp-version", "v", "", "BP version")
	f.StringVarP(&bp_config, "bp-config", "c", "", "BP config file")
	// TS
	f.StringVarP(&ts_key, "ts-key", "K", "", "TS auth key")
	// Slack
	f.StringVarP(&webhook, "notif-webhook", "s", "", "Notification webhook URL")

	// MARK ALL AS REQUIRED:
	cmd.MarkFlagRequired("id")
	cmd.MarkFlagRequired("user")
	cmd.MarkFlagRequired("p64-pass")
	// BP
	cmd.MarkFlagRequired("websocket-endpoint")
	cmd.MarkFlagRequired("bp-key")
	cmd.MarkFlagRequired("bp-version")
	cmd.MarkFlagRequired("bp-config")
	// TS
	cmd.MarkFlagRequired("ts-key")
	// Slack
	cmd.MarkFlagRequired("notif-webhook")

	return cmd
}

func main() {

	if err := (&helpers.SystemChecker{}).CheckAll(); err != nil {
		fmt.Fprintf(os.Stderr, "[ERROR] Initialization failed: %v\n", err)
		os.Exit(1)
	}
	if err := newRootCmd().Execute(); err != nil {
		fmt.Println("[!] Aborted")
		os.Exit(1)
	}
}
