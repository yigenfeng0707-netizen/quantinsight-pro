"""
QuantInsight Pro - 数据采集管道单元测试
========================================

测试覆盖:
1. test_checkpoint_manager: 断点续传
2. test_data_validator: 数据校验
3. test_metrics_registry: 监控指标
4. test_csv_source: CSV 数据源
5. test_pipeline_end_to_end: 端到端测试
6. test_pipeline_error_handling: 错误处理

运行: pytest test_data_pipeline.py -v
"""

import asyncio
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from data_pipeline import (
    DataPipeline,
    DataSource,
    DataValidator,
    DataValidationError,
    DataSourceError,
    CSVSource,
    PipelineConfig,
    CheckpointManager,
    MetricsRegistry,
)


# ============================================================================
# 异步辅助函数 (避免 pytest-asyncio 依赖)
# ============================================================================

def run_async(coro):
    """在同步上下文中运行异步协程"""
    return asyncio.run(coro)


# ============================================================================
# 测试 1: 断点续传
# ============================================================================

def test_checkpoint_manager():
    """测试 Checkpoint 的保存/加载/清除"""
    with tempfile.TemporaryDirectory() as tmpdir:
        cp = CheckpointManager(tmpdir)

        # 1. 初始状态: 无 checkpoint
        assert run_async(cp.load("test_key")) is None

        # 2. 保存
        run_async(cp.save("test_key", {"value": 42, "list": [1, 2, 3]}))

        # 3. 加载
        loaded = run_async(cp.load("test_key"))
        assert loaded is not None
        assert loaded["value"] == 42
        assert loaded["list"] == [1, 2, 3]

        # 4. 清除
        run_async(cp.clear("test_key"))
        assert run_async(cp.load("test_key")) is None

        # 5. 不存在的 key 返回 None
        assert run_async(cp.load("nonexistent")) is None


# ============================================================================
# 测试 2: 数据校验
# ============================================================================

def test_data_validator_valid():
    """测试有效数据校验"""
    validator = DataValidator()
    df = pd.DataFrame({
        "date": pd.date_range("2024-01-01", periods=100, freq="B"),
        "close": np.linspace(100, 110, 100),
    })
    validated = validator.validate(df, context="test")
    assert len(validated) == 100
    assert (validated["close"] > 0).all()


def test_data_validator_empty():
    """测试空数据报错"""
    validator = DataValidator()
    with pytest.raises(DataValidationError, match="为空"):
        validator.validate(pd.DataFrame(), context="empty")


def test_data_validator_missing_columns():
    """测试缺失列报错"""
    validator = DataValidator()
    df = pd.DataFrame({"wrong_col": [1, 2, 3]})
    with pytest.raises(DataValidationError, match="缺少"):
        validator.validate(df, context="invalid")


def test_data_validator_negative_prices():
    """测试负价格被过滤"""
    validator = DataValidator(min_data_points=10)  # 降低阈值便于测试
    n = 100
    df = pd.DataFrame({
        "date": pd.date_range("2024-01-01", periods=n, freq="B"),
        "close": [100.0 if i % 2 == 0 else -50.0 for i in range(n)],
    })
    validated = validator.validate(df, context="negative")
    # 负价格被移除
    assert (validated["close"] > 0).all()
    assert len(validated) == 50  # 100 中 50 个为负被移除


def test_data_validator_too_few_points():
    """测试数据点过少报错"""
    validator = DataValidator(min_data_points=30)
    df = pd.DataFrame({
        "date": pd.date_range("2024-01-01", periods=10, freq="B"),
        "close": np.linspace(100, 110, 10),
    })
    with pytest.raises(DataValidationError, match="过少"):
        validator.validate(df, context="short")


def test_data_validator_drop_na():
    """测试 NaN 被移除"""
    validator = DataValidator()
    df = pd.DataFrame({
        "date": pd.date_range("2024-01-01", periods=50, freq="B"),
        "close": [100.0 if i % 5 != 0 else np.nan for i in range(50)],
    })
    validated = validator.validate(df, context="nan")
    assert validated["close"].isna().sum() == 0
    assert len(validated) == 40  # 50 - 10 NaN


# ============================================================================
# 测试 3: 监控指标
# ============================================================================

def test_metrics_registry():
    """测试 Metrics 的 counter/gauge/histogram"""
    metrics = MetricsRegistry()

    # Counter
    run_async(metrics.inc_counter("requests", value=1))
    run_async(metrics.inc_counter("requests", value=3))
    exported = metrics.export()
    assert exported["counters"]["requests"] == 4

    # Counter with labels
    run_async(metrics.inc_counter("requests", value=2, labels={"status": "success"}))
    run_async(metrics.inc_counter("requests", value=1, labels={"status": "error"}))
    exported = metrics.export()
    assert exported["counters"]["requests{status=success}"] == 2
    assert exported["counters"]["requests{status=error}"] == 1

    # Gauge
    run_async(metrics.set_gauge("queue_size", 42))
    exported = metrics.export()
    assert exported["gauges"]["queue_size"] == 42

    # Histogram
    for v in [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]:
        run_async(metrics.observe_histogram("latency", float(v)))
    exported = metrics.export()
    hist = exported["histograms"]["latency"]
    assert hist["count"] == 10
    assert hist["mean"] == 5.5
    assert hist["p50"] == 5.5
    assert hist["p95"] > 9


