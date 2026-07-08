# -*- coding: utf-8 -*-
"""
QuantInsight Pro - 统一市场数据快照
====================================

全应用 UI 共用同一套指数/北向资金数值，避免首页与实时看板不一致。
数据链路：SQLite macro_indices / northbound_flow → 静态演示缓存 → refresh_data.py 后台刷新
"""
from __future__ import annotations

import logging
import time
from functools import lru_cache
from typing import Dict, List, Optional, Tuple

import pandas as pd

logger = logging.getLogger(__name__)

_SQLITE_INDICES_TTL_SEC = 60
_sqlite_indices_cache: Dict[str, Dict[str, float | str]] | None = None
_sqlite_indices_cache_at: float = 0.0

# 与 refresh_data / 首页展示对齐的 canonical 演示值（SQLite 无数据时使用）
CANONICAL_INDICES: Dict[str, Dict[str, float | str]] = {
    "sh000300": {"name": "沪深300", "price": 3892.45, "change_pct": 0.45},
    "sh000905": {"name": "中证500", "price": 5823.67, "change_pct": -0.22},
    "sz399006": {"name": "创业板指", "price": 2067.39, "change_pct": -0.61},
}

NORTHBOUND_NET_YI = 38.52
NORTHBOUND_DIRECTION = "净流入"

# 大盘别名 → canonical symbol
_INDEX_ALIASES = {
    "上证指数": "sh000300",
    "沪深300": "sh000300",
    "深证成指": "sh000905",
    "中证500": "sh000905",
    "创业板指": "sz399006",
    "创业板": "sz399006",
}


def _price_frame(symbol: str, price: float, change_pct: float) -> pd.DataFrame:
    prev = price / (1 + change_pct / 100.0) if change_pct else price
    return pd.DataFrame({
        "date": pd.to_datetime(["2026-07-06", "2026-07-07"]),
        "close": [prev, price],
    })


def _load_indices_from_sqlite_uncached() -> Dict[str, Dict[str, float | str]]:
    try:
        from features.sqlite_data_layer import QIDataDB

        raw = QIDataDB().get_macro_indices()
        if not raw:
            return {}
        out: Dict[str, Dict[str, float | str]] = {}
        for symbol, meta in CANONICAL_INDICES.items():
            name = str(meta["name"])
            series = raw.get(name) or raw.get(symbol)
            if not series:
                continue
            try:
                dates = sorted(series.keys())
                if not dates:
                    continue
                last, prev = dates[-1], dates[-2] if len(dates) > 1 else dates[-1]
                price = float(series[last])
                prev_price = float(series[prev])
                chg = (price / prev_price - 1) * 100 if prev_price else 0.0
                out[symbol] = {"name": name, "price": round(price, 2), "change_pct": round(chg, 2)}
            except (TypeError, ValueError, KeyError):
                continue
        return out
    except Exception as e:
        logger.debug("macro_indices sqlite: %s", e)
        return {}


def _load_indices_from_sqlite() -> Dict[str, Dict[str, float | str]]:
    global _sqlite_indices_cache, _sqlite_indices_cache_at
    now = time.time()
    if _sqlite_indices_cache is not None and (now - _sqlite_indices_cache_at) < _SQLITE_INDICES_TTL_SEC:
        return _sqlite_indices_cache
    _sqlite_indices_cache = _load_indices_from_sqlite_uncached()
    _sqlite_indices_cache_at = now
    return _sqlite_indices_cache


def get_index_snapshot(symbol: str) -> pd.DataFrame:
    """返回指数近两日 close 序列（供 load_index / 首页 metric 使用）。"""
    sqlite_vals = _load_indices_from_sqlite()
    meta = sqlite_vals.get(symbol) or CANONICAL_INDICES.get(symbol, CANONICAL_INDICES["sh000300"])
    price = float(meta["price"])
    chg = float(meta["change_pct"])
    return _price_frame(symbol, price, chg)


def get_indices_for_display() -> List[Dict]:
    """供 dashboard / 报告使用的指数列表。"""
    sqlite_vals = _load_indices_from_sqlite()
    rows = []
    for symbol, default in CANONICAL_INDICES.items():
        meta = sqlite_vals.get(symbol, default)
        price = float(meta["price"])
        chg = float(meta["change_pct"])
        change_amt = round(price * chg / 100.0, 2)
        rows.append({
            "name": str(meta["name"]),
            "symbol": symbol,
            "price": price,
            "change": change_amt,
            "change_pct": chg,
        })
    return rows


