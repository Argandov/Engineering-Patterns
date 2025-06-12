#!/bin/bash

# Ensure conntrack accounting is enabled
#
# Only necessary once, and should already be persisted
# echo 1 | sudo tee /proc/sys/net/netfilter/nf_conntrack_acct

# Tailscale's "Client" and 
CLIENT=$(tailscale status --json | jq -r '.Self.DNSName' | cut -d'.' -f1 | cut -d'-' -f1)
HOST=$(tailscale status --json | jq -r '.Self.DNSName' | cut -d'.' -f1)

# Ports to monitor
PORTS=(61001 61002 61003)

# Debugging purposes, as conntrack is not as reliable sometimes:
OUT="./syslog_conntrack.prom"
#OUT="/var/lib/prometheus/node-exporter/syslog_conntrack.prom"
: > "$OUT"

for port in "${PORTS[@]}"; do
    declare -A ip_bytes=()

    while IFS= read -r line; do
        src=$(echo "$line" | grep -oP 'src=\K[\d.]+' | head -n1)
        bytes=$(echo "$line" | grep -oP 'bytes=\K\d+' | tr -d '[:space:]')

        [[ -n "$src" && -n "$bytes" && "$bytes" =~ ^[0-9]+$ ]] || continue
        ip_bytes["$src"]=$(( ${ip_bytes["$src"]:-0} + $bytes ))
    done < <(sudo conntrack -L 2>/dev/null | grep "dport=$port")

    # Export active sender count per port
    echo "syslog_active_senders_count{client=\"$CLIENT\", collector=\"$HOST\", port=\"$port\"} ${#ip_bytes[@]}" >> "$OUT"

    # Export bytes per source IP
    for ip in "${!ip_bytes[@]}"; do
        echo "syslog_active_senders_bytes{client=\"$CLIENT\", collector=\"$HOST\", port=\"$port\", src=\"$ip\"} ${ip_bytes[$ip]}" >> "$OUT"
    done
done
