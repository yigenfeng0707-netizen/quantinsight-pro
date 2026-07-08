# -*- coding: utf-8 -*-
"""
QuantInsight Pro - UI 主题 V3.0
=================================

V3.0 升级重点:
- 全局 UI 一致性：所有模块页面统一视觉风格
- 金融科技美学：深色背景 + 青色/紫色渐变强调
- 排版规范：h1/h2/h3/body/small 统一字号/颜色/边框
- 侧边栏增强：渐变激活态、悬停位移、分割线
- 卡片/指标统一：16px 圆角、青色边框、深色背景、悬停高亮
- 图表容器：深色背景 + 圆角 + 内边距
- 状态指示器：涨/跌/中性/信息 四色规范
- 表格增强：青色表头、交替行色、悬停高亮

品牌色规范:
- 深空蓝: #0A0E27 (主背景)
- 霓虹青: #00D4FF (主强调)
- 金色:   #FFB800 (次强调)
- 紫罗兰: #7B61FF (渐变强调)
- 浅色文字: #FFFFFF (主文字)
- 次要文字: #C8D0E0 (次文字)
- 中性灰: #8A92B0 (辅助文字)
- 警示红: #FF4D4F (错误/跌)
- 成功绿: #00C896 (成功/涨)
"""

import streamlit as st

# ============ 品牌色 (V3.0 增强饱和度) ============
BRAND_DEEP = "#0A0E27"      # 深空蓝
BRAND_CYAN = "#00D4FF"      # 霓虹青 (主强调)
BRAND_GOLD = "#FFB800"      # 金色 (次强调)
BRAND_PURPLE = "#7B61FF"    # 紫罗兰 (渐变强调)
BRAND_GREEN = "#00C896"     # 成功绿 / 涨
BRAND_RED = "#FF4D4F"       # 警示红 / 跌
BRAND_ORANGE = "#FF7A45"    # 橙色 (量化)

# 文字 (V3.0 增强对比度)
TEXT_PRIMARY = "#FFFFFF"       # 纯白 - 主要文字 (对比度 21:1)
TEXT_SECONDARY = "#C8D0E0"     # 浅灰 - 次要文字 (对比度 9.6:1, WCAG AAA)
TEXT_MUTED = "#8A92B0"         # 中性灰 - 辅助文字 (对比度 5.7:1, WCAG AA)
TEXT_DISABLED = "#5A6072"      # 深灰 - 禁用文字

# 背景 (V3.0 增强层次)
BG_PRIMARY = "#0A0E27"      # 主背景
BG_SECONDARY = "#131938"    # 次背景 (卡片)
BG_TERTIARY = "#1C2347"     # 三级背景 (悬停)
BG_HOVER = "#252D5C"        # 悬停态
BG_ACTIVE = "#00D4FF"       # 激活态 (霓虹青)
BG_CARD = "#0D1230"         # 卡片背景 (统一)


