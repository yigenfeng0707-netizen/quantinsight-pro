#!/bin/bash
set -e
echo "=== QuantInsight Pro Deploy ==="
cd /opt/quantinsight

echo "[1/5] Pulling latest code..."
git pull origin main

echo "[2/5] Installing dependencies..."
pip install bcrypt>=4.0.0 2>&1 | tail -3

echo "[3/5] Creating admin account..."
cd streamlit_app
python -m admin.bootstrap_admin

echo "[4/5] Restarting service..."
systemctl restart quantinsight

echo "[5/5] Checking service status..."
sleep 3
systemctl is-active quantinsight
echo ""
echo "=== Deploy Complete ==="
