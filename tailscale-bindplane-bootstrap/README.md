# Pattern: Tailscale + Bindplane Zero-Touch Onboarding

---

OLD SHELL SCRIPT. USE GOLANG VERSION IN THIS REPOSITORY.

---

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

## Filling up script Args

- `PREFIX`: Optional. A prefix for tailscale node name ($prefix-$hostname)
-   - For example, $PREFIX = "PROD", the tailscale nodename orhost becomes "PROD-$hostname" → (PROD-node01).
- `USERNAME`: User to add to the server. This user will be added to the Linux box, and it's the one we will SSH as via Tailscale.
- `B64PASS_STD`: Encoded B64 password (`echo 'mypassword' | base64`). This is not for security but for operability.
- `TAILSCALE_AUTH_KEY`: Well, Tailscale's authentication key.
- `BINDPLANE_SCRIPT_URL`: Updated Bindplane agent version URL Download.
    - i.e. `https://github.com/observIQ/bindplane-agent/releases/download/v1.76.3/install_unix.sh` (The versions get updated constantly, and it's generated automatically in Bindplane console)
- `SLACK_CNL`: Slack channel to send Webhooks to.
- `BINDPLANE_ARGS`: Given by ObservIQ's Bindplane UI when installing a new Linux agent. 

## Security 

The usefulness of this script, and its secure usage only works under certain circumstances. Threat model accordingly, and use responsibly.

Perhaps, for Cloud environments, it can be adapted (Or translated to Python) to leverage Cloud's SDKs to pull secrets from such services (Secret Managers) via VM's Roles. 

It is assumed that the user has already covered:

- As this script contains sensitive data, a way to securely host this script is necessary, and allow it to be accessible ONLY by the intended server is needed.
- In hostile environments: A tight ACL setup in Tailscale so that the "controller" machine cannot be accessed by "agent machines", AND this "agents" cannot access each other either.
    - A sample ACL is provided
- Note: Also, in hostile environments, the "controller" machine should also be an isolated system.

## Sample usage
```bash
    curl -s https://your.link/bootstrap.sh | sudo bash
```
