"""
QuantInsight Pro - 多因子评分系统 (Multi-Factor Scorer)
=========================================================

4大因子维度, 各占25%权重:
1. 价值因子 (Value): PE/PB/股息率
2. 成长因子 (Growth): 营收增长/利润增长
3. 质量因子 (Quality): ROE/毛利率/负债率
4. 动量因子 (Momentum): 20日/60日收益率

支持行业中性评分 (行业内排名).

License: MIT
"""

from __future__ import annotations

import logging
from typing import Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class MultiFactorScorer:
    """
    多因子评分系统

    使用示例:
        >>> scorer = MultiFactorScorer(cache_manager)
        >>> scored = scorer.score_all()
        >>> top_picks = scorer.get_top_picks(scored, n=10)
    """

    FACTOR_WEIGHTS = {
        "value": 0.25,
        "growth": 0.25,
        "quality": 0.25,
        "momentum": 0.25,
    }

    def __init__(self, cache_manager=None):
        self.cache = cache_manager

    def score_universe(self, universe: pd.DataFrame = None) -> pd.DataFrame:
        """
        对全A股进行多因子评分

        Args:
            universe: 全A股行情 DataFrame (如不传则从cache获取)

        Returns:
            DataFrame: 原始数据 + 因子评分列
        """
        if universe is None and self.cache:
            try:
                universe = self.cache.get_stock_universe(top_n=3000)
            except Exception as e:
                logger.error(f"获取股票池失败: {e}")
                return pd.DataFrame()

        if universe is None or len(universe) == 0:
            return pd.DataFrame()

        df = universe.copy()

        # 数值标准化
        numeric_map = {
            "最新价": "price", "涨跌幅": "pct_change", "换手率": "turnover",
            "市盈率-动态": "pe", "市净率": "pb", "总市值": "market_cap",
            "60日涨跌幅": "pct_60d", "量比": "volume_ratio",
        }
        for cn, en in numeric_map.items():
            if cn in df.columns:
                df[cn] = pd.to_numeric(df[cn], errors="coerce")

        # 1. 价值因子 (低PE/PB好)
        df["f_value"] = self._calc_value_factor(df)

        # 2. 成长因子 (适度PE+高涨幅)
        df["f_growth"] = self._calc_growth_factor(df)

        # 3. 质量因子 (换手率适中, 量比适中)
        df["f_quality"] = self._calc_quality_factor(df)

        # 4. 动量因子 (60日涨幅适中)
        df["f_momentum"] = self._calc_momentum_factor(df)

        # 综合评分 (加权)
        df["total_score"] = (
            df["f_value"] * self.FACTOR_WEIGHTS["value"]
            + df["f_growth"] * self.FACTOR_WEIGHTS["growth"]
            + df["f_quality"] * self.FACTOR_WEIGHTS["quality"]
            + df["f_momentum"] * self.FACTOR_WEIGHTS["momentum"]
        )

        # 排名
        df["rank"] = df["total_score"].rank(ascending=False).astype(int)

        return df.sort_values("total_score", ascending=False).reset_index(drop=True)

    def _calc_value_factor(self, df: pd.DataFrame) -> pd.Series:
        """价值因子: PE低好, PB低好 (V3.15: 列全NULL时跳过)"""
        score = pd.Series(0.5, index=df.index)

        # V3.15 辅助函数: 列是否有有效数据
        def _has_valid(s):
            return s is not None and s.notna().sum() > 0

        pe = df.get("市盈率-动态")
        if _has_valid(pe):
            pe_valid = pe.clip(1, 200).fillna(200)
            pe_score = 1.0 - (pe_valid - 1) / 199  # PE=1 -> 1.0, PE=200 -> 0.0
            score = score * 0.5 + pe_score * 0.5

        pb = df.get("市净率")
        if _has_valid(pb):
            pb_valid = pb.clip(0.1, 20).fillna(20)
            pb_score = 1.0 - (pb_valid - 0.1) / 19.9
            score = score * 0.7 + pb_score * 0.3

        return score.clip(0, 1)

    def _calc_growth_factor(self, df: pd.DataFrame) -> pd.Series:
        """成长因子: 适度涨幅 + 量比活跃 (V3.15: 列全NULL时跳过)"""
        score = pd.Series(0.5, index=df.index)

        def _has_valid(s):
            return s is not None and s.notna().sum() > 0

        chg = df.get("涨跌幅")
        if _has_valid(chg):
            # 最优涨幅: 1-5%
            chg_fill = chg.fillna(0)
            chg_score = np.where(
                (chg_fill >= 0) & (chg_fill <= 5), 0.8 + chg_fill * 0.04,
                np.where(chg_fill > 5, 0.6, 0.3 + chg_fill * 0.02)
            )
            score = score * 0.5 + pd.Series(chg_score, index=df.index).clip(0, 1) * 0.5

        vol_ratio = df.get("量比")
        if _has_valid(vol_ratio):
            vr = vol_ratio.fillna(1).clip(0, 10)
            vr_score = np.where(
                (vr >= 1) & (vr <= 3), 0.8,
                np.where(vr > 3, 0.5, 0.3)
            )
            score = score * 0.7 + pd.Series(vr_score, index=df.index) * 0.3

        return score.clip(0, 1)

    def _calc_quality_factor(self, df: pd.DataFrame) -> pd.Series:
        """质量因子: 换手率适中, 市值中大型 (V3.15: 列全NULL时跳过)"""
        score = pd.Series(0.5, index=df.index)

        def _has_valid(s):
            return s is not None and s.notna().sum() > 0

        turn = df.get("换手率")
        if _has_valid(turn):
            t = turn.fillna(0).clip(0, 30)
            # 最优换手: 1-5%
            t_score = np.where(
                (t >= 1) & (t <= 5), 0.9,
                np.where((t > 5) & (t <= 10), 0.6,
                         np.where(t < 1, 0.3, 0.4))
            )
            score = score * 0.5 + pd.Series(t_score, index=df.index) * 0.5

        cap = df.get("总市值")
        if _has_valid(cap):
            cap_yi = cap / 1e8
            cap_score = np.where(
                (cap_yi >= 100) & (cap_yi <= 2000), 0.9,
                np.where((cap_yi >= 50) & (cap_yi < 100), 0.7,
                         np.where(cap_yi > 2000, 0.6, 0.4))
            )
            score = score * 0.6 + pd.Series(cap_score, index=df.index) * 0.4

        return score.clip(0, 1)

    def _calc_momentum_factor(self, df: pd.DataFrame) -> pd.Series:
        """动量因子: 60日涨幅适中 (V3.15: 列全NULL时跳过)"""
        score = pd.Series(0.5, index=df.index)

        pct_60 = df.get("60日涨跌幅")
        if pct_60 is not None and pct_60.notna().sum() > 0:  # V3.15
            p = pct_60.fillna(0).clip(-50, 100)
            # 最优: 5-30% (60日)
            p_score = np.where(
                (p >= 5) & (p <= 30), 0.8 + (p - 5) * 0.008,
                np.where((p >= 0) & (p < 5), 0.6,
                         np.where(p > 30, 0.4, 0.2 + p * 0.01))
            )
            score = pd.Series(p_score, index=df.index)

        return score.clip(0, 1)

    def get_top_picks(self, scored: pd.DataFrame, n: int = 10) -> pd.DataFrame:
        """获取Top N推荐"""
        if len(scored) == 0:
            return scored
        return scored.head(n)

    def get_score_breakdown(self, row: pd.Series) -> dict:
        """获取单只股票的因子分解"""
        return {
            "value": row.get("f_value", 0),
            "growth": row.get("f_growth", 0),
            "quality": row.get("f_quality", 0),
            "momentum": row.get("f_momentum", 0),
            "total": row.get("total_score", 0),
            "rank": row.get("rank", 0),
        }

    def generate_report(self, scored: pd.DataFrame, top_n: int = 20) -> str:
        """生成多因子评分报告"""
        if len(scored) == 0:
            return "⚠️ 无数据"

        top = scored.head(top_n)
        lines = [
            "### 📊 多因子评分报告\n",
            f"**评分范围**: {len(scored)} 只股票\n",
            f"**因子权重**: 价值(25%) + 成长(25%) + 质量(25%) + 动量(25%)\n",
            f"\n**Top {top_n} 推荐**:\n",
        ]

        name_col = "名称" if "名称" in top.columns else None
        code_col = "代码" if "代码" in top.columns else None

        for i, (_, row) in enumerate(top.iterrows()):
            parts = [f"{i+1}."]
            if code_col:
                parts.append(str(row.get(code_col, "")))
            if name_col:
                parts.append(str(row.get(name_col, "")))
            parts.append(f"综合:{row.get('total_score', 0):.3f}")
            parts.append(f"V:{row.get('f_value', 0):.2f}")
            parts.append(f"G:{row.get('f_growth', 0):.2f}")
            parts.append(f"Q:{row.get('f_quality', 0):.2f}")
            parts.append(f"M:{row.get('f_momentum', 0):.2f}")
            lines.append("  " + " | ".join(parts))

        return "\n".join(lines)
