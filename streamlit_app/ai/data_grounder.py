"""
QuantInsight Pro - 数据接地层 (Data Grounder)
================================================

将 AI 回答与平台实际数据 (行情/财务/回测结果/新闻) 连接,
让 LLM 基于真实数据生成回答, 减少幻觉.

业内领先的 "AI+数据" 深度融合架构.

License: MIT
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional

import pandas as pd

logger = logging.getLogger(__name__)


class DataGrounder:
    """
    数据接地器

    根据用户问题, 自动从平台数据源中检索相关数据,
    作为 LLM 的上下文 (context), 实现数据驱动的回答.

    接地维度:
    1. 行情数据: 实时价格, 涨跌幅, 成交量
    2. 财务数据: PE/PB, 营收, 净利润
    3. 资金流向: 主力/北向净流入
    4. 新闻舆情: 最新相关新闻
    5. 回测结果: 平台策略回测指标
    6. 宏观数据: GDP/CPI/PMI

    使用示例:
        >>> grounder = DataGrounder(cache_manager)
        >>> context = grounder.ground("分析新能源行业投资机会")
        >>> # context 包含: 相关股票行情, 行业估值, 资金流向, 最新新闻
    """

    # 行业关键词映射
    INDUSTRY_KEYWORDS = {
        "新能源": ["BK0900", "宁德时代", "隆基绿能", "比亚迪", "阳光电源", "新能源车"],
        "半导体": ["BK0438", "中芯国际", "北方华创", "韦尔股份", "海光信息", "芯片"],
        "医药": ["BK0465", "恒瑞医药", "药明康德", "迈瑞医疗", "创新药"],
        "消费": ["BK0896", "贵州茅台", "五粮液", "海天味业", "白酒"],
        "银行": ["BK0475", "工商银行", "招商银行", "建设银行", "净息差"],
        "证券": ["BK0473", "中信证券", "东方财富", "两融余额"],
        "房地产": ["BK0451", "万科", "保利发展", "房贷利率"],
        "军工": ["BK0490", "中航沈飞", "航发动力", "国防预算"],
        "AI": ["BK1128", "科大讯飞", "商汤", "算力", "大模型"],
        "汽车": ["BK0481", "比亚迪", "长城汽车", "新能源车销量"],
    }

    def __init__(self, cache_manager=None, qi_db=None):
        """
        Args:
            cache_manager: DataCacheManager 实例 (可选)
            qi_db: QIDataDB 实例 (可选, V3.11 新增)
        """
        self.cache = cache_manager
        self.qi_db = qi_db  # V3.11: 新增 SQLite 数据库实例
        self._grounded_data = {}

    def ground(self, question: str) -> dict:
        """
        根据问题自动接地数据

        Returns:
            dict: {
                "stocks": DataFrame,      # 相关股票行情
                "financials": dict,        # 关键财务指标
                "fund_flow": DataFrame,    # 资金流向
                "news": DataFrame,         # 相关新闻
                "macro": dict,             # 宏观数据
                "context_text": str,       # 整合后的文本上下文
            }
        """
        result = {
            "stocks": None,
            "financials": {},
            "fund_flow": None,
            "news": None,
            "macro": {},
            "context_text": "",
        }

        if self.cache is None and self.qi_db is None:
            result["context_text"] = "⚠️ 数据源未配置, AI 基于预训练知识回答"
            return result

        context_parts = []

        # 1. 识别相关行业/主题
        matched_industries = self._match_industries(question)
        if matched_industries:
            context_parts.append(f"📊 **相关板块**: {', '.join(matched_industries)}")

        # 2. 拉取相关股票行情
        try:
            universe = None
            # V3.11: 优先从 SQLite 读取
            if self.qi_db is not None:
                try:
                    sqlite_df = self.qi_db.get_stock_spot()
                    if sqlite_df is not None and len(sqlite_df) > 0:
                        universe = sqlite_df
                        logger.info("股票行情数据来源: SQLite (stock_spot)")
                except Exception:
                    pass
            # SQLite 没有数据时, 回退到 cache
            if universe is None and self.cache is not None:
                universe = self.cache.get_stock_universe(top_n=500)
                if universe is not None and len(universe) > 0:
                    logger.info("股票行情数据来源: cache (get_stock_universe)")
            if universe is not None and len(universe) > 0:
                # 过滤相关行业的股票
                relevant = self._filter_relevant_stocks(universe, question, matched_industries)
                if relevant is not None and len(relevant) > 0:
                    result["stocks"] = relevant
                    summary = self._summarize_stocks(relevant)
                    context_parts.append(f"📈 **相关个股行情**:\n{summary}")
        except Exception as e:
            logger.warning(f"接地股票数据失败: {e}")

        # V3.11: 拉取板块资金流 (从 SQLite)
        if self.qi_db is not None:
            try:
                sector_df = self.qi_db.get_sector_flow()
                if sector_df is not None and len(sector_df) > 0:
                    logger.info("板块资金流数据来源: SQLite (sector_flow)")
                    sector_summary = self._summarize_sector_flow(sector_df)
                    if sector_summary:
                        context_parts.append(f"🏦 **板块资金流**:\n{sector_summary}")
            except Exception as e:
                logger.warning(f"接地板块资金流失败: {e}")

        # V3.11: 拉取北向资金 (从 SQLite)
        if self.qi_db is not None:
            try:
                nb_df = self.qi_db.get_northbound_flow(days=5)
                if nb_df is not None and len(nb_df) > 0:
                    logger.info("北向资金数据来源: SQLite (northbound_flow)")
                    nb_summary = self._summarize_northbound(nb_df)
                    if nb_summary:
                        context_parts.append(f"🌐 **北向资金(近5日)**:\n{nb_summary}")
            except Exception as e:
                logger.warning(f"接地北向资金失败: {e}")

        # V3.11: 拉取宏观指标 (从 SQLite macro_indices 表)
        if self.qi_db is not None:
            try:
                conn = self.qi_db._get_conn()
                import pandas as _pd
                macro_df = _pd.read_sql(
                    "SELECT indicator_name, value FROM macro_indices ORDER BY date DESC",
                    conn,
                )
                if macro_df is not None and len(macro_df) > 0:
                    logger.info("宏观指标数据来源: SQLite (macro_indices)")
                    # 取每个指标最新值
                    latest_macro = macro_df.drop_duplicates(subset=["indicator_name"], keep="first")
                    macro_text = ", ".join(
                        f"{row['indicator_name']}: {row['value']}"
                        for _, row in latest_macro.iterrows()
                        if _pd.notna(row.get("value"))
                    )
                    if macro_text:
                        context_parts.append(f"🌍 **宏观指标**: {macro_text}")
            except Exception as e:
                logger.warning(f"接地宏观指标失败: {e}")

        # 3. 拉取资金流向
        if self.cache is not None:
            try:
                fund_flow = self.cache.get_fund_flow_rank("今日")
                if fund_flow is not None and len(fund_flow) > 0:
                    result["fund_flow"] = fund_flow.head(20)
                    top_inflow = self._summarize_fund_flow(fund_flow)
                    context_parts.append(f"💰 **今日资金流向**:\n{top_inflow}")
            except Exception as e:
                logger.warning(f"接地资金流向失败: {e}")

        # 4. 拉取最新新闻
        if self.cache is not None:
            try:
                news = self.cache.get_news("财经", 20)
                if news is not None and len(news) > 0:
                    result["news"] = news
                    news_summary = self._summarize_news(news)
                    context_parts.append(f"📰 **最新财经新闻**:\n{news_summary}")
            except Exception as e:
                logger.warning(f"接地新闻数据失败: {e}")

        # 5. 宏观数据
        if self.cache is not None:
            try:
                macro = self.cache.get_macro_summary()
                if macro:
                    result["macro"] = macro
                    macro_text = ", ".join(f"{k}: {v}" for k, v in macro.items() if v != "N/A")
                    if macro_text:
                        context_parts.append(f"🌍 **宏观数据**: {macro_text}")
            except Exception as e:
                logger.warning(f"接地宏观数据失败: {e}")

        # 6. 组装上下文
        if context_parts:
            result["context_text"] = "\n\n".join(context_parts)
        else:
            result["context_text"] = "当前数据源暂无数据, AI 基于预训练知识回答."

        self._grounded_data = result
        return result

    def _match_industries(self, question: str) -> list[str]:
        """匹配问题中的行业关键词"""
        matched = []
        for industry, keywords in self.INDUSTRY_KEYWORDS.items():
            if industry in question or any(kw in question for kw in keywords):
                matched.append(industry)
        return matched

    def _filter_relevant_stocks(self, universe: pd.DataFrame, question: str, industries: list[str]) -> pd.DataFrame:
        """从全A股中过滤相关股票"""
        if "名称" not in universe.columns:
            return universe.head(20)

        # 按关键词过滤
        mask = pd.Series([False] * len(universe), index=universe.index)

        for industry in industries:
            keywords = self.INDUSTRY_KEYWORDS.get(industry, [])
            for kw in keywords:
                if len(kw) >= 2:
                    mask |= universe["名称"].str.contains(kw, na=False)

        # 也按涨跌幅排序取 top
        filtered = universe[mask]
        if len(filtered) == 0:
            # 没匹配到具体股票, 返回涨幅前10 + 跌幅前10
            if "涨跌幅" in universe.columns:
                top_gain = universe.nlargest(10, "涨跌幅")
                top_loss = universe.nsmallest(10, "涨跌幅")
                filtered = pd.concat([top_gain, top_loss]).drop_duplicates()
            else:
                filtered = universe.head(20)

        return filtered.head(30)

    def _summarize_stocks(self, df: pd.DataFrame) -> str:
        """摘要化股票数据"""
        lines = []
        display_cols = []
        for col in ["代码", "名称", "最新价", "涨跌幅", "市盈率-动态", "市净率"]:
            if col in df.columns:
                display_cols.append(col)

        for _, row in df.head(10).iterrows():
            parts = []
            for col in display_cols:
                val = row.get(col, "")
                if pd.notna(val):
                    if col == "涨跌幅":
                        parts.append(f"{val:+.2f}%")
                    elif col in ("最新价", "市盈率-动态", "市净率"):
                        parts.append(f"{col}:{val:.2f}")
                    else:
                        parts.append(str(val))
            if parts:
                lines.append("  " + " | ".join(parts))

        return "\n".join(lines[:10]) if lines else "暂无数据"

    def _summarize_fund_flow(self, df: pd.DataFrame) -> str:
        """摘要化资金流向"""
        lines = []
        # 取净流入前5
        flow_cols = [c for c in df.columns if "主力净流入" in str(c) or "净流入" in str(c)]
        name_col = "名称" if "名称" in df.columns else df.columns[1] if len(df.columns) > 1 else None

        if flow_cols and name_col:
            sorted_df = df.sort_values(flow_cols[0], ascending=False).head(5)
            for _, row in sorted_df.iterrows():
                name = row.get(name_col, "")
                flow_val = row.get(flow_cols[0], 0)
                if isinstance(flow_val, (int, float)):
                    lines.append(f"  {name}: 净流入 {flow_val/1e8:.2f}亿")
                else:
                    lines.append(f"  {name}: {flow_val}")

        return "\n".join(lines) if lines else "资金流向数据暂无"

    def _summarize_news(self, df: pd.DataFrame) -> str:
        """摘要化新闻"""
        lines = []
        title_col = None
        for col in ["标题", "title", "新闻标题"]:
            if col in df.columns:
                title_col = col
                break

        if title_col:
            for _, row in df.head(8).iterrows():
                title = row.get(title_col, "")
                if title:
                    lines.append(f"  • {title}")

        return "\n".join(lines) if lines else "最新新闻暂无"

    def _summarize_sector_flow(self, df: pd.DataFrame) -> str:
        """V3.11: 摘要化板块资金流"""
        lines = []
        # 兼容中英文列名
        name_col = None
        for col in ["板块名称", "sector_name", "板块"]:
            if col in df.columns:
                name_col = col
                break
        pct_col = None
        for col in ["涨跌幅", "change_pct"]:
            if col in df.columns:
                pct_col = col
                break
        flow_col = None
        for col in ["净流入", "net_flow", "主力净流入"]:
            if col in df.columns:
                flow_col = col
                break

        if name_col is None:
            return ""

        # 取涨幅前5
        if pct_col is not None:
            try:
                df_sorted = df.copy()
                df_sorted[pct_col] = pd.to_numeric(df_sorted[pct_col], errors="coerce")
                top = df_sorted.sort_values(pct_col, ascending=False).head(5)
                for _, row in top.iterrows():
                    name = row.get(name_col, "")
                    pct = row.get(pct_col, 0)
                    if pd.notna(pct):
                        lines.append(f"  {name}: {pct:+.2f}%")
            except Exception:
                pass

        return "\n".join(lines) if lines else "板块资金流数据暂无"

    def _summarize_northbound(self, df: pd.DataFrame) -> str:
        """V3.11: 摘要化北向资金"""
        lines = []
        flow_col = None
        for col in ["net_flow", "当日净流入", "north_flow"]:
            if col in df.columns:
                flow_col = col
                break
        date_col = None
        for col in ["date", "日期"]:
            if col in df.columns:
                date_col = col
                break

        if flow_col is None or date_col is None:
            return ""

        try:
            for _, row in df.iterrows():
                date = row.get(date_col, "")
                flow = row.get(flow_col, 0)
                if pd.notna(flow):
                    try:
                        flow_val = float(flow)
                        if abs(flow_val) > 1e8:
                            lines.append(f"  {date}: 净流入 {flow_val/1e8:.2f}亿")
                        else:
                            lines.append(f"  {date}: 净流入 {flow_val:.2f}")
                    except (ValueError, TypeError):
                        pass
        except Exception:
            pass

        return "\n".join(lines) if lines else "北向资金数据暂无"

    def get_grounded_context(self) -> str:
        """获取上次接地的上下文文本"""
        return self._grounded_data.get("context_text", "")

    def build_llm_prompt_context(self, question: str) -> str:
        """
        构建完整的 LLM 上下文 prompt

        将接地数据格式化为 system prompt 的一部分,
        指导 LLM 基于这些数据回答.
        """
        grounded = self.ground(question)
        context = grounded.get("context_text", "")

        if not context or "暂无" in context:
            return ""

        return (
            f"\n\n以下是从平台数据库检索到的实时数据, 请基于这些数据回答用户问题:\n\n"
            f"{context}\n\n"
            f"请注意:\n"
            f"1. 优先使用上述数据, 标注数据来源\n"
            f"2. 如果数据不足以回答, 可以结合专业知识补充, 但需明确区分\n"
            f"3. 投资建议需附风险提示\n"
            f"4. 数据时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
        )
