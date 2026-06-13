"""
QuantInsight Pro - 智能选股引擎 (Stock Screener)
==================================================

对标 AI涨乐 的"一句话选股"功能:
- 自然语言 → 结构化筛选条件
- 多维度过滤 (估值/成长/质量/动量/资金流)
- 可解释的推荐逻辑

License: MIT
"""

from __future__ import annotations

import json
import logging
import re
from typing import Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class NaturalLanguageScreener:
    """
    自然语言选股引擎

    使用示例:
        >>> screener = NaturalLanguageScreener(cache_manager, llm_config)
        >>> result = screener.screen("找出低估值高分红的银行股")
        >>> print(result["summary"])
    """

    # 快捷条件模板
    QUICK_TEMPLATES = {
        "低估值蓝筹": {"pe_max": 15, "pb_max": 2, "market_cap_min": 200},
        "高成长小盘": {"pe_min": 20, "pe_max": 60, "market_cap_max": 100},
        "高股息防御": {"dividend_yield_min": 3, "pe_max": 20},
        "强势突破": {"pct_change_min": 3, "turnover_min": 3},
        "超跌反弹": {"pct_change_max": -5, "pe_max": 30},
    }

    def __init__(self, cache_manager=None, llm_config: dict = None):
        self.cache = cache_manager
        self.llm_config = llm_config or {}

    def screen(self, query: str, top_n: int = 20) -> dict:
        """
        执行自然语言选股

        Args:
            query: 自然语言查询
            top_n: 返回前N只

        Returns:
            dict: {
                "query": str,
                "filters": dict,
                "results": DataFrame,
                "summary": str,
                "total_matched": int,
            }
        """
        # 1. 解析条件
        filters = self._parse_query(query)

        # 2. 获取股票池
        universe = self._get_universe()
        if universe is None or len(universe) == 0:
            return {
                "query": query,
                "filters": filters,
                "results": pd.DataFrame(),
                "summary": "⚠️ 股票池数据不可用, 请检查网络连接.",
                "total_matched": 0,
            }

        # 3. 执行筛选
        filtered = self._apply_filters(universe, filters)

        # 4. 评分排序
        scored = self._score_and_sort(filtered)

        # 5. 取 Top N
        top_results = scored.head(top_n)

        # 6. 生成摘要
        summary = self._generate_summary(query, filters, universe, filtered, top_results)

        return {
            "query": query,
            "filters": filters,
            "results": top_results,
            "summary": summary,
            "total_matched": len(filtered),
            "total_universe": len(universe),
        }

    def _parse_query(self, query: str) -> dict:
        """解析自然语言为过滤条件"""
        # 尝试 LLM 解析
        if self.llm_config and self.llm_config.get("api_key"):
            try:
                return self._llm_parse(query)
            except Exception as e:
                logger.warning(f"LLM 解析失败: {e}")

        # Fallback: 规则解析
        return self._rule_parse(query)

    def _llm_parse(self, query: str) -> dict:
        """LLM 解析自然语言条件"""
        import requests

        system = """将选股条件解析为JSON (不要markdown):
{
  "sector": "行业(可选)",
  "pe_max": 数值, "pe_min": 数值,
  "pb_max": 数值, "pb_min": 数值,
  "market_cap_min": 亿元, "market_cap_max": 亿元,
  "pct_change_min": %, "pct_change_max": %,
  "turnover_min": %, "turnover_max": %,
  "price_min": 元, "price_max": 元,
  "keywords": ["关键词"],
  "sort_by": "排序字段", "sort_asc": false,
  "top_n": 20
}"""
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": f"解析: {query}"},
        ]

        headers = {"Authorization": f"Bearer {self.llm_config['api_key']}", "Content-Type": "application/json"}
        payload = {"model": self.llm_config["model"], "messages": messages, "temperature": 0.3, "max_tokens": 500}

        resp = requests.post(self.llm_config["base_url"], headers=headers, json=payload, timeout=15)
        resp.raise_for_status()
        content = resp.json()["choices"][0]["message"].get("content", "")

        json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', content, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        return self._rule_parse(query)

    def _rule_parse(self, query: str) -> dict:
        """规则解析"""
        f = {}

        # 估值
        if any(kw in query for kw in ["低估值", "便宜", "低PE"]):
            f["pe_max"] = 20
        if any(kw in query for kw in ["高分红", "高股息", "红利"]):
            f.setdefault("pe_max", 25)
        if any(kw in query for kw in ["高成长", "高增长"]):
            f["pe_min"] = 15
            f["pe_max"] = 80

        # 市值
        if any(kw in query for kw in ["大盘", "蓝筹"]):
            f["market_cap_min"] = 500
        if any(kw in query for kw in ["小盘", "中小"]):
            f["market_cap_max"] = 200
        if "微盘" in query:
            f["market_cap_max"] = 50

        # 行业
        industries = {
            "银行": ["银行", "工商银行", "招商银行"],
            "新能源": ["新能源", "宁德时代", "隆基", "比亚迪"],
            "半导体": ["半导体", "芯片", "中芯", "北方华创"],
            "医药": ["医药", "恒瑞", "药明", "迈瑞"],
            "白酒": ["白酒", "茅台", "五粮液", "泸州老窖"],
            "消费": ["消费", "食品", "饮料"],
            "军工": ["军工", "国防", "航空"],
            "房地产": ["房地产", "地产", "万科", "保利"],
            "证券": ["证券", "券商", "中信证券"],
            "AI": ["AI", "人工智能", "算力", "大模型"],
            "汽车": ["汽车", "新能源车"],
        }
        for industry, keywords in industries.items():
            if any(kw in query for kw in keywords):
                f["keywords"] = [industry]
                break

        # 动量
        if any(kw in query for kw in ["涨停", "强势", "突破"]):
            f["pct_change_min"] = 5
        if any(kw in query for kw in ["跌停", "超跌", "下跌"]):
            f["pct_change_max"] = -3

        f.setdefault("top_n", 20)
        return f

    def _get_universe(self) -> Optional[pd.DataFrame]:
        """获取股票池"""
        if self.cache:
            try:
                return self.cache.get_stock_universe(top_n=3000)
            except Exception as e:
                logger.warning(f"获取股票池失败: {e}")
        return None

    def _apply_filters(self, universe: pd.DataFrame, filters: dict) -> pd.DataFrame:
        """应用过滤条件"""
        df = universe.copy()

        # 数值列标准化
        numeric_cols = {
            "最新价": "price", "涨跌幅": "pct_change", "成交量": "volume",
            "成交额": "amount", "振幅": "amplitude", "换手率": "turnover",
            "市盈率-动态": "pe", "市净率": "pb", "总市值": "market_cap",
            "60日涨跌幅": "pct_60d",
        }

        for cn_col, en_name in numeric_cols.items():
            if cn_col in df.columns:
                df[cn_col] = pd.to_numeric(df[cn_col], errors="coerce")

        # PE 过滤
        pe_col = "市盈率-动态" if "市盈率-动态" in df.columns else None
        if pe_col:
            if "pe_max" in filters:
                df = df[(df[pe_col] <= filters["pe_max"]) & (df[pe_col] > 0)]
            if "pe_min" in filters:
                df = df[df[pe_col] >= filters["pe_min"]]

        # PB 过滤
        pb_col = "市净率" if "市净率" in df.columns else None
        if pb_col:
            if "pb_max" in filters:
                df = df[(df[pb_col] <= filters["pb_max"]) & (df[pb_col] > 0)]
            if "pb_min" in filters:
                df = df[df[pb_col] >= filters["pb_min"]]

        # 市值过滤 (东方财富返回的是元, 需转换为亿)
        cap_col = "总市值" if "总市值" in df.columns else None
        if cap_col:
            if "market_cap_min" in filters:
                df = df[df[cap_col] >= filters["market_cap_min"] * 1e8]
            if "market_cap_max" in filters:
                df = df[df[cap_col] <= filters["market_cap_max"] * 1e8]

        # 涨跌幅过滤
        chg_col = "涨跌幅" if "涨跌幅" in df.columns else None
        if chg_col:
            if "pct_change_min" in filters:
                df = df[df[chg_col] >= filters["pct_change_min"]]
            if "pct_change_max" in filters:
                df = df[df[chg_col] <= filters["pct_change_max"]]

        # 换手率过滤
        turn_col = "换手率" if "换手率" in df.columns else None
        if turn_col:
            if "turnover_min" in filters:
                df = df[df[turn_col] >= filters["turnover_min"]]

        # 价格过滤
        price_col = "最新价" if "最新价" in df.columns else None
        if price_col:
            if "price_min" in filters:
                df = df[df[price_col] >= filters["price_min"]]
            if "price_max" in filters:
                df = df[df[price_col] <= filters["price_max"]]

        # 关键词过滤
        name_col = "名称" if "名称" in df.columns else None
        if name_col and "keywords" in filters:
            mask = pd.Series([False] * len(df), index=df.index)
            for kw in filters["keywords"]:
                # 搜索行业名称或相关关键词
                mask |= df[name_col].str.contains(kw, na=False)
            if mask.any():
                df = df[mask]

        return df.reset_index(drop=True)

    def _score_and_sort(self, df: pd.DataFrame) -> pd.DataFrame:
        """综合评分排序"""
        if len(df) == 0:
            return df

        df = df.copy()
        df["_score"] = 0.0

        # PE 评分 (低PE好, 权重30%)
        pe_col = "市盈率-动态" if "市盈率-动态" in df.columns else None
        if pe_col:
            pe = df[pe_col].clip(1, 200).fillna(200)
            df["_score"] += (1 / pe) * 30

        # 涨跌幅评分 (适度涨幅好, 0-5%, 权重20%)
        chg_col = "涨跌幅" if "涨跌幅" in df.columns else None
        if chg_col:
            chg = df[chg_col].fillna(0)
            df["_score"] += chg.clip(-10, 10) * 0.5

        # 换手率评分 (适度换手好, 1-5%, 权重20%)
        turn_col = "换手率" if "换手率" in df.columns else None
        if turn_col:
            turn = df[turn_col].fillna(0)
            optimal = 3.0
            df["_score"] += (1 / (1 + abs(turn - optimal))) * 10

        # 市值评分 (中大盘稳定, 权重15%)
        cap_col = "总市值" if "总市值" in df.columns else None
        if cap_col:
            cap_yi = df[cap_col] / 1e8
            # 100-1000亿最优
            df["_score"] += np.where(
                (cap_yi >= 100) & (cap_yi <= 1000), 5,
                np.where((cap_yi >= 50) & (cap_yi < 100), 3, 1)
            )

        # PB 评分 (低PB好, 权重15%)
        pb_col = "市净率" if "市净率" in df.columns else None
        if pb_col:
            pb = df[pb_col].clip(0.1, 20).fillna(20)
            df["_score"] += (1 / pb) * 5

        return df.sort_values("_score", ascending=False).reset_index(drop=True)

    def _generate_summary(self, query, filters, universe, filtered, top_results) -> str:
        """生成选股结果摘要"""
        lines = [
            f"### 🎯 智能选股结果\n",
            f"**查询**: {query}\n",
            f"**筛选范围**: {len(universe)} 只 → **符合条件**: {len(filtered)} 只\n",
        ]

        # 显示过滤条件
        filter_desc = []
        if "pe_max" in filters:
            filter_desc.append(f"PE ≤ {filters['pe_max']}")
        if "market_cap_min" in filters:
            filter_desc.append(f"市值 ≥ {filters['market_cap_min']}亿")
        if "keywords" in filters:
            filter_desc.append(f"行业: {', '.join(filters['keywords'])}")
        if "pct_change_min" in filters:
            filter_desc.append(f"涨幅 ≥ {filters['pct_change_min']}%")
        if filter_desc:
            lines.append(f"**筛选条件**: {' | '.join(filter_desc)}\n")

        if len(top_results) == 0:
            lines.append("\n⚠️ 未找到符合条件的股票, 建议放宽筛选条件.")
            return "\n".join(lines)

        # 结果表格
        lines.append(f"\n**Top {len(top_results)} 推荐**:\n")

        display_cols = []
        for col in ["代码", "名称", "最新价", "涨跌幅", "换手率", "市盈率-动态", "市净率", "总市值"]:
            if col in top_results.columns:
                display_cols.append(col)

        for i, (_, row) in enumerate(top_results.iterrows()):
            parts = [f"{i+1}."]
            for col in display_cols:
                val = row.get(col)
                if pd.notna(val):
                    if col == "涨跌幅":
                        parts.append(f"{val:+.2f}%")
                    elif col == "总市值":
                        parts.append(f"市值:{val/1e8:.0f}亿")
                    elif col in ("最新价", "换手率", "市盈率-动态", "市净率"):
                        parts.append(f"{col}:{val:.2f}")
                    else:
                        parts.append(str(val))
            lines.append("  " + " | ".join(parts))

        # 推荐逻辑
        lines.append(f"\n\n💡 **推荐逻辑**: 综合估值(PE/PB)、动量(涨跌幅)、活跃度(换手率)和规模(市值)进行多维度评分排序.")
        lines.append("\n⚠️ *以上结果仅供参考, 不构成投资建议.*")

        return "\n".join(lines)