# ============ CSS 注入 (V3.0 全面一致性增强) ============
def inject_custom_css():
    """注入自定义 CSS - V3.0 全面一致性 + 金融科技美学"""
    css = f"""
<style>
/* ============================================================
   QuantInsight Pro V3.0 — 全局一致性金融科技主题
   ============================================================ */

/* ============ 1. 全局页面 ============ */
.main {{
    background: linear-gradient(135deg, {BG_PRIMARY} 0%, #0F1532 100%);
    color: {TEXT_PRIMARY};
}}
.stApp {{
    background: {BG_PRIMARY};
}}
section.main > div {{
    padding-top: 2rem !important;
}}

/* ============ 2. 排版一致性 ============ */
h1 {{
    color: {TEXT_PRIMARY} !important;
    font-weight: 800 !important;
    font-size: 28px !important;
    border-left: 4px solid {BRAND_CYAN} !important;
    padding-left: 14px !important;
    margin-bottom: 16px !important;
    line-height: 1.3 !important;
}}
h2 {{
    color: {TEXT_PRIMARY} !important;
    font-weight: 700 !important;
    font-size: 22px !important;
    border-left: 3px solid {BRAND_GOLD} !important;
    padding-left: 12px !important;
    padding-bottom: 4px !important;
    margin-top: 28px !important;
    margin-bottom: 12px !important;
    line-height: 1.3 !important;
}}
h3 {{
    color: {TEXT_SECONDARY} !important;
    font-weight: 700 !important;
    font-size: 18px !important;
    margin-top: 20px !important;
    margin-bottom: 8px !important;
    line-height: 1.4 !important;
}}
h4 {{
    color: {TEXT_PRIMARY} !important;
    font-weight: 600 !important;
    font-size: 16px !important;
}}
p, li, span {{
    color: {TEXT_SECONDARY} !important;
    line-height: 1.7 !important;
    font-size: 14px !important;
}}
small, .small-text {{
    color: {TEXT_MUTED} !important;
    font-size: 12px !important;
    line-height: 1.5 !important;
}}
strong, b {{
    color: {BRAND_GOLD} !important;
    font-weight: 700 !important;
}}
code {{
    color: {BRAND_CYAN} !important;
    background: {BG_TERTIARY} !important;
    border-radius: 4px !important;
    padding: 2px 6px !important;
    font-size: 13px !important;
}}
pre {{
    background: {BG_SECONDARY} !important;
    border: 1px solid {BRAND_CYAN}30 !important;
    border-radius: 8px !important;
    padding: 12px !important;
}}
a {{
    color: {BRAND_CYAN} !important;
    text-decoration: none !important;
    font-weight: 600 !important;
    transition: all 0.2s ease !important;
}}
a:hover {{
    color: {BRAND_PURPLE} !important;
    text-shadow: 0 0 8px {BRAND_CYAN}50;
}}

/* ============ 3. 侧边栏 (V3.0 全面增强) ============ */
[data-testid="stSidebar"] {{
    background: linear-gradient(180deg, #0A0E27 0%, #131938 100%);
    border-right: 2px solid {BRAND_CYAN}30;
}}
/* 侧边栏标题 */
[data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {{
    color: {BRAND_CYAN} !important;
    font-weight: 700 !important;
}}
/* 侧边栏菜单项 — 大字号 + 充足间距 */
[data-testid="stSidebar"] .stRadio > label {{
    color: {TEXT_SECONDARY} !important;
    font-weight: 600 !important;
    font-size: 15px !important;
    padding: 12px 16px !important;
    border-radius: 8px !important;
    transition: all 0.2s ease !important;
    background: transparent !important;
    border: 1px solid transparent !important;
}}
/* 悬停：位移 + 阴影 */
[data-testid="stSidebar"] .stRadio > label:hover {{
    background: {BG_HOVER} !important;
    color: {TEXT_PRIMARY} !important;
    border-color: {BRAND_CYAN}50 !important;
    transform: translateX(4px) !important;
    box-shadow: 0 2px 8px {BRAND_CYAN}20 !important;
}}
[data-testid="stSidebar"] .stRadio [data-testid="stMarkdownContainer"] p {{
    color: {TEXT_SECONDARY} !important;
    font-weight: 600 !important;
    font-size: 15px !important;
}}
/* 侧边栏激活项 — 渐变背景 + 白色文字 */
[data-testid="stSidebar"] .stRadio input[type="radio"]:checked + div {{
    background: linear-gradient(90deg, {BRAND_CYAN} 0%, {BRAND_PURPLE} 100%) !important;
    color: #FFFFFF !important;
    font-weight: 800 !important;
    box-shadow: 0 4px 12px {BRAND_CYAN}40 !important;
}}
[data-testid="stSidebar"] .stRadio input[type="radio"]:checked + div p {{
    color: #FFFFFF !important;
    font-weight: 800 !important;
}}
/* 侧边栏分割线 — 细青色线 */
[data-testid="stSidebar"] hr {{
    border: none !important;
    height: 1px !important;
    background: {BRAND_CYAN}30 !important;
    margin: 8px 12px !important;
}}

/* ============ 4. 按钮 (V3.0 渐变+悬停) ============ */
.stButton > button {{
    background: linear-gradient(135deg, {BRAND_CYAN} 0%, {BRAND_PURPLE} 100%) !important;
    color: #FFFFFF !important;
    font-weight: 700 !important;
    font-size: 15px !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 10px 24px !important;
    box-shadow: 0 4px 12px {BRAND_CYAN}30 !important;
    transition: all 0.2s ease !important;
    letter-spacing: 0.3px !important;
}}
.stButton > button:hover {{
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 20px {BRAND_CYAN}50 !important;
    filter: brightness(1.1) !important;
}}
.stButton > button:active {{
    transform: translateY(0) !important;
    filter: brightness(0.95) !important;
}}
/* 次要按钮 */
.stButton > button[kind="secondary"],
.stButton > button[kind="secondary"]:hover {{
    background: {BG_TERTIARY} !important;
    color: {TEXT_PRIMARY} !important;
    border: 1px solid {BRAND_CYAN}50 !important;
}}

/* ============ 5. 输入框 (V3.0 统一深色+青色焦点) ============ */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stNumberInput > div > div > input {{
    background: {BG_SECONDARY} !important;
    color: {TEXT_PRIMARY} !important;
    border: 1px solid {BRAND_CYAN}40 !important;
    border-radius: 8px !important;
    font-size: 14px !important;
    padding: 10px 14px !important;
    transition: all 0.2s ease !important;
}}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus,
.stNumberInput > div > div > input:focus {{
    border-color: {BRAND_CYAN} !important;
    box-shadow: 0 0 0 3px {BRAND_CYAN}30 !important;
    outline: none !important;
}}
/* 输入框标签 */
.stTextInput label, .stTextArea label, .stNumberInput label {{
    color: {TEXT_SECONDARY} !important;
    font-weight: 600 !important;
    font-size: 14px !important;
}}

/* ============ 6. Selectbox / Multiselect (V3.0) ============ */
.stSelectbox > div > div,
.stMultiSelect > div > div {{
    background: {BG_SECONDARY} !important;
    border: 1px solid {BRAND_CYAN}40 !important;
    border-radius: 8px !important;
    color: {TEXT_PRIMARY} !important;
    transition: all 0.2s ease !important;
}}
.stSelectbox > div > div:hover,
.stMultiSelect > div > div:hover {{
    border-color: {BRAND_CYAN}80 !important;
}}
.stSelectbox label, .stMultiSelect label {{
    color: {TEXT_SECONDARY} !important;
    font-weight: 600 !important;
    font-size: 14px !important;
}}
/* 下拉菜单 */
.stSelectbox div[data-baseweb="popover"] {{
    background: {BG_SECONDARY} !important;
    border: 1px solid {BRAND_CYAN}30 !important;
    border-radius: 8px !important;
}}
.stSelectbox li {{
    color: {TEXT_SECONDARY} !important;
    font-size: 14px !important;
}}
.stSelectbox li:hover {{
    background: {BG_HOVER} !important;
    color: {TEXT_PRIMARY} !important;
}}

/* ============ 7. Tabs (V3.0 深色+青色下划线) ============ */
.stTabs [data-baseweb="tab-list"] {{
    gap: 4px;
    background: {BG_SECONDARY};
    border-radius: 8px;
    padding: 4px;
    border-bottom: 2px solid {BRAND_CYAN}20 !important;
}}
.stTabs [data-baseweb="tab"] {{
    background: transparent !important;
    color: {TEXT_SECONDARY} !important;
    font-weight: 600 !important;
    font-size: 14px !important;
    padding: 10px 20px !important;
    border-radius: 6px 6px 0 0 !important;
    transition: all 0.2s ease !important;
    border-bottom: 2px solid transparent !important;
}}
.stTabs [data-baseweb="tab"]:hover {{
    background: {BG_HOVER} !important;
    color: {TEXT_PRIMARY} !important;
}}
/* 激活 Tab — 青色下划线 */
.stTabs [aria-selected="true"] {{
    background: transparent !important;
    color: {BRAND_CYAN} !important;
    font-weight: 800 !important;
    border-bottom: 3px solid {BRAND_CYAN} !important;
    box-shadow: none !important;
}}
/* Tab 面板 */
.stTabs [data-baseweb="tab-panel"] {{
    background: {BG_SECONDARY} !important;
    border-radius: 0 0 8px 8px !important;
    padding: 16px !important;
    border: 1px solid {BRAND_CYAN}15 !important;
    border-top: none !important;
}}

/* ============ 8. Expander (V3.0 深色+青色边框) ============ */
.streamlit-expanderHeader {{
    background: {BG_SECONDARY} !important;
    color: {TEXT_PRIMARY} !important;
    font-weight: 700 !important;
    font-size: 15px !important;
    border-radius: 8px !important;
    border: 1px solid {BRAND_CYAN}30 !important;
    transition: all 0.2s ease !important;
}}
.streamlit-expanderHeader:hover {{
    border-color: {BRAND_CYAN}60 !important;
}}
.streamlit-expanderContent {{
    background: {BG_PRIMARY} !important;
    border: 1px solid {BRAND_CYAN}20 !important;
    border-top: none !important;
    border-radius: 0 0 8px 8px !important;
    padding: 12px 16px !important;
}}

/* ============ 9. Metric 卡片 (V3.0 统一深色+青色强调) ============ */
[data-testid="stMetricValue"] {{
    color: {BRAND_CYAN} !important;
    font-size: 28px !important;
    font-weight: 800 !important;
}}
[data-testid="stMetricLabel"] {{
    color: {TEXT_SECONDARY} !important;
    font-size: 14px !important;
    font-weight: 600 !important;
}}
[data-testid="stMetricDelta"] {{
    font-size: 13px !important;
    font-weight: 700 !important;
}}
/* Metric 容器 — 卡片化：深色背景 + 青色边框 + 16px 圆角 */
[data-testid="stMetric"] {{
    background: {BG_CARD} !important;
    border: 1px solid rgba(0,212,255,0.2) !important;
    border-radius: 16px !important;
    padding: 16px 20px !important;
    transition: all 0.2s ease !important;
}}
[data-testid="stMetric"]:hover {{
    border-color: rgba(0,212,255,0.5) !important;
    box-shadow: 0 4px 16px rgba(0,212,255,0.1) !important;
}}

/* ============ 10. DataFrame / 表格 (V3.0 深色+青色表头+交替行) ============ */
.stDataFrame {{
    background: {BG_SECONDARY} !important;
    border: 1px solid {BRAND_CYAN}30 !important;
    border-radius: 12px !important;
    overflow: hidden;
}}
/* Glide 数据网格 (Streamlit 内部) */
.stDataFrame [data-testid="stDataFrame"] {{
    background: {BG_SECONDARY} !important;
}}
.stDataFrame table {{
    color: {TEXT_PRIMARY} !important;
}}
.stDataFrame th {{
    background: {BG_TERTIARY} !important;
    color: {BRAND_CYAN} !important;
    font-weight: 700 !important;
    font-size: 13px !important;
    text-transform: uppercase !important;
    letter-spacing: 0.5px !important;
    padding: 10px 14px !important;
    border-bottom: 2px solid {BRAND_CYAN}40 !important;
}}
.stDataFrame td {{
    color: {TEXT_SECONDARY} !important;
    font-size: 13px !important;
    padding: 8px 14px !important;
    border-bottom: 1px solid {BRAND_CYAN}10 !important;
}}
.stDataFrame tr:nth-child(even) td {{
    background: rgba(0,212,255,0.03) !important;
}}
.stDataFrame tr:nth-child(odd) td {{
    background: {BG_SECONDARY} !important;
}}
.stDataFrame tr:hover td {{
    background: {BG_HOVER} !important;
    color: {TEXT_PRIMARY} !important;
}}
/* st.table / st.data_editor (HTML 表格) */
.stTable {{
    background: {BG_SECONDARY} !important;
    color: {TEXT_PRIMARY} !important;
    border-radius: 12px !important;
    overflow: hidden !important;
    border: 1px solid {BRAND_CYAN}30 !important;
}}
.stTable thead tr th {{
    background: {BG_TERTIARY} !important;
    color: {BRAND_CYAN} !important;
    font-weight: 700 !important;
    font-size: 13px !important;
    text-transform: uppercase !important;
    letter-spacing: 0.5px !important;
    padding: 10px 14px !important;
    border-bottom: 2px solid {BRAND_CYAN}40 !important;
}}
.stTable tbody tr:nth-child(even) {{
    background: rgba(0,212,255,0.03) !important;
}}
.stTable tbody tr:nth-child(odd) {{
    background: {BG_SECONDARY} !important;
}}
.stTable tbody tr:hover {{
    background: {BG_HOVER} !important;
}}
.stTable td {{
    color: {TEXT_SECONDARY} !important;
    font-size: 13px !important;
    padding: 8px 14px !important;
    border-bottom: 1px solid {BRAND_CYAN}10 !important;
}}

/* ============ 11. Slider (V3.0 青色轨道+紫色滑块) ============ */
.stSlider > div > div > div > div {{
    background: linear-gradient(90deg, {BRAND_CYAN} 0%, {BRAND_PURPLE} 100%) !important;
}}
.stSlider [role="slider"] {{
    background: {BRAND_PURPLE} !important;
    border: 2px solid {BRAND_CYAN} !important;
    box-shadow: 0 0 8px {BRAND_CYAN}40 !important;
}}
.stSlider label {{
    color: {TEXT_SECONDARY} !important;
    font-weight: 600 !important;
    font-size: 14px !important;
}}

/* ============ 12. Progress (V3.0 青色→紫色渐变) ============ */
.stProgress > div > div > div {{
    background: linear-gradient(90deg, {BRAND_CYAN} 0%, {BRAND_PURPLE} 100%) !important;
    border-radius: 4px !important;
}}
.stProgress > div > div {{
    background: {BG_TERTIARY} !important;
    border-radius: 4px !important;
}}

/* ============ 13. Alert / Info / Warning / Error ============ */
.stAlert {{
    border-radius: 8px !important;
    border-left: 4px solid {BRAND_CYAN} !important;
    background: {BG_SECONDARY} !important;
    color: {TEXT_PRIMARY} !important;
    font-size: 14px !important;
}}
.stAlert[data-baseweb="notification"] {{
    background: {BG_SECONDARY} !important;
}}

/* ============ 14. Spinner ============ */
.stSpinner > div {{
    border-top-color: {BRAND_CYAN} !important;
}}

/* ============ 15. Toast / Status ============ */
[data-baseweb="toast"] {{
    background: {BG_SECONDARY} !important;
    color: {TEXT_PRIMARY} !important;
    border-left: 4px solid {BRAND_CYAN} !important;
}}

/* ============ 16. 图表容器 (V3.0 新增) ============ */
.stPlotlyChart, .stPyplotChart, .stAltairChart, .stVegaLiteChart,
.element-container .stPlotlyChart {{
    background: {BG_SECONDARY} !important;
    border: 1px solid {BRAND_CYAN}20 !important;
    border-radius: 12px !important;
    padding: 12px !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.2) !important;
}}
/* Plotly 模式栏 */
.js-plotly-plot .plotly .modebar {{
    background: transparent !important;
}}
.js-plotly-plot .plotly .modebar-btn path {{
    fill: {TEXT_MUTED} !important;
}}
.js-plotly-plot .plotly .modebar-btn:hover path {{
    fill: {BRAND_CYAN} !important;
}}
/* ECharts / 通用图表容器 */
div[data-testid="stDecoration"] + div > div {{
    border-radius: 12px !important;
}}

/* ============ 17. 状态指示器颜色 (V3.0 新增) ============ */
/* 涨/正面 */
.positive, .up, .delta-positive, [data-testid="stMetricDelta-positive"] {{
    color: {BRAND_GREEN} !important;
}}
/* 跌/负面 */
.negative, .down, .delta-negative, [data-testid="stMetricDelta-negative"] {{
    color: {BRAND_RED} !important;
}}
/* 中性 */
.neutral {{
    color: {BRAND_GOLD} !important;
}}
/* 信息 */
.info-indicator {{
    color: {BRAND_CYAN} !important;
}}
/* Metric Delta SVG 图标隐藏 (用颜色区分即可) */
[data-testid="stMetricDelta"] svg {{
    display: none !important;
}}

/* ============ 18. Checkbox / Toggle (V3.0) ============ */
.stCheckbox label {{
    color: {TEXT_SECONDARY} !important;
    font-weight: 600 !important;
    font-size: 14px !important;
}}
.stCheckbox input[type="checkbox"]:checked + div {{
    background: {BRAND_CYAN} !important;
    border-color: {BRAND_CYAN} !important;
}}

/* ============ 19. Date Input / Time Input (V3.0) ============ */
.stDateInput > div > div > input,
.stTimeInput > div > div > input {{
    background: {BG_SECONDARY} !important;
    color: {TEXT_PRIMARY} !important;
    border: 1px solid {BRAND_CYAN}40 !important;
    border-radius: 8px !important;
}}
.stDateInput label, .stTimeInput label {{
    color: {TEXT_SECONDARY} !important;
    font-weight: 600 !important;
    font-size: 14px !important;
}}

/* ============ 20. Divider (V3.0) ============ */
hr {{
    border: none !important;
    height: 1px !important;
    background: {BRAND_CYAN}20 !important;
    margin: 16px 0 !important;
}}

/* ============ 21. Tooltip / Popover (V3.0) ============ */
.stTooltip {{
    background: {BG_TERTIARY} !important;
    color: {TEXT_PRIMARY} !important;
    border: 1px solid {BRAND_CYAN}30 !important;
    border-radius: 6px !important;
}}

/* ============ 22. 滚动条 (V3.0 美化) ============ */
::-webkit-scrollbar {{
    width: 10px;
    height: 10px;
}}
::-webkit-scrollbar-track {{
    background: {BG_PRIMARY};
}}
::-webkit-scrollbar-thumb {{
    background: linear-gradient(180deg, {BRAND_CYAN} 0%, {BRAND_PURPLE} 100%);
    border-radius: 5px;
}}
::-webkit-scrollbar-thumb:hover {{
    background: linear-gradient(180deg, {BRAND_PURPLE} 0%, {BRAND_CYAN} 100%);
}}

/* ============ 23. 隐藏 Streamlit 品牌/footer ============ */
footer, footer * {{
    visibility: hidden !important;
    height: 0 !important;
}}
#MainMenu {{
    visibility: hidden;
}}
.stDeployButton {{
    display: none !important;
}}
header[data-testid="stHeader"] {{
    background: transparent;
}}

/* ============ 24. 隐藏默认导航 ============ */
[data-testid="stSidebarNav"] {{
    display: none !important;
}}

/* ============ 24. 容器 / 卡片通用 (V3.0) ============ */
.element-container div[data-testid="stVerticalBlock"] {{
    gap: 8px !important;
}}
/* 通用卡片容器样式 — 用于自定义 HTML 卡片 */
.qi-card {{
    background: {BG_CARD} !important;
    border: 1px solid rgba(0,212,255,0.2) !important;
    border-radius: 16px !important;
    padding: 16px 20px !important;
    transition: all 0.2s ease !important;
}}
.qi-card:hover {{
    border-color: rgba(0,212,255,0.5) !important;
    box-shadow: 0 4px 16px rgba(0,212,255,0.1) !important;
}}

/* ============ 25. 响应式布局 (V3.10) ============ */
/* Metric 卡片自适应: 小屏幕下自动换行 */
[data-testid="stMetric"] {{
    min-width: 0 !important;
    flex-shrink: 1 !important;
}}
[data-testid="stMetricValue"] {{
    font-size: clamp(16px, 2.5vw, 24px) !important;
    word-break: break-word !important;
    overflow-wrap: break-word !important;
}}
[data-testid="stMetricLabel"] {{
    font-size: clamp(11px, 1.5vw, 14px) !important;
    white-space: normal !important;
    overflow-wrap: break-word !important;
}}
/* 列容器自适应: 防止内容溢出 */
div[data-testid="stHorizontalBlock"] > div {{
    min-width: 0 !important;
    overflow: hidden !important;
}}
/* 文字自适应换行 */
.stMarkdown, .stText {{
    word-break: break-word !important;
    overflow-wrap: break-word !important;
}}
/* 表格自适应 */
.stDataFrame, .stTable {{
    overflow-x: auto !important;
}}
/* 自定义 HTML 卡片自适应 */
.qi-card {{
    max-width: 100% !important;
    overflow: hidden !important;
    box-sizing: border-box !important;
}}
/* 侧边栏自适应 */
[data-testid="stSidebar"] {{
    min-width: 200px !important;
    max-width: 320px !important;
}}
/* Tab 标签自适应 */
[data-testid="stTabs"] button {{
    font-size: clamp(12px, 1.5vw, 14px) !important;
    white-space: nowrap !important;
    padding: 8px 12px !important;
}}
/* 按钮自适应 */
.stButton > button {{
    white-space: nowrap !important;
    min-width: fit-content !important;
}}
/* 输入框自适应 */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea {{
    font-size: clamp(13px, 1.5vw, 15px) !important;
}}

/* ============ 26. 响应式断点 (Mobile / Tablet / Desktop) ============ */
/* Charts: always fill container width */
.stPlotlyChart, [data-testid="stPlotlyChart"],
.stPyplotChart, .stAltairChart, .stVegaLiteChart,
.js-plotly-plot, .plotly, .plot-container {{
    width: 100% !important;
    max-width: 100% !important;
    box-sizing: border-box !important;
}}
.js-plotly-plot .main-svg {{
    max-width: 100% !important;
}}

/* Tables: horizontal scroll on narrow viewports */
[data-testid="stDataFrame"] > div,
[data-testid="stDataFrame"] [data-testid="stDataFrameResizable"],
.stTable > div,
.stDataFrame {{
    overflow-x: auto !important;
    -webkit-overflow-scrolling: touch !important;
    max-width: 100% !important;
}}

/* Homepage feature cards */
.feature-card {{
    max-width: 100% !important;
    box-sizing: border-box !important;
}}

/* Tablet: 768px – 1024px */
@media (min-width: 768px) and (max-width: 1024px) {{
    section.main > div {{
        padding-top: 1.5rem !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
    }}
    .block-container {{
        padding-left: 1rem !important;
        padding-right: 1rem !important;
    }}
    h1 {{ font-size: 24px !important; }}
    h2 {{ font-size: 20px !important; }}
    h3 {{ font-size: 16px !important; }}

    /* Multi-column rows wrap to 2-up grid */
    div[data-testid="stHorizontalBlock"] {{
        flex-wrap: wrap !important;
        gap: 0.5rem !important;
    }}
    div[data-testid="stHorizontalBlock"] > div {{
        flex: 1 1 calc(50% - 6px) !important;
        min-width: calc(50% - 6px) !important;
    }}

    .qi-hero {{
        padding: 28px 20px !important;
    }}
    .qi-hero h1 {{
        font-size: 2rem !important;
    }}
    .qi-hero .qi-hero-emoji {{
        font-size: 2rem !important;
    }}

    .qi-sidebar-brand .qi-brand-title-main {{
        font-size: 1.25rem !important;
    }}
    .qi-sidebar-brand .qi-brand-title-pro {{
        font-size: 0.82rem !important;
    }}

    [data-testid="stSidebar"] {{
        min-width: 220px !important;
        max-width: 280px !important;
    }}
}}

/* Mobile: < 768px */
@media (max-width: 767px) {{
    section.main > div {{
        padding-top: 1rem !important;
        padding-left: 0.65rem !important;
        padding-right: 0.65rem !important;
    }}
    .block-container {{
        padding-left: 0.75rem !important;
        padding-right: 0.75rem !important;
        max-width: 100% !important;
    }}
    h1 {{
        font-size: 20px !important;
        padding-left: 10px !important;
    }}
    h2 {{ font-size: 17px !important; }}
    h3 {{ font-size: 15px !important; }}
    p, li, span {{ font-size: 13px !important; }}

    /* Stack st.columns vertically */
    div[data-testid="stHorizontalBlock"] {{
        flex-direction: column !important;
        flex-wrap: nowrap !important;
        gap: 0.5rem !important;
    }}
    div[data-testid="stHorizontalBlock"] > div {{
        width: 100% !important;
        flex: 1 1 auto !important;
        min-width: 0 !important;
    }}

    [data-testid="stMetricValue"] {{
        font-size: 18px !important;
    }}
    [data-testid="stMetricLabel"] {{
        font-size: 12px !important;
    }}

    .stButton > button {{
        white-space: normal !important;
        width: 100% !important;
        line-height: 1.35 !important;
        padding: 0.5rem 0.75rem !important;
    }}

    [data-testid="stTabs"] [data-baseweb="tab-list"] {{
        flex-wrap: wrap !important;
        gap: 4px !important;
    }}
    [data-testid="stTabs"] button {{
        white-space: normal !important;
        flex: 1 1 auto !important;
        min-height: 2.5rem !important;
    }}

    .qi-sidebar-brand {{
        padding: 8px 8px !important;
        margin-bottom: 8px !important;
    }}
    .qi-sidebar-brand .qi-brand-title-main {{
        font-size: 1.15rem !important;
    }}
    .qi-sidebar-brand .qi-brand-title-pro {{
        font-size: 0.78rem !important;
    }}
    .qi-sidebar-brand .qi-brand-subtitle {{
        font-size: 0.68rem !important;
    }}
    .qi-sidebar-brand .qi-brand-project-id {{
        font-size: 0.6rem !important;
        word-break: break-all !important;
    }}

    .qi-hero {{
        padding: 20px 16px !important;
        margin-bottom: 16px !important;
    }}
    .qi-hero .qi-hero-title-row {{
        flex-wrap: wrap !important;
        gap: 8px !important;
    }}
    .qi-hero h1 {{
        font-size: 1.65rem !important;
    }}
    .qi-hero .qi-hero-emoji {{
        font-size: 1.75rem !important;
    }}
    .qi-hero .qi-hero-stats {{
        flex-direction: column !important;
        gap: 10px !important;
    }}
    .qi-hero p {{
        font-size: 0.9rem !important;
    }}

    .feature-card {{
        padding: 16px !important;
        margin-bottom: 8px !important;
    }}

    [data-testid="stSidebar"] {{
        min-width: unset !important;
        max-width: min(300px, 88vw) !important;
    }}
    [data-testid="stSidebar"] .stRadio > label {{
        font-size: 14px !important;
        padding: 10px 12px !important;
    }}
    [data-testid="stSidebar"] .stRadio > label:hover {{
        transform: none !important;
    }}

    /* Plotly modebar: compact on touch */
    .js-plotly-plot .plotly .modebar {{
        top: 0 !important;
        right: 0 !important;
    }}
}}

/* Desktop: > 1024px — preserve layout, ensure charts scale */
@media (min-width: 1025px) {{
    div[data-testid="stHorizontalBlock"] > div {{
        min-width: 0 !important;
    }}
}}
</style>
"""
    st.markdown(css, unsafe_allow_html=True)


