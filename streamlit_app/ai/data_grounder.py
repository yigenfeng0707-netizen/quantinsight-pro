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
import re
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

        # 5. 宏观数据 — SQLite 优先，避免 akshare 原始列误解析
        try:
            from features.extended_data_sources import fetch_macro_from_sqlite
            res = fetch_macro_from_sqlite()
            if res.ok and isinstance(res.data, dict):
                snap = res.data.get("snapshot") or res.data
                parts = []
                if isinstance(snap, dict):
                    for key, records in snap.items():
                        if isinstance(records, list) and records:
                            last = records[-1]
                            if isinstance(last, dict):
                                val = last.get("value") or last.get("今值")
                                if val is not None:
                                    parts.append(f"{key.upper()}: {val}")
                if parts:
                    result["macro"] = snap
                    context_parts.append(
                        f"🌍 **宏观数据(A股)**: {', '.join(parts[:6])} [来源: {res.source}]"
                    )
        except Exception as e:
            logger.warning(f"接地宏观数据失败: {e}")

        if "macro" not in result and self.cache is not None:
            try:
                macro = self.cache.get_macro_summary()
                if macro:
                    result["macro"] = macro
                    macro_text = ", ".join(
                        f"{k}: {v}" for k, v in macro.items()
                        if v != "N/A" and k.endswith(("_date",)) is False
                    )
                    if macro_text:
                        context_parts.append(f"🌍 **宏观数据**: {macro_text} [来源: 宏观数据]")
            except Exception as e:
                logger.warning(f"接地宏观缓存失败: {e}")

        # 5.5 (代码, 日期) 点查 — 精确取数接地
        if self.qi_db is not None:
            try:
                hits = self._ground_point_queries(question)
                if hits:
                    result["point_hits"] = hits
                    lines = []
                    for h in hits:
                        line = f"- {h['code']} @ {h['date']}: 收盘 {h['close']} 元"
                        if h.get("pct_change") is not None:
                            line += f", 涨跌幅 {h['pct_change']:.2f}%"
                        if h.get("turnover") is not None:
                            line += f", 换手率 {h['turnover']:.2f}%"
                        lines.append(line)
                    context_parts.append(
                        "🎯 **精确取数(SQL 点查 stock_history)**:\n"
                        + "\n".join(lines)
                        + "\n以上为本地行情库落库数据，可直接引用并标注来源，无需拒答。"
                    )
            except Exception as e:
                logger.warning(f"接地点查失败: {e}")

        # 5.6 模板化确定性计算（区间统计 / 涨幅筛选 / 多跳）
        if self.qi_db is not None:
            try:
                comp = self._ground_computed_queries(question)
                if comp:
                    result["computed"] = comp
                    # V4.0 语义层：把指标口径注入命中描述（引用链可展示"怎么算出来的"）
                    try:
                        from semantic.layer import get_parser
                        cal_map = {m.name: m.caliber
                                   for m in get_parser().parse(question) if m.caliber}
                        for c in comp:
                            for name, cal in cal_map.items():
                                if name in c["description"] and "口径" not in c["description"]:
                                    c["description"] += f"｜口径: {cal}"
                    except Exception:
                        pass  # 语义层不可用不影响既有计算路径
                    lines = [f"- {c['description']} → {c['answer']}" for c in comp]
                    context_parts.append(
                        "🧮 **确定性计算(SQL 聚合 stock_history)**:\n"
                        + "\n".join(lines)
                        + "\n以上结果由落库数据确定性计算得出。作答时直接引用最终数值，"
                        "不要复述中间值或重新推算。"
                    )
            except Exception as e:
                logger.warning(f"接地计算失败: {e}")

        # 5.7 财务指标接地（语义层：实体链接 + 指标解析 → financials 表）
        if self.qi_db is not None:
            try:
                fin = self._ground_financial_queries(question)
                if fin:
                    result["financial_hits"] = fin
                    lines = [f"- {c['description']} → {c['answer']}" for c in fin]
                    context_parts.append(
                        "💰 **财务指标接地(financials 表)**:\n"
                        + "\n".join(lines)
                        + "\n以上为落库财报数据，作答时直接引用数值，注明报告期与口径。"
                    )
            except Exception as e:
                logger.warning(f"接地财务指标失败: {e}")

        # 6. 组装上下文
        if context_parts:
            result["context_text"] = "\n\n".join(context_parts)
        else:
            result["context_text"] = "当前数据源暂无数据, AI 基于预训练知识回答."

        self._grounded_data = result
        return result

    def _ground_point_queries(self, question: str) -> list[dict]:
        """(代码, 日期) 点查 stock_history — 精确取数接地

        问题里出现具体代码与日期时，直接 SQL 查落库 K 线，把该行作为可引用
        证据放进上下文。这是"取数工具接入 Agent 链路"的最小实现。
        无日期时回退到该代码最近一根有收盘价的 K 线（兼答"数据覆盖到哪天"）。
        """
        if self.qi_db is None:
            return []
        # 消融实验闸门：设置该环境变量可回到"无点查"的原始系统状态
        import os
        if os.environ.get("QI_DISABLE_POINT_QUERY"):
            return []

        code_re = re.compile(r"(?<!\d)\d{6}(?!\d)")
        date_re = re.compile(r"(?<!\d)(\d{4})[-/年](\d{1,2})[-/月](\d{1,2})")

        codes = []
        for m in code_re.findall(question):
            if m not in codes and self.qi_db.history_has_code(m):
                codes.append(m)
        # V4.0 语义层：实体链接补码（"茅台" → 600519），与正则代码合并去重
        try:
            from semantic.layer import get_linker
            for ent in get_linker().link(question):
                if ent.kind == "Stock" and ent.code and ent.code not in codes \
                        and self.qi_db.history_has_code(ent.code):
                    codes.append(ent.code)
        except Exception:
            pass  # 语义层缺失时回到纯代码匹配
        if not codes:
            return []

        dates = []
        for y, mo, d in date_re.findall(question):
            try:
                iso = f"{int(y):04d}-{int(mo):02d}-{int(d):02d}"
            except ValueError:
                continue
            if iso not in dates:
                dates.append(iso)

        cols = ("code", "date", "open", "close", "high", "low",
                "volume", "pct_change", "turnover")
        sql_point = (
            "SELECT code, date, open, close, high, low, volume, pct_change, turnover "
            "FROM stock_history WHERE code = ? AND date = ? AND close IS NOT NULL"
        )
        sql_latest = (
            "SELECT code, date, open, close, high, low, volume, pct_change, turnover "
            "FROM stock_history WHERE code = ? AND close IS NOT NULL "
            "ORDER BY date DESC LIMIT 1"
        )

        hits = []
        conn = self.qi_db._get_conn()
        for code in codes:
            if dates:
                for date in dates:
                    row = conn.execute(sql_point, (code, date)).fetchone()
                    if row:
                        hits.append(dict(zip(cols, row)))
            else:
                row = conn.execute(sql_latest, (code,)).fetchone()
                if row:
                    hits.append(dict(zip(cols, row)))
        return hits

    def _ground_computed_queries(self, question: str) -> list[dict]:
        """模板化确定性计算 — 区间统计 / 涨幅筛选 / 多跳

        命中评测/真实问句模板时，用 SQL + Python 对落库数据做确定性计算，
        把最终数值作为可引用证据放进上下文。公式与金标准口径一致：
        - 区间涨跌幅 = (末日收盘/首日收盘 - 1) * 100（首日在窗口内）
        - 区间最高价 = max(high)
        - 最大回撤 = max((peak_close - close)/peak_close) * 100，按收盘价滚动峰值
        - 筛选：当日 pct_change 降序 TOP N（剔除 pct_change 为空的行）
        - 多跳：区间涨幅 TOP5（窗口>=30 根、收盘无空值、有换手率）→ 平均换手率最低者 → 其区间涨幅
        """
        if self.qi_db is None:
            return []
        import os
        # 消融实验闸门：QI_DISABLE_POINT_QUERY 回到原始系统；QI_DISABLE_COMPUTED 仅关计算模板（保留点查）
        if os.environ.get("QI_DISABLE_POINT_QUERY") or os.environ.get("QI_DISABLE_COMPUTED"):
            return []

        conn = self.qi_db._get_conn()
        out = []

        # T2: 区间统计（涨跌幅 / 最高价 / 最大回撤）
        m = re.search(
            r"(\d{6})\s*从\s*(\d{4}-\d{1,2}-\d{1,2})\s*到\s*(\d{4}-\d{1,2}-\d{1,2})\s*"
            r"(?:的|期间的)?(区间涨跌幅|区间最高价|按收盘价的买入持有最大回撤)",
            question,
        )
        if m:
            code, start, end, kind = m.group(1), m.group(2), m.group(3), m.group(4)
            rows = conn.execute(
                "SELECT date, close, high FROM stock_history "
                "WHERE code = ? AND date >= ? AND date <= ? AND close IS NOT NULL "
                "ORDER BY date",
                (code, start, end),
            ).fetchall()
            if len(rows) >= 30:
                span = f"{code} {start}~{end}"
                if kind == "区间涨跌幅":
                    val = (rows[-1][1] / rows[0][1] - 1) * 100
                    out.append({
                        "answer": f"{round(val, 2)}",
                        "description": f"{span} 区间涨跌幅",
                        "date": end,
                    })
                elif kind == "区间最高价":
                    val = max(r[2] for r in rows if r[2] is not None)
                    out.append({
                        "answer": f"{round(val, 2)}",
                        "description": f"{span} 区间最高价",
                        "date": end,
                    })
                else:
                    peak, mdd = rows[0][1], 0.0
                    for _, close, _high in rows:
                        peak = max(peak, close)
                        mdd = max(mdd, (peak - close) / peak)
                    out.append({
                        "answer": f"{round(mdd * 100, 2)}",
                        "description": f"{span} 按收盘价买入持有最大回撤",
                        "date": end,
                    })

        # T4: 当日涨幅 TOP N 筛选
        m = re.search(r"(\d{4}-\d{1,2}-\d{1,2})\s*涨幅最高的\s*(\d+)\s*只", question)
        if m:
            date, topn = m.group(1), int(m.group(2))
            rows = conn.execute(
                "SELECT code FROM stock_history WHERE date = ? "
                "AND pct_change IS NOT NULL ORDER BY pct_change DESC LIMIT ?",
                (date, topn),
            ).fetchall()
            if len(rows) >= topn:
                out.append({
                    "answer": "、".join(r[0] for r in rows),
                    "description": f"{date} 涨幅最高 {topn} 只标的（代码，按涨幅降序）",
                    "date": date,
                })

        # T5: 多跳（区间涨幅 TOP5 → 平均换手率最低者 → 区间涨幅）
        m = re.search(
            r"在\s*(\d{4}-\d{1,2}-\d{1,2})\s*至\s*(\d{4}-\d{1,2}-\d{1,2})\s*区间内，"
            r"区间涨幅排名前\s*(\d+)\s*的标的中，平均换手率最低的那只，其区间涨幅是多少",
            question,
        )
        if m:
            start, end, topn = m.group(1), m.group(2), int(m.group(3))
            rows = conn.execute(
                "SELECT code, date, close, turnover FROM stock_history "
                "WHERE date >= ? AND date <= ? ORDER BY code, date",
                (start, end),
            ).fetchall()
            series: dict[str, list[tuple]] = {}
            for code, _d, close, turn in rows:
                series.setdefault(code, []).append((close, turn))
            ranked = []
            for code, pts in series.items():
                if len(pts) < 30 or any(c is None for c, _t in pts):
                    continue
                turns = [t for _c, t in pts if t is not None]
                if not turns:
                    continue
                ret = pts[-1][0] / pts[0][0] - 1
                ranked.append((code, ret, sum(turns) / len(turns)))
            if len(ranked) >= topn:
                top = sorted(ranked, key=lambda x: x[1], reverse=True)[:topn]
                pick = min(top, key=lambda x: x[2])
                out.append({
                    "answer": f"{round(pick[1] * 100, 2)}",
                    "description": (
                        f"{start}~{end} 区间涨幅 TOP{topn} 中平均换手率最低者为 "
                        f"{pick[0]}，其区间涨幅"
                    ),
                    "date": end,
                })
        return out

    def _ground_financial_queries(self, question: str) -> list[dict]:
        """财务指标接地（V4.0 语义层）

        语义层解析问题中的实体（如"茅台"→600519）与财务指标（如"营业收入"
        →revenue + 口径），从 financials 表确定性取数，作为可引用证据。
        无实体或无财务指标命中时返回空——回到原有问答路径。
        """
        if self.qi_db is None:
            return []
        try:
            from semantic.layer import get_linker, get_parser
            entities = [e for e in get_linker().link(question)
                        if e.kind == "Stock" and e.code]
            metrics = [m for m in get_parser().parse(question)
                       if m.binding_table == "financials"]
        except Exception:
            return []
        if not entities or not metrics:
            return []

        col_map = {m.binding_column: m for m in metrics}
        out = []
        for ent in entities:
            df = self.qi_db.get_financials(ent.code, list(col_map))
            if df is None or df.empty:
                continue
            # 每个指标只取最新报告期（get_financials 已按 period 倒序）
            seen_keys = set()
            for _, row in df.iterrows():
                m = col_map.get(row["metric_key"])
                if m is None or row["metric_key"] in seen_keys:
                    continue
                seen_keys.add(row["metric_key"])
                try:
                    value = float(row["value"])
                except (TypeError, ValueError):
                    continue
                name = ent.name or ent.code
                out.append({
                    "answer": f"{value:,.2f}",
                    "description": (
                        f"{name} {m.name}（{row['period']} 年报，单位：{row.get('unit', '元')}）"
                        f"｜口径: {m.caliber}"
                    ),
                    "date": row["period"],
                })
        return out

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
        """摘要化新闻（优先 A 股/国内财经，过滤海外市场快讯）"""
        lines = []
        title_col = None
        for col in ["标题", "title", "新闻标题"]:
            if col in df.columns:
                title_col = col
                break

        global_kw = (
            "纽约", "道琼斯", "纳斯达克", "标普500", "标普", "日经", "恒生",
            "美联储", "欧股", "德股", "法国下调", "环球财经", "美股",
        )
        if title_col:
            for _, row in df.head(15).iterrows():
                title = str(row.get(title_col, "")).strip()
                if not title or any(k in title for k in global_kw):
                    continue
                src = str(row.get("来源", row.get("source", ""))).strip()
                if src and any(k in src for k in ("环球", "global")):
                    continue
                lines.append(f"  • {title}" + (f" [{src}]" if src else ""))

        return "\n".join(lines[:8]) if lines else "最新 A 股财经新闻暂无"

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
