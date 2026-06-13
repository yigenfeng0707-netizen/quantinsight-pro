"""
QuantInsight Pro - 市场大盘面板 (Market Dashboard)
====================================================

实时市场概览: 指数/板块热力图/涨跌家数/资金流全景/市场宽度

License: MIT
"""

from __future__ import annotations
import logging
from typing import Optional
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class MarketDashboard:
    """市场大盘面板"""

    def __init__(self, cache_manager=None):
        self.cache = cache_manager

    def get_market_overview(self) -> dict:
        """获取市场概览数据"""
        result = {
            "indices": {},
            "breadth": {},
            "fund_flow": {},
            "sector_heatmap": [],
        }

        if not self.cache:
            return result

        # 指数数据
        for name, symbol in [("沪深300", "sh000300"), ("中证500", "sh000905"), ("创业板指", "sz399006")]:
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
            except Exception:
                pass

        # 涨跌家数
        try:
            universe = self.cache.get_stock_universe(top_n=5000)
            if universe is not None and "涨跌幅" in universe.columns:
                universe["涨跌幅"] = pd.to_numeric(universe["涨跌幅"], errors="coerce")
                up = (universe["涨跌幅"] > 0).sum()
                down = (universe["涨跌幅"] < 0).sum()
                flat = (universe["涨跌幅"] == 0).sum()
                limit_up = (universe["涨跌幅"] >= 9.5).sum()
                limit_down = (universe["涨跌幅"] <= -9.5).sum()
                result["breadth"] = {
                    "up": int(up), "down": int(down), "flat": int(flat),
                    "limit_up": int(limit_up), "limit_down": int(limit_down),
                    "total": len(universe),
                    "up_ratio": round(up / max(len(universe), 1) * 100, 1),
                }
        except Exception:
            pass

        # 北向资金
        try:
            north = self.cache.get_northbound_flow()
            if north is not None and len(north) > 0:
                latest = north.iloc[-1]
                flow = latest.get("当日净流入", latest.get("当日资金流入", 0))
                if isinstance(flow, (int, float)):
                    result["fund_flow"]["northbound"] = round(flow / 1e8, 2)
        except Exception:
            pass

        return result

    def get_summary_text(self) -> str:
        """生成市场摘要文本"""
        data = self.get_market_overview()
        lines = ["### 📊 市场大盘\n"]

        # 指数
        if data["indices"]:
            lines.append("**主要指数**:")
            for name, info in data["indices"].items():
                emoji = "🟢" if info["change_pct"] >= 0 else "🔴"
                lines.append(f"  {emoji} {name}: {info['price']:.2f} ({info['change_pct']:+.2f}%)")

        # 涨跌家数
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

        # 北向资金
        ff = data.get("fund_flow", {})
        if "northbound" in ff:
            flow = ff["northbound"]
            direction = "净流入" if flow > 0 else "净流出"
            lines.append(f"\n**北向资金**: {direction} {abs(flow):.1f}亿")

        return "\n".join(lines)
