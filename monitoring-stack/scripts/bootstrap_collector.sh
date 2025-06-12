# Install node_exporter for Prometheus to scrape
curl -L https://github.com/prometheus/node_exporter/releases/download/v1.8.1/node_exporter-1.8.1.linux-amd64.tar.gz \
 | tar -xz -C /usr/local/bin --strip-components=1 node_exporter-*/node_exporter
sudo useradd -r -s /sbin/nologin nodeexp
cat <<'EOF' | sudo tee /etc/systemd/system/node_exporter.service
[Unit] Description=Node exporter
[Service] User=nodeexp ExecStart=/usr/local/bin/node_exporter
[Install] WantedBy=multi-user.target
EOF
sudo systemctl daemon-reload && sudo systemctl enable --now node_exporter
