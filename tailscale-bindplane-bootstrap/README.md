# Pattern: Tailscale + Bindplane Zero-Touch Onboarding

## Problem

Onboarding log ingestion agents across isolated client networks with secure access, minimal setup, and strict isolation.
This is a blueprint for initial installation of Tailscale and Bindplane agents for Zero Trust remote administration and monitoring.

## Solution

This pattern uses:

- Tailscale for mesh connectivity
- Bindplane for agent or server monitoring
- A bootstrap script that installs both with required tokens

## Purpose

This approach enables:

- Zero-touch deployment in distributed environments
- Strong security boundaries per tenant

## Security requirements

It is assumed that the user has already covered:

- This script contains sensitive data. A way to securely host this script, and be accessible ONLY from the intended server is needed.
- In hostile environments: A tight ACL setup in Tailscale so that the "controller" machine cannot be accessed by "agent machines", AND this "agents" cannot access each other either.
    - A sample ACL is provided
- Note: Also, in hostile environments, the "controller" machine should be an isolated system.

## Usage
```bash
    curl -s https://your.link/bootstrap.sh | sudo bash
```
