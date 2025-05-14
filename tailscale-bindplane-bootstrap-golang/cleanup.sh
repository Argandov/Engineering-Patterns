#!/usr/bin/env bash
set -euo pipefail

# Change this to match the user you created
USER_TO_REMOVE="" # CHANGE THIS

echo "[*] Stopping and disabling services…"
systemctl stop observiq-otel-collector tailscaled || true
systemctl disable observiq-otel-collector tailscaled || true
systemctl daemon-reload

echo "[*] Uninstalling Bindplane agent…"
# If there’s an official uninstall command, call it:
if command -v bindplane >/dev/null 2>&1; then
  bindplane uninstall || true
fi
# Otherwise, remove its files and service unit
rm -f /etc/systemd/system/observiq-otel-collector.service
rm -rf /opt/observiq-otel-collector

echo "[*] Uninstalling Tailscale…"
# bring Tailscale down cleanly
tailscale down 2>/dev/null || true
# remove package and data
apt-get remove --purge -y tailscale
rm -rf /var/lib/tailscale /var/lib/tailscaled

echo "[*] Deleting user ${USER_TO_REMOVE}…"
# kill any remaining processes
pkill -u "${USER_TO_REMOVE}" 2>/dev/null || true
# delete the user and their home directory
userdel -r "${USER_TO_REMOVE}" 2>/dev/null || true

echo "[*] Cleanup complete."

