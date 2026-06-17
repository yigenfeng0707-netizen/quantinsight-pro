"""
QuantInsight Pro - 主Agent编排器 (Orchestrator)
================================================

实现 "规划-执行-反思-调整" 智能闭环,
业内领先的主Agent调度 + 多Agent协作机制.

工作流:
1. Plan: 解析用户意图, 分解子任务, 选择子Agent
2. Execute: 调度子Agent执行, 并行/串行
3. Reflect: 评估输出完整性, 一致性, 矛盾检测
4. Adjust: 对不完整/矛盾的子任务重新执行
5. Synthesize: 合并子Agent输出为统一回答

License: MIT
"""

from __future__ import annotations

import json
import logging
import re
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class OrchestratorResult:
    """编排器最终输出"""
    title: str = ""
    summary: str = ""
    data: dict = field(default_factory=dict)
    recommendation: str = ""
    reasoning: str = ""
    reasoning_chain: list = field(default_factory=list)
    citations: list = field(default_factory=list)
    agent_results: list = field(default_factory=list)
    duration_ms: float = 0
    reflection_count: int = 0

    def to_dict(self) -> dict:
        return asdict(self)


class MainAgent:
    """
    主编排 Agent

    协调 5 个专业子 Agent 完成复杂投研任务:
    - StockSelectionAgent: 选股
    - AnalysisAgent: 分析
    - RiskAgent: 风控
    - PortfolioAgent: 组合
    - MarketMonitorAgent: 监控

    使用示例:
        >>> agent = MainAgent(cache_manager=cache, llm_config=config)
        >>> result = agent.process_query("分析新能源行业投资机会")
        >>> print(result.summary)
    """

    # 意图 → Agent 映射
    INTENT_AGENT_MAP = {
        "选股": ["stock_selection", "analysis"],
        "选": ["stock_selection"],
        "推荐": ["stock_selection", "analysis"],
        "找": ["stock_selection"],
        "筛选": ["stock_selection"],
        "分析": ["analysis", "risk"],
        "研究": ["analysis"],
        "评估": ["analysis", "risk"],
        "估值": ["analysis"],  # V3.11 新增
        "投资逻辑": ["analysis"],  # V3.11 新增
        "投资机会": ["analysis"],  # V3.11 新增
        "行业": ["analysis"],  # V3.11 新增
        "半导体": ["analysis"],  # V3.11 新增
        "新能源": ["analysis"],  # V3.11 新增
        "医药": ["analysis"],  # V3.11 新增
        "消费": ["analysis"],  # V3.11 新增
        "银行": ["analysis"],  # V3.11 新增
        "风险": ["risk"],
        "预警": ["market_monitor"],
        "监控": ["market_monitor"],
        "盯盘": ["market_monitor"],
        "行情": ["market_monitor", "analysis"],
        "组合": ["portfolio", "risk"],
        "持仓": ["portfolio"],
        "配置": ["portfolio", "analysis"],
    }

    MAX_REFLECTION_CYCLES = 2  # 最大反思次数

    def __init__(self, cache_manager=None, llm_config: dict = None, rag_engine=None, qi_db=None):
        """
        Args:
            cache_manager: DataCacheManager 实例
            llm_config: LLM 配置 dict
            rag_engine: FinancialRAG 实例 (可选)
            qi_db: QIDataDB 实例 (可选, V3.11 新增)
        """
        self.cache = cache_manager
        self.llm_config = llm_config or {}
        self.rag = rag_engine
        self.qi_db = qi_db  # V3.11: SQLite 数据库实例

    def process_query(self, question: str, history: list = None) -> OrchestratorResult:
        """
        处理用户查询 (完整流程)

        Args:
            question: 用户问题
            history: 对话历史

        Returns:
            OrchestratorResult
        """
        t0 = time.time()

        # === Phase 1: Plan ===
        plan = self._plan(question, history)

        # === Phase 2: Execute ===
        agent_results = self._execute(plan, question)

        # === Phase 3: Reflect ===
        reflection_count = 0
        for cycle in range(self.MAX_REFLECTION_CYCLES):
            issues = self._reflect(agent_results, question)
            if not issues:
                break
            reflection_count += 1
            # === Phase 4: Adjust ===
            adjusted = self._adjust(issues, plan, question)
            agent_results.update(adjusted)

        # === Phase 5: Synthesize ===
        result = self._synthesize(question, agent_results, plan)
        result.duration_ms = (time.time() - t0) * 1000
        result.reflection_count = reflection_count

        return result

    # ========================================================================
    # Phase 1: Plan (规划)
    # ========================================================================

    def _plan(self, question: str, history: list = None) -> dict:
        """
        解析意图, 分解子任务, 选择子Agent

        Returns:
            dict: {"intent": str, "agents": [str], "sub_tasks": [{agent, task}]}
        """
        plan = {
            "intent": "analysis",
            "agents": ["analysis"],
            "sub_tasks": [],
        }

        # 基于关键词匹配意图
        matched_agents = set()
        for keyword, agents in self.INTENT_AGENT_MAP.items():
            if keyword in question:
                matched_agents.update(agents)

        if matched_agents:
            plan["agents"] = list(matched_agents)
            plan["intent"] = list(matched_agents)[0]

        # 如果没有匹配, 默认用 analysis + market_monitor
        if not matched_agents:
            plan["agents"] = ["analysis", "market_monitor"]

        # 构造子任务
        for agent_name in plan["agents"]:
            plan["sub_tasks"].append({
                "agent": agent_name,
                "task": question,
            })

        logger.info(f"Plan: intent={plan['intent']}, agents={plan['agents']}")
        return plan

    # ========================================================================
    # Phase 2: Execute (执行)
    # ========================================================================

    def _execute(self, plan: dict, question: str) -> dict:
        """
        调度子Agent执行任务

        Returns:
            dict: {agent_name: AgentResult}
        """
        from ai.sub_agents import get_agent, AgentResult

        results = {}

        for sub_task in plan.get("sub_tasks", []):
            agent_name = sub_task["agent"]
            task_desc = sub_task["task"]

            try:
                agent = get_agent(agent_name, self.cache, self.llm_config, self.qi_db)
                result = agent.execute(task_desc)
                results[agent_name] = result
                logger.info(f"Execute: {agent_name} -> success={result.success}")
            except Exception as e:
                logger.error(f"Execute: {agent_name} 失败: {e}")
                results[agent_name] = AgentResult(
                    agent_name=agent_name,
                    success=False,
                    error=str(e),
                )

        return results

    # ========================================================================
    # Phase 3: Reflect (反思)
    # ========================================================================

    def _reflect(self, results: dict, question: str) -> list[dict]:
        """
        评估子Agent输出的完整性和一致性

        Returns:
            list: 需要调整的 issues [{agent, reason}]
        """
        issues = []

        for agent_name, result in results.items():
            if not result.success:
                issues.append({
                    "agent": agent_name,
                    "reason": f"执行失败: {result.error}",
                })
            elif not result.summary and not result.data:
                issues.append({
                    "agent": agent_name,
                    "reason": "输出为空",
                })

        return issues

    # ========================================================================
    # Phase 4: Adjust (调整)
    # ========================================================================

    def _adjust(self, issues: list, plan: dict, question: str) -> dict:
        """
        对失败的子任务重新执行 (可修改策略)

        Returns:
            dict: 更新后的 {agent_name: AgentResult}
        """
        from ai.sub_agents import get_agent, AgentResult

        adjusted = {}

        for issue in issues:
            agent_name = issue["agent"]
            logger.info(f"Adjust: 重新执行 {agent_name}, 原因: {issue['reason']}")

            try:
                # 简化任务重试
                agent = get_agent(agent_name, self.cache, self.llm_config, self.qi_db)
                result = agent.execute(question)
                adjusted[agent_name] = result
            except Exception as e:
                adjusted[agent_name] = AgentResult(
                    agent_name=agent_name,
                    success=False,
                    error=f"重试仍失败: {e}",
                )

        return adjusted

    # ========================================================================
    # Phase 5: Synthesize (合成)
    # ========================================================================

    def _synthesize(self, question: str, results: dict, plan: dict) -> OrchestratorResult:
        """
        合并子Agent输出为统一回答

        策略:
        - 如果只有1个Agent成功, 直接用其输出
        - 如果有多个Agent, 用 LLM 合并各自的 summary/data
        - 添加统一的 reasoning chain 和 citations
        """
        from ai.sub_agents import _call_llm

        # 收集成功结果
        success_results = {k: v for k, v in results.items() if v.success}
        all_results = list(results.values())

        if not success_results:
            return OrchestratorResult(
                title="分析失败",
                summary="所有子Agent执行失败, 请检查网络连接或稍后重试.",
                recommendation="请稍后重试, 或简化查询条件.",
                agent_results=[asdict(r) for r in all_results],
            )

        # 合并标题
        title_parts = []
        for name, r in success_results.items():
            if name == "stock_selection":
                title_parts.append("智能选股")
            elif name == "analysis":
                title_parts.append("投资分析")
            elif name == "risk":
                title_parts.append("风险评估")
            elif name == "market_monitor":
                title_parts.append("市场监控")
            elif name == "portfolio":
                title_parts.append("组合分析")

        title = " + ".join(title_parts) if title_parts else "AI 投研分析"

        # 合并摘要 - 多个 Agent 时用 LLM 合成
        summary_parts = []
        for name, r in success_results.items():
            if r.summary:
                summary_parts.append(f"[{name}] {r.summary}")

        if len(success_results) > 1 and self.llm_config and self.llm_config.get('api_key'):
            # 多 Agent 结果用 LLM 合成统一摘要
            agent_summaries = "\n\n---\n\n".join(summary_parts)

            # V3.11: 从 SQLite 注入数据上下文
            sqlite_context = ""
            if self.qi_db:
                try:
                    # 行业板块数据
                    sector_df = self.qi_db.get_sector_flow()
                    if sector_df is not None and len(sector_df) > 0:
                        top_sectors = sector_df.head(5)
                        sqlite_context += "\n📊 板块资金流(TOP5):\n"
                        for _, row in top_sectors.iterrows():
                            name = row.get('板块名称', row.get('板块', 'N/A'))
                            pct = row.get('涨跌幅', row.get('change_pct', 0))
                            sqlite_context += f"  {name}: {pct}%\n"
                except Exception as e:
                    logger.warning(f"合成时读取 sector_flow 失败: {e}")
                try:
                    # 北向资金
                    nb_df = self.qi_db.get_northbound_flow(days=3)
                    if nb_df is not None and len(nb_df) > 0:
                        latest = nb_df.iloc[-1]
                        sqlite_context += f"\n🌐 北向资金(最近): {latest.to_dict()}\n"
                except Exception as e:
                    logger.warning(f"合成时读取 northbound_flow 失败: {e}")

            synthesize_prompt = f"""你是 QuantInsight Pro 的投研合成助手. 请将以下多个专业Agent的分析结果合成为一份连贯、结构化的投研报告摘要.

用户问题: {question}

各Agent分析结果:
{agent_summaries}

实时数据上下文:
{sqlite_context}

请输出合成后的摘要 (Markdown格式), 要求:
1. 保留各Agent的核心观点和数据
2. 消除重复内容
3. 突出关键结论和投资建议
4. 标注数据来源"""
            try:
                llm_summary = _call_llm(
                    [{"role": "user", "content": synthesize_prompt}],
                    self.llm_config,
                    temperature=0.5,
                )
                if llm_summary and len(llm_summary) > 50:
                    summary = llm_summary
                else:
                    summary = "\n\n---\n\n".join(summary_parts)
            except Exception:
                summary = "\n\n---\n\n".join(summary_parts)
        else:
            summary = "\n\n---\n\n".join(summary_parts)

        # 合并数据
        merged_data = {}
        for name, r in success_results.items():
            if r.data:
                for k, v in r.data.items():
                    merged_data[f"{name}.{k}" if k in merged_data else k] = v

        # 合并引用
        all_citations = []
        for r in success_results.values():
            if r.citations:
                all_citations.extend(r.citations)

        # 构建推理链
        reasoning_chain = []
        reasoning_chain.append(f"📋 **PLAN**: 解析意图 → 选择Agent: {list(success_results.keys())}")
        for name, r in success_results.items():
            status = "✅" if r.success else "❌"
            reasoning_chain.append(f"🔧 **EXECUTE** [{name}]: {status} (置信度: {r.confidence:.0%})")
        reasoning_chain.append(f"🔄 **REFLECT**: 反思 {len([r for r in all_results if not r.success])} 个问题")
        reasoning_chain.append(f"✅ **SYNTHESIZE**: 合并 {len(success_results)} 个Agent输出")

        # 推荐理由
        recommendation = ""
        for name, r in success_results.items():
            if name == "analysis" and r.data and "recommendation" in r.data:
                recommendation = r.data["recommendation"]
                break
            if name == "stock_selection":
                top_stocks = r.data.get("top_stocks", [])
                if top_stocks:
                    names = [s.get("名称", "") for s in top_stocks[:5] if s.get("名称")]
                    if names:
                        recommendation = f"关注标的: {', '.join(names)}"

        if not recommendation:
            recommendation = "建议结合自身风险偏好和市场情况综合决策, 投资有风险, 入市需谨慎."

        return OrchestratorResult(
            title=f"🤖 {title}",
            summary=summary,
            data=merged_data,
            recommendation=recommendation,
            reasoning="\n".join(reasoning_chain),
            reasoning_chain=reasoning_chain,
            citations=[str(c) for c in all_citations],
            agent_results=[asdict(r) for r in all_results],
        )

    # ========================================================================
    # 快捷方法
    # ========================================================================

    def quick_answer(self, question: str) -> dict:
        """快捷回答 (兼容旧接口, 返回 dict)"""
        result = self.process_query(question)
        return {
            "title": result.title,
            "summary": result.summary,
            "data": result.data,
            "recommendation": result.recommendation,
            "reasoning": result.reasoning,
            "reasoning_chain": result.reasoning_chain,
            "citations": result.citations,
        }


# ============================================================================
# 全局单例
# ============================================================================

_main_agent: Optional[MainAgent] = None


def get_main_agent(cache_manager=None, llm_config: dict = None) -> MainAgent:
    """获取全局 MainAgent 单例"""
    global _main_agent
    if _main_agent is None or (cache_manager and llm_config):
        _main_agent = MainAgent(
            cache_manager=cache_manager,
            llm_config=llm_config,
        )
    return _main_agent
