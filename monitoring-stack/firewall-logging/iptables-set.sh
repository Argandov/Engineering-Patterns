#!/bin/bash

# For each port we want to monitor, we run:
# Run: ./iptables-set.sh 443

PORT=$1
PROTO="tcp"
echo "Adding iptables rule for TCP port $PORT..."
sudo iptables -C INPUT -p tcp --dport "$PORT" -j ACCEPT 2>/dev/null || \
sudo iptables -A INPUT -p tcp --dport "$PORT" -j ACCEPT -m comment --comment "Monitor $PROTO $PORT"
