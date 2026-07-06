#!/usr/bin/env bash
# QuantInsight Pro · ECS 首次/更新部署（CentOS 7.9）
# 用法: bash deploy/setup.sh
set -euo pipefail

REPO="${REPO:-https://github.com/yigenfeng0707-netizen/quantinsight-pro.git}"
REPO_DIR="${REPO_DIR:-/opt/quantinsight-repo}"
APP_DIR="${APP_DIR:-/opt/quantinsight}"
DOMAIN="${DOMAIN:-quantinsight.cn}"
CONDA="${CONDA:-/opt/miniconda3}"

echo "==> [1/9] 系统依赖..."
yum install -y git nginx wget 2>&1 | tail -3

echo "==> [2/9] Python 3.11 (Miniconda)..."
if [ ! -x "$CONDA/bin/python" ]; then
  wget -q https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O /tmp/miniconda.sh
  bash /tmp/miniconda.sh -b -p "$CONDA"
fi
"$CONDA/bin/conda" install -y python=3.11 pip 2>&1 | tail -5

echo "==> [3/9] 拉取代码..."
if [ -d "$REPO_DIR/.git" ]; then
  git -C "$REPO_DIR" pull --ff-only origin main
else
  rm -rf "$REPO_DIR"
  git clone "$REPO" "$REPO_DIR"
fi

echo "==> [4/9] 同步 streamlit_app -> $APP_DIR ..."
mkdir -p "$APP_DIR/data" "$APP_DIR/.streamlit"
rsync -a --delete \
  --exclude '__pycache__' --exclude '.pytest_cache' --exclude '*.pyc' \
  "$REPO_DIR/streamlit_app/" "$APP_DIR/"
cp -f "$REPO_DIR/deploy/requirements-prod.txt" "$APP_DIR/requirements-prod.txt"

echo "==> [5/9] 安装 Python 依赖（约 3-5 分钟）..."
"$CONDA/bin/pip" install -q -U pip
"$CONDA/bin/pip" install -q -r "$APP_DIR/requirements-prod.txt"

echo "==> [6/9] 初始化管理员..."
cd "$APP_DIR"
"$CONDA/bin/python" -m admin.bootstrap_admin || true

echo "==> [7/9] systemd + nginx..."
cp -f "$REPO_DIR/deploy/quantinsight.service" /etc/systemd/system/quantinsight.service
systemctl daemon-reload
systemctl enable quantinsight

mkdir -p /etc/nginx/ssl /var/www/acme
if [ -f "/etc/nginx/ssl/www.${DOMAIN}.pem" ]; then
  cp -f "$REPO_DIR/deploy/nginx-quantinsight.conf" /etc/nginx/conf.d/quantinsight.conf
else
  echo "提示: 未检测到 SSL，先用 HTTP 模式 + ACME"
  cp -f "$REPO_DIR/deploy/nginx-quantinsight-http.conf" /etc/nginx/conf.d/quantinsight.conf
fi
rm -f /etc/nginx/conf.d/default.conf 2>/dev/null || true
nginx -t
systemctl enable nginx
systemctl restart nginx

systemctl restart quantinsight

echo "==> [8/9] 健康检查..."
sleep 8
systemctl is-active quantinsight || (journalctl -u quantinsight --no-pager -n 30; exit 1)
curl -sf http://127.0.0.1:8501/_stcore/health && echo " streamlit ok" || echo " streamlit starting..."

echo "==> [9/9] SSL（可选）..."
if [ ! -f "/etc/nginx/ssl/www.${DOMAIN}.pem" ] && [ -x /root/.acme.sh/acme.sh ]; then
  bash "$REPO_DIR/deploy/ssl-acme.sh" || echo "SSL 申请跳过，可稍后手动运行 deploy/ssl-acme.sh"
fi

echo ""
echo "部署完成"
echo "  应用目录: $APP_DIR"
echo "  代码仓库: $REPO_DIR"
echo "  域名: https://${DOMAIN}/"
echo "  日志: journalctl -u quantinsight -f"
