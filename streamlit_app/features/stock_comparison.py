"""
QuantInsight Pro - 股票对比工具 (Stock Comparator)
===================================================

最多5只股票横向对比:
- 估值对比 (PE/PB/PS/市值)
- 财务对比 (营收/利润/ROE)
- 技术对比 (涨跌幅/成交量)
- 雷达图可视化

License: MIT
"""

from __future__ import annotations

import logging
from typing import Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class StockComparator:
    """
    股票对比器

    使用示例:
        >>> comparator = StockComparator(cache_manager)
        >>> result = comparator.compare(["600519", "000858", "002594"])
    """

    def __init__(self, cache_manager=None):
        self.cache = cache_manager

    def compare(self, stock_codes: list[str]) -> dict:
        """
        对比多只股票

        Args:
            stock_codes: 股票代码列表 (最多5只)

        Returns:
            dict: {
                "comparison_df": DataFrame,
                "radar_data": dict,
                "summary": str,
            }
        """
        if not stock_codes:
            return {"comparison_df": pd.DataFrame(), "summary": "请提供股票代码"}

        stock_codes = stock_codes[:5]  # 最多5只

        # 从股票池获取数据
        profiles = []
        for code in stock_codes:
            profile = self._get_stock_data(code)
            if profile:
                profiles.append(profile)

        if not profiles:
            return {"comparison_df": pd.DataFrame(), "summary": "⚠️ 未找到相关股票数据"}

        df = pd.DataFrame(profiles)
        summary = self._generate_comparison_summary(df)
        radar_data = self._build_radar_data(df)

        return {
            "comparison_df": df,
            "radar_data": radar_data,
            "summary": summary,
        }

    def _get_stock_data(self, code_or_name: str) -> Optional[dict]:
        """获取单只股票数据 (支持代码或名称)"""
        if not self.cache:
            return {"代码": code_or_name, "名称": code_or_name, "最新价": 0, "涨跌幅": 0, "换手率": 0, "市盈率-动态": 0, "市净率": 0, "总市值": 0, "成交额": 0, "60日涨跌幅": 0}

        try:
            universe = self.cache.get_stock_universe(top_n=5000)
            if universe is not None:
                # Try matching by code first, then by name
                match = None
                if "代码" in universe.columns:
                    match = universe[universe["代码"] == code_or_name]
                if (match is None or len(match) == 0) and "名称" in universe.columns:
                    match = universe[universe["名称"].str.contains(code_or_name, na=False)]
                if match is not None and len(match) > 0:
                    row = match.iloc[0]
                    return {
                        "代码": row.get("代码", code_or_name),
                        "名称": row.get("名称", ""),
                        "最新价": float(row.get("最新价", 0)),
                        "涨跌幅": float(row.get("涨跌幅", 0)),
                        "换手率": float(row.get("换手率", 0)),
                        "市盈率-动态": float(row.get("市盈率-动态", 0)),
                        "市净率": float(row.get("市净率", 0)),
                        "总市值": float(row.get("总市值", 0)),
                        "成交额": float(row.get("成交额", 0)),
                        "60日涨跌幅": float(row.get("60日涨跌幅", 0)) if "60日涨跌幅" in universe.columns else 0,
                    }
        except Exception as e:
            logger.warning(f"获取 {code_or_name} 数据失败: {e}")

        return {"代码": code_or_name, "名称": code_or_name, "最新价": 0, "涨跌幅": 0, "换手率": 0, "市盈率-动态": 0, "市净率": 0, "总市值": 0, "成交额": 0, "60日涨跌幅": 0}

    def _build_radar_data(self, df: pd.DataFrame) -> dict:
        """构建雷达图数据 (归一化到0-1)"""
        dimensions = []
        # Pre-initialize values dict for all stock codes
        values = {code: [] for code in df["代码"]} if "代码" in df.columns else {}

        # PE (反向, 低好)
        if "市盈率-动态" in df.columns:
            pe = df["市盈率-动态"].clip(1, 200)
            pe_norm = 1 - (pe - pe.min()) / (pe.max() - pe.min() + 0.01)
            dimensions.append("估值(低PE)")
            for i, code in enumerate(df["代码"]):
                values.setdefault(code, []).append(float(pe_norm.iloc[i]))

        # 涨跌幅
        if "涨跌幅" in df.columns:
            chg = df["涨跌幅"].clip(-10, 10)
            chg_norm = (chg - chg.min()) / (chg.max() - chg.min() + 0.01)
            dimensions.append("短期动量")
            for i, code in enumerate(df["代码"]):
                values.setdefault(code, []).append(float(chg_norm.iloc[i]))

        # 换手率
        if "换手率" in df.columns:
            turn = df["换手率"].clip(0, 15)
            turn_norm = (turn - turn.min()) / (turn.max() - turn.min() + 0.01)
            dimensions.append("活跃度")
            for i, code in enumerate(df["代码"]):
                values.setdefault(code, []).append(float(turn_norm.iloc[i]))

        # 市值 (对数)
        if "总市值" in df.columns:
            cap = np.log10(df["总市值"].clip(1e8, 1e13))
            cap_norm = (cap - cap.min()) / (cap.max() - cap.min() + 0.01)
            dimensions.append("规模")
            for i, code in enumerate(df["代码"]):
                values.setdefault(code, []).append(float(cap_norm.iloc[i]))

        # 60日涨幅
        if "60日涨跌幅" in df.columns:
            p60 = df["60日涨跌幅"].clip(-30, 100)
            p60_norm = (p60 - p60.min()) / (p60.max() - p60.min() + 0.01)
            dimensions.append("中期动量")
            for i, code in enumerate(df["代码"]):
                values.setdefault(code, []).append(float(p60_norm.iloc[i]))

        return {"dimensions": dimensions, "values": values}

    def _generate_comparison_summary(self, df: pd.DataFrame) -> str:
        """生成对比摘要"""
        lines = ["### 📊 股票对比结果\n"]

        name_col = "名称" if "名称" in df.columns else None
        for _, row in df.iterrows():
            parts = []
            if "代码" in row:
                parts.append(f"**{row['代码']}**")
            if name_col and pd.notna(row.get("名称")):
                parts.append(row["名称"])
            if "最新价" in row and pd.notna(row["最新价"]):
                parts.append(f"¥{row['最新价']:.2f}")
            if "涨跌幅" in row and pd.notna(row["涨跌幅"]):
                parts.append(f"{row['涨跌幅']:+.2f}%")
            if "市盈率-动态" in row and pd.notna(row["市盈率-动态"]):
                parts.append(f"PE:{row['市盈率-动态']:.1f}")
            lines.append("- " + " | ".join(parts))

        # 推荐
        if "涨跌幅" in df.columns:
            best = df.loc[df["涨跌幅"].idxmax()]
            best_name = best.get("名称", best.get("代码", ""))
            lines.append(f"\n💡 **今日最强**: {best_name} ({best['涨跌幅']:+.2f}%)")

        if "市盈率-动态" in df.columns:
            valid_pe = df[(df["市盈率-动态"] > 0) & (df["市盈率-动态"] < 500)]
            if len(valid_pe) > 0:
                cheapest = valid_pe.loc[valid_pe["市盈率-动态"].idxmin()]
                cheap_name = cheapest.get("名称", cheapest.get("代码", ""))
                lines.append(f"💰 **最低估值**: {cheap_name} (PE: {cheapest['市盈率-动态']:.1f})")

        return "\n".join(lines)
