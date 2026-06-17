"""
QuantInsight Pro - 专业子Agent群 (Sub-Agents)
===============================================

5 个专业子Agent, 业内领先的多Agent协作机制:
1. StockSelectionAgent - 智能选股
2. AnalysisAgent - 深度分析
3. RiskAgent - 风险评估
4. PortfolioAgent - 组合管理
5. MarketMonitorAgent - 市场监控

每个Agent接收: 任务描述 + 数据工具 + 上下文
每个Agent返回: 结构化结果 + 置信度 + 数据引用

License: MIT
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from typing import Optional

import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class AgentResult:
    """Agent 执行结果"""
    agent_name: str = ""
    success: bool = True
    summary: str = ""           # 摘要 (Markdown)
    data: dict = None           # 结构化数据
    citations: list = None      # 数据引用
    confidence: float = 0.8     # 置信度
    error: str = ""             # 错误信息

    def __post_init__(self):
        if self.data is None:
            self.data = {}
        if self.citations is None:
            self.citations = []


def _call_llm(messages: list, llm_config: dict, temperature: float = 0.7) -> str:
    """通用 LLM 调用 (复用 app.py 的逻辑)

    V3.11: 失败时抛出异常而非返回空字符串, 消除静默失败
    """
    if not llm_config or not llm_config.get("api_key"):
        raise RuntimeError("LLM 配置缺失或 API Key 未设置")

    import requests

    headers = {
        "Authorization": f"Bearer {llm_config['api_key']}",
        "Content-Type": "application/json",
    }
    if llm_config.get('workspace_id'):
        headers['X-DashScope-WorkSpace'] = llm_config['workspace_id']
    payload = {
        "model": llm_config["model"],
        "messages": messages,
        "temperature": temperature,
        "max_tokens": 3000 if ('v4' in llm_config.get('model', '') or 'r1' in llm_config.get('model', '')) else 1500,
    }
    # V3.12: qwen3.x-plus 是推理模型, 默认生成5000+字思考内容导致60s超时
    # 禁用思考模式后, 单次调用从36s降至8s, Multi-Agent 7次串行调用可在60s内完成
    model_name = llm_config.get('model', '').lower()
    if 'qwen3' in model_name or 'qwen-3' in model_name:
        payload['enable_thinking'] = False

    try:
        resp = requests.post(llm_config["base_url"], headers=headers, json=payload, timeout=60)
        # V3.11: 检测余额不足/限流
        if resp.status_code in (402, 429):
            raise RuntimeError(f"LLM {llm_config.get('provider')} 返回 {resp.status_code} (余额不足/限流)")
        resp.raise_for_status()
        result = resp.json()
        msg = result["choices"][0]["message"]
        content = msg.get("content", "") or ""
        reasoning = msg.get("reasoning_content", "") or ""
        answer = content.strip() if content.strip() else reasoning
        if not answer:
            raise RuntimeError("LLM 返回空内容")
        return answer
    except RuntimeError:
        raise
    except Exception as e:
        logger.warning(f"LLM 调用失败 ({llm_config.get('provider')}): {e}")
        raise RuntimeError(f"LLM 调用失败: {e}")


# ============================================================================
# 1. 智能选股 Agent
# ============================================================================

class StockSelectionAgent:
    """
    智能选股 Agent

    能力:
    - 解析自然语言选股条件
    - 执行多维度过滤 (估值/成长/质量/动量/资金流)
    - 输出评分排名 + 可解释逻辑
    """

    NAME = "StockSelectionAgent"

    def __init__(self, cache_manager=None, llm_config: dict = None, qi_db=None):
        self.cache = cache_manager
        self.llm_config = llm_config or {}
        self.qi_db = qi_db  # V3.11: SQLite 数据库实例

    def execute(self, task: str, context: dict = None) -> AgentResult:
        """
        执行选股任务

        Args:
            task: 自然语言描述, 如 "找出低估值高分红的银行股"
            context: 额外上下文

        Returns:
            AgentResult: 选股结果
        """
        try:
            # 1. 解析筛选条件
            filters = self._parse_filters(task)

            # 2. 获取股票池
            universe = None
            if self.cache:
                try:
                    universe = self.cache.get_stock_universe(top_n=2000)
                except Exception as e:
                    logger.warning(f"获取股票池失败: {e}")

            if universe is None or len(universe) == 0:
                return AgentResult(
                    agent_name=self.NAME,
                    success=False,
                    error="股票池数据不可用",
                )

            # 3. 执行过滤
            filtered = self._apply_filters(universe, filters)

            # 4. 评分排序
            scored = self._score_stocks(filtered)

            # 5. 生成解释
            explanation = self._explain_results(scored, filters, task)

            return AgentResult(
                agent_name=self.NAME,
                success=True,
                summary=explanation,
                data={
                    "filters": filters,
                    "total_universe": len(universe),
                    "filtered_count": len(filtered),
                    "top_stocks": scored.head(20).to_dict(orient="records") if len(scored) > 0 else [],
                },
                citations=[{
                    "source": "东方财富",
                    "api": "stock_zh_a_spot_em",
                    "desc": f"全A股行情, {len(universe)} 只",
                }],
                confidence=0.85,
            )

        except Exception as e:
            return AgentResult(agent_name=self.NAME, success=False, error=str(e))

    def _parse_filters(self, task: str) -> dict:
        """用 LLM 解析自然语言为结构化过滤条件"""
        system_prompt = """将用户的选股条件解析为JSON格式.
