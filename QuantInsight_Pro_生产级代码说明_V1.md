# QuantInsight Pro - 生产级数据采集模块说明

**项目**: QuantInsight Pro
**项目编号**: 2026FINTECH-FINT-0093
**版本**: V1.0
**日期**: 2026-06-06
**许可**: MIT License

---

## 1. 模块定位

`data_pipeline.py` 是 QuantInsight Pro 投研平台的生产级数据采集层, 提供:
- **多数据源**: Akshare (生产) / CSV (回放) / 抽象基类 (扩展)
- **3 大数据类型**: 指数 / 申万行业 / 行业成分股
- **生产特性**: 重试 / 断点续传 / 校验 / 监控 / 并发
- **异步**: asyncio + 协程, 高并发不阻塞

## 2. 核心组件

### 2.1 PipelineConfig (配置)

| 字段 | 默认值 | 说明 |
|------|--------|------|
| max_retries | 3 | 最大重试次数 |
| retry_base_delay | 1.0s | 指数退避基数 |
| rate_limit_per_sec | 10 | 每秒限流 |
| enable_checkpoint | True | 启用断点续传 |
| enable_validation | True | 启用数据校验 |
| enable_prometheus | True | 启用监控 |

### 2.2 DataSource (抽象基类)

3 个数据源实现:
- **AkshareSource**: A 股免费数据 (生产)
- **CSVSource**: 本地文件 (测试/回放)
- **基类**: 自定义数据源

### 2.3 CheckpointManager (断点续传)

- 本地 JSON 存储, 原子写入
- 多任务 key 隔离
- 启动时自动恢复

### 2.4 DataValidator (数据校验)

5 项校验:
1. 必填列 (date, close)
2. 空值过滤
3. 负价格过滤
4. 涨跌幅合理性 (≤20%)
5. 数据点数量 (≥30)

### 2.5 MetricsRegistry (监控)

内存版 Prometheus:
- Counter: 请求总数 (按 status/context 分组)
- Gauge: 队列大小
- Histogram: 请求延迟 (mean/p50/p95/p99)

### 2.6 DataPipeline (主类)

核心 API:
- `fetch_index_data(symbol, start, end)`: 拉取指数
- `fetch_sw_industries()`: 申万行业
- `fetch_industry_constituents(code)`: 行业成分股
- `fetch_batch(symbols, max_concurrent)`: 批量并发

## 3. 使用示例

### 3.1 同步 (CLI 友好)

```python
import asyncio
from data_pipeline import DataPipeline, AkshareSource, PipelineConfig

source = AkshareSource(rate_limit=5)
pipeline = DataPipeline(source, PipelineConfig(checkpoint_dir="./ckpt"))

async def main():
    df = await pipeline.fetch_index_data("hs300", "2020-01-01", "2025-12-31")
    print(df.head())
    print(pipeline.get_metrics())

asyncio.run(main())
```

### 3.2 批量并发

```python
results = await pipeline.fetch_batch(
    ["hs300", "zz500", "cyb"],
    "2020-01-01",
    "2025-12-31",
    max_concurrent=3,
)
for sym, df in results.items():
    print(f"{sym}: {len(df)} points")
```

### 3.3 错误处理

```python
from data_pipeline import DataSourceError, NetworkError, DataValidationError

try:
    df = await pipeline.fetch_index_data("invalid", "2020-01-01")
except NetworkError as e:
    print(f"网络错误: {e}")
except DataValidationError as e:
    print(f"数据校验错误: {e}")
except DataSourceError as e:
    print(f"其他错误: {e}")
```

## 4. 单元测试 (14 测试 100% 通过)

```bash
$ python -m pytest test_data_pipeline.py -v

collected 14 items

test_checkpoint_manager             PASSED
test_data_validator_valid           PASSED
test_data_validator_empty           PASSED
test_data_validator_missing_columns PASSED
test_data_validator_negative_prices PASSED
test_data_validator_too_few_points  PASSED
test_data_validator_drop_na         PASSED
test_metrics_registry               PASSED
test_csv_source_index               PASSED
test_csv_source_date_filter         PASSED
test_csv_source_missing_file        PASSED
test_pipeline_end_to_end            PASSED
test_pipeline_error_handling        PASSED
test_pipeline_batch                 PASSED

============================= 14 passed in 2.86s ==============================
```

## 5. 与 Streamlit App 集成

`streamlit_app/app.py` 已使用此模块:

```python
from data_pipeline import DataPipeline, AkshareSource, PipelineConfig
import streamlit as st

@st.cache_data(ttl=3600)
def load_index(symbol):
    source = AkshareSource(rate_limit=5)
    pipeline = DataPipeline(source, PipelineConfig(checkpoint_dir="./ckpt"))
    return asyncio.run(pipeline.fetch_index_data(symbol))

# 页面调用
df = load_index("hs300")
st.line_chart(df.set_index("date")["close"])
```

## 6. 生产部署建议

### 6.1 Docker 化

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY backtest_engine.py data_pipeline.py ./
CMD ["python", "-m", "data_pipeline", "fetch"]
```

### 6.2 K8s 部署

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: data-pipeline
spec:
  replicas: 2
  template:
    spec:
      containers:
      - name: pipeline
        image: quantinsight/data-pipeline:v1.0
        resources:
          requests:
            memory: "256Mi"
            cpu: "500m"
        volumeMounts:
        - name: ckpt
          mountPath: /app/ckpt
      volumes:
      - name: ckpt
        persistentVolumeClaim:
          claimName: checkpoint-pvc
```

### 6.3 监控集成

```python
# 替换内置 MetricsRegistry 为 prometheus_client
from prometheus_client import Counter, Histogram, start_http_server

requests_total = Counter('pipeline_requests_total', 'Total requests', ['status'])
latency = Histogram('pipeline_request_duration_seconds', 'Request latency')

# 在 fetch 方法中:
requests_total.labels(status='success').inc()
latency.observe(elapsed)
```

## 7. 性能基准

测试环境: Windows 11 / Python 3.12 / 单核

| 操作 | 数据量 | 耗时 |
|------|--------|------|
| 单指数拉取 (首次) | 2,767 点 | ~2s |
| 单指数拉取 (checkpoint) | 2,767 点 | <0.1s |
| 批量 3 指数并发 | 3 × 2,767 点 | ~3s |
| 校验 2,767 点 | - | ~0.05s |
| 监控 1,000 请求 | - | <0.01s |

## 8. 局限与未来

| 局限 | 未来增强 |
|------|----------|
| akshare 限流 10 req/s | 接入 Tushare Pro (5000 req/min) |
| 内存监控 | 替换为 prometheus_client |
| 无增量更新 | 支持增量拉取 (增量 checkpoint) |
| 无数据质量评分 | 加入数据质量评分 (DQ) |
| 单机部署 | 分布式 (Celery / Ray) |

## 9. 学术引用

```bibtex
@software{quantinsight_data_pipeline_2026,
  author = {冯亦根, 王宇寒, 官馨, 梁理智},
  title  = {QuantInsight Pro: Production-Grade Data Pipeline for China A-Share Quantitative Research},
  year   = {2026},
  url    = {https://github.com/yigenfeng0707-netizen/quantinsight-pro},
  note   = {Data pipeline v1.0.0, MIT License}
}
```

---

**版本**: V1.0.0
**日期**: 2026-06-06
**许可**: MIT License
**测试**: 14 单元测试, 100% 通过
