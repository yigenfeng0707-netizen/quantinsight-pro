# -*- coding: utf-8 -*-
"""
Streamlit UI 统一数据桥接层
==========================

读取优先级与 refresh_data 对齐，并返回数据来源标签供页面展示。
"""
from __future__ import annotations

import logging
from typing import Dict, Optional, Tuple

import pandas as pd

logger = logging.getLogger(__name__)

SOURCE_SQLITE_SPOT = "SQLite 实时缓存"
SOURCE_SQLITE_HISTORY = "SQLite 历史快照 (沪深300+中证500)"
SOURCE_QVERIS_RT = "QVeris 实时"
SOURCE_EASTMONEY = "东方财富直连"
SOURCE_BAOSTOCK = "Baostock"
SOURCE_AKSHARE = "AKShare"
SOURCE_DEMO = "演示数据"


def _normalize_spot(df: pd.DataFrame) -> pd.DataFrame:
    col_map = {
        "code": "代码", "name": "名称", "latest_price": "最新价",
        "change_pct": "涨跌幅", "pe_ttm": "市盈率-动态",
        "pb": "市净率", "total_mv": "总市值",
        "turnover_rate": "换手率", "amount": "成交额",
        "change_pct_60d": "60日涨跌幅",
    }
    rename = {k: v for k, v in col_map.items() if k in df.columns}
    return df.rename(columns=rename) if rename else df


def get_history_stats() -> dict:
    try:
        from features.sqlite_data_layer import QIDataDB
        return QIDataDB().get_history_stats()
    except Exception:
        return {"stock_count": 0, "bar_count": 0, "last_updated": None, "source": None}


def resolve_spot_dataframe() -> Tuple[pd.DataFrame, str]:
    """UI 行情表: SQLite spot → 历史最新价 → QVeris Top50 → 空表"""
    try:
        from features.sqlite_data_layer import QIDataDB
        db = QIDataDB()
        df = db.get_stock_spot()
        if df is not None and not df.empty:
            return _normalize_spot(df), SOURCE_SQLITE_SPOT

        df = db.get_spot_from_history_latest()
        if df is not None and not df.empty:
            stats = db.get_history_stats()
            label = SOURCE_SQLITE_HISTORY
            if stats.get("stock_count"):
                label = f"{SOURCE_SQLITE_HISTORY} · {stats['stock_count']} 只"
            return _normalize_spot(df), label
    except Exception as e:
        logger.debug("resolve_spot sqlite: %s", e)

    try:
        from features.qveris_source import fetch_realtime_batch, is_configured
        if is_configured():
            codes = _default_watchlist_codes()[:50]
            df = fetch_realtime_batch(codes)
            if df is not None and not df.empty:
                return df, SOURCE_QVERIS_RT
    except Exception as e:
        logger.debug("resolve_spot qveris: %s", e)

    return pd.DataFrame(), SOURCE_DEMO


def resolve_stock_quote(code: str) -> Tuple[Dict, str]:
    """单股实时快照 (个股页 / 选股)"""
    code = str(code).strip().zfill(6)[-6:]
    if not code:
        return {}, SOURCE_DEMO

    try:
        from features.sqlite_data_layer import QIDataDB
        db = QIDataDB()
        spot = db.get_stock_spot()
        if spot is not None and not spot.empty and "code" in spot.columns:
            row = spot[spot["code"].astype(str).str.zfill(6).str[-6:] == code]
            if not row.empty:
                r = row.iloc[0].to_dict()
                return {
                    "代码": code,
                    "名称": r.get("name", code),
                    "最新价": r.get("latest_price"),
                    "涨跌幅": r.get("change_pct"),
                }, SOURCE_SQLITE_SPOT

        hist = db.get_stock_history(code, days=5)
        if hist is not None and not hist.empty:
            last = hist.sort_values("date").iloc[-1]
            return {
                "代码": code,
                "名称": code,
                "最新价": last.get("close"),
                "涨跌幅": last.get("pct_change"),
            }, SOURCE_SQLITE_HISTORY
    except Exception as e:
        logger.debug("resolve_stock_quote sqlite: %s", e)

    try:
        from features.qveris_source import fetch_realtime_snapshot, is_configured
        if is_configured():
            snap = fetch_realtime_snapshot(code)
            if snap:
                return snap, SOURCE_QVERIS_RT
    except Exception as e:
        logger.debug("resolve_stock_quote qveris: %s", e)

    return {"代码": code, "名称": code}, SOURCE_DEMO


