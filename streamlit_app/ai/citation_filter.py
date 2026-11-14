# -*- coding: utf-8 -*-
"""QuantInsight Pro - 引用相关性过滤器 (Citation Relevance Filter)
====================================================

问题：数据接地点查会把问题中提到的**每一个** (代码, 日期) 都生成引用，
在区间/比较/回测类问题里，区间起点的点查引用成了"计算中间量的引用"，
它们支撑计算过程，却不支撑最终答案 —— 反映在评测上就是引用精确率 (CP) 偏低
（507 条 S3 实测 CP=0.8021，假阳性 100% 为此类"起点日期点查引用"）。

过滤规则（确定性、可复现，不依赖 LLM）：
1. 日期维度：问题提到 >=2 个日期（区间题）时，只保留落在锚点日期（问题中
   最晚日期）上的引用；单日期问题保留该日期上的引用；不携带任何问题日期的
   引用（如宏观/板块快照）视为背景信息，保留。
2. 代码维度：引用内容中出现的股票代码若全部不在问题中，视为无关引用剔除；
   不含代码的引用不受影响。

开关：默认开启；设环境变量 QI_DISABLE_CITATION_FILTER=1 关闭（消融用）。

用法（编排器在合成阶段调用）:
    from ai.citation_filter import filter_citations
    kept = filter_citations(question, citations)
"""
from __future__ import annotations

import os
import re

DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")
CODE_RE = re.compile(r"\b\d{6}\b")


def is_enabled() -> bool:
    return os.getenv("QI_DISABLE_CITATION_FILTER", "") != "1"


def _citation_blob(c) -> str:
    """引用 -> 文本。兼容 dict 与字符串两种形态。"""
    if isinstance(c, dict):
        return " ".join(
            str(c.get(k, "")) for k in ("source", "api_name", "description", "data_snippet")
        )
    return str(c)


def filter_citations(question: str, citations: list) -> list:
    """按问题相关性过滤引用列表。

    Args:
        question: 用户问题原文
        citations: 引用列表（dict 或字符串）
    Returns:
        过滤后的引用列表（保持原顺序与对象类型）
    """
    if not is_enabled() or not citations:
        return list(citations or [])

    q = question or ""
    q_dates = DATE_RE.findall(q)
    q_codes = set(CODE_RE.findall(q))
    # 区间题的锚点日期 = 问题中出现的最晚日期（终值才是答案落点）
    anchor = max(q_dates) if q_dates else None

    kept = []
    for c in citations:
        blob = _citation_blob(c)
        # 日期维度
        if anchor is not None:
            has_q_date = any(d in blob for d in q_dates)
            if has_q_date and anchor not in blob:
                continue  # 携带了问题日期但不是锚点 -> 计算中间量引用
        # 代码维度
        c_codes = set(CODE_RE.findall(blob))
        if q_codes and c_codes and not (c_codes & q_codes):
            continue  # 只含问题外代码 -> 无关引用
        kept.append(c)
    return kept
