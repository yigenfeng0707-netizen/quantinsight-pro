"""
QuantInsight Pro - 智能选股引擎 (Stock Screener)
==================================================

业内领先的"一句话选股"功能:
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

    def screen(self, query: str, top_n: int = 20, universe: pd.DataFrame = None) -> dict:
        """
        执行自然语言选股

        Args:
            query: 自然语言查询
            top_n: 返回前N只
            universe: 直接传入股票池 (V3.14: 优先使用, 避免cache注入失败)

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

        # 2. 获取股票池 (V3.14: 优先使用直接传入的 universe)
        if universe is not None and len(universe) > 0:
            df_universe = universe
        else:
            df_universe = self._get_universe()
        if df_universe is None or len(df_universe) == 0:
            return {
                "query": query,
                "filters": filters,
                "results": pd.DataFrame(),
                "summary": "⚠️ 股票池数据不可用, 请检查网络连接.",
                "total_matched": 0,
            }

        # 3. 执行筛选
        filtered = self._apply_filters(df_universe, filters)

        # 4. 评分排序
        scored = self._score_and_sort(filtered)

        # 5. 取 Top N
        top_results = scored.head(top_n)

        # 6. 生成摘要
        summary = self._generate_summary(query, filters, df_universe, filtered, top_results)

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
        if self.llm_config.get('workspace_id'):
            headers['X-DashScope-WorkSpace'] = self.llm_config['workspace_id']
        is_reasoning = 'v4' in self.llm_config.get('model', '') or 'r1' in self.llm_config.get('model', '')
        payload = {"model": self.llm_config["model"], "messages": messages, "temperature": 0.3, "max_tokens": 1000 if is_reasoning else 500}
        # V3.12: qwen3.x 推理模型禁用思考, 避免超时
        model_name_lower = self.llm_config.get('model', '').lower()
        if 'qwen3' in model_name_lower or 'qwen-3' in model_name_lower:
            payload['enable_thinking'] = False

        resp = requests.post(self.llm_config["base_url"], headers=headers, json=payload, timeout=90)  # V3.14: 30→90
        resp.raise_for_status()
        msg = resp.json()["choices"][0]["message"]
        content = msg.get("content", "") or ""
        reasoning = msg.get("reasoning_content", "") or ""
        if not content.strip() and reasoning.strip():
            content = reasoning

        json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', content, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        return self._rule_parse(query)

    def _rule_parse(self, query: str) -> dict:
        """增强规则解析 - 支持常见中文选股查询模式"""
        f = {}

        # ---- 数值提取辅助 ----
        def _extract_num(pattern, text, group=1):
            m = re.search(pattern, text)
            return float(m.group(group)) if m else None

        # ---- 市盈率 (PE) ----
        # "市盈率小于20" / "PE<20" / "市盈率低于30"
        pe_val = _extract_num(r'(?:市盈率|PE|pe)[^\d]*?(?:小于|低于|不超过|<|＜|不超过)\s*(\d+\.?\d*)', query)
        if pe_val is not None:
            f["pe_max"] = pe_val
        pe_val = _extract_num(r'(?:市盈率|PE|pe)[^\d]*?(?:大于|高于|超过|>|＞)\s*(\d+\.?\d*)', query)
        if pe_val is not None:
            f["pe_min"] = pe_val
        # 关键词兜底
        if "pe_max" not in f and any(kw in query for kw in ["低估值", "便宜", "低PE"]):
            f["pe_max"] = 20
        if "pe_min" not in f and any(kw in query for kw in ["高成长", "高增长"]):
            f["pe_min"] = 15
            f.setdefault("pe_max", 80)

        # ---- ROE ----
        roe_val = _extract_num(r'(?:ROE|roe|净资产收益率)[^\d]*?(?:大于|高于|超过|>|＞)\s*(\d+\.?\d*)', query)
        if roe_val is not None:
            f["roe_min"] = roe_val
        roe_val = _extract_num(r'(?:ROE|roe|净资产收益率)[^\d]*?(?:小于|低于|不超过|<|＜)\s*(\d+\.?\d*)', query)
        if roe_val is not None:
            f["roe_max"] = roe_val

        # ---- 股价区间 ----
        # "股价在50到100之间" / "价格50-100" / "股价大于50"
        price_low = _extract_num(r'(?:股价|价格|现价)[^\d]*?(?:在|从)?\s*(\d+\.?\d*)\s*(?:到|至|-|—|~)', query)
        price_high = _extract_num(r'(?:股价|价格|现价)[^\d]*?(?:到|至|-|—|~)\s*(\d+\.?\d*)', query)
        if price_low is not None:
            f["price_min"] = price_low
        if price_high is not None:
            f["price_max"] = price_high
        # "股价大于50" / "股价超过100"
        price_val = _extract_num(r'(?:股价|价格|现价)[^\d]*?(?:大于|高于|超过|>|＞)\s*(\d+\.?\d*)', query)
        if price_val is not None and "price_min" not in f:
            f["price_min"] = price_val
        price_val = _extract_num(r'(?:股价|价格|现价)[^\d]*?(?:小于|低于|不超过|<|＜)\s*(\d+\.?\d*)', query)
        if price_val is not None and "price_max" not in f:
            f["price_max"] = price_val

        # ---- 市值 ----
        # "市值超过1000亿" / "市值大于500亿" / "市值小于100亿"
        cap_val = _extract_num(r'(?:市值|总市值)[^\d]*?(?:超过|大于|高于|>|＞)\s*(\d+\.?\d*)\s*亿', query)
        if cap_val is not None:
            f["market_cap_min"] = cap_val
        cap_val = _extract_num(r'(?:市值|总市值)[^\d]*?(?:小于|低于|不超过|<|＜)\s*(\d+\.?\d*)\s*亿', query)
        if cap_val is not None:
            f["market_cap_max"] = cap_val
        # 万亿级别
        cap_val = _extract_num(r'(?:市值|总市值)[^\d]*?(?:超过|大于|高于|>|＞)\s*(\d+\.?\d*)\s*万亿', query)
        if cap_val is not None:
            f["market_cap_min"] = cap_val * 10000
        # 关键词兜底
        if "market_cap_min" not in f and any(kw in query for kw in ["大盘", "蓝筹"]):
            f["market_cap_min"] = 500
        if "market_cap_max" not in f and any(kw in query for kw in ["小盘", "中小"]):
            f["market_cap_max"] = 200
        if "微盘" in query:
            f["market_cap_max"] = 50

        # ---- 营收增长 ----
        # "连续3年营收增长" / "营收增长超过20%"
        rev_val = _extract_num(r'(?:营收|收入|营业收入)[^\d]*?(?:增长|增速|同比)[^\d]*?(?:超过|大于|高于|>|＞)?\s*(\d+\.?\d*)\s*%?', query)
        if rev_val is not None:
            f["revenue_growth_min"] = rev_val
        # "连续N年营收增长"
        years_val = _extract_num(r'连续\s*(\d+)\s*年(?:营收|收入|盈利)?增长', query)
        if years_val is not None:
            f["revenue_growth_years"] = int(years_val)
            f.setdefault("revenue_growth_min", 0)
        if any(kw in query for kw in ["高成长", "高增长", "连续增长"]):
            f.setdefault("revenue_growth_min", 10)

        # ---- 行业 ----
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
            "保险": ["保险", "中国平安", "人寿"],
            "钢铁": ["钢铁", "宝钢"],
            "煤炭": ["煤炭", "中国神华"],
            "电力": ["电力", "长江电力", "华能"],
        }
        for industry, keywords in industries.items():
            if any(kw in query for kw in keywords):
                f["keywords"] = [industry]
                break

        # ---- 高分红/股息 ----
        if any(kw in query for kw in ["高分红", "高股息", "红利"]):
            f.setdefault("pe_max", 25)
            f["dividend_yield_min"] = 3

        # ---- 动量 ----
        if any(kw in query for kw in ["涨停", "强势", "突破"]):
            f["pct_change_min"] = 5
        if any(kw in query for kw in ["跌停", "超跌", "下跌"]):
            f["pct_change_max"] = -3
        # "涨幅超过5%" / "涨幅大于3%"
        chg_val = _extract_num(r'(?:涨幅|涨跌)[^\d]*?(?:超过|大于|高于|>|＞)\s*(\d+\.?\d*)', query)
        if chg_val is not None:
            f["pct_change_min"] = chg_val
        chg_val = _extract_num(r'(?:跌幅|跌)[^\d]*?(?:超过|大于|高于|>|＞)\s*(\d+\.?\d*)', query)
        if chg_val is not None:
            f["pct_change_max"] = -chg_val

        # ---- 换手率 ----
        turn_val = _extract_num(r'(?:换手率)[^\d]*?(?:大于|高于|超过|>|＞)\s*(\d+\.?\d*)', query)
        if turn_val is not None:
            f["turnover_min"] = turn_val

        # ---- 排序 ----
        if any(kw in query for kw in ["涨幅最大", "涨幅排序", "涨幅前"]):
            f["sort_by"] = "pct_change"
            f["sort_asc"] = False
        elif any(kw in query for kw in ["估值最低", "PE最低", "市盈率最低"]):
            f["sort_by"] = "pe"
            f["sort_asc"] = True
        elif any(kw in query for kw in ["市值最大", "市值排序"]):
            f["sort_by"] = "market_cap"
            f["sort_asc"] = False
        elif any(kw in query for kw in ["股息最高", "分红最高"]):
            f["sort_by"] = "dividend_yield"
            f["sort_asc"] = False

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
        """应用过滤条件 (V3.14: 列全NULL时跳过该过滤条件)"""
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

        # V3.14 辅助函数: 检查列是否有有效数据
        def _has_valid_data(col_name):
            if col_name not in df.columns:
                return False
            return df[col_name].notna().sum() > 0

        # PE 过滤 (V3.14: 列全NULL时跳过)
        pe_col = "市盈率-动态" if "市盈率-动态" in df.columns else None
        if pe_col and _has_valid_data(pe_col):
            if "pe_max" in filters:
                df = df[(df[pe_col] <= filters["pe_max"]) & (df[pe_col] > 0)]
            if "pe_min" in filters:
                df = df[df[pe_col] >= filters["pe_min"]]

        # PB 过滤 (V3.14: 列全NULL时跳过)
        pb_col = "市净率" if "市净率" in df.columns else None
        if pb_col and _has_valid_data(pb_col):
            if "pb_max" in filters:
                df = df[(df[pb_col] <= filters["pb_max"]) & (df[pb_col] > 0)]
            if "pb_min" in filters:
                df = df[df[pb_col] >= filters["pb_min"]]

        # 市值过滤 (东方财富返回的是元, 需转换为亿) (V3.14: 列全NULL时跳过)
        cap_col = "总市值" if "总市值" in df.columns else None
        if cap_col and _has_valid_data(cap_col):
            if "market_cap_min" in filters:
                df = df[df[cap_col] >= filters["market_cap_min"] * 1e8]
            if "market_cap_max" in filters:
                df = df[df[cap_col] <= filters["market_cap_max"] * 1e8]

        # 涨跌幅过滤
        chg_col = "涨跌幅" if "涨跌幅" in df.columns else None
        if chg_col and _has_valid_data(chg_col):
            if "pct_change_min" in filters:
                df = df[df[chg_col] >= filters["pct_change_min"]]
            if "pct_change_max" in filters:
                df = df[df[chg_col] <= filters["pct_change_max"]]

        # 换手率过滤 (V3.14: 列全NULL时跳过)
        turn_col = "换手率" if "换手率" in df.columns else None
        if turn_col and _has_valid_data(turn_col):
            if "turnover_min" in filters:
                df = df[df[turn_col] >= filters["turnover_min"]]

        # 价格过滤
        price_col = "最新价" if "最新价" in df.columns else None
        if price_col and _has_valid_data(price_col):
            if "price_min" in filters:
                df = df[df[price_col] >= filters["price_min"]]
            if "price_max" in filters:
                df = df[df[price_col] <= filters["price_max"]]

        # 关键词过滤 (V3.14: 扩展行业关键词映射)
        name_col = "名称" if "名称" in df.columns else None
        if name_col and "keywords" in filters:
            # 行业关键词扩展映射
            industry_expand = {
                "消费": ["消费", "食品", "饮料", "乳", "酒", "茅", "五粮", "泸州", "美的", "海尔", "格力", "伊利", "蒙牛", "海天", "安井", "永辉", "苏宁", "王府井"],
                "白酒": ["茅", "五粮", "泸州", "老窖", "汾酒", "洋河", "古井", "今世缘", "水井坊", "舍得", "酒鬼", "迎驾", "口子"],
                "新能源": ["新能源", "宁德", "比亚迪", "隆基", "阳光电源", "通威", "特变", "晶澳", "天合", "亿纬", "赣锋", "天齐", "华友"],
                "半导体": ["半导体", "芯片", "集成电路", "中芯", "华虹", "韦尔", "兆易", "北方华创", "中微", "紫光", "长电", "通富", "华天", "晶晨", "圣邦", "澜起", "汇顶"],
                "银行": ["银行", "工商银行", "建设银行", "农业银行", "中国银行", "招商银行", "兴业银行", "交通银行", "邮储", "平安银行", "中信银行", "浦发", "民生", "光大"],
                "医药": ["医药", "恒瑞", "药明", "迈瑞", "片仔癀", "云南白药", "复星", "华润", "智飞", "长春高新", "百济神州", "信达"],
                "证券": ["证券", "券商", "中信证券", "海通", "国泰", "华泰", "招商证券", "广发", "东方财富", "中金"],
                "保险": ["保险", "中国平安", "人寿", "太保", "新华保险", "人保"],
                "房地产": ["房地产", "地产", "万科", "保利", "招商蛇口", "绿地", "华夏幸福", "碧桂园"],
                "AI": ["AI", "人工智能", "算力", "大模型", "科大讯飞", "寒武纪", "商汤", "旷视", "海光", "景嘉微"],
                "汽车": ["汽车", "新能源车", "比亚迪", "长城", "长安", "上汽", "广汽", "一汽", "吉利", "蔚来", "理想", "小鹏"],
            }
            mask = pd.Series([False] * len(df), index=df.index)
            for kw in filters["keywords"]:
                # 先直接搜索关键词
                mask |= df[name_col].str.contains(kw, na=False)
                # 再搜索扩展的行业关键词
                expanded = industry_expand.get(kw, [])
                for ex_kw in expanded:
                    mask |= df[name_col].str.contains(ex_kw, na=False)
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
            lines.append("\n⚠️ 严格条件下未找到符合股票, 为您智能放宽条件推荐:\n")

            # 回退方案：放宽条件重试
            relaxed_filters = dict(filters)
            if "pe_max" in relaxed_filters:
                relaxed_filters["pe_max"] = relaxed_filters["pe_max"] * 1.5
            if "pct_change_min" in relaxed_filters:
                relaxed_filters["pct_change_min"] = max(0, relaxed_filters["pct_change_min"] - 2)

            try:
                relaxed_results = self._apply_filters(universe, relaxed_filters)
                if len(relaxed_results) > 0:
                    relaxed_top = relaxed_results.sort_values('涨跌幅', ascending=False).head(5)
                    lines.append("\n**💡 放宽条件后 Top 5**:\n")
                    for i, (_, row) in enumerate(relaxed_top.iterrows(), 1):
                        lines.append(
                            f"{i}. **{row.get('名称', 'N/A')}** ({row.get('代码', '')}) "
                            f"- 价:{row.get('最新价', 0):.2f} "
                            f"涨幅:{row.get('涨跌幅', 0):+.2f}% "
                            f"PE:{row.get('市盈率-动态', 0):.1f}"
                        )
            except Exception:
                pass

            # 提供建议
            suggestions = []
            if "pe_max" in filters:
                suggestions.append(f"将PE上限从{filters['pe_max']}放宽到{filters['pe_max']*1.5:.0f}")
            if "pct_change_min" in filters:
                suggestions.append("降低涨幅要求")
            if "market_cap_min" in filters:
                suggestions.append("降低市值门槛")
            if "keywords" in filters:
                suggestions.append("尝试其他行业关键词")
            if suggestions:
                lines.append("\n**🎯 建议**:\n" + "\n".join([f"- {s}" for s in suggestions]))
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