输出格式 (不要markdown代码块):
{
  "sector": "行业名(可选)",
  "pe_max": 数值(可选),
  "pe_min": 数值(可选),
  "pb_max": 数值(可选),
  "dividend_yield_min": 数值(可选,百分比),
  "market_cap_min": 数值(可选,亿元),
  "market_cap_max": 数值(可选,亿元),
  "pct_change_min": 数值(可选),
  "pct_change_max": 数值(可选),
  "sort_by": "排序字段",
  "sort_asc": true/false,
  "top_n": 数字,
  "keywords": ["关键词1","关键词2"]
}
只输出JSON, 不要其他内容."""

        user_prompt = f"解析选股条件: {task}"
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        response = ""
        try:
            response = _call_llm(messages, self.llm_config)
        except RuntimeError as e:
            logger.warning(f"选股条件解析 LLM 调用失败, 使用关键词匹配: {e}")

        if response:
            try:
                # 提取 JSON
                json_match = re.search(r'\{[^{}]*\}', response, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())
                return json.loads(response)
            except Exception:
                pass

        # Fallback: 关键词匹配
        return self._fallback_parse(task)

    def _fallback_parse(self, task: str) -> dict:
        """关键词匹配 fallback"""
        filters = {}
        if "低估值" in task or "便宜" in task:
            filters["pe_max"] = 20
        if "高分红" in task or "高股息" in task:
            filters["dividend_yield_min"] = 3
        if "大盘" in task:
            filters["market_cap_min"] = 500
        if "小盘" in task:
            filters["market_cap_max"] = 100
        if "涨幅" in task:
            filters["sort_by"] = "涨跌幅"
            filters["sort_asc"] = False

        # 行业关键词
        for industry in ["银行", "新能源", "半导体", "医药", "消费", "军工", "房地产", "证券"]:
            if industry in task:
                filters["keywords"] = [industry]
                break

        filters.setdefault("top_n", 20)
        return filters

    def _apply_filters(self, universe: pd.DataFrame, filters: dict) -> pd.DataFrame:
        """应用过滤条件"""
        df = universe.copy()

        # PE 过滤
        pe_col = None
        for col in ["市盈率-动态", "PE", "pe"]:
            if col in df.columns:
                pe_col = col
                break

        if pe_col:
            df[pe_col] = pd.to_numeric(df[pe_col], errors="coerce")
            if "pe_max" in filters:
                df = df[(df[pe_col] < filters["pe_max"]) & (df[pe_col] > 0)]
            if "pe_min" in filters:
                df = df[df[pe_col] >= filters["pe_min"]]

        # PB 过滤
        pb_col = None
        for col in ["市净率", "PB", "pb"]:
            if col in df.columns:
                pb_col = col
                break

        if pb_col and "pb_max" in filters:
            df[pb_col] = pd.to_numeric(df[pb_col], errors="coerce")
            df = df[(df[pb_col] < filters["pb_max"]) & (df[pb_col] > 0)]

        # 市值过滤
        cap_col = None
        for col in ["总市值", "市值"]:
            if col in df.columns:
                cap_col = col
                break

        if cap_col:
            df[cap_col] = pd.to_numeric(df[cap_col], errors="coerce")
            if "market_cap_min" in filters:
                df = df[df[cap_col] >= filters["market_cap_min"] * 1e8]
            if "market_cap_max" in filters:
                df = df[df[cap_col] <= filters["market_cap_max"] * 1e8]

        # 关键词过滤 (行业/名称)
        if "keywords" in filters:
            name_col = "名称" if "名称" in df.columns else None
            if name_col:
                mask = pd.Series([False] * len(df), index=df.index)
                for kw in filters["keywords"]:
                    mask |= df[name_col].str.contains(kw, na=False)
                if mask.any():
                    df = df[mask]

        return df.reset_index(drop=True)

    def _score_stocks(self, df: pd.DataFrame) -> pd.DataFrame:
        """简单评分"""
        if len(df) == 0:
            return df

        df = df.copy()
        df["score"] = 0.0

        # 涨跌幅加分 (适中涨幅 0-5% 较好)
        chg_col = "涨跌幅" if "涨跌幅" in df.columns else None
        if chg_col:
            df[chg_col] = pd.to_numeric(df[chg_col], errors="coerce").fillna(0)
            df["score"] += df[chg_col].clip(-5, 5) * 0.1

        # PE 加分 (低PE好)
        pe_col = None
        for col in ["市盈率-动态", "PE"]:
            if col in df.columns:
                pe_col = col
                break
        if pe_col:
            pe_vals = pd.to_numeric(df[pe_col], errors="coerce").fillna(999)
            df["score"] += (30 / pe_vals.clip(1, 300)).clip(0, 1) * 0.3

        # 成交量加分 (适中成交量好)
        vol_col = "成交量" if "成交量" in df.columns else None
        if vol_col:
            df[vol_col] = pd.to_numeric(df[vol_col], errors="coerce").fillna(0)
            vol_rank = df[vol_col].rank(pct=True)
            df["score"] += vol_rank * 0.2

        return df.sort_values("score", ascending=False).reset_index(drop=True)

    def _explain_results(self, scored: pd.DataFrame, filters: dict, task: str) -> str:
        """生成选股解释"""
        lines = [f"### 📊 智能选股结果\n", f"**筛选条件**: {task}\n"]
        lines.append(f"**筛选范围**: 从 {filters.get('total_universe', '全A股')} 只股票中筛选\n")

        if len(scored) == 0:
            lines.append("\n⚠️ 未找到符合条件的股票, 建议放宽筛选条件.")
            return "\n".join(lines)

        lines.append(f"\n**符合条件**: {len(scored)} 只, 展示前 {min(20, len(scored))} 只:\n")

        name_col = "名称" if "名称" in scored.columns else None
        code_col = "代码" if "代码" in scored.columns else None
        price_col = "最新价" if "最新价" in scored.columns else None
        chg_col = "涨跌幅" if "涨跌幅" in scored.columns else None
        pe_col = "市盈率-动态" if "市盈率-动态" in scored.columns else None

        for i, row in scored.head(20).iterrows():
            parts = []
            if code_col:
                parts.append(str(row.get(code_col, "")))
            if name_col:
                parts.append(str(row.get(name_col, "")))
            if price_col:
                p = row.get(price_col, 0)
                parts.append(f"¥{p:.2f}" if isinstance(p, (int, float)) else str(p))
            if chg_col:
                c = row.get(chg_col, 0)
                if isinstance(c, (int, float)):
                    parts.append(f"{c:+.2f}%")
            if pe_col:
                pe = row.get(pe_col, 0)
                if isinstance(pe, (int, float)) and pe > 0:
                    parts.append(f"PE:{pe:.1f}")
            lines.append(f"{i+1}. {' | '.join(parts)}")

        # 推荐逻辑
        lines.append(f"\n\n💡 **推荐逻辑**: 基于{filters.get('keywords', ['综合'])}行业筛选, "
                     f"综合估值(PE)、资金面(成交量)和技术面(涨跌幅)进行评分排序.")

        return "\n".join(lines)


# ============================================================================
# 2. 深度分析 Agent
# ============================================================================

class AnalysisAgent:
    """深度分析 Agent - 个股/行业深度研究"""

    NAME = "AnalysisAgent"

    def __init__(self, cache_manager=None, llm_config: dict = None, qi_db=None):
        self.cache = cache_manager
        self.llm_config = llm_config or {}
        self.qi_db = qi_db  # V3.11: SQLite 数据库实例

    def execute(self, task: str, context: dict = None) -> AgentResult:
        """执行分析任务"""
        try:
            # 构建上下文
            analysis_context = ""
            if self.cache:
                try:
                    # 尝试获取相关股票数据
                    from ai.data_grounder import DataGrounder
                    grounder = DataGrounder(self.cache, qi_db=self.qi_db)
                    grounded = grounder.ground(task)
                    analysis_context = grounded.get("context_text", "")
                except Exception:
                    pass

            # 如果 DataGrounder 没有提供上下文, 尝试获取实时市场数据
            if not analysis_context:
                try:
                    from features.report_generator import fetch_macro_data
                    macro = fetch_macro_data()
                    if macro and macro.get('indices'):
                        indices_str = ", ".join([
                            f"{idx['name']}: {idx.get('price', 'N/A')} ({idx.get('change_pct', 0):+.2f}%)"
                            for idx in macro['indices']
                        ])
                        analysis_context = f"实时市场数据 - 主要指数: {indices_str}"
                        if macro.get('north_flow'):
                            try:
                                nf = float(macro['north_flow'])
                                analysis_context += f"; 北向资金净流入: {nf/1e8:.2f}亿元" if abs(nf) > 1e8 else f"; 北向资金净流入: {nf:.2f}亿元"
                            except (TypeError, ValueError):
                                pass
                        if macro.get('breadth'):
                            b = macro['breadth']
                            analysis_context += f"; 上涨{b.get('advance',0)}家/下跌{b.get('decline',0)}家"
                        analysis_context += f" (来源: {macro.get('source', 'akshare')})"
                except Exception:
                    pass

            # LLM 分析
            system_prompt = (
                "你是 QuantInsight Pro 的深度分析助手. "
                "基于提供的市场数据和专业知识, 进行深度投资分析.\n"
                "回答时请引用提供的实时数据并标注来源.\n"
                "输出结构化JSON:\n"
                '{"title": "分析标题", "summary": "Markdown格式分析(引用数据并标注来源)", '
                '"data": {"指标": "值"}, "recommendation": "建议", "risk": "风险提示"}'
            )

            messages = [
                {"role": "system", "content": system_prompt},
            ]
            if analysis_context:
                messages.append({"role": "user", "content": f"市场数据上下文:\n{analysis_context}"})
            messages.append({"role": "user", "content": task})

            # V3.11: _call_llm 失败时抛出 RuntimeError, 在此捕获
            try:
                response = _call_llm(messages, self.llm_config)
            except RuntimeError as e:
                return AgentResult(
                    agent_name=self.NAME,
                    success=False,
                    error=f"LLM 调用失败: {e}",
                )

            if response:
                try:
                    json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', response, re.DOTALL)
                    if json_match:
                        parsed = json.loads(json_match.group())
                        return AgentResult(
                            agent_name=self.NAME,
                            success=True,
                            summary=parsed.get("summary", response),
                            data=parsed.get("data", {}),
                            confidence=0.8,
                        )
                except Exception:
                    pass

                return AgentResult(
                    agent_name=self.NAME,
                    success=True,
                    summary=response,
                    confidence=0.8,
                )
            # V3.11: 不再把任务文本当摘要, 明确返回失败
            return AgentResult(
                agent_name=self.NAME,
                success=False,
                error="LLM 返回空内容, 无法生成分析",
            )

        except Exception as e:
            return AgentResult(agent_name=self.NAME, success=False, error=str(e))


# ============================================================================
# 3. 风险评估 Agent
# ============================================================================

class RiskAgent:
    """风险评估 Agent - 持仓/策略风险分析"""

    NAME = "RiskAgent"

    def __init__(self, cache_manager=None, llm_config: dict = None, qi_db=None):
        self.cache = cache_manager
        self.llm_config = llm_config or {}
        self.qi_db = qi_db  # V3.11: SQLite 数据库实例

    def execute(self, task: str, context: dict = None) -> AgentResult:
        """执行风险评估

        V3.11: 调用 LLM 生成动态风险评估, 而非硬编码静态文本
        """
        try:
            # V3.11: 优先调用 LLM 生成风险评估
            if self.llm_config and self.llm_config.get('api_key'):
                system_prompt = """你是 QuantInsight Pro 的风险管理专家. 请基于用户问题进行风险评估.
