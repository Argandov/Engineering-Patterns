#!/bin/bash

# Custom exporter for iptables logging.
# Customize the desired list of ports so it mirrors the iptables-set.sh script executed earlier. 
SYSLOG_PORTS=(61001 61002 61003)

# "Client" (See README.md)
CLI=$(tailscale status --json | jq -r '.Self.DNSName' | cut -d'.' -f1 | cut -d'-' -f1)
# Tailscale's hostname
HOST=$(tailscale status --json | jq -r '.Self.DNSName' | cut -d'.' -f1)

OUT="/var/lib/prometheus/node-exporter/bindplane_ports.prom"
: > "$OUT"  # Truncate file

for port in "${SYSLOG_PORTS[@]}"; do
    line=$(sudo iptables -L -v -n -x | grep "dpt:$port" | grep -i "Monitor TCP $port" | head -n1)

    if [[ -n "$line" ]]; then
        pkts=$(echo "$line" | awk '{print $1}')
        bytes=$(echo "$line" | awk '{print $2}')
        echo "syslog_port_packets_total{port=\"$port\", client=\"$CLI\", collector=\"$HOST\"} $pkts" >> "$OUT"
        echo "syslog_port_bytes_total{port=\"$port\", client=\"$CLI\", collector=\"$HOST\"} $bytes" >> "$OUT"
    else
        echo "!! No iptables rule found for port $port with comment 'Monitor TCP $port'"
    fi
done
