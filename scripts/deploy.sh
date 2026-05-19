#!/bin/bash
# Deploys Settlement Monitor to IONOS VPS and installs as a systemd service.
set -e

SERVER_IP="74.208.242.240"
SERVER_USER="root"
SERVER_PASS="S4aqdCL2TsBhEjgq"
REMOTE_DIR="/opt/settlements"
PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

echo "=== Settlement Monitor — Deploying to $SERVER_IP ==="

# Install sshpass if needed (used for password-based SSH/rsync)
if ! command -v sshpass &>/dev/null; then
  echo "Installing sshpass..."
  brew install sshpass 2>/dev/null || {
    echo "Error: sshpass not found and brew install failed."
    echo "Install manually: brew install hudochenkov/sshpass/sshpass"
    exit 1
  }
fi

SSH="sshpass -p $SERVER_PASS ssh -o StrictHostKeyChecking=no $SERVER_USER@$SERVER_IP"
RSYNC="sshpass -p $SERVER_PASS rsync -avz --exclude venv --exclude __pycache__ --exclude '*.pyc' --exclude logs --exclude settlements.db -e 'ssh -o StrictHostKeyChecking=no'"

# ── 1. Copy project files ──────────────────────────────────────────────────
echo ""
echo ">>> Copying project files..."
eval "$RSYNC $PROJECT_DIR/ $SERVER_USER@$SERVER_IP:$REMOTE_DIR/"

# ── 2. Remote setup ────────────────────────────────────────────────────────
echo ""
echo ">>> Running remote setup..."
$SSH bash <<'REMOTE'
set -e

REMOTE_DIR="/opt/settlements"
cd "$REMOTE_DIR"

echo "--- Updating apt..."
apt-get update -qq
apt-get install -y -qq python3 python3-pip python3-venv

echo "--- Creating virtual environment..."
python3 -m venv venv

echo "--- Installing Python dependencies..."
venv/bin/pip install -q --upgrade pip
venv/bin/pip install -q -r requirements.txt

echo "--- Installing Playwright Chromium..."
venv/bin/playwright install chromium
venv/bin/playwright install-deps chromium

echo "--- Creating logs directory..."
mkdir -p logs

REMOTE

# ── 3. Install systemd service ─────────────────────────────────────────────
echo ""
echo ">>> Installing systemd service..."
$SSH bash <<'REMOTE'
cat > /etc/systemd/system/settlements.service <<EOF
[Unit]
Description=Settlement Monitor
After=network.target

[Service]
Type=simple
WorkingDirectory=/opt/settlements
ExecStart=/opt/settlements/venv/bin/python main.py daemon
Restart=always
RestartSec=30
StandardOutput=append:/opt/settlements/logs/monitor.log
StandardError=append:/opt/settlements/logs/monitor.err

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable settlements
systemctl restart settlements

sleep 3
systemctl status settlements --no-pager
REMOTE

echo ""
echo "✓ Deployed and running on $SERVER_IP"
echo ""
echo "Watch logs:    ssh root@$SERVER_IP 'tail -f /opt/settlements/logs/monitor.log'"
echo "Stop service:  ssh root@$SERVER_IP 'systemctl stop settlements'"
echo "Start service: ssh root@$SERVER_IP 'systemctl start settlements'"