# ============ 通用 UI 组件 ============
def render_page_header(title: str, subtitle: str = "", icon: str = "📊"):
    """渲染页面头部 (V3.0 增强版)"""
    st.markdown(f"""
<div style="
    background: linear-gradient(135deg, rgba(0,212,255,0.1) 0%, rgba(123,97,255,0.1) 100%);
    border-left: 4px solid {BRAND_CYAN};
    border-radius: 16px;
    padding: 20px 24px;
    margin-bottom: 20px;
    box-shadow: 0 4px 16px rgba(0,0,0,0.3);
    border: 1px solid rgba(0,212,255,0.2);
">
    <h1 style="margin:0; padding:0; font-size:28px; border:none;">{icon} {title}</h1>
    {f'<p style="color:#C8D0E0; font-size:15px; margin:8px 0 0 0; font-weight:500;">{subtitle}</p>' if subtitle else ''}
</div>
""", unsafe_allow_html=True)


def render_metric_card(label: str, value: str, delta: str = "", icon: str = "📈", color: str = "cyan"):
    """渲染指标卡 (V3.0 增强 — 统一卡片样式)"""
    color_map = {
        "cyan": BRAND_CYAN,
        "gold": BRAND_GOLD,
        "green": BRAND_GREEN,
        "red": BRAND_RED,
        "purple": BRAND_PURPLE,
        "orange": BRAND_ORANGE,
    }
    c = color_map.get(color, BRAND_CYAN)
    delta_color = BRAND_GREEN if not delta.startswith("-") else BRAND_RED
    delta_html = f'<span style="color:{delta_color}; font-size:13px; font-weight:700;">{delta}</span>' if delta else ""
    st.markdown(f"""
<div class="qi-card" style="
    background: {BG_CARD};
    border: 1px solid rgba(0,212,255,0.2);
    border-radius: 16px;
    padding: 16px 20px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    transition: all 0.2s ease;
">
    <div style="color:{TEXT_MUTED}; font-size:13px; font-weight:600; margin-bottom:6px;">{icon} {label}</div>
    <div style="color:{c}; font-size:26px; font-weight:800; line-height:1.2;">{value}</div>
    <div style="margin-top:6px;">{delta_html}</div>
</div>
""", unsafe_allow_html=True)


