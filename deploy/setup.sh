#!/usr/bin/env bash
# QuantInsight Pro · ECS 首次/更新部署（CentOS 7.9）
# 用法: bash deploy/setup.sh
set -euo pipefail

REPO="${REPO:-https://github.com/yigenfeng0707-netizen/quantinsight-pro.git}"
REPO_DIR="${REPO_DIR:-/opt/quantinsight-repo}"
APP_DIR="${APP_DIR:-/opt/quantinsight}"
DOMAIN="${DOMAIN:-3blue1brownlab.cn}"
# 默认安装目标；若已存在 conda/miniconda 则自动复用，不会重复安装
CONDA_INSTALL_PREFIX="${CONDA_INSTALL_PREFIX:-/opt/miniconda3}"

# 查找已有 conda/miniconda，返回安装根目录；未找到则返回空
resolve_conda_prefix() {
  local candidate base
  for candidate in \
    "${CONDA_INSTALL_PREFIX}" \
    /opt/miniconda3 /opt/conda /usr/local/miniconda3 \
    "${HOME}/miniconda3" "${HOME}/anaconda3"; do
    if [ -n "$candidate" ] && [ -x "$candidate/bin/python" ]; then
      echo "$candidate"
      return 0
    fi
  done
  if command -v conda >/dev/null 2>&1; then
    base="$(conda info --base 2>/dev/null || true)"
    if [ -n "$base" ] && [ -x "$base/bin/python" ]; then
      echo "$base"
      return 0
    fi
  fi
  return 1
}

echo "==> [1/9] 系统依赖..."
yum install -y git nginx wget gcc gcc-c++ 2>&1 | tail -3
if ! swapon --show | grep -q swapfile; then
  echo "    添加 2G swap（低内存服务器防 OOM）..."
  fallocate -l 2G /swapfile 2>/dev/null || dd if=/dev/zero of=/swapfile bs=1M count=2048 status=progress
  chmod 600 /swapfile && mkswap /swapfile && swapon /swapfile
  grep -q '/swapfile' /etc/fstab || echo '/swapfile none swap sw 0 0' >> /etc/fstab
fi

echo "==> [2/9] Python 环境（复用已有 conda，不重复安装）..."
if CONDA="$(resolve_conda_prefix)"; then
  echo "    Miniconda/Conda 已存在，跳过安装: $CONDA"
else
  CONDA="$CONDA_INSTALL_PREFIX"
  echo "    未检测到 Conda，首次安装 Miniconda3-py39 到 $CONDA ..."
  wget -q https://repo.anaconda.com/miniconda/Miniconda3-py39_4.12.0-Linux-x86_64.sh -O /tmp/miniconda.sh
  bash /tmp/miniconda.sh -b -p "$CONDA"
  rm -f /tmp/miniconda.sh
fi
"$CONDA/bin/python" --version

echo "==> [3/9] 拉取代码..."
if [ -d "$REPO_DIR/.git" ]; then
  cd "$REPO_DIR" && git pull --ff-only origin main && cd -
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

echo "==> [5/9] 安装 Python 依赖（pip wheel，约 5-8 分钟）..."
PIP="$CONDA/bin/pip"
"$PIP" install -q -U pip wheel setuptools
"$PIP" install -q --only-binary=:all: pyarrow==14.0.2 || "$PIP" install -q pyarrow==14.0.2
"$PIP" install -q numpy==1.24.4
"$PIP" install -q pandas==2.0.3 scipy==1.10.1
"$PIP" install -q matplotlib==3.7.5 scikit-learn==1.3.2
"$PIP" install -q streamlit==1.28.2 plotly==5.18.0 openpyxl requests bcrypt jieba
"$PIP" install -q xgboost==2.0.3
"$PIP" install -q shap==0.44.1
"$PIP" install -q akshare snownlp

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
