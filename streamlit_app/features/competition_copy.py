# -*- coding: utf-8 -*-
"""AFAC2026 金融智能创新大赛 — 统一品牌文案与页面副标题。"""

PROJECT_ID = "2026FINTECH-FINT-0093"
COMPETITION_SHORT = "AFAC2026 · 金融智能创新大赛"
TEAM = "InsightQuant（慧点资本）"
RECOMMENDER = "杭州永字资产管理有限公司"

HERO_TITLE = "QuantInsight Pro"
HERO_SUBTITLE = f"{COMPETITION_SHORT} · 项目编号 {PROJECT_ID}"
SIDEBAR_BRAND_HTML = (
    '<div class="qi-sidebar-brand" style="padding:12px 10px; margin:-0.25rem -0.25rem 10px -0.25rem;'
    'background:linear-gradient(145deg,#071525 0%,#123a5c 48%,#0a2840 100%);'
    'border-radius:12px;border:1px solid rgba(0,212,255,0.38);'
    'box-shadow:0 6px 20px rgba(0,212,255,0.14),inset 0 1px 0 rgba(255,255,255,0.06);">'
    '<div style="line-height:1.15;margin-bottom:8px;">'
    '<span class="qi-brand-title-main" style="font-size:1.42rem;font-weight:800;letter-spacing:-0.02em;'
    'background:linear-gradient(92deg,#00D4FF 0%,#4DE8FF 42%,#D4AF37 88%);'
    '-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;">'
    'QuantInsight</span>'
    '<span class="qi-brand-title-pro" style="font-size:0.92rem;font-weight:700;color:#F0C75E;'
    'margin-left:5px;vertical-align:super;text-shadow:0 0 12px rgba(212,175,55,0.35);">'
    'Pro</span>'
    '</div>'
    '<div style="display:flex;flex-wrap:wrap;gap:6px;align-items:center;margin-bottom:6px;">'
    '<span class="qi-brand-badge" style="font-size:0.66rem;font-weight:700;letter-spacing:0.06em;color:#041018;'
    'background:linear-gradient(90deg,#00D4FF,#00FF88);padding:3px 9px;border-radius:999px;'
    'box-shadow:0 2px 8px rgba(0,255,136,0.25);">AFAC2026</span>'
    '<span class="qi-brand-subtitle" style="font-size:0.72rem;font-weight:600;color:#C5E4F7;">金融智能创新大赛</span>'
    '</div>'
    f'<div class="qi-brand-project-id" style="font-size:0.67rem;color:#7EB8D8;font-family:ui-monospace,monospace;'
    f'letter-spacing:0.03em;padding:4px 8px;border-radius:6px;'
    f'background:rgba(0,212,255,0.08);border:1px solid rgba(0,212,255,0.18);">'
    f'{PROJECT_ID}</div>'
    '</div>'
)
HERO_TAGLINE = "AI 驱动的另类数据量化投研 Demo · 多源数据 · SHAP 可解释 · 智能问答"

SIDEBAR_TAGLINE = COMPETITION_SHORT

DATA_SOURCE_LINE = (
    "数据链路：SQLite 本地缓存 → 东方财富直连 HTTP → Baostock/AKShare 备用 · "
    "后台 `python refresh_data.py` 定时刷新（ECS 上东方财富可能限流，演示数据自动兜底）"
)

PAGE_SUBTITLES = {
    "home": "AFAC2026 参赛 Demo · 另类数据 + AI 投研 + 量化回测一体化展示",
    "ai_qa": "自然语言投研问答 · 多源数据 grounding · AFAC2026 项目 0093",
    "screener": "自然语言选股 · 多因子评分 · 个股对比 · 可解释 AI 辅助决策",
    "individual": "个股基本面 · SHAP 可解释 · AI 问答 · 报告导出（按需加载）",
    "dashboard": "大盘指数 · 北向资金 · 涨跌停 · 行业排行 · SQLite 优先快速加载",
    "monitor": "7×24 市场宽度监控 · 智能预警 · 北向资金追踪",
    "portfolio": "组合管理 · 实时盈亏 · 风险指标",
    "sim_trade": "模拟交易 · 风控引擎 · 订单管理",
    "smart_cmd": "自然语言指令 · 任务调度 · 自动报告",
    "alt_data": "宏观景气 · 市场情绪 · 产业链 · 舆情/大宗/研报/卫星指数",
    "backtest": "11 年+ 真实回测 · 多策略 · SHAP 可解释（按需展开）",
    "factor": "因子挖掘 · IC 测试 · 信号验证",
    "macro_fusion": "宏观周期 · 因子融合 · Exabel 风格看板",
    "signal": "信号验证中心 · 回测与实盘对照",
    "semantic": "语义检索 · 研报与新闻向量搜索",
    "industry": "行业分析 · 板块资金 · 龙头追踪",
}

HIGHLIGHTS = [
    ("📊", "多源数据融合", "SQLite + 东方财富 + 定时刷新，ECS 稳定可用"),
    ("🧠", "SHAP 可解释", "不只给结论，展示因子贡献与决策路径"),
    ("🤖", "LLM 投研问答", "RAG grounding 真实行情，支持上下文对话"),
    ("📈", "量化回测", "双均线/布林/多因子，11 年+ 历史验证"),
]

COMPETITION_INFO = (
    f"**项目编号**：{PROJECT_ID}\n\n"
    f"**大赛**：{COMPETITION_SHORT}\n\n"
    f"**参赛团队**：{TEAM}\n\n"
    f"**推荐单位**：{RECOMMENDER}"
)
