# Pattern: Tailscale + Bindplane Zero-Touch Onboarding

## PROGRAM OVERVIEW:

This program does the following:

- Performs some initial checks:
    - User under which the program is running exists has sudo permissions
    - Server has internet access and can retrieve Tailscale and Bindplane install scripts by calling this URLS.

- Creates a user, which name is hardcoded in the YAML file
    - Sets a password -> Passed in as environment variable Base64 encoded
    - Places user in sudoers
- Enables SSH and runs ssh server
- Installs Tailscale

- Upon success or failure, sends a Slack notification via Webhook. 
-
![Slack webhook notification screenshot](/img/webhook.png)

## EXECUTION

Running:

```bash
sudo ./bootstrap -i $C_ID -u $USERNAME -p $B64_PASSWORDK -w $OPAMP_ENDPOINT -k $BP_KEY -v $BP_VERSION -c $BP_CONFIG -K $TS_KEY -s $SLACK_WEBHOOK_ENDPOINT
```

Where:
- C_ID: A prefix for our Tailscale agents. i.e. Tailscale agents become $C_ID-$hostname. For example, `homelab-webserver01`
- USERNAME: The new username we need for our system,
- B64_PASSWORD: Encoded password this program will assign to our user,
- OPAMP_ENDPOINT: The Bindplane endpoint, WITHOUT `ws://`. i.e. "app.bindplane.com/v1/opamp"
- BP_KEY: Bindplane Key
- BP_VERSION: Bindplane version. This will be passed at installation, and also to the download url at Github. i.e. `1.72.3`
- BP_CONFIG: Full Configuration string. For example, "`configuration=homelab,installid=<UUID>`"
- TS_KEY: Tailscale key. Format: "`tskey-auth-<key>"`
- WEBHOOK: Slack Webhook endpoint. ONLY the path. For example, `FAT02THA0XS/HDPOUN71SHG9/JHFNBIO8YHBN8NN0FE80PJD0F7mTK`

### Helper Scripts

- `build.sh` -> Auto Go Build for Linux amd/arm64, and MacOS (ARM64)
- `cleanup.sh` -> This uninstalls everything, including deleting the user created.

## Problem

Onboarding log ingestion agents across isolated client networks with secure access, minimal setup, and strict isolation.
This is a blueprint for initial installation of Tailscale and Bindplane agents for Zero Trust remote administration and monitoring.

I haven't figured out yet a name for classifying the "controller" and "client" nodes. This script installs "client" nodes in Tailscale. A clear distinction in Tailscale ACLs could be `tag:admin` and `tag:client`.

This script is ONLY to be used between trusted systems and strictly inside trust boundaries, as it contains sensitive data. Also, it can be used for one-shot deployments or for short burst periods (I.e. temporary Tailscale auth keys, temporary or even authenticated file sharing between client and script fileserver, etc). See Security section below.

## Solution

This pattern uses:

- Tailscale for mesh connectivity
- Bindplane for agent or server monitoring
- A bootstrap script that installs both with required tokens

This is often used when I need to bootstrap servers on Virtualized or even Cloud environments. Bindplane is optional, but required when I have a centralized monitoring solution (The bindplane configuration will depend on the use case, and this bootstrap script will only install the agent). 

## Purpose

This approach enables:

- Zero-touch deployment in distributed environments
- Strong security boundaries per tenant