def resolve_stock_history(code: str, days: int = 365) -> Tuple[Optional[pd.DataFrame], str]:
    """个股历史 K 线"""
    code = str(code).strip().zfill(6)[-6:]
    try:
        from features.sqlite_data_layer import QIDataDB
        df = QIDataDB().get_stock_history(code, days=days)
        if df is not None and not df.empty:
            return df, SOURCE_SQLITE_HISTORY
    except Exception as e:
        logger.debug("resolve_stock_history sqlite: %s", e)

    try:
        from datetime import datetime, timedelta
        from features.qveris_source import fetch_stock_history, is_configured
        if is_configured():
            end = datetime.now().strftime("%Y%m%d")
            start = (datetime.now() - timedelta(days=days)).strftime("%Y%m%d")
            df = fetch_stock_history(code, start, end)
            if df is not None and not df.empty:
                return df, SOURCE_QVERIS_RT
    except Exception as e:
        logger.debug("resolve_stock_history qveris: %s", e)

    return None, SOURCE_DEMO


def lookup_code_in_local_db(stock_input: str) -> Tuple[str, str]:
    """代码/名称解析: spot → history 代码表"""
    text = (stock_input or "").strip()
    if not text:
        return "", ""

    df, _ = resolve_spot_dataframe()
    if df is not None and not df.empty:
        code_col = next((c for c in df.columns if c in ("代码", "code")), None)
        name_col = next((c for c in df.columns if c in ("名称", "name")), None)
        if code_col:
            if text.isdigit():
                bare = text.zfill(6)[-6:]
                mask = df[code_col].astype(str).str.zfill(6).str[-6:] == bare
                if mask.any():
                    name = df.loc[mask, name_col].iloc[0] if name_col else bare
                    return bare, str(name)
            if name_col:
                mask = df[name_col].astype(str).str.contains(text, na=False)
                if mask.any():
                    return str(df.loc[mask, code_col].iloc[0]), str(df.loc[mask, name_col].iloc[0])

    if text.isdigit():
        bare = text.zfill(6)[-6:]
        try:
            from features.sqlite_data_layer import QIDataDB
            if QIDataDB().history_has_code(bare):
                quote, _ = resolve_stock_quote(bare)
                return bare, str(quote.get("名称", bare))
        except Exception:
            pass
        return bare, bare

    return "", text


def _default_watchlist_codes() -> list:
    try:
        from pathlib import Path
        root = Path(__file__).resolve().parents[1] / "data"
        codes = []
        for fname in ("hs300_codes.txt", "zz500_codes.txt"):
            p = root / fname
            if p.exists():
                codes.extend(ln.strip() for ln in p.read_text(encoding="utf-8").splitlines() if ln.strip())
        if codes:
            return list(dict.fromkeys(codes))
    except Exception:
        pass
    from features.qveris_source import DEFAULT_TOP100_CODES
    return list(DEFAULT_TOP100_CODES)


def qveris_status() -> dict:
    try:
        from features.qveris_source import is_configured, QVerisClient
        if not is_configured():
            return {"ok": False, "detail": "未配置 API Key", "credits": None}
        client = QVerisClient()
        r = client.discover("ping", limit=1)
        credits = r.get("remaining_credits")
        return {"ok": True, "detail": f"已连接 · 余额 {credits} 积分", "credits": credits}
    except Exception as e:
        return {"ok": False, "detail": str(e)[:80], "credits": None}
