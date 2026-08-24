# QuantInsight Pro - ModelScope 创空间 Docker 镜像
# 端口规则：必须 7860（8080 被平台占用）
FROM python:3.11-slim

# 中文字体（matplotlib 中文图表不乱码）+ curl（健康探测）
RUN apt-get update && apt-get install -y --no-install-recommends \
    fonts-noto-cjk \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 先装依赖（利用层缓存）
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    -i https://pypi.tuna.tsinghua.edu.cn/simple

# 应用代码 + 数据库（qi_data.db 已随仓库携带）
COPY . .

EXPOSE 7860

HEALTHCHECK --interval=30s --timeout=10s --start-period=90s --retries=3 \
    CMD curl -sf http://localhost:7860/ || exit 1

CMD ["streamlit", "run", "app.py", "--server.port=7860", "--server.address=0.0.0.0", "--server.headless=true"]
