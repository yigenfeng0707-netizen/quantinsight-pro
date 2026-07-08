"""
QuantInsight Pro - 市场大盘面板 (Market Dashboard)
====================================================

实时市场概览: 指数/板块热力图/涨跌家数/资金流全景/市场宽度

License: MIT
"""

from __future__ import annotations
import logging
from typing import Optional
import pandas as pd

logger = logging.getLogger(__name__)

_STATIC_INDICES = {
    "沪深300": {"price": 3892.45, "change_pct": 0.45},
    "中证500": {"price": 5823.67, "change_pct": -0.22},
    "创业板指": {"price": 2067.39, "change_pct": -0.61},
}


class MarketDashboard:
    """市场大盘面板 — UI 快速路径，不调用 get_stock_universe(5000)"""

    def __init__(self, cache_manager=None):
        self.cache = cache_manager

    def get_market_overview(self) -> dict:
        """获取市场概览数据 (SQLite / extended_data_sources 优先)"""
        result = {
            "indices": {},
            "breadth": {},
            "fund_flow": {},
            "sector_heatmap": [],
        }

        # ---- 指数: cache → 静态 ----
        for name, symbol in [("沪深300", "sh000300"), ("中证500", "sh000905"), ("创业板指", "sz399006")]:
            loaded = False
            if self.cache:
                try:
                    df = self.cache.get_index_data(symbol)
                    if df is not None and len(df) > 1:
                        latest = df.iloc[-1]
                        prev = df.iloc[-2]
                        change = (latest["close"] - prev["close"]) / prev["close"] * 100
                        result["indices"][name] = {
                            "price": float(latest["close"]),
                            "change_pct": round(change, 2),
                        }
                        loaded = True
                except Exception:
                    pass
            if not loaded and name in _STATIC_INDICES:
                s = _STATIC_INDICES[name]
                result["indices"][name] = {"price": s["price"], "change_pct": s["change_pct"]}

        # ---- 涨跌家数: SQLite market_breadth → fetch_limit_stats ----
        breadth = self._load_breadth_fast()
        if breadth:
            result["breadth"] = breadth

        # ---- 北向资金: SQLite → extended ----
        north_yi = self._load_northbound_yi()
        if north_yi is not None:
            result["fund_flow"]["northbound"] = north_yi

        return result

    def _load_breadth_fast(self) -> dict:
        try:
            from features.sqlite_data_layer import QIDataDB
            row = QIDataDB().get_market_breadth()
            if row:
                up = int(row.get("up_count", row.get("up", 0)) or 0)
                down = int(row.get("down_count", row.get("down", 0)) or 0)
                flat = int(row.get("flat_count", row.get("flat", 0)) or 0)
                limit_up = int(row.get("limit_up", 0) or 0)
                limit_down = int(row.get("limit_down", 0) or 0)
                total = int(row.get("total", up + down + flat) or (up + down + flat))
                if total > 0:
                    return {
                        "up": up,
                        "down": down,
                        "flat": flat,
                        "limit_up": limit_up,
                        "limit_down": limit_down,
                        "total": total,
                        "up_ratio": round(up / max(total, 1) * 100, 1),
                    }
        except Exception as e:
            logger.debug("market_breadth sqlite: %s", e)

        try:
            from features.extended_data_sources import fetch_limit_stats
            res = fetch_limit_stats()
            if res.ok and isinstance(res.data, dict):
                d = res.data
                total = int(d.get("total", 0) or 0)
                up = int(d.get("up", 0) or 0)
                if total > 0:
                    return {
                        "up": up,
                        "down": int(d.get("down", 0) or 0),
                        "flat": int(d.get("flat", 0) or 0),
                        "limit_up": int(d.get("limit_up", 0) or 0),
                        "limit_down": int(d.get("limit_down", 0) or 0),
                        "total": total,
                        "up_ratio": round(up / max(total, 1) * 100, 1),
                    }
        except Exception as e:
            logger.debug("fetch_limit_stats: %s", e)

        # 轻量兜底：SQLite stock_spot 抽样（不循环分页）
        try:
            from features.sqlite_data_layer import QIDataDB
            spot = QIDataDB().get_stock_spot()
            if spot is not None and not spot.empty:
                chg_col = next(
                    (c for c in spot.columns if c in ("change_pct", "涨跌幅")),
                    None,
                )
                if chg_col:
                    s = pd.to_numeric(spot[chg_col], errors="coerce").dropna()
                    up = int((s > 0).sum())
                    down = int((s < 0).sum())
                    flat = int((s == 0).sum())
                    total = len(s)
                    if total > 0:
                        return {
                            "up": up,
                            "down": down,
                            "flat": flat,
                            "limit_up": int((s >= 9.8).sum()),
                            "limit_down": int((s <= -9.8).sum()),
                            "total": total,
                            "up_ratio": round(up / total * 100, 1),
                        }
        except Exception as e:
            logger.debug("spot breadth fallback: %s", e)

        return {}

    def _load_northbound_yi(self) -> Optional[float]:
        try:
            from features.sqlite_data_layer import QIDataDB
            df = QIDataDB().get_northbound_flow(days=5)
            if df is not None and not df.empty:
                flow_col = next(
                    (c for c in df.columns if "net_flow" in c.lower() or "净流入" in str(c)),
                    df.columns[-1],
                )
                val = float(pd.to_numeric(df[flow_col].iloc[-1], errors="coerce"))
                if val == val:  # not NaN
                    return round(val / 1e8 if abs(val) > 1e6 else val, 2)
        except Exception as e:
            logger.debug("northbound sqlite: %s", e)

        try:
            from features.extended_data_sources import fetch_northbound_series
            res = fetch_northbound_series(days=5)
            if res.ok and isinstance(res.data, pd.DataFrame) and not res.data.empty:
                df = res.data
                flow_col = next(
                    (c for c in df.columns if "净流入" in str(c) or "net" in str(c).lower()),
                    df.columns[-1],
                )
                val = float(pd.to_numeric(df[flow_col].iloc[-1], errors="coerce"))
                if val == val:
                    return round(val / 1e8 if abs(val) > 1e6 else val, 2)
        except Exception as e:
            logger.debug("northbound series: %s", e)

        if self.cache:
            try:
                north = self.cache.get_northbound_flow()
                if north is not None and len(north) > 0:
                    latest = north.iloc[-1]
                    flow = latest.get("当日净流入", latest.get("当日资金流入", 0))
                    if isinstance(flow, (int, float)):
                        return round(float(flow) / 1e8 if abs(float(flow)) > 1e6 else float(flow), 2)
            except Exception:
                pass
        return None

    def get_summary_text(self) -> str:
        """生成市场摘要文本"""
        data = self.get_market_overview()
        lines = ["### 📊 市场大盘\n"]

        if data["indices"]:
            lines.append("**主要指数**:")
            for name, info in data["indices"].items():
                emoji = "🟢" if info["change_pct"] >= 0 else "🔴"
                lines.append(f"  {emoji} {name}: {info['price']:.2f} ({info['change_pct']:+.2f}%)")

        b = data.get("breadth", {})
        if b:
            lines.append(f"\n**涨跌统计**: 上涨 {b.get('up', 0)} 家 / 下跌 {b.get('down', 0)} 家 / 平盘 {b.get('flat', 0)} 家")
            lines.append(f"  涨停 {b.get('limit_up', 0)} 家 / 跌停 {b.get('limit_down', 0)} 家")
            ratio = b.get("up_ratio", 50)
            if ratio > 60:
                lines.append("  📈 市场偏强, 上涨家数占多数")
            elif ratio < 40:
                lines.append("  📉 市场偏弱, 下跌家数占多数")
            else:
                lines.append("  ⚖️ 市场均衡, 涨跌家数相当")

        ff = data.get("fund_flow", {})
        if "northbound" in ff:
            flow = ff["northbound"]
            direction = "净流入" if flow > 0 else "净流出"
            lines.append(f"\n**北向资金**: {direction} {abs(flow):.1f}亿")

        return "\n".join(lines)
