# Tailscale + BindPlane Zero-Touch Bootstrap

> **Note:** This documentation was enhanced with AI assistance to improve clarity and organization.

A Go-based bootstrap utility for automated deployment of Tailscale mesh networking and BindPlane monitoring agents across distributed environments.

## Overview

This tool automates the complete setup process for remote systems by:

- **System Preparation**: Validates prerequisites and creates secure user accounts
- **SSH Configuration**: Ensures SSH service is running and properly configured  
- **Tailscale Installation**: Sets up mesh networking with automatic device registration
- **BindPlane Agent**: Deploys monitoring agent with custom configuration
- **Service Verification**: Confirms all components are running correctly
- **Slack Notifications**: Provides real-time deployment status updates

![Deployment Notification](./img/webhook.png)

## Quick Start

### Prerequisites

- Linux system with internet connectivity
- Root/sudo access
- Valid Tailscale auth key
- BindPlane endpoint and API key
- Slack webhook URL (optional)

### Installation

Download the appropriate binary from releases or build locally:

```bash
# Build for multiple platforms
./build.sh

# Run cleanup if needed
./cleanup.sh
```

### Usage

```bash
sudo ./bootstrap-linux-amd64 \
  -i <client-id> \
  -u <username> \
  -p <base64-password> \
  -w <bindplane-endpoint> \
  -k <bindplane-key> \
  -v <bindplane-version> \
  -c <bindplane-config> \
  -K <tailscale-key> \
  -s <slack-webhook>
```

### Example

```bash
sudo ./bootstrap-linux-amd64 \
  -i homelab \
  -u hl-user \
  -p 'cGFzc3dvcmQxMjMK' \
  -w 'app.bindplane.com/v1/opamp' \
  -k 'DEADBEEFC8D775H07XWQ3X' \
  -v '1.76.4' \
  -c "configuration=LinuxCollectorAgent,install_id=deadbeef-d15c-420f-9ede-b1de5f57d6c4" \
  -K "tskey-auth-deadbeef-DEADBEEFNAUpShGkh5FN71Yai2a76H" \
  -s "DEADBEEF/B08D2NPSHG9/NO98hp0SptEFE80PDEADBEEF"
```

## Configuration Parameters

| Flag | Description | Example |
|------|-------------|---------|
| `-i` | Client ID prefix for Tailscale hostnames | `homelab` |
| `-u` | Username to create on target system | `hl-user` |
| `-p` | Base64-encoded password for new user | `cGFzc3dvcmQxMjMK` |
| `-w` | BindPlane OpAMP endpoint (without `ws://`) | `app.bindplane.com/v1/opamp` |
| `-k` | BindPlane API key | `DEADBEEFC8D775H07XWQ3X` |
| `-v` | BindPlane agent version | `1.76.4` |
| `-c` | BindPlane configuration string | `configuration=LinuxCollectorAgent` |
| `-K` | Tailscale authentication key | `tskey-auth-...` |
| `-s` | Slack webhook path (optional) | `TEAM/CHANNEL/TOKEN` |

## Use Cases

- **Zero-touch deployments** in cloud and virtualized environments
- **Secure remote administration** through Tailscale mesh networking
- **Centralized monitoring** with BindPlane observability
- **Multi-tenant isolation** with proper ACL boundaries

## Security Considerations

⚠️ **Important**: This tool is designed for trusted environments only.

- Contains sensitive authentication tokens
- Should be used within established trust boundaries
- Recommended for one-shot deployments or time-limited scenarios
- Consider using temporary Tailscale auth keys when possible

## Architecture

The tool follows a modular structure:

```
├── main.go              # CLI interface and orchestration
├── helpers/             # Utility functions
│   ├── checkers.go      # System validation
│   ├── downloader.go    # File retrieval
│   ├── executor.go      # Command execution
│   └── notifier.go      # Slack integration
├── pkg/                 # Core functionality
│   ├── bindplane.go     # BindPlane agent setup
│   ├── tailscale.go     # Tailscale installation
│   └── verify.go        # Service verification
└── system/              # System management
    ├── ssh.go           # SSH configuration
    └── user.go          # User management
```

## Development

### Building

```bash
# Build for all supported platforms
./build.sh

# Manual build
go build -o bootstrap .
```

### Dependencies

- Go 1.22.1+
- github.com/spf13/cobra for CLI

## License

See [LICENSE.md](LICENSE.md) for details.