def render_info_box(content: str, kind: str = "info"):
    """渲染信息框 (V3.0 增强)"""
    color_map = {
        "info": BRAND_CYAN,
        "success": BRAND_GREEN,
        "warning": BRAND_GOLD,
        "error": BRAND_RED,
        "tip": BRAND_PURPLE,
    }
    icon_map = {
        "info": "💡",
        "success": "✅",
        "warning": "⚠️",
        "error": "❌",
        "tip": "🎯",
    }
    c = color_map.get(kind, BRAND_CYAN)
    icon = icon_map.get(kind, "💡")
    st.markdown(f"""
<div style="
    background: {BG_SECONDARY};
    border-left: 4px solid {c};
    border-radius: 8px;
    padding: 14px 18px;
    margin: 12px 0;
    color: {TEXT_PRIMARY};
    font-size: 14px;
    line-height: 1.7;
">
    {icon} <strong style="color:{c};">{content}</strong>
</div>
""", unsafe_allow_html=True)


def render_section_title(title: str, icon: str = "🔹"):
    """渲染区块标题 (V3.0 增强 — 金色左边框)"""
    st.markdown(f"""
<div style="
    display: flex;
    align-items: center;
    margin: 24px 0 12px 0;
    padding-bottom: 8px;
    border-bottom: 2px solid {BRAND_CYAN}30;
    border-left: 3px solid {BRAND_GOLD};
    padding-left: 12px;
">
    <span style="font-size: 22px; margin-right: 8px;">{icon}</span>
    <h2 style="margin: 0; padding: 0; color: {TEXT_PRIMARY}; font-size: 22px; font-weight: 700; border:none;">{title}</h2>
</div>
""", unsafe_allow_html=True)


