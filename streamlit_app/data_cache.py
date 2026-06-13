"""
QuantInsight Pro - Streamlit 缓存适配层
=========================================

桥接异步 DataPipeline 与 Streamlit 的 @st.cache_data,
提供按数据类型分层的 TTL 缓存策略.

缓存策略:
- 实时行情: 60s
- 个股历史: 3600s (1h)
- 财务报表: 86400s (24h)
- 资金流向: 300s (5min)
- 宏观数据: 86400s (24h)
- 新闻舆情: 1800s (30min)

License: MIT
"""

from __future__ import annotations

import logging
from typing import Optional, Callable

import pandas as pd

logger = logging.getLogger(__name__)

# ============================================================================
# TTL 缓存配置 (秒)
# ============================================================================

CACHE_TTL = {
    "realtime": 60,          # 实时行情
    "history": 3600,         # 个股历史
    "financials": 86400,     # 财务报表
    "fund_flow": 300,        # 资金流向
    "macro": 86400,          # 宏观数据
    "news": 1800,            # 新闻舆情
    "index": 3600,           # 指数数据
    "industry": 86400,       # 行业数据
    "valuation": 3600,       # 估值数据
    "stock_comment": 1800,   # 股评数据
}


class DataCacheManager:
    """
    数据缓存管理器 (Streamlit 集成)

    将 EastMoneyChoiceSource 的同步方法包装为 Streamlit 缓存函数.
    每种数据类型使用不同的 TTL.

    使用示例:
        >>> from eastmoney_source import EastMoneyChoiceSource
        >>> from data_cache import DataCacheManager
        >>>
        >>> source = EastMoneyChoiceSource()
        >>> cache = DataCacheManager(source)
        >>>
        >>> # 在 Streamlit 中使用
        >>> df = cache.get_stock_universe()  # 缓存 60s
        >>> df = cache.get_stock_history("600519")  # 缓存 1h
    """

    def __init__(self, source):
        """
        Args:
            source: EastMoneyChoiceSource 实例
        """
        self.source = source
        self._st = None

    def _import_st(self):
        if self._st is None:
            import streamlit as st
            self._st = st
        return self._st

    def _make_cached(self, func: Callable, ttl: int) -> Callable:
        """将函数包装为 Streamlit 缓存函数"""
        st = self._import_st()
        return st.cache_data(ttl=ttl, show_spinner=False)(func)

    # ========================================================================
    # 实时行情 (TTL: 60s)
    # ========================================================================

    def get_stock_universe(self, top_n: int = 0) -> pd.DataFrame:
        """获取全A股实时行情 (缓存60s)"""
        @self._make_cached_func(CACHE_TTL["realtime"])
        def _load(top_n_inner):
            return self.source.fetch_stock_universe(top_n=top_n_inner)
        return _load(top_n)

    # ========================================================================
    # 个股历史 (TTL: 1h)
    # ========================================================================

    def get_stock_history(
        self, symbol: str, start: str = "20200101", end: str = ""
    ) -> pd.DataFrame:
        """获取个股历史OHLCV (缓存1h)"""
        @self._make_cached_func(CACHE_TTL["history"])
        def _load(sym, st, en):
            return self.source.fetch_stock_history(sym, st, en)
        return _load(symbol, start, end)

    # ========================================================================
    # 指数数据 (TTL: 1h)
    # ========================================================================

    def get_index_data(
        self, symbol: str, start: str = "2015-01-01", end: str = ""
    ) -> pd.DataFrame:
        """获取指数数据 (缓存1h)"""
        if not end:
            from datetime import datetime
            end = datetime.now().strftime("%Y-%m-%d")

        @self._make_cached_func(CACHE_TTL["index"])
        def _load(sym, st, en):
            return self.source.fetch_index(sym, st, en)
        return _load(symbol, start, end)

    # ========================================================================
    # 财务报表 (TTL: 24h)
    # ========================================================================

    def get_earnings_report(self, date: str = "20240930") -> pd.DataFrame:
        """获取业绩报表 (缓存24h)"""
        @self._make_cached_func(CACHE_TTL["financials"])
        def _load(dt):
            return self.source.fetch_earnings_report(dt)
        return _load(date)

    def get_balance_sheet(self, date: str = "20240930") -> pd.DataFrame:
        """获取资产负债表 (缓存24h)"""
        @self._make_cached_func(CACHE_TTL["financials"])
        def _load(dt):
            return self.source.fetch_balance_sheet(dt)
        return _load(date)

    def get_income_statement(self, date: str = "20240930") -> pd.DataFrame:
        """获取利润表 (缓存24h)"""
        @self._make_cached_func(CACHE_TTL["financials"])
        def _load(dt):
            return self.source.fetch_income_statement(dt)
        return _load(date)

    def get_cashflow_statement(self, date: str = "20240930") -> pd.DataFrame:
        """获取现金流量表 (缓存24h)"""
        @self._make_cached_func(CACHE_TTL["financials"])
        def _load(dt):
            return self.source.fetch_cashflow_statement(dt)
        return _load(date)

    # ========================================================================
    # 资金流向 (TTL: 5min)
    # ========================================================================

    def get_fund_flow_rank(self, indicator: str = "今日") -> pd.DataFrame:
        """获取资金流向排名 (缓存5min)"""
        @self._make_cached_func(CACHE_TTL["fund_flow"])
        def _load(ind):
            return self.source.fetch_fund_flow_rank(ind)
        return _load(indicator)

    def get_northbound_holdings(
        self, market: str = "北向", indicator: str = "今日排行"
    ) -> pd.DataFrame:
        """获取北向持仓 (缓存5min)"""
        @self._make_cached_func(CACHE_TTL["fund_flow"])
        def _load(mkt, ind):
            return self.source.fetch_northbound_holdings(mkt, ind)
        return _load(market, indicator)

    def get_northbound_flow(self) -> pd.DataFrame:
        """获取北向资金净流入 (缓存5min)"""
        @self._make_cached_func(CACHE_TTL["fund_flow"])
        def _load():
            return self.source.fetch_northbound_flow()
        return _load()

    # ========================================================================
    # 行业数据 (TTL: 24h)
    # ========================================================================

    def get_industry_constituents(self, industry_code: str) -> pd.DataFrame:
        """获取行业成分股 (缓存24h)"""
        @self._make_cached_func(CACHE_TTL["industry"])
        def _load(code):
            return self.source.fetch_industry_constituents(code)
        return _load(industry_code)

    def get_sw_industries(self) -> pd.DataFrame:
        """获取申万行业列表 (缓存24h)"""
        @self._make_cached_func(CACHE_TTL["industry"])
        def _load():
            return self.source.fetch_sw_industries()
        return _load()

    # ========================================================================
    # 新闻舆情 (TTL: 30min)
    # ========================================================================

    def get_news(self, keyword: str = "财经", count: int = 50) -> pd.DataFrame:
        """获取财经新闻 (缓存30min)"""
        @self._make_cached_func(CACHE_TTL["news"])
        def _load(kw, cnt):
            return self.source.fetch_news(kw, cnt)
        return _load(keyword, count)

    # ========================================================================
    # 宏观数据 (TTL: 24h)
    # ========================================================================

    def get_macro_summary(self) -> dict:
        """获取宏观数据摘要 (缓存24h)"""
        @self._make_cached_func(CACHE_TTL["macro"])
        def _load():
            return self.source.fetch_macro_summary()
        return _load()

    # ========================================================================
    # 估值/股评 (TTL: 1h / 30min)
    # ========================================================================

    def get_valuation(self, symbol: str) -> pd.DataFrame:
        """获取估值对比 (缓存1h)"""
        @self._make_cached_func(CACHE_TTL["valuation"])
        def _load(sym):
            return self.source.fetch_valuation(sym)
        return _load(symbol)

    def get_stock_comment(self, symbol: str) -> pd.DataFrame:
        """获取股评评分 (缓存30min)"""
        @self._make_cached_func(CACHE_TTL["stock_comment"])
        def _load(sym):
            return self.source.fetch_stock_comment(sym)
        return _load(symbol)

    def get_stock_profile(self, symbol: str) -> dict:
        """获取个股基本信息 (缓存24h)"""
        @self._make_cached_func(CACHE_TTL["industry"])
        def _load(sym):
            return self.source.fetch_stock_profile(sym)
        return _load(symbol)

    # ========================================================================
    # 内部辅助
    # ========================================================================

    def _make_cached_func(self, ttl: int):
        """创建缓存装饰器"""
        st = self._import_st()

        def decorator(func):
            return st.cache_data(ttl=ttl, show_spinner=False)(func)
        return decorator


# ============================================================================
# 全局单例工厂
# ============================================================================

_cache_instance: Optional[DataCacheManager] = None


def get_data_cache() -> DataCacheManager:
    """获取全局 DataCacheManager 单例"""
    global _cache_instance
    if _cache_instance is None:
        from eastmoney_source import EastMoneyChoiceSource
        source = EastMoneyChoiceSource(rate_limit=5)
        _cache_instance = DataCacheManager(source)
    return _cache_instance
