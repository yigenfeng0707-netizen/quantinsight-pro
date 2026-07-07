#!/usr/bin/env bash
# 仅切换 nginx 域名/SSL（不重装依赖）
# 用法: DOMAIN=3blue1brownlab.cn bash deploy/apply-domain.sh
set -euo pipefail

DOMAIN="${DOMAIN:-3blue1brownlab.cn}"
REPO_DIR="${REPO_DIR:-/opt/quantinsight-repo}"

mkdir -p /etc/nginx/ssl /var/www/acme
if [ -f "/etc/nginx/ssl/www.${DOMAIN}.pem" ]; then
  echo "使用已有 SSL: /etc/nginx/ssl/www.${DOMAIN}.pem"
  cp -f "$REPO_DIR/deploy/nginx-quantinsight.conf" /etc/nginx/conf.d/quantinsight.conf
else
  echo "未找到 SSL，使用 HTTP 模式"
  cp -f "$REPO_DIR/deploy/nginx-quantinsight-http.conf" /etc/nginx/conf.d/quantinsight.conf
fi
rm -f /etc/nginx/conf.d/default.conf 2>/dev/null || true
nginx -t
systemctl restart nginx
echo "Demo: http://${DOMAIN}/ (SSL 证书存在时亦支持 https://${DOMAIN}/)"
curl -sf "http://127.0.0.1:8501/_stcore/health" && echo " streamlit ok"