def render_loading_state(text: str = "加载中..."):
    """渲染加载状态"""
    return st.spinner(f"⏳ {text}")


def render_empty_state(title: str, hint: str = "", icon: str = "📭"):
    """渲染空状态 (V3.0 增强)"""
    st.markdown(f"""
<div style="
    background: {BG_SECONDARY};
    border: 1px dashed {BRAND_CYAN}40;
    border-radius: 16px;
    padding: 40px 20px;
    text-align: center;
    margin: 20px 0;
">
    <div style="font-size: 48px; margin-bottom: 12px;">{icon}</div>
    <div style="color: {TEXT_SECONDARY}; font-size: 16px; font-weight: 600; margin-bottom: 8px;">{title}</div>
    {f'<div style="color: {TEXT_MUTED}; font-size: 12px;">{hint}</div>' if hint else ''}
</div>
""", unsafe_allow_html=True)


def render_progress_card(title: str, progress: float, status: str = "进行中"):
    """渲染进度卡 (V3.0 增强)"""
    pct = int(progress * 100)
    st.markdown(f"""
<div style="
    background: {BG_CARD};
    border: 1px solid rgba(0,212,255,0.2);
    border-radius: 16px;
    padding: 16px 20px;
    margin: 12px 0;
">
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
        <span style="color: {TEXT_PRIMARY}; font-size: 14px; font-weight: 600;">{title}</span>
        <span style="color: {BRAND_CYAN}; font-size: 13px; font-weight: 700;">{pct}%</span>
    </div>
    <div style="
        background: {BG_PRIMARY};
        border-radius: 6px;
        height: 8px;
        overflow: hidden;
    ">
        <div style="
            background: linear-gradient(90deg, {BRAND_CYAN} 0%, {BRAND_PURPLE} 100%);
            height: 100%;
            width: {pct}%;
            transition: width 0.5s ease;
        "></div>
    </div>
    <div style="color: {TEXT_MUTED}; font-size: 12px; margin-top: 6px;">{status}</div>
</div>
""", unsafe_allow_html=True)


# ============ 兼容旧接口 (app.py 调用) ============
def apply_theme():
    """应用主题 — 注入自定义 CSS (兼容旧接口)"""
    inject_custom_css()


def render_theme_toggle():
    """渲染主题切换 — V3.0 统一深色主题，保留切换入口 (兼容旧接口)"""
    st.sidebar.markdown(
        f'<div style="color:{TEXT_MUTED}; font-size:11px; text-align:center;">'
        f'🎨 深色主题 V3.0</div>',
        unsafe_allow_html=True
    )
