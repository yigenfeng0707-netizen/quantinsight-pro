"""
QuantInsight Pro - 引用溯源系统 (Citation System)
===================================================

追踪 AI 回答中使用的数据来源, 生成结构化引用链.
业内领先的 "规划-工具调用-数据-结论" 推理可视化.

License: MIT
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class Citation:
    """单条引用"""
    source: str = ""           # 数据源: "东方财富" / "akshare" / "知识库" / "LLM推理"
    api_name: str = ""         # 接口名: "stock_zh_a_spot_em"
    description: str = ""      # 描述: "全A股实时行情"
    date: str = ""             # 数据日期
    url: str = ""              # 来源URL (可选)
    confidence: float = 1.0    # 置信度 0-1
    data_snippet: str = ""     # 数据摘要 (前100字)

    def to_display(self) -> str:
        """生成显示用文本"""
        parts = [f"[{self.source}]"]
        if self.api_name:
            parts.append(f"API: {self.api_name}")
        if self.description:
            parts.append(self.description)
        if self.date:
            parts.append(f"日期: {self.date}")
        return " | ".join(parts)


@dataclass
class ReasoningStep:
    """推理步骤"""
    step_type: str = ""        # "plan" / "tool_call" / "data_retrieve" / "analysis" / "reflect" / "conclusion"
    description: str = ""      # 步骤描述
    agent: str = ""            # 执行的 Agent
    input_data: str = ""       # 输入摘要
    output_data: str = ""      # 输出摘要
    duration_ms: float = 0     # 耗时
    citations: list = field(default_factory=list)

    def to_display(self) -> str:
        """生成显示用文本"""
        icon_map = {
            "plan": "📋", "tool_call": "🔧", "data_retrieve": "📊",
            "analysis": "🧠", "reflect": "🔄", "conclusion": "✅",
        }
        icon = icon_map.get(self.step_type, "•")
        result = f"{icon} **{self.step_type.upper()}** ({self.agent}): {self.description}"
        if self.duration_ms > 0:
            result += f" `[{self.duration_ms:.0f}ms]`"
        return result


class CitationTracker:
    """
    引用追踪器

    在 AI 回答过程中追踪:
    1. 使用了哪些数据源
    2. 调用了哪些 API
    3. 每个推理步骤的输入输出
    4. 最终结论的数据支撑

    使用示例:
        >>> tracker = CitationTracker()
        >>> tracker.add_reasoning("plan", "MainAgent", "解析用户问题", "分析新能源行业投资机会")
        >>> tracker.add_citation("东方财富", "stock_zh_a_spot_em", "A股实时行情", date="2026-06-13")
        >>> tracker.add_reasoning("analysis", "AnalysisAgent", "分析估值水平", "新能源板块PE 22.5x")
        >>> tracker.add_citation("知识库", "rag_retrieval", "新能源行业研报", confidence=0.85)
        >>> result = tracker.export()
    """

    def __init__(self):
        self.steps: list[ReasoningStep] = []
        self.citations: list[Citation] = []
        self._start_time = datetime.now()
        self._step_start = datetime.now()

    def add_reasoning(
        self,
        step_type: str,
        agent: str,
        description: str,
        output_data: str = "",
        input_data: str = "",
    ) -> ReasoningStep:
        """添加推理步骤"""
        now = datetime.now()
        duration = (now - self._step_start).total_seconds() * 1000
        self._step_start = now

        step = ReasoningStep(
            step_type=step_type,
            agent=agent,
            description=description,
            input_data=input_data[:200],
            output_data=output_data[:200],
            duration_ms=duration,
            citations=[c.to_display() for c in self.citations[-3:]],  # 最近3条引用
        )
        self.steps.append(step)
        return step

    def add_citation(
        self,
        source: str,
        api_name: str = "",
        description: str = "",
        date: str = "",
        url: str = "",
        confidence: float = 1.0,
        data_snippet: str = "",
    ) -> Citation:
        """添加数据引用"""
        citation = Citation(
            source=source,
            api_name=api_name,
            description=description,
            date=date or datetime.now().strftime("%Y-%m-%d"),
            url=url,
            confidence=confidence,
            data_snippet=data_snippet[:100],
        )
        self.citations.append(citation)
        return citation

    def add_citations_from_dataframe(self, source: str, api_name: str, df, description: str = ""):
        """从 DataFrame 自动添加引用"""
        if df is not None and len(df) > 0:
            snippet = f"{len(df)} 行, 列: {list(df.columns[:5])}"
            self.add_citation(
                source=source,
                api_name=api_name,
                description=description or api_name,
                confidence=0.9,
                data_snippet=snippet,
            )

    def export(self) -> dict:
        """导出完整追踪数据"""
        total_time = (datetime.now() - self._start_time).total_seconds() * 1000
        return {
            "reasoning_chain": [asdict(s) for s in self.steps],
            "citations": [asdict(c) for c in self.citations],
            "total_duration_ms": total_time,
            "step_count": len(self.steps),
            "citation_count": len(self.citations),
        }

    def get_reasoning_display(self) -> list[str]:
        """获取推理链显示文本 (用于UI展示)"""
        return [step.to_display() for step in self.steps]

    def get_citations_display(self) -> list[str]:
        """获取引用列表显示文本"""
        return [c.to_display() for c in self.citations]

    def get_summary(self) -> str:
        """获取摘要"""
        return (
            f"推理步骤: {len(self.steps)} 步 | "
            f"数据来源: {len(self.citations)} 个 | "
            f"耗时: {(datetime.now() - self._start_time).total_seconds():.1f}s"
        )