# ============================================================================
# 测试 4: CSV 数据源
# ============================================================================

def test_csv_source_index(tmp_path):
    """测试 CSV 数据源拉取指数"""
    # 创建测试 CSV
    df = pd.DataFrame({
        "date": pd.date_range("2024-01-01", periods=100, freq="B"),
        "close": np.linspace(100, 110, 100),
    })
    csv_path = tmp_path / "_data_hs300_full.csv"
    df.to_csv(csv_path, index=False)

    source = CSVSource(str(tmp_path))
    loaded = source.fetch_index("hs300", "2024-01-01", "2024-12-31")
    assert len(loaded) == 100
    assert list(loaded.columns) == ["date", "close"]


def test_csv_source_date_filter(tmp_path):
    """测试日期过滤"""
    df = pd.DataFrame({
        "date": pd.date_range("2024-01-01", periods=250, freq="B"),  # 1 年
        "close": np.linspace(100, 110, 250),
    })
    (tmp_path / "_data_hs300_full.csv").write_text(df.to_csv(index=False))

    source = CSVSource(str(tmp_path))
    loaded = source.fetch_index("hs300", "2024-06-01", "2024-08-31")
    assert len(loaded) > 0
    assert loaded["date"].min() >= pd.Timestamp("2024-06-01")
    assert loaded["date"].max() <= pd.Timestamp("2024-08-31")


def test_csv_source_missing_file(tmp_path):
    """测试文件不存在报错"""
    source = CSVSource(str(tmp_path))
    with pytest.raises(DataSourceError, match="不存在"):
        source.fetch_index("hs300", "2024-01-01", "2024-12-31")


# ============================================================================
# 测试 5: 端到端测试
# ============================================================================

def test_pipeline_end_to_end(tmp_path):
    """测试管道端到端流程"""
    # 准备测试数据
    df_test = pd.DataFrame({
        "date": pd.date_range("2024-01-01", periods=200, freq="B"),
        "close": np.linspace(100, 120, 200),
    })
    (tmp_path / "_data_hs300_full.csv").write_text(df_test.to_csv(index=False))

    # 初始化管道
    source = CSVSource(str(tmp_path))
    config = PipelineConfig(
        enable_checkpoint=True,
        checkpoint_dir=str(tmp_path / "checkpoints"),
        enable_validation=True,
    )
    pipeline = DataPipeline(source, config)

    # 1. 首次拉取
    df1 = run_async(pipeline.fetch_index_data("hs300", "2024-01-01", "2024-12-31"))
    assert len(df1) == 200

    # 2. 验证 checkpoint 已保存
    cp_path = tmp_path / "checkpoints" / "index_hs300_2024-01-01_2024-12-31.json"
    assert cp_path.exists()

    # 3. 第二次拉取应使用 checkpoint
    df2 = run_async(pipeline.fetch_index_data("hs300", "2024-01-01", "2024-12-31"))
    assert len(df2) == 200

    # 4. 禁用 cache 重新拉取
    df3 = run_async(pipeline.fetch_index_data("hs300", "2024-01-01", "2024-12-31", use_cache=False))
    assert len(df3) == 200


# ============================================================================
# 测试 6: 错误处理
# ============================================================================

def test_pipeline_error_handling(tmp_path):
    """测试管道的错误处理"""
    # 测试 1: 数据源失败
    source = CSVSource(str(tmp_path))  # 空目录
    config = PipelineConfig(
        enable_checkpoint=False,
        max_retries=2,
        retry_base_delay=0.1,  # 加速测试
    )
    pipeline = DataPipeline(source, config)

    with pytest.raises(DataSourceError):
        run_async(pipeline.fetch_index_data("hs300", "2024-01-01", "2024-12-31"))


def test_pipeline_batch(tmp_path):
    """测试批量并发拉取"""
    # 准备 3 个测试文件
    for sym in ["hs300", "zz500", "cyb"]:
        df = pd.DataFrame({
            "date": pd.date_range("2024-01-01", periods=100, freq="B"),
            "close": np.linspace(100, 110, 100),
        })
        (tmp_path / f"_data_{sym}_full.csv").write_text(df.to_csv(index=False))

    source = CSVSource(str(tmp_path))
    config = PipelineConfig(enable_checkpoint=False)
    pipeline = DataPipeline(source, config)

    results = run_async(pipeline.fetch_batch(
        ["hs300", "zz500", "cyb"],
        "2024-01-01",
        "2024-12-31",
        max_concurrent=2,
    ))
    assert len(results) == 3
    assert all(len(df) == 100 for df in results.values())


# ============================================================================
# 主入口
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