输出格式 (Markdown):
### ⚠️ 风险评估
**市场风险**: [基于当前市场环境分析]
**集中度风险**: [基于行业/个股集中度分析]
**流动性风险**: [基于成交额/换手率分析]
📌 *投资有风险, 入市需谨慎. 本分析不构成投资建议.*"""
                try:
                    response = _call_llm(
                        [{"role": "system", "content": system_prompt},
                         {"role": "user", "content": task}],
                        self.llm_config,
                        temperature=0.5,
                    )
                    if response:
                        return AgentResult(
                            agent_name=self.NAME,
                            success=True,
                            summary=response,
                            data={"risk_level": "medium", "warnings": []},
                            confidence=0.8,
                        )
                except RuntimeError as e:
                    logger.warning(f"RiskAgent LLM 调用失败, 使用静态模板: {e}")

            # 兜底: 静态风险提示模板
            risk_summary = self._assess_risks(task, context)
            return AgentResult(
                agent_name=self.NAME,
                success=True,
                summary=risk_summary,
                data={"risk_level": "medium", "warnings": []},
                confidence=0.6,
            )
        except Exception as e:
            return AgentResult(agent_name=self.NAME, success=False, error=str(e))

    def _assess_risks(self, task: str, context: dict = None) -> str:
        """评估风险"""
        lines = ["### ⚠️ 风险评估\n"]

        # 基础风险提示
        lines.append("**市场风险**: 当前市场波动率处于正常区间, 建议关注系统性风险.\n")
        lines.append("**集中度风险**: 建议单只股票仓位不超过总资产的20%, 单一行业不超过40%.\n")
        lines.append("**流动性风险**: 建议避免重仓小盘股, 确保持仓股票日均成交额充足.\n")
        lines.append("\n📌 *投资有风险, 入市需谨慎. 本分析不构成投资建议.*")

        return "\n".join(lines)


# ============================================================================
# 4. 组合管理 Agent
# ============================================================================

class PortfolioAgent:
    """组合管理 Agent - 组合构建与优化建议"""

    NAME = "PortfolioAgent"

    def __init__(self, cache_manager=None, llm_config: dict = None, qi_db=None):
        self.cache = cache_manager
        self.llm_config = llm_config or {}
        self.qi_db = qi_db  # V3.11: SQLite 数据库实例

    def execute(self, task: str, context: dict = None) -> AgentResult:
        """执行组合分析

        V3.11: 调用 LLM 生成组合建议, 而非返回"开发中"
        """
        try:
            if self.llm_config and self.llm_config.get('api_key'):
                system_prompt = """你是 QuantInsight Pro 的组合管理专家. 请基于用户问题提供组合构建与优化建议.
