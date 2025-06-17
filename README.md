# Engineering Patterns (Monorepo)

A monorepo consisting of a curated collection of infrastructure and automation patterns from the field.

Each folder contains a reproducible implementation of a high-leverage solution, designed for clarity, portability, and reuse. Each project corresponds to independent projects I've built. 

General scripts and engineering *blueprints*.

---

## Contents

| Pattern | Description |
|--------|-------------|
| `tailscale-bindplane-bootstrap-golang/` | Go lang Zero-touch onboarding for log agents using Tailscale mesh + Bindplane |
| `iris-serverless-security-pipeline` | Serverless ETL pipeline using Cloud Run to ingest, transform, and ship logs to GCP Storage with Slack alerts. |
| `monitoring-stack` | Monitoring stack with Grafana, Prometheus, Loki elements inside Tailscale, with additional custom Prometheus exporters for network traffic metrics
| `zero-trust-vpn-gateway/` | Blueprint for routing home lab traffic through a secure ProtonVPN gateway |
| `tailscale-bindplane-bootstrap/` | (DEPRECATED: Old, less secure) Zero-touch onboarding for log agents using Tailscale mesh + Bindplane |

---

## What is a Pattern?

An Engineering Pattern is a repeatable solution to a common problem in ops, security, or automation.

Each one includes:
- A clear problem statement
- A battle-tested solution
- Implementation details (code, diagrams, configs)
- Key insights and learnings

---

## Why This Repo?

This repo exists to:
- Capture brainchilds born from real patterns
- Make my tooling portable and reusable, instead of having 1 repo for every pattern
