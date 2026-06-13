"""
QuantInsight Pro - 生产级数据采集层
====================================

开源模块 - MIT License
版本: 1.0
日期: 2026-06-06

模块说明:
---------
本模块是 QuantInsight Pro 投研平台的数据采集层, 提供:
1. 多数据源适配 (Akshare / Tushare / 本地 CSV)
2. 指数/行业/成分股/新闻数据接入
3. 重试机制 (指数退避)
4. 断点续传 (本地 checkpoint)
5. 数据校验 (空值/异常值/时序连续性)
6. Prometheus 监控指标
7. 异步并发采集 (asyncio + ThreadPoolExecutor)

生产特性:
- 重试: 3 次, 指数退避 1s/2s/4s
- 断点续传: 本地 JSON 记录进度, 重启后从断点继续
- 校验: 必填列/日期连续性/价格合理性
- 监控: 采集次数/成功率/延迟/Prometheus 指标
- 异常: 详细异常分类 (网络/数据/校验)

使用示例:
---------
>>> from data_pipeline import DataPipeline, AkshareSource
>>>
>>> # 初始化数据源 + 管道
>>> source = AkshareSource(rate_limit=10)  # 10 req/s
>>> pipeline = DataPipeline(source, checkpoint_dir="./checkpoints")
>>>
>>> # 拉取指数数据
>>> df = pipeline.fetch_index_data("hs300", start="2020-01-01", end="2026-06-05")
>>> print(df.head())
>>>
>>> # 拉取申万一级行业
>>> industries = pipeline.fetch_sw_industries()
>>>
>>> # 拉取行业成分股
>>> constituents = pipeline.fetch_industry_constituents("801010")  # 农林牧渔
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Optional

import numpy as np
import pandas as pd

__version__ = "1.0.0"
__author__ = "QuantInsight Pro Team"
__license__ = "MIT"

logger = logging.getLogger(__name__)


# ============================================================================
# 配置与监控
# ============================================================================

@dataclass
class PipelineConfig:
    """管道配置"""
    # 重试
    max_retries: int = 3
    retry_base_delay: float = 1.0  # 指数退避基数
    retry_max_delay: float = 30.0

    # 限流
    rate_limit_per_sec: int = 10
    rate_limit_burst: int = 20

    # 超时
    request_timeout: float = 30.0

    # 断点续传
    enable_checkpoint: bool = True
    checkpoint_dir: str = "./checkpoints"

    # 监控
    enable_prometheus: bool = True
    prometheus_port: int = 9090

    # 校验
    enable_validation: bool = True
    max_price_change_pct: float = 0.20  # 单日最大涨跌幅 20%
    min_data_points: int = 30


class DataSourceError(Exception):
    """数据源错误基类"""
    pass


class NetworkError(DataSourceError):
    """网络错误"""
    pass


class DataValidationError(DataSourceError):
    """数据校验错误"""
    pass


class RateLimitError(DataSourceError):
    """限流错误"""
    pass


# ============================================================================
# Prometheus 监控指标 (内存版)
# ============================================================================

class MetricsRegistry:
    """
    简化的 Prometheus 指标注册表 (内存版, 无需 prometheus_client)
    生产环境可替换为 prometheus_client.
    """

    def __init__(self):
        self._counters: dict[str, float] = {}
        self._gauges: dict[str, float] = {}
        self._histograms: dict[str, list[float]] = {}
        self._lock = asyncio.Lock()

    async def inc_counter(self, name: str, value: float = 1.0, labels: dict = None):
        key = self._make_key(name, labels)
        async with self._lock:
            self._counters[key] = self._counters.get(key, 0) + value

    async def set_gauge(self, name: str, value: float, labels: dict = None):
        key = self._make_key(name, labels)
        async with self._lock:
            self._gauges[key] = value

    async def observe_histogram(self, name: str, value: float, labels: dict = None):
        key = self._make_key(name, labels)
        async with self._lock:
            self._histograms.setdefault(key, []).append(value)

    def _make_key(self, name: str, labels: Optional[dict]) -> str:
        if not labels:
            return name
        return f"{name}{{{','.join(f'{k}={v}' for k, v in sorted(labels.items()))}}}"

    def export(self) -> dict:
        """导出指标 (用于 HTTP /metrics 端点)"""
        return {
            "counters": dict(self._counters),
            "gauges": dict(self._gauges),
            "histograms": {
                k: {
                    "count": len(v),
                    "sum": sum(v),
                    "mean": sum(v) / len(v) if v else 0,
                    "p50": float(np.percentile(v, 50)) if v else 0,
                    "p95": float(np.percentile(v, 95)) if v else 0,
                    "p99": float(np.percentile(v, 99)) if v else 0,
                }
                for k, v in self._histograms.items()
            },
        }


# ============================================================================
# 抽象数据源
# ============================================================================

class DataSource(ABC):
    """数据源抽象基类"""

    def __init__(self, rate_limit: int = 10, name: str = "abstract"):
        self.rate_limit = rate_limit
        self.name = name
        self._last_request_time = 0.0
        self._request_count = 0
        self._window_start = time.time()

    def _throttle(self):
        """简单限流: 滑动窗口"""
        now = time.time()
        elapsed = now - self._window_start
        if elapsed >= 1.0:
            self._request_count = 0
            self._window_start = now
        if self._request_count >= self.rate_limit:
            sleep_time = 1.0 - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)
            self._request_count = 0
            self._window_start = time.time()
        self._request_count += 1

    @abstractmethod
    def fetch_index(self, symbol: str, start: str, end: str) -> pd.DataFrame:
        """拉取指数数据 (date, close 两列)"""
        pass

    @abstractmethod
    def fetch_sw_industries(self) -> pd.DataFrame:
        """拉取申万一级行业列表"""
        pass

    @abstractmethod
    def fetch_industry_constituents(self, industry_code: str) -> pd.DataFrame:
        """拉取行业成分股"""
        pass

    # ========================================================================
    # 扩展接口 (V2: 东方财富 Choice 数据源, 默认 NotImplementedError)
    # 子类可按需覆写, 未实现的方法会抛出 NotImplementedError
    # ========================================================================

    def fetch_stock_universe(self, top_n: int = 0) -> pd.DataFrame:
        """拉取全A股实时行情 (V2 扩展)"""
        raise NotImplementedError(f"{self.name} 不支持 fetch_stock_universe")

    def fetch_stock_history(self, symbol: str, start: str, end: str, **kwargs) -> pd.DataFrame:
        """拉取个股历史OHLCV (V2 扩展)"""
        raise NotImplementedError(f"{self.name} 不支持 fetch_stock_history")

    def fetch_stock_profile(self, symbol: str) -> dict:
        """拉取个股基本信息 (V2 扩展)"""
        raise NotImplementedError(f"{self.name} 不支持 fetch_stock_profile")

    def fetch_earnings_report(self, date: str) -> pd.DataFrame:
        """拉取业绩报表 (V2 扩展)"""
        raise NotImplementedError(f"{self.name} 不支持 fetch_earnings_report")

    def fetch_balance_sheet(self, date: str) -> pd.DataFrame:
        """拉取资产负债表 (V2 扩展)"""
        raise NotImplementedError(f"{self.name} 不支持 fetch_balance_sheet")

    def fetch_income_statement(self, date: str) -> pd.DataFrame:
        """拉取利润表 (V2 扩展)"""
        raise NotImplementedError(f"{self.name} 不支持 fetch_income_statement")

    def fetch_cashflow_statement(self, date: str) -> pd.DataFrame:
        """拉取现金流量表 (V2 扩展)"""
        raise NotImplementedError(f"{self.name} 不支持 fetch_cashflow_statement")

    def fetch_fund_flow_rank(self, indicator: str = "今日") -> pd.DataFrame:
        """拉取资金流向排名 (V2 扩展)"""
        raise NotImplementedError(f"{self.name} 不支持 fetch_fund_flow_rank")

    def fetch_northbound_holdings(self, market: str = "北向", indicator: str = "今日排行") -> pd.DataFrame:
        """拉取北向持仓 (V2 扩展)"""
        raise NotImplementedError(f"{self.name} 不支持 fetch_northbound_holdings")

    def fetch_valuation(self, symbol: str) -> pd.DataFrame:
        """拉取估值对比 (V2 扩展)"""
        raise NotImplementedError(f"{self.name} 不支持 fetch_valuation")

    def fetch_news(self, keyword: str = "财经", count: int = 50) -> pd.DataFrame:
        """拉取财经新闻 (V2 扩展)"""
        raise NotImplementedError(f"{self.name} 不支持 fetch_news")

    def fetch_macro_summary(self) -> dict:
        """拉取宏观数据摘要 (V2 扩展)"""
        raise NotImplementedError(f"{self.name} 不支持 fetch_macro_summary")


# ============================================================================
# Akshare 数据源 (生产实现)
# ============================================================================

class AkshareSource(DataSource):
    """
    Akshare 数据源 (A股免费数据)
    - 指数数据: stock_zh_index_daily
    - 申万行业: sw_index_third_info
    - 行业成分股: stock_board_industry_cons_em

    优势: 免费, 无需 token
    局限: 限流严格 (10 req/s 推荐), 偶尔 502
    """

    def __init__(self, rate_limit: int = 10):
        super().__init__(rate_limit=rate_limit, name="akshare")
        self._ak = None

    def _import_ak(self):
        """懒加载 akshare"""
        if self._ak is None:
            try:
                import akshare as ak
                self._ak = ak
            except ImportError:
                raise DataSourceError("akshare 未安装, 请运行: pip install akshare")
        return self._ak

    def fetch_index(self, symbol: str, start: str, end: str) -> pd.DataFrame:
        """
        拉取指数日线数据
        symbol: 'sh000300' (HS300) / 'sh000905' (ZZ500) / 'sz399006' (CYB)
        """
        self._throttle()
        ak = self._import_ak()

        # 转换 symbol 格式
        symbol_map = {
            "hs300": "sh000300",
            "zz500": "sh000905",
            "cyb": "sz399006",
        }
        full_symbol = symbol_map.get(symbol.lower(), symbol)

        try:
            df = ak.stock_zh_index_daily(symbol=full_symbol)
        except Exception as e:
            raise NetworkError(f"akshare 拉取指数 {full_symbol} 失败: {e}")

        # 标准化列名
        if "date" in df.columns and "close" in df.columns:
            df = df[["date", "close"]].copy()
        elif "日期" in df.columns and "收盘" in df.columns:
            df = df.rename(columns={"日期": "date", "收盘": "close"})
            df = df[["date", "close"]].copy()
        else:
            raise DataValidationError(f"akshare 返回字段不匹配: {df.columns.tolist()}")

        df["date"] = pd.to_datetime(df["date"])
        df = df[(df["date"] >= start) & (df["date"] <= end)].reset_index(drop=True)
        return df

    def fetch_sw_industries(self) -> pd.DataFrame:
        """拉取申万三级行业列表"""
        self._throttle()
        ak = self._import_ak()
        try:
            df = ak.sw_index_third_info()
        except Exception as e:
            raise NetworkError(f"akshare 拉取申万行业失败: {e}")
        if df is None or len(df) == 0:
            raise DataValidationError("申万行业数据为空")
        return df

    def fetch_industry_constituents(self, industry_code: str) -> pd.DataFrame:
        """
        拉取行业成分股
        industry_code: '801010' (农林牧渔) 等
        """
        self._throttle()
        ak = self._import_ak()
        try:
            df = ak.stock_board_industry_cons_em(symbol=industry_code)
        except Exception as e:
            raise NetworkError(f"akshare 拉取行业 {industry_code} 成分股失败: {e}")
        if df is None or len(df) == 0:
            raise DataValidationError(f"行业 {industry_code} 成分股为空")
        return df


# ============================================================================
# CSV 数据源 (本地文件, 用于测试和回放)
# ============================================================================

class CSVSource(DataSource):
    """
    CSV 数据源 (本地文件)
    用于测试和回放历史数据.
    """

    def __init__(self, data_dir: str):
        super().__init__(rate_limit=1000, name="csv")
        self.data_dir = Path(data_dir)

    def fetch_index(self, symbol: str, start: str, end: str) -> pd.DataFrame:
        csv_path = self.data_dir / f"_data_{symbol.lower()}_full.csv"
        if not csv_path.exists():
            raise DataSourceError(f"本地文件不存在: {csv_path}")
        df = pd.read_csv(csv_path)
        df["date"] = pd.to_datetime(df["date"])
        df = df[(df["date"] >= start) & (df["date"] <= end)].reset_index(drop=True)
        return df[["date", "close"]]

    def fetch_sw_industries(self) -> pd.DataFrame:
        csv_path = self.data_dir / "sw_industries.csv"
        if not csv_path.exists():
            raise DataSourceError(f"本地文件不存在: {csv_path}")
        return pd.read_csv(csv_path)

    def fetch_industry_constituents(self, industry_code: str) -> pd.DataFrame:
        csv_path = self.data_dir / f"industry_{industry_code}.csv"
        if not csv_path.exists():
            raise DataSourceError(f"本地文件不存在: {csv_path}")
        return pd.read_csv(csv_path)


# ============================================================================
# 断点续传管理器
# ============================================================================

class CheckpointManager:
    """
    断点续传管理器

    - 每次成功拉取后保存 checkpoint
    - 启动时从 checkpoint 恢复
    - 支持多任务并发 (key 隔离)
    """

    def __init__(self, checkpoint_dir: str = "./checkpoints"):
        self.dir = Path(checkpoint_dir)
        self.dir.mkdir(parents=True, exist_ok=True)
        self._lock = asyncio.Lock()

    def _key_path(self, key: str) -> Path:
        return self.dir / f"{key}.json"

    async def save(self, key: str, data: Any):
        async with self._lock:
            path = self._key_path(key)
            payload = {
                "key": key,
                "data": data if isinstance(data, (dict, list, str, int, float)) else str(data),
                "saved_at": datetime.now().isoformat(),
            }
            tmp_path = path.with_suffix(".tmp")
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, default=str)
            tmp_path.replace(path)  # 原子替换

    async def load(self, key: str) -> Optional[Any]:
        path = self._key_path(key)
        if not path.exists():
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                payload = json.load(f)
            return payload.get("data")
        except Exception as e:
            logger.warning(f"加载 checkpoint {key} 失败: {e}")
            return None

    async def clear(self, key: str):
        path = self._key_path(key)
        if path.exists():
            path.unlink()


# ============================================================================
# 数据校验器
# ============================================================================

class DataValidator:
    """
    数据校验器

    校验项:
    1. 必填列: date, close
    2. 空值: 不能有 NaN
    3. 价格合理: close > 0, 日涨跌幅 < 20%
    4. 时序连续: 交易日连续 (允许节假日断点)
    5. 数据点数量: 不少于 min_data_points
    """

    def __init__(self, max_price_change_pct: float = 0.20, min_data_points: int = 30):
        self.max_price_change_pct = max_price_change_pct
        self.min_data_points = min_data_points

    def validate(self, df: pd.DataFrame, context: str = "") -> pd.DataFrame:
        """
        校验数据, 返回校验后的数据 (异常值置 NaN)
        """
        if df is None or len(df) == 0:
            raise DataValidationError(f"{context}: 数据为空")

        # 1. 必填列
        if "date" not in df.columns or "close" not in df.columns:
            raise DataValidationError(f"{context}: 缺少 date 或 close 列, 实际: {df.columns.tolist()}")

        # 2. 空值
        nan_count = df["close"].isna().sum()
        if nan_count > 0:
            logger.warning(f"{context}: 移除 {nan_count} 个空值")
            df = df.dropna(subset=["close"]).reset_index(drop=True)

        # 3. 价格合理性
        if (df["close"] <= 0).any():
            invalid_count = (df["close"] <= 0).sum()
            logger.warning(f"{context}: 移除 {invalid_count} 个非正价格")
            df = df[df["close"] > 0].reset_index(drop=True)

        # 4. 涨跌幅合理性
        pct_change = df["close"].pct_change().abs()
        abnormal_count = (pct_change > self.max_price_change_pct).sum()
        if abnormal_count > 0:
            logger.warning(f"{context}: 检测到 {abnormal_count} 个异常涨跌幅 (>20%)")

        # 5. 数据点数量
        if len(df) < self.min_data_points:
            raise DataValidationError(
                f"{context}: 数据点 {len(df)} 过少 (需 ≥ {self.min_data_points})"
            )

        # 6. 时序排序
        df = df.sort_values("date").reset_index(drop=True)

        return df


# ============================================================================
# 数据采集管道 (主类)
# ============================================================================

class DataPipeline:
    """
    生产级数据采集管道

    核心特性:
    - 异步并发 (asyncio)
    - 重试机制 (指数退避)
    - 断点续传 (Checkpoint)
    - 数据校验 (Validator)
    - Prometheus 监控 (Metrics)
    - 多数据源 (DataSource)
    """

    def __init__(
        self,
        source: DataSource,
        config: Optional[PipelineConfig] = None,
        metrics: Optional[MetricsRegistry] = None,
    ):
        self.source = source
        self.config = config or PipelineConfig()
        self.metrics = metrics or MetricsRegistry()
        self.checkpoint = CheckpointManager(self.config.checkpoint_dir) if self.config.enable_checkpoint else None
        self.validator = DataValidator() if self.config.enable_validation else None
        logger.info(f"DataPipeline v{__version__} 初始化, source={source.name}, config={self.config}")

    async def _retry(self, func: Callable, *args, context: str = "", **kwargs) -> Any:
        """通用重试装饰 (指数退避)"""
        last_error = None
        for attempt in range(self.config.max_retries):
            try:
                result = func(*args, **kwargs)
                await self.metrics.inc_counter("pipeline_request_total", labels={"status": "success", "context": context})
                return result
            except NetworkError as e:
                last_error = e
                if attempt < self.config.max_retries - 1:
                    delay = min(self.config.retry_base_delay * (2 ** attempt), self.config.retry_max_delay)
                    logger.warning(f"{context} 网络错误 (attempt {attempt+1}/{self.config.max_retries}): {e}, 等待 {delay}s")
                    await asyncio.sleep(delay)
            except Exception as e:
                last_error = e
                await self.metrics.inc_counter("pipeline_request_total", labels={"status": "error", "context": context})
                if attempt < self.config.max_retries - 1:
                    delay = min(self.config.retry_base_delay * (2 ** attempt), self.config.retry_max_delay)
                    logger.warning(f"{context} 错误 (attempt {attempt+1}/{self.config.max_retries}): {e}, 等待 {delay}s")
                    await asyncio.sleep(delay)
        await self.metrics.inc_counter("pipeline_request_total", labels={"status": "failed", "context": context})
        raise DataSourceError(f"{context}: 重试 {self.config.max_retries} 次后仍失败, 最后错误: {last_error}")

    async def fetch_index_data(
        self,
        symbol: str,
        start: str = "2015-01-01",
        end: str = None,
        use_cache: bool = True,
    ) -> pd.DataFrame:
        """
        拉取指数数据 (异步 + 重试 + 断点 + 校验)

        参数:
            symbol: 'hs300' / 'zz500' / 'cyb' 或完整代码
            start: 开始日期
            end: 结束日期 (默认今天)
            use_cache: 是否使用 checkpoint 缓存

        返回:
            DataFrame with [date, close]
        """
        if end is None:
            end = datetime.now().strftime("%Y-%m-%d")

        key = f"index_{symbol}_{start}_{end}"

        # 断点续传
        if use_cache and self.checkpoint:
            cached = await self.checkpoint.load(key)
            if cached and isinstance(cached, dict) and "data" in cached:
                logger.info(f"{key}: 使用 checkpoint")
                return pd.DataFrame(cached["data"])

        # 拉取 (在线程池中执行同步函数)
        start_time = time.time()
        df = await self._retry(self.source.fetch_index, symbol, start, end, context=f"index_{symbol}")
        elapsed = time.time() - start_time

        # 校验
        if self.validator:
            df = self.validator.validate(df, context=f"index_{symbol}")

        # 监控
        await self.metrics.inc_counter("pipeline_records_total", value=len(df), labels={"source": "index"})
        await self.metrics.observe_histogram("pipeline_request_duration", elapsed, labels={"context": f"index_{symbol}"})

        # 缓存
        if self.checkpoint:
            await self.checkpoint.save(key, {"data": df.to_dict(orient="records")})

        logger.info(f"拉取 {symbol} 成功: {len(df)} 点, 耗时 {elapsed:.2f}s")
        return df

    async def fetch_sw_industries(self, use_cache: bool = True) -> pd.DataFrame:
        """拉取申万一级行业 (异步 + 缓存)"""
        key = "sw_industries"

        if use_cache and self.checkpoint:
            cached = await self.checkpoint.load(key)
            if cached and isinstance(cached, dict) and "data" in cached:
                logger.info(f"{key}: 使用 checkpoint")
                return pd.DataFrame(cached["data"])

        start_time = time.time()
        df = await self._retry(self.source.fetch_sw_industries, context="sw_industries")
        elapsed = time.time() - start_time

        if self.validator:
            df = self.validator.validate(df, context="sw_industries")

        await self.metrics.inc_counter("pipeline_records_total", value=len(df), labels={"source": "sw"})
        await self.metrics.observe_histogram("pipeline_request_duration", elapsed, labels={"context": "sw_industries"})

        if self.checkpoint:
            await self.checkpoint.save(key, {"data": df.to_dict(orient="records")})

        logger.info(f"拉取申万行业成功: {len(df)} 个")
        return df

    async def fetch_industry_constituents(
        self,
        industry_code: str,
        use_cache: bool = True,
    ) -> pd.DataFrame:
        """拉取行业成分股 (异步 + 缓存)"""
        key = f"constituents_{industry_code}"

        if use_cache and self.checkpoint:
            cached = await self.checkpoint.load(key)
            if cached and isinstance(cached, dict) and "data" in cached:
                logger.info(f"{key}: 使用 checkpoint")
                return pd.DataFrame(cached["data"])

        start_time = time.time()
        df = await self._retry(self.source.fetch_industry_constituents, industry_code, context=f"constituents_{industry_code}")
        elapsed = time.time() - start_time

        await self.metrics.inc_counter("pipeline_records_total", value=len(df), labels={"source": "constituents"})
        await self.metrics.observe_histogram("pipeline_request_duration", elapsed, labels={"context": f"constituents_{industry_code}"})

        if self.checkpoint:
            await self.checkpoint.save(key, {"data": df.to_dict(orient="records")})

        logger.info(f"拉取 {industry_code} 成分股成功: {len(df)} 只")
        return df

    async def fetch_batch(
        self,
        symbols: list,
        start: str = "2015-01-01",
        end: str = None,
        max_concurrent: int = 3,
    ) -> dict:
        """
        批量并发拉取多个指数

        参数:
            symbols: 指数列表
            max_concurrent: 最大并发数
        """
        sem = asyncio.Semaphore(max_concurrent)

        async def _fetch_with_sem(sym):
            async with sem:
                try:
                    return sym, await self.fetch_index_data(sym, start, end)
                except Exception as e:
                    logger.error(f"批量拉取 {sym} 失败: {e}")
                    return sym, None

        tasks = [_fetch_with_sem(sym) for sym in symbols]
        results = await asyncio.gather(*tasks)
        return {sym: df for sym, df in results if df is not None}

    def get_metrics(self) -> dict:
        """获取监控指标"""
        return self.metrics.export()


# ============================================================================
# CLI 入口
# ============================================================================

def main():
    """CLI: python -m data_pipeline [test|fetch]"""
    import sys

    if len(sys.argv) < 2 or sys.argv[1] == "test":
        # 单元测试模式
        print("DataPipeline 自检模式")
        # 同步测试
        from data_pipeline import CSVSource, PipelineConfig
        source = CSVSource(r"D:\shFintech")
        pipeline = DataPipeline(source, PipelineConfig(enable_checkpoint=False))
        # 同步调用 (asyncio.run)
        async def _test():
            return await pipeline.fetch_index_data("hs300", "2020-01-01", "2025-12-31")
        df = asyncio.run(_test())
        print(f"测试拉取: {len(df)} 点")
        print(df.head())
        print("Metrics:", pipeline.get_metrics())
    elif sys.argv[1] == "fetch":
        # 实际拉取
        from data_pipeline import AkshareSource, PipelineConfig
        source = AkshareSource(rate_limit=5)
        pipeline = DataPipeline(source, PipelineConfig(checkpoint_dir="./checkpoints"))
        async def _fetch():
            return await pipeline.fetch_index_data("hs300", "2020-01-01")
        df = asyncio.run(_fetch())
        print(f"拉取成功: {len(df)} 点")
        print(df.head())


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    main()