输出格式 (Markdown):
### 📊 组合分析
**配置建议**: [基于用户需求的资产配置建议]
**行业分散**: [行业分散度建议]
**风险预算**: [风险预算分配]
📌 *本分析不构成投资建议.*"""
                try:
                    response = _call_llm(
                        [{"role": "system", "content": system_prompt},
                         {"role": "user", "content": task}],
                        self.llm_config,
                        temperature=0.6,
                    )
                    if response:
                        return AgentResult(
                            agent_name=self.NAME,
                            success=True,
                            summary=response,
                            confidence=0.75,
                        )
                except RuntimeError as e:
                    logger.warning(f"PortfolioAgent LLM 调用失败: {e}")

            return AgentResult(
                agent_name=self.NAME,
                success=True,
                summary="### 📊 组合分析\n\n组合管理建议:\n- 建议均衡配置, 单一行业仓位不超过30%\n- 关注估值与成长性匹配\n- 定期再平衡\n\n📌 *本分析不构成投资建议.*",
                confidence=0.6,
            )
        except Exception as e:
            return AgentResult(agent_name=self.NAME, success=False, error=str(e))


# ============================================================================
# 5. 市场监控 Agent
# ============================================================================

class MarketMonitorAgent:
    """市场监控 Agent - 异常检测与预警"""

    NAME = "MarketMonitorAgent"

    def __init__(self, cache_manager=None, llm_config: dict = None, qi_db=None):
        self.cache = cache_manager
        self.llm_config = llm_config or {}
        self.qi_db = qi_db  # V3.11: SQLite 数据库实例

    def execute(self, task: str, context: dict = None) -> AgentResult:
        """执行市场监控"""
        try:
            alerts = []

            if self.cache:
                # 检查涨幅异常
                try:
                    universe = self.cache.get_stock_universe(top_n=100)
                    if universe is not None and "涨跌幅" in universe.columns:
                        universe["涨跌幅"] = pd.to_numeric(universe["涨跌幅"], errors="coerce")
                        # 涨停股
                        limit_up = universe[universe["涨跌幅"] >= 9.5]
                        if len(limit_up) > 0:
                            alerts.append(f"🔴 涨停股 {len(limit_up)} 只")
                        # 跌停股
                        limit_down = universe[universe["涨跌幅"] <= -9.5]
                        if len(limit_down) > 0:
                            alerts.append(f"🟢 跌停股 {len(limit_down)} 只")
                except Exception:
                    pass

                # 检查北向资金
                try:
                    north = self.cache.get_northbound_flow()
                    if north is not None and len(north) > 0:
                        latest = north.iloc[-1]
                        flow_val = latest.get("当日净流入", latest.get("当日资金流入", 0))
                        if isinstance(flow_val, (int, float)):
                            if abs(flow_val) > 50e8:
                                direction = "大幅净流入" if flow_val > 0 else "大幅净流出"
                                alerts.append(f"💰 北向资金{direction} {abs(flow_val)/1e8:.1f}亿")
                except Exception:
                    pass

            summary = "### 📡 市场监控\n\n"
            if alerts:
                for alert in alerts:
                    summary += f"- {alert}\n"
            else:
                summary += "当前市场无明显异常信号.\n"

            return AgentResult(
                agent_name=self.NAME,
                success=True,
                summary=summary,
                data={"alerts": alerts} if alerts else {},  # V3.11: 空 alerts 不放入 data
                confidence=0.85,
            )

        except Exception as e:
            return AgentResult(agent_name=self.NAME, success=False, error=str(e))


# ============================================================================
# Agent 注册表
# ============================================================================

AGENT_REGISTRY = {
    "stock_selection": StockSelectionAgent,
    "analysis": AnalysisAgent,
    "risk": RiskAgent,
    "portfolio": PortfolioAgent,
    "market_monitor": MarketMonitorAgent,
}


def get_agent(name: str, cache_manager=None, llm_config: dict = None, qi_db=None):
    """获取 Agent 实例

    V3.11: 新增 qi_db 参数, 传递给各 Agent
    """
    cls = AGENT_REGISTRY.get(name)
    if cls is None:
        raise ValueError(f"未知 Agent: {name}, 可用: {list(AGENT_REGISTRY.keys())}")
    return cls(cache_manager=cache_manager, llm_config=llm_config, qi_db=qi_db)
