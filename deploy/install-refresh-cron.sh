#!/usr/bin/env bash
# 安装 QuantInsight 数据刷新 cron (root)
set -euo pipefail

APP_DIR="${APP_DIR:-/opt/quantinsight}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CRON_SRC="${CRON_SRC:-${SCRIPT_DIR}/quantinsight-refresh.cron}"
CRON_DST="/etc/cron.d/quantinsight-refresh"

mkdir -p "${APP_DIR}/logs"
touch "${APP_DIR}/logs/refresh.log"
chmod 644 "${APP_DIR}/logs/refresh.log"

if [ -f "${CRON_DST}" ]; then
  chmod 644 "${CRON_DST}"
elif [ -f "${CRON_SRC}" ]; then
  install -m 644 "${CRON_SRC}" "${CRON_DST}"
else
  echo "missing cron file: ${CRON_SRC} or ${CRON_DST}" >&2
  exit 1
fi

# CentOS 7: cron.d 文件需无多余空行导致解析问题，并重启 crond
if systemctl is-active crond >/dev/null 2>&1; then
  systemctl restart crond
elif systemctl is-active cron >/dev/null 2>&1; then
  systemctl restart cron
else
  systemctl enable crond 2>/dev/null || systemctl enable cron 2>/dev/null || true
  systemctl start crond 2>/dev/null || systemctl start cron 2>/dev/null || true
fi

echo "已安装 ${CRON_DST}"
echo "日志: ${APP_DIR}/logs/refresh.log"
echo ""
echo "当前 cron 配置:"
cat "${CRON_DST}"
echo ""
echo "验证 crond:"
systemctl is-active crond 2>/dev/null || systemctl is-active cron 2>/dev/null || echo "crond status unknown"
