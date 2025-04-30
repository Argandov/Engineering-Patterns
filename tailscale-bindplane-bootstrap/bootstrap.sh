#!/usr/bin/env bash
set -euo pipefail

# ==========================================================
# Bootstrap script for installation of:
# - Tailscale
# - Bindplane agent
# ==========================================================
# ----------------------
# Initial Validation
# ----------------------
if [ -z "${BASH_VERSION:-}" ]; then
  echo "[ERROR] This script needs to be run in Bash"
  exit 1
fi

# ----------------------
# Initial Config
# ----------------------
PREFIX=""
USERNAME=""
readonly B64PASS_STD=''
TAILSCALE_AUTH_KEY=""            # Tailscale auth key
TAILSCALE_HOSTNAME="$PREFIX-$(hostname)"       # Tailnet host name
BINDPLANE_SCRIPT_URL=""
SLACK_CNL=''

declare -a BINDPLANE_ARGS=(
	-e '' 
	-s '' 
	-v '' 
	-k ''
)
# -----------------------------------
# End Initial Config
# -----------------------------------

# Decode password
PASSWORD=$(printf '%s' "$B64PASS_STD" | base64 -d)

# Stdout colors - only if TTY
if [ -t 1 ]; then
  GREEN="\e[32m"; CYAN="\e[36m"; RED="\e[31m"; RESET="\e[0m"
else
  GREEN=""; CYAN=""; RED=""; RESET=""
fi

log()    { echo -e "${CYAN}[INFO]${RESET} $1"; }
error_exit() { echo -e "${RED}[ERROR]${RESET} $1 "; exit 1; }

require_command() {
  command -v "$1" >/dev/null 2>&1 || error_exit "Command '$1' not found. Please install it and try again."
}

check_sudo() {
  sudo -n true 2>/dev/null || error_exit "This script requires sudo. Please run as root."
  log "Sudo permission verified."
}

check_internet() {
  local urls=("https://tailscale.com/install.sh" "$BINDPLANE_SCRIPT_URL")
  for url in "${urls[@]}"; do
    curl -fsSL --max-time 10 "$url" >/dev/null 2>&1 \
      || error_exit "Error connecting to '$url'. Please check your internet connection or Firewall settings and try again."
  done
  log "Verified internet connection."
}

create_user() {
  if id "$USERNAME" >/dev/null 2>&1; then
    log "User '$USERNAME' already exists."
  else
    log "Creating user '$USERNAME'..."
    useradd -m -s /bin/bash "$USERNAME" || error_exit "Error creating user."
    echo "${USERNAME}:${PASSWORD}" | chpasswd || error_exit "Error assigning password."
    usermod -aG sudo "$USERNAME" || error_exit "Error assigning user to sudoers."
    log "User '$USERNAME' created and configured."
  fi
}

send_slack_notification() {
  local msg="Collected: [$USERNAME@$(hostname)]. Tailsnet: ['${TAILSCALE_HOSTNAME}']."
  local payload
  payload=$(printf '{"text": "%s"}' "$msg")
  if ! curl -fsSL -H "Content-Type: application/json" -d "$payload" "$SLACK_CNL" >/dev/null 2>&1; then
    warn "Error sending Slack notification."
  else
    log "Slack notification sent."
  fi
}

enable_ssh() {
  log "Verifying OpenSSH Server installation..."

  # 1) OpenSSH Installation check
  if ! dpkg -s openssh-server >/dev/null 2>&1; then
    log "Installing OpenSSH Server..."
    apt-get update -qq || error_exit "Error updating package index."
    apt-get install -y openssh-server >/dev/null 2>&1 \
      || error_exit "Error installing OpenSSH Server. Please check your internet connection and try again."
  fi

  # 2) Enable and start SSH
  systemctl enable --now ssh >/dev/null 2>&1 \
    || error_exit "Error starting OpenSSH Server."

  log "OpenSSH Server installed and enabled."
}

install_tailscale() {
  log "Installing Tailscale..."
  # Silent install, logging to /tmp/bootstrap-tailscale.log
  if ! bash <(curl -fsSL https://tailscale.com/install.sh) >/tmp/bootstrap-tailscale.log 2>&1; then
    error_exit "Error installing Tailscale. see /tmp/bootstrap-tailscale.log"
  fi
  systemctl enable --now tailscaled >/dev/null 2>&1 || error_exit "Error starting Tailscale."
  if ! tailscale up --authkey "$TAILSCALE_AUTH_KEY" --hostname "$TAILSCALE_HOSTNAME" >/tmp/bootstrap-tailscale.log 2>&1; then
    error_exit "Error connecting to Tailscale. see /tmp/bootstrap-tailscale.log"
  fi
  log "Tailscale configured correctly as $TAILSCALE_HOSTNAME."
}

install_bindplane() {
  log "Installing Bindplane Agent..."
  curl -fsSL "$BINDPLANE_SCRIPT_URL" -o /tmp/install-bindplane.sh >/dev/null 2>&1
  if ! bash /tmp/install-bindplane.sh "${BINDPLANE_ARGS[@]}" >/tmp/bootstrap-bindplane.log 2>&1; then
    error_exit "Error installing Bindplane Agent. see /tmp/bootstrap-bindplane.log"
  fi
  log "Bindplane agent installed and configured."
}

verify_services() {
  log "Verifying services..."
  systemctl is-active --quiet tailscaled && log "tailscaled active" || error_exit "tailscaled not active."
  systemctl is-active --quiet observiq-otel-collector && log "observiq-otel-collector active" || error_exit "observiq-otel-collector not active."
  log "Services verified."  
}

main() {
  check_sudo
  require_command curl; require_command bash; require_command systemctl; require_command base64
  check_internet
  create_user
  enable_ssh
  install_tailscale
  install_bindplane
  verify_services
  send_slack_notification
  log "${GREEN} OK. Bootstrap complete.${RESET}"
}

main "$@"
