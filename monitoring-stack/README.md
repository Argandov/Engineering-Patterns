# Hades: Monitoring Stack

This engineering pattern is a skeleton for a monitoring stack with Grafana Loki, Prometheus and Grafana, and specific and custom log sources. "Hades" is the name I coined for this project. 

## Project Structure:

```
|-- docker-compose.yml
|-- grafana-dashboards-backup.sh
|-- grafana-data
|   |-- grafana-storage
|   `-- dashboards
|-- loki-data
|   `-- loki-config.yml
|-- prometheus-data
|   `-- prometheus.yml
`-- reload-config.sh
```
# Docker usage

This monitoring stack uses docker compose, and binds docker volumes to relative paths to our project.

# Tailscale usage

This architecture assumes everything is inside Tailscale, and tailnet machines have a hostname of `$CLIENT-$HOSTNAME`, where "client" might be the environment, or any logical categorization we desire to use (i.e. dev, prod, proxmox, homelab, etc.)

# Prometheus

## System setup

## Prometheus data ownership

```bash
# Nobody (Docker runs as nobody)
# Prometheus runs as "nobody" inside the container.
sudo chown -R 65534:65534 /home/user/prometheus-data/data
```

## prometheus.yml

**client:** Environment the machines are on
    - i.e. Dev, Prod, etc. In my case, it's Proxmox
    - This allows for fine grained filtering in PQL or Grafana
**collector:** The actual name of the server: Can be its hostname or any "alias" we want. i.e. "Proxmox main node"

## IPTABLES Exporters (Prometheus)

*Note: this relies on Tailscale assigning $CLIENT_$HOSTNAME as the TS Hostname*

## Conntrack exporter

For a given port specified in [Conntrack exporter](firewall-logging/conntrack_exporter.sh), this exporter will attempt to track down unique "sending" IP addresses, and they incoming bytes. This method is prone to errors due to how TCP Connections might be established and how Conntrack tracks them. 

- Number of active senders: syslog_active_senders_count
- Accumulated bytes per sender: syslog_active_senders_bytes{src="..."}

# Grafana

- Script for backing up Grafana dashboards by using Grafana's API

Note: Grafana's Password is specified in `docker-compose.yml` - It's a good idea to not use it this way, and let Grafana itself handle it. 

## **Grafana Data Ownership**

If, for some reason, we want to be able to manipulate Grafana's config files, and stay away from `grafana.db` and bind mount Docker volume, we can follow this steps.

**This gives our local user safe, passwordless write access to Grafana’s config files, without breaking Docker’s security model.**

Grafana runs as a user/group with **UID/GID 472** inside the Docker container. When we **bind-mount host folders** into the container (e.g., ./grafana-data/), files are created with UID:GID 472:472, which causes **permission issues for our regular user**.

To solve this **without using sudo all the time**, we “mimic” Grafana’s GID behavior on the host, and  **allow your user to safely manage Grafana files:**

```bash
# 1. Create the 'grafana' group with GID 472 (if it doesn't already exist)
sudo groupadd -g 472 grafana

# 2. Add your current user to the 'grafana' group
sudo usermod -aG grafana $USER
```

**Restart shell session after this**

```bash
**exec su -l $USER**
```

**or log out/in to apply group membership.**

**Set Group Permissions on Grafana Folders**

```bash
# Give read+write access to the group (Only after our group assignment has been actually applied)
sudo chmod -R g+rw grafana-data/

# Ensure new files inherit the group automatically
sudo find grafana-data/ -type d -exec chmod g+s {} +
```

Now any file or folder created inside grafana-data/ by Grafana will remain editable by you — no root tricks needed.

**Set umask for group-writable defaults**

To make sure files you create also play nice with the grafana group:

```bash
echo 'umask 002' >> ~/.bashrc
source ~/.bashrc
```

**Result**

- Grafana writes files with GID 472 (grafana)
- You are part of the grafana group
- No need for sudo or constant `chown`
