#!/usr/bin/env bash
# 为 quantinsight.cn 申请 Let's Encrypt 证书（CentOS 7 + acme.sh）
set -euo pipefail

DOMAIN="${DOMAIN:-quantinsight.cn}"
REPO_DIR="${REPO_DIR:-/opt/quantinsight-repo}"
EMAIL="${SSL_EMAIL:-admin@${DOMAIN}}"

if ! command -v acme.sh &>/dev/null; then
  curl -fsSL https://get.acme.sh | sh -s email="$EMAIL"
  source ~/.bashrc 2>/dev/null || true
fi

mkdir -p /var/www/acme /etc/nginx/ssl

# 确保 HTTP 模式 nginx 运行
cp -f "$REPO_DIR/deploy/nginx-quantinsight-http.conf" /etc/nginx/conf.d/quantinsight.conf
nginx -t && systemctl reload nginx

~/.acme.sh/acme.sh --issue -d "$DOMAIN" -d "www.${DOMAIN}" -w /var/www/acme --force

~/.acme.sh/acme.sh --install-cert -d "$DOMAIN" \
  --key-file "/etc/nginx/ssl/www.${DOMAIN}.key" \
  --fullchain-file "/etc/nginx/ssl/www.${DOMAIN}.pem" \
  --reloadcmd "cp -f $REPO_DIR/deploy/nginx-quantinsight.conf /etc/nginx/conf.d/quantinsight.conf && nginx -t && systemctl reload nginx"

cp -f "$REPO_DIR/deploy/nginx-quantinsight.conf" /etc/nginx/conf.d/quantinsight.conf
nginx -t && systemctl reload nginx
echo "SSL 已安装: /etc/nginx/ssl/www.${DOMAIN}.pem"