def resolve_index_symbol(name: str) -> Optional[str]:
    return _INDEX_ALIASES.get(name)


def get_northbound_yi() -> float:
    """今日北向净流入（亿元）。"""
    net, _ = get_northbound_tuple()
    return round(abs(net) / 1e8 if abs(net) > 1e6 else abs(net), 2)


@lru_cache(maxsize=1)
def _northbound_sqlite_tuple() -> Optional[Tuple[float, str]]:
    try:
        from features.sqlite_data_layer import QIDataDB

        nb_df = QIDataDB().get_northbound_flow(days=5)
        if nb_df is not None and len(nb_df) > 0:
            flow_col = next(
                (c for c in nb_df.columns if "net_flow" in c.lower() or "净流入" in str(c)),
                None,
            )
            if flow_col is None:
                for c in nb_df.columns:
                    if nb_df[c].dtype in ("float64", "int64", "float32", "int32"):
                        flow_col = c
                        break
            if flow_col:
                net = float(pd.to_numeric(nb_df[flow_col].iloc[-1], errors="coerce"))
                if net == net:
                    direction = "净流入" if net >= 0 else "净流出"
                    return (net, direction)
    except Exception as e:
        logger.debug("northbound sqlite: %s", e)
    return None


def get_northbound_tuple_fast() -> Tuple[float, str]:
    """UI 快速路径：SQLite → 静态演示，不触发 HTTP/akshare。"""
    cached = _northbound_sqlite_tuple()
    if cached is not None:
        return cached
    return (NORTHBOUND_NET_YI * 1e8, NORTHBOUND_DIRECTION)


def get_northbound_tuple() -> Tuple[float, str]:
    """今日北向净流入（元或亿统一为元量级）及方向。"""
    fast = get_northbound_tuple_fast()
    if _northbound_sqlite_tuple() is not None:
        return fast

    try:
        from features.extended_data_sources import fetch_northbound_series

        res = fetch_northbound_series(days=5)
        if res.ok and isinstance(res.data, pd.DataFrame) and not res.data.empty:
            df = res.data
            flow_col = next(
                (c for c in df.columns if "净流入" in str(c) or "net" in str(c).lower()),
                df.columns[-1],
            )
            net = float(pd.to_numeric(df[flow_col].iloc[-1], errors="coerce"))
            if net == net:
                direction = "净流入" if net >= 0 else "净流出"
                return (net, direction)
    except Exception as e:
        logger.debug("northbound series: %s", e)

    return fast


def get_home_market_snapshot() -> Dict[str, object]:
    """首页四指标一次性读取，避免重复 SQLite 连接。"""
    indices = _load_indices_from_sqlite()
    out: Dict[str, object] = {}
    for symbol in ("sh000300", "sh000905", "sz399006"):
        meta = indices.get(symbol) or CANONICAL_INDICES[symbol]
        out[symbol] = _price_frame(symbol, float(meta["price"]), float(meta["change_pct"]))
    out["northbound"] = get_northbound_tuple_fast()
    return out


def get_sector_flow_top(n: int = 10) -> Optional[pd.DataFrame]:
    """板块资金流 TOP N — SQLite 优先。"""
    try:
        from features.sqlite_data_layer import QIDataDB

        sector = QIDataDB().get_sector_flow()
        if sector is not None and not sector.empty:
            latest_date = sector["date"].max() if "date" in sector.columns else None
            if latest_date is not None:
                sector = sector[sector["date"] == latest_date].copy()
            name_col = "sector_name" if "sector_name" in sector.columns else "board_name"
            if name_col in sector.columns:
                out = sector.copy()
                out["名称"] = out[name_col]
                if "change_pct" in out.columns:
                    out["涨跌幅"] = pd.to_numeric(out["change_pct"], errors="coerce")
                if "net_flow" in out.columns:
                    out["净流入"] = pd.to_numeric(out["net_flow"], errors="coerce")
                return out.head(n)
    except Exception as e:
        logger.debug("sector_flow sqlite: %s", e)

    try:
        from features.extended_data_sources import fetch_concept_boards

        res = fetch_concept_boards(top_n=n)
        if res.ok and isinstance(res.data, pd.DataFrame) and not res.data.empty:
            return res.data.head(n)
    except Exception as e:
        logger.debug("concept boards: %s", e)
    return None
