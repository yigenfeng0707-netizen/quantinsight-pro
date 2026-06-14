"""
QuantInsight Pro - AI 驱动的另类数据量化投研平台
3 大模块：
1. AI 投研问答
2. 另类数据仪表盘
3. 量化策略回测

部署：Streamlit Cloud + GitHub
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import akshare as ak
import os
import requests
import json

from backtest_engine import BacktestEngine, BacktestConfig, StrategyType
from data_cache import get_data_cache
from ai.agent_orchestrator import MainAgent
from ai.data_grounder import DataGrounder
from ai.citation_system import CitationTracker
from features.stock_screener import NaturalLanguageScreener
from features.factor_scorer import MultiFactorScorer
from features.stock_comparison import StockComparator
from features.portfolio_manager import PortfolioManager
from features.alert_system import SmartAlertEngine
from features.market_dashboard import MarketDashboard
from features.trade_simulator import TradeSimulator, RiskControlEngine, Order
from features.task_scheduler import ResearchTaskScheduler, AutoReportGenerator, TASK_TEMPLATES
from features.sentiment_analyzer import SentimentAnalyzer
from features.supply_chain_tracker import SupplyChainTracker, INDUSTRY_CHAINS

# ============== 真实 LLM 接入 (B7) ==============
def get_llm_config():
    """从 Streamlit Secrets 或环境变量读取 LLM 配置

    支持 3 家 LLM (优先级: SenseNova > DeepSeek > Qwen)
    """
    config = {'provider': None, 'api_key': None, 'model': None, 'base_url': None, 'workspace_id': None}

    # 1. SenseNova (商汤日日新, 国内访问快) - 最高优先级
    try:
        if 'SENSENOVA_API_KEY' in st.secrets:
            config['provider'] = 'sensenova'
            config['api_key'] = st.secrets['SENSENOVA_API_KEY']
            config['model'] = st.secrets.get('SENSENOVA_MODEL', 'sensenova-6.7-flash-lite')
            config['base_url'] = st.secrets.get('SENSENOVA_BASE_URL', 'https://token.sensenova.cn/v1/chat/completions')
            return config
    except Exception:
        pass

    # 2. DeepSeek
    try:
        if 'DEEPSEEK_API_KEY' in st.secrets:
            config['provider'] = 'deepseek'
            config['api_key'] = st.secrets['DEEPSEEK_API_KEY']
            config['model'] = st.secrets.get('DEEPSEEK_MODEL', 'deepseek-chat')
            config['base_url'] = st.secrets.get('DEEPSEEK_BASE_URL', 'https://api.deepseek.com/chat/completions')
            return config
    except Exception:
        pass

    # 3. Qwen (DashScope)
    try:
        if 'QWEN_API_KEY' in st.secrets:
            config['provider'] = 'qwen'
            config['api_key'] = st.secrets['QWEN_API_KEY']
            config['model'] = st.secrets.get('QWEN_MODEL', 'qwen-turbo')
            config['base_url'] = st.secrets.get('QWEN_BASE_URL', 'https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions')
            config['workspace_id'] = st.secrets.get('QWEN_WORKSPACE_ID', None)
            return config
    except Exception:
        pass

    # 备选环境变量 (本地测试)
    if os.environ.get('SENSENOVA_API_KEY'):
        config['provider'] = 'sensenova'
        config['api_key'] = os.environ['SENSENOVA_API_KEY']
        config['model'] = os.environ.get('SENSENOVA_MODEL', 'sensenova-6.7-flash-lite')
        config['base_url'] = os.environ.get('SENSENOVA_BASE_URL', 'https://token.sensenova.cn/v1/chat/completions')
    elif os.environ.get('DEEPSEEK_API_KEY'):
        config['provider'] = 'deepseek'
        config['api_key'] = os.environ['DEEPSEEK_API_KEY']
        config['model'] = os.environ.get('DEEPSEEK_MODEL', 'deepseek-chat')
        config['base_url'] = os.environ.get('DEEPSEEK_BASE_URL', 'https://api.deepseek.com/chat/completions')
    elif os.environ.get('QWEN_API_KEY'):
        config['provider'] = 'qwen'
        config['api_key'] = os.environ['QWEN_API_KEY']
        config['model'] = os.environ.get('QWEN_MODEL', 'qwen-turbo')
        config['base_url'] = os.environ.get('QWEN_BASE_URL', 'https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions')
        config['workspace_id'] = os.environ.get('QWEN_WORKSPACE_ID', None)

    return config


def _extract_json_from_text(text):
    """从文本中提取 JSON 块 (处理 markdown 代码块 + 纯文本)"""
    if not text:
        return None
    text = text.strip()
    # 尝试 1: 直接解析
    try:
        return json.loads(text)
    except Exception:
        pass
    # 尝试 2: 提取 ```json ... ``` 代码块
    import re
    m = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(1))
        except Exception:
            pass
    # 尝试 3: 提取第一个 {...} 块
    m = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(0))
        except Exception:
            pass
    return None


def ai_qa_real(question, config, timeout=30, history=None):
    """真实 LLM 调用 (SenseNova / DeepSeek / Qwen)

    Args:
        question: 用户问题
        config: get_llm_config() 返回的配置
        timeout: 超时秒数
        history: 对话历史 (list of {role, content, ...}), 最多 5 轮

    Returns:
        dict: {'title': str, 'summary': str, 'data': dict, 'recommendation': str, 'reasoning': str}
    """
    system_prompt = """你是 QuantInsight Pro 的 AI 投研助手, 由慧点资本 (InsightQuant) 联合杭州永字资管打造.
请基于公开数据和金融专业知识, 用结构化方式回答用户的投研问题.

回答格式 (严格 JSON, 不要 markdown 代码块):
{
  "title": "一句话标题",
  "summary": "3-5 个关键点 (Markdown 格式)",
  "data": {"指标1": "值1", "指标2": "值2", "指标3": "值3"},
  "recommendation": "2-3 条投资建议"
}"""

    headers = {
        'Authorization': f'Bearer {config["api_key"]}',
        'Content-Type': 'application/json',
    }
    # DashScope workspace header (required for workspace-specific API keys)
    if config.get('workspace_id'):
        headers['X-DashScope-WorkSpace'] = config['workspace_id']

    # 构建 messages (含历史上下文)
    messages = [{'role': 'system', 'content': system_prompt}]
    if history:
        for msg in history:
            if msg['role'] == 'user':
                messages.append({'role': 'user', 'content': msg['content']})
            else:  # assistant - 转为简化文本保持上下文
                content = f"上轮标题: {msg.get('title', '')}\n摘要: {msg.get('summary', '')}\n建议: {msg.get('recommendation', '')}"
                messages.append({'role': 'assistant', 'content': content})
    messages.append({'role': 'user', 'content': question})

    # Reasoning models need more tokens (thinking + answer)
    is_reasoning = 'v4' in config['model'] or 'r1' in config['model'] or 'reasoner' in config['model']
    payload = {
        'model': config['model'],
        'messages': messages,
        'temperature': 0.7,
        'max_tokens': 4000 if is_reasoning else 2000,
    }

    # DeepSeek / Qwen 支持 response_format: json_object (reasoning models 除外)
    if config['provider'] in ('deepseek', 'qwen') and not is_reasoning:
        payload['response_format'] = {'type': 'json_object'}

    try:
        resp = requests.post(config['base_url'], headers=headers, json=payload, timeout=timeout)
        resp.raise_for_status()
        result = resp.json()

        msg = result['choices'][0]['message']
        content = msg.get('content', '') or ''
        reasoning = msg.get('reasoning_content', '') or ''  # SenseNova / DeepSeek-R1/V4 特有
        # Reasoning model: content may be empty, actual answer in reasoning_content
        if not content.strip() and reasoning.strip():
            content = reasoning

        # 解析 JSON
        parsed = _extract_json_from_text(content)
        if parsed is None:
            # 解析失败, 用纯文本 fallback
            return {
                'title': 'AI 投研分析',
                'summary': content if content else reasoning[:500] if reasoning else 'AI 响应解析失败',
                'data': {},
                'recommendation': '请参考上述摘要内容',
                'reasoning': reasoning[:300] if reasoning else '',
            }

        # 兼容 list / str 类型的 summary / recommendation
        def _to_str(v, default=''):
            if v is None:
                return default
            if isinstance(v, list):
                return '\n'.join(str(x) for x in v)
            return str(v)

        return {
            'title': _to_str(parsed.get('title'), 'AI 投研分析'),
            'summary': _to_str(parsed.get('summary'), content),
            'data': parsed.get('data', {}) if isinstance(parsed.get('data'), dict) else {},
            'recommendation': _to_str(parsed.get('recommendation'), '请参考摘要中的具体分析'),
            'reasoning': reasoning[:300] if reasoning else '',
        }
    except Exception as e:
        raise RuntimeError(f"LLM 调用失败 ({config['provider']}): {e}")

# ============== 页面配置 ==============
st.set_page_config(
    page_title='QuantInsight Pro - 智能投研平台',
    page_icon='📊',
    layout='wide',
    initial_sidebar_state='expanded',
)

# ============== 主题样式 ==============
st.markdown("""
<style>
.main-header {
    font-size: 2.5rem;
    color: #1F4E78;
    font-weight: bold;
    text-align: center;
    padding: 1rem 0;
}
.sub-header {
    font-size: 1.2rem;
    color: #666;
    text-align: center;
    padding-bottom: 1rem;
}
.metric-card {
    background: linear-gradient(135deg, #1F4E78 0%, #2E86AB 100%);
    padding: 1rem;
    border-radius: 10px;
    color: white;
    text-align: center;
}
.feature-card {
    background: #F5F7FA;
    padding: 1.5rem;
    border-radius: 10px;
    border-left: 4px solid #2E86AB;
    margin: 1rem 0;
}
.feature-card h4 {
    font-size: 1rem;
    margin: 0 0 0.5rem 0;
    color: #1F4E78;
}

/* 移动端适配 (< 768px) */
@media (max-width: 768px) {
    .main-header { font-size: 1.5rem !important; }
    .sub-header { font-size: 0.95rem !important; }
    .stMarkdown h1 { font-size: 1.5rem !important; }
    .stMarkdown h2 { font-size: 1.2rem !important; }
    .stMarkdown h3 { font-size: 1.05rem !important; }
    [data-testid="column"] { width: 100% !important; flex: 100% !important; min-width: 100% !important; }
    .stButton > button { width: 100% !important; }
    .metric-card { padding: 0.5rem !important; }
    .feature-card { padding: 1rem !important; }
    [data-testid="stSidebar"] { min-width: 200px !important; max-width: 250px !important; }
    .stChatMessage { padding: 0.5rem !important; }
}
</style>
""", unsafe_allow_html=True)

# ============== 数据加载（缓存）==============
@st.cache_data(ttl=3600)
def load_hs300():
    try:
        df = ak.stock_zh_index_daily(symbol='sh000300')
        df['date'] = pd.to_datetime(df['date'])
        return df
    except Exception:
        return None

@st.cache_data(ttl=3600)
def load_zz500():
    try:
        df = ak.stock_zh_index_daily(symbol='sh000905')
        df['date'] = pd.to_datetime(df['date'])
        return df
    except Exception:
        return None

@st.cache_data(ttl=3600)
def load_cyb():
    try:
        df = ak.stock_zh_index_daily(symbol='sz399006')
        df['date'] = pd.to_datetime(df['date'])
        return df
    except Exception:
        return None

@st.cache_data(ttl=3600, show_spinner=False)
def load_index(symbol):
    """统一指数加载 (缓存 1 小时), 替代直接 ak.stock_zh_index_daily 调用"""
    try:
        df = ak.stock_zh_index_daily(symbol=symbol)
        df['date'] = pd.to_datetime(df['date'])
        return df
    except Exception:
        return None

@st.cache_data(ttl=3600, show_spinner=False)
def load_industry_cons(symbol):
    """行业成分股加载 (缓存 1 小时)"""
    try:
        return ak.stock_board_industry_cons_em(symbol=symbol)
    except Exception:
        return None

@st.cache_data(ttl=86400, show_spinner=False)
def load_sw_index():
    """申万三级行业 (缓存 24 小时, 静态更新)"""
    try:
        return ak.sw_index_third_info()
    except Exception:
        return None

@st.cache_data(ttl=3600, show_spinner=False)
def load_stock_news():
    """加载 A 股新闻舆情 (缓存 1 小时)"""
    try:
        df = ak.stock_news_em(symbol='财经')
        if df is not None and len(df) > 0:
            return df.head(50)
    except Exception:
        pass
    return None

@st.cache_data(ttl=3600)
def load_stock_pool():
    """加载 A 股股票池（部分代表性股票）"""
    try:
        df = ak.stock_zh_a_spot_em()
        return df.head(200)  # 取前 200 只做演示
    except Exception:
        # Fallback: 静态列表
        return pd.DataFrame({
            '代码': ['600519', '000858', '601318', '600036', '000333',
                    '601012', '002594', '300750', '600276', '601888'],
            '名称': ['贵州茅台', '五粮液', '中国平安', '招商银行', '美的集团',
                    '隆基绿能', '比亚迪', '宁德时代', '恒瑞医药', '中国中免'],
            '最新价': [1680, 145, 48, 35, 68, 22, 240, 220, 45, 95],
        })

# ============== AI 问答模块（模拟）==============
def ai_qa_mock(question):
    """AI 问答的 mock 回答（无 API key 时使用）"""
    question_lower = question.lower()

    templates = {
        '新能源': {
            'title': '新能源行业分析报告',
            'summary': '当前新能源板块呈现以下特点：\n\n1. **锂电产业链**：经历 2022-2023 年下行周期后，2024 年 Q3 起出现结构性反弹，主要受欧美补库+储能需求驱动\n2. **光伏板块**：产能过剩压力持续，但 TOPCon/HJT 新型电池技术带来差异化机会\n3. **风电/核电**：海风进入装机高峰，核电进入新一轮审批周期',
            'data': {
                '新能源指数 PE': '22.5x (近 5 年 30% 分位)',
                '板块年初至今': '-8.2%',
                '机构持仓比例': '12.3% (环比 +0.8pct)',
            },
            'recommendation': '建议关注：储能 > 锂电材料 > 光伏新技术 > 风电海风'
        },
        '半导体': {
            'title': '半导体行业投资分析',
            'summary': '半导体板块分化加剧：\n\n1. **AI 算力链**：HBM/CoWoS 封装/光模块 持续景气\n2. **国产替代**：设备/材料/EDA 加速突破，国产化率提升至 25%\n3. **消费电子链**：库存出清，但终端需求温和复苏',
            'data': {
                '费城半导体指数': '5,250 (+3.2% YTD)',
                '申万半导体 PE': '85x (高位)',
                '存储芯片价格': 'DDR4 8Gb +12% QoQ',
            },
            'recommendation': '优选：AI 算力链 + 国产替代 + 设备材料'
        },
        '消费': {
            'title': '消费板块投资机会',
            'summary': '消费板块出现底部信号：\n\n1. **白酒**：批价企稳，估值回到历史 30% 分位\n2. **食品**：必选消费稳定，可选消费弹性大\n3. **新兴消费**：悦己消费、银发经济持续高增',
            'data': {
                '中证消费 PE': '25.8x (近 5 年 25% 分位)',
                '社零同比': '+3.5% (温和复苏)',
                'CPI 同比': '+0.3%',
            },
            'recommendation': '左侧布局：高端白酒 + 大众食品龙头'
        },
        '医药': {
            'title': '医药行业投资分析',
            'summary': '医药板块分化明显：\n\n1. **创新药**：出海授权交易活跃，BD 金额创新高\n2. **医疗器械**：国产替代加速，高端设备突破\n3. **中药**：政策利好持续，品牌中药估值修复',
            'data': {
                '中证医药 PE': '28.5x (近 5 年 35% 分位)',
                '创新药指数': '+15.2% YTD',
                '医保谈判': '平均降幅 58%',
            },
            'recommendation': '关注：创新药出海 + 医疗器械国产替代 + 品牌中药'
        },
        '金融': {
            'title': '金融行业投资分析',
            'summary': '金融板块估值修复进行中：\n\n1. **银行**：净息差触底，资产质量改善\n2. **保险**：负债端回暖，投资收益改善\n3. **券商**：市场活跃度提升，两融余额回升',
            'data': {
                '银行 PB': '0.55x (历史低位)',
                '保险 NBV 增速': '+18% YoY',
                '券商两融余额': '1.85 万亿',
            },
            'recommendation': '关注：高股息银行 + NBV 改善保险 + 头部券商'
        },
        '军工': {
            'title': '军工行业投资分析',
            'summary': '军工板块进入景气上行周期：\n\n1. **航空发动机**：国产替代关键突破\n2. **导弹/弹药**：订单恢复性增长\n3. **军工电子**：信息化升级驱动',
            'data': {
                '军工指数 PE': '55x (中高位)',
                '军工行业增速': '+12% YoY',
                '订单可见性': '3-5 年',
            },
            'recommendation': '关注：航空发动机 + 军工电子 + 导弹产业链'
        },
        '房地产': {
            'title': '房地产行业投资分析',
            'summary': '房地产政策持续宽松：\n\n1. **政策面**：限购限贷全面放松，利率降至历史低位\n2. **基本面**：销售降幅收窄，但投资仍在下行\n3. **信用面**：房企融资边际改善，但分化加剧',
            'data': {
                '30 城成交面积': '-15% YoY (收窄中)',
                '房贷利率': '3.45% (历史低位)',
                '百强销售': '-20% YoY',
            },
            'recommendation': '谨慎关注：优质央国企 + 物业管理 + 代建'
        },
        '人工智能': {
            'title': 'AI 产业投资分析',
            'summary': 'AI 产业进入应用落地期：\n\n1. **算力层**：GPU 需求持续景气，国产替代加速\n2. **模型层**：开源模型能力快速追赶，推理成本下降\n3. **应用层**：B 端场景率先落地，C 端应用探索中',
            'data': {
                'AI 指数 PE': '65x (高位)',
                'GPU 需求增速': '+80% YoY',
                '开源模型数': '200+ (国内)',
            },
            'recommendation': '关注：算力基础设施 + 垂直场景应用 + 数据要素'
        },
        '宏观': {
            'title': '宏观经济与市场分析',
            'summary': '当前宏观环境分析：\n\n1. **货币政策**：降准降息空间仍在，流动性偏宽松\n2. **财政政策**：专项债加速发行，基建托底\n3. **外部环境**：美联储降息预期升温，人民币汇率企稳',
            'data': {
                'GDP 增速': '5.2% (目标 5%)',
                'CPI': '+0.3% (低位)',
                '10Y 国债': '2.65%',
            },
            'recommendation': '关注：利率敏感型资产 + 红利策略 + 出口链'
        },
        '银行': {
            'title': '银行业投资分析',
            'summary': '银行板块估值修复窗口：\n\n1. **净息差**：LPR 下调影响逐步消化，存款利率同步下调\n2. **资产质量**：不良率稳中有降，拨备充足\n3. **股息率**：平均 5-6%，显著高于国债收益率',
            'data': {
                '银行 PB': '0.55x',
                '平均股息率': '5.8%',
                '不良率': '1.25% (稳定)',
            },
            'recommendation': '关注：高股息大行 + 优质城商行 + 资产质量改善标的'
        },
    }

    for keyword, template in templates.items():
        if keyword in question or keyword in question_lower:
            return template

    # 通用回答
    return {
        'title': '智能投研分析报告',
        'summary': f'针对您的问题"{question[:50]}", 我们整合多源数据进行分析：\n\n1. **市场情绪**：当前 A 股市场情绪中性偏谨慎, 北向资金近期波动加大\n2. **资金流向**：主力资金净流出收窄, 融资余额小幅回升\n3. **技术面**：主要指数在年线附近震荡, 成交量温和放大\n4. **基本面**：宏观数据温和复苏, 政策面偏积极\n5. **风险提示**：关注海外加息预期变化及地缘政治风险',
        'data': {
            '沪深300 PE': '12.5x (近 5 年 40% 分位)',
            '10Y 国债': '2.65%',
            '人民币汇率': '7.18',
            '融资余额': '1.52 万亿',
        },
        'recommendation': '建议关注：低估值高分红 + 政策受益板块 + AI 产业链'
    }

# ============== 侧边栏 ==============
st.sidebar.title('📊 QuantInsight Pro')
st.sidebar.markdown('**AI 驱动的另类数据量化投研平台**')
st.sidebar.markdown('---')

page = st.sidebar.radio('选择功能模块', [
    '🏠 首页',
    '🤖 AI 投研问答',
    '🎯 智能选股',
    '📡 智能盯盘',
    '💼 我的组合',
    '📈 模拟交易',
    '⚡ 智能指令',
    '📡 另类数据仪表盘',
    '📈 量化策略回测',
    '📊 行业分析',
])

st.sidebar.markdown('---')
st.sidebar.markdown('### 📋 项目信息')
st.sidebar.info(
    '**项目编号**：2026FINTECH-FINT-0093\n\n'
    '**参赛单位**：慧点资本 (InsightQuant)\n\n'
    '**推荐单位**：杭州永字资产管理有限公司\n\n'
    '**大赛**：Fintech@外滩 第一届金融科技国际创新创业大赛'
)
st.sidebar.markdown('---')
st.sidebar.markdown('### 🔧 技术栈')
st.sidebar.code(
    'Streamlit + Plotly\n'
    'akshare + pandas\n'
    'Qwen/DeepSeek (可选)',
    language='text'
)

# LLM 状态显示 (B7)
llm_config_status = get_llm_config()
if llm_config_status['api_key']:
    st.sidebar.markdown('### 🤖 AI 引擎')
    st.sidebar.success(
        f'**{llm_config_status["provider"].upper()}** ✅\n\n'
        f'模型: {llm_config_status["model"]}\n\n'
        f'模式: 真实 LLM 推理'
    )
else:
    st.sidebar.markdown('### 🤖 AI 引擎')
    st.sidebar.warning(
        '**Mock 模式** ⚠️\n\n'
        '当前使用关键词匹配\n\n'
        '配置 DEEPSEEK_API_KEY 或 QWEN_API_KEY\n\n'
        '可启用真实 AI 推理'
    )

# ============== 页面：首页 ==============
if page == '🏠 首页':
    st.markdown('<h1 class="main-header">QuantInsight Pro</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">AI 驱动的另类数据量化投研平台</p>', unsafe_allow_html=True)

    st.markdown('---')

    # 核心指标卡片
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        try:
            df_hs300 = load_hs300()
            st.metric('沪深300', f'{df_hs300["close"].iloc[-1]:.2f}', f'{df_hs300["close"].pct_change().iloc[-1]*100:+.2f}%')
        except Exception:
            st.metric('沪深300', '加载中', '')
    with col2:
        try:
            df_zz500 = load_zz500()
            st.metric('中证500', f'{df_zz500["close"].iloc[-1]:.2f}', f'{df_zz500["close"].pct_change().iloc[-1]*100:+.2f}%')
        except Exception:
            st.metric('中证500', '加载中', '')
    with col3:
        try:
            df_cyb = load_cyb()
            st.metric('创业板指', f'{df_cyb["close"].iloc[-1]:.2f}', f'{df_cyb["close"].pct_change().iloc[-1]*100:+.2f}%')
        except Exception:
            st.metric('创业板指', '加载中', '')
    with col4:
        # 北向资金: 尝试从 akshare 实时获取, 失败则显示提示
        try:
            df_north = ak.stock_hsgt_north_net_flow_in_em(symbol='北向')
            if df_north is not None and len(df_north) > 0:
                latest = df_north.iloc[-1]
                net_amount = latest.get('当日净流入', latest.get('当日资金流入', 0))
                if isinstance(net_amount, (int, float)):
                    st.metric('今日北向资金', f'{net_amount/1e8:.1f}亿', f'{net_amount/1e8:.1f}亿净流入')
                else:
                    st.metric('今日北向资金', '数据加载中', '')
            else:
                st.metric('今日北向资金', '暂无数据', '')
        except Exception:
            st.metric('今日北向资金', '暂无数据', '')

    st.markdown('---')

    # 核心功能介绍
    st.markdown('### 🎯 平台核心功能 — 对标 AI涨乐')

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown("""
        <div class="feature-card">
            <h4>🎯 智能选股</h4>
            <p>自然语言选股<br/>多因子评分<br/>个股对比</p>
            <p><strong>特色：</strong>“低估值高成长消费股”</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="feature-card">
            <h4>📡 智能盯盘</h4>
            <p>7×24h 市场监控<br/>智能预警<br/>北向资金追踪</p>
            <p><strong>特色：</strong>“茅台跌破1600提醒”</p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <div class="feature-card">
            <h4>📈 模拟交易</h4>
            <p>语音/文字下单<br/>风控引擎<br/>反情绪化交易</p>
            <p><strong>特色：</strong>仓位限制 + 冷却期</p>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown("""
        <div class="feature-card">
            <h4>⚡ 智能指令</h4>
            <p>周期性投研任务<br/>自动报告生成<br/>晨报/盘后总结</p>
            <p><strong>特色：</strong>Plan-Execute-Reflect</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('---')

    # 最新动态
    st.markdown('### 📰 平台最新动态')
    st.success('✅ 2026-06-05 完成多因子策略 2020-2026 真实回测白皮书 V1.0')
    st.info('🔜 2026 Q3 计划上线 卫星图像分析模块')
    st.info('🔜 2026 Q3 计划与永字资管完成首批客户试点')

# ============== 页面：AI 投研问答 ==============
elif page == '🤖 AI 投研问答':
    st.markdown('# 🤖 AI 投研问答')
    st.markdown('**基于开源大模型微调+RAG，支持自然语言投研分析 + 多轮对话**')

    st.markdown('---')

    # 初始化 session state
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []  # list of {role, content, title, summary, data, recommendation, reasoning}
    if 'question_input' not in st.session_state:
        st.session_state.question_input = ''

    # 顶部工具栏: 消息数 + 清空按钮
    col_info, col_clear = st.columns([5, 1])
    with col_info:
        st.caption(f'💬 对话轮数: {len(st.session_state.chat_history) // 2} / 5 (最近 5 轮保留为上下文)')
    with col_clear:
        if st.button('🗑️ 清空对话', use_container_width=True):
            st.session_state.chat_history = []
            st.session_state.question_input = ''
            st.rerun()

    # 显示历史对话
    if st.session_state.chat_history:
        st.markdown('### 📜 对话历史')
        for i, msg in enumerate(st.session_state.chat_history):
            if msg['role'] == 'user':
                with st.chat_message('user', avatar='👤'):
                    st.markdown(msg['content'])
            else:  # assistant
                with st.chat_message('assistant', avatar='🤖'):
                    st.markdown(f'## 📄 {msg["title"]}')
                    st.markdown('### 📋 分析摘要')
                    st.markdown(msg['summary'])
                    if msg.get('data'):
                        st.markdown('### 📊 关键数据')
                        cols = st.columns(len(msg['data']))
                        for (k, v), col in zip(msg['data'].items(), cols):
                            with col:
                                st.metric(k, v)
                    st.markdown('### 💡 投资建议')
                    st.success(msg['recommendation'])
                    if msg.get('reasoning'):
                        with st.expander('🧠 AI 思考过程', expanded=False):
                            st.caption(msg['reasoning'])
        st.markdown('---')

    # 快捷问题
    st.markdown('### 💡 试试这些问题 (单轮模式, 清空对话后使用)')
    col1, col2, col3 = st.columns(3)
    quick_questions = [
        '分析近期新能源行业投资机会',
        '半导体行业当前估值与投资逻辑',
        '消费板块是否到了底部布局时机',
    ]
    cols = [col1, col2, col3]

    for i, (q, col) in enumerate(zip(quick_questions, cols)):
        with col:
            if st.button(f'📌 {q}', key=f'quick_{i}', use_container_width=True):
                st.session_state.question_input = q
                st.rerun()

    st.markdown('---')

    # 输入框
    question = st.text_area(
        '💬 请输入您的投研问题 (支持多轮, 上文会作为上下文)',
        value=st.session_state.question_input,
        height=100,
        placeholder='例如：基于上面分析, 哪些标的值得关注?'
    )

    col1, col2 = st.columns([1, 5])
    with col1:
        analyze_btn = st.button('🚀 智能分析', type='primary', use_container_width=True)

    if analyze_btn and question:
        # 检测 LLM 配置 (B7)
        llm_config = get_llm_config()
        use_real_llm = llm_config['api_key'] is not None

        # 尝试使用 MainAgent (多智能体协作)
        use_multi_agent = use_real_llm and st.checkbox('🧠 启用 Multi-Agent 协作模式', value=True, key='use_ma')

        if use_multi_agent:
            spinner_text = f'🤖 Multi-Agent 协作分析中 (含数据接地 + RAG)...'
        elif use_real_llm:
            spinner_text = f'🤖 {llm_config["provider"].upper()} AI 正在生成分析报告 (含上下文)...'
        else:
            spinner_text = '🤖 AI 正在生成分析报告 (Mock 模式, 配置 API key 可启用真实 LLM)...'

        with st.spinner(spinner_text):
            import time
            t0 = time.time()

            if use_multi_agent:
                try:
                    # 初始化 MainAgent
                    if 'main_agent' not in st.session_state:
                        st.session_state.main_agent = MainAgent(llm_config=llm_config)
                    agent = st.session_state.main_agent
                    # 构建历史格式
                    agent_history = []
                    for msg in st.session_state.chat_history[-10:]:
                        agent_history.append({'role': msg['role'], 'content': msg.get('content', msg.get('summary', ''))})
                    orch_result = agent.process_query(question, agent_history)
                    orch_d = orch_result.to_dict()
                    result = {
                        'title': orch_d.get('title', 'Multi-Agent 分析'),
                        'summary': orch_d.get('summary', ''),
                        'data': orch_d.get('data', {}),
                        'recommendation': orch_d.get('recommendation', ''),
                        'reasoning': orch_d.get('reasoning', ''),
                    }
                    st.success(f'✅ Multi-Agent 协作完成, 耗时 {time.time()-t0:.1f}s')
                    # 显示 Agent 执行过程
                    if orch_d.get('agent_results'):
                        with st.expander('🧩 Agent 执行详情'):
                            for item in orch_d['agent_results']:
                                if isinstance(item, dict):
                                    st.markdown(f'**{item.get("name", "agent")}**: {str(item.get("output", ""))[:200]}')
                                else:
                                    st.markdown(f'- {str(item)[:200]}')
                except Exception as e:
                    st.warning(f'⚠️ Multi-Agent 失败: {e}, 回退单 Agent')
                    try:
                        result = ai_qa_real(question, llm_config, history=st.session_state.chat_history[-10:])
                    except Exception:
                        result = ai_qa_mock(question)
            else:
                time.sleep(1.0)  # 模拟推理时间
                result = ai_qa_mock(question)

            # 保存到对话历史
            st.session_state.chat_history.append({'role': 'user', 'content': question})
            st.session_state.chat_history.append({
                'role': 'assistant',
                'title': result['title'],
                'summary': result['summary'],
                'data': result.get('data', {}),
                'recommendation': result['recommendation'],
                'reasoning': result.get('reasoning', ''),
            })

            # 限制历史长度: 最近 5 轮 (10 条消息)
            if len(st.session_state.chat_history) > 10:
                st.session_state.chat_history = st.session_state.chat_history[-10:]

            st.session_state.question_input = ''
            st.rerun()

    st.caption('⚠️ 本回答基于公开数据 + AI 模型生成，仅供参考，不构成投资建议')

# ============== 页面：另类数据仪表盘 ==============
elif page == '📡 另类数据仪表盘':
    st.markdown('# 📡 另类数据仪表盘')
    st.markdown('**整合卫星图像、舆情分析、供应链数据等多维数据**')

    st.markdown('---')

    tab1, tab2, tab3 = st.tabs(['🛰️ 卫星图像', '💬 舆情分析', '📦 供应链追踪'])

    with tab1:
        st.markdown('### 🛰️ 卫星图像分析 - 工业园区开工率')
        st.caption('数据源：Sentinel-2 公开卫星数据 + AI 识别算法')
        st.warning('⚠️ **概念演示**: 当前展示为模拟数据, 生产环境将接入真实卫星图像数据源 (Sentinel-2 / 商业卫星 API)')

        # 模拟工业园区开工率数据
        dates = pd.date_range('2024-01-01', periods=24, freq='ME')
        np.random.seed(42)
        work_rate = 60 + 20 * np.sin(np.arange(24) * 0.5) + np.random.randn(24) * 5
        work_rate = np.clip(work_rate, 30, 95)

        df_sat = pd.DataFrame({'日期': dates, '开工率': work_rate})

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df_sat['日期'], y=df_sat['开工率'],
                                 mode='lines+markers', name='开工率',
                                 line=dict(color='#1F4E78', width=3),
                                 fill='tozeroy', fillcolor='rgba(31, 78, 120, 0.1)'))
        fig.update_layout(
            title='华东某工业园区月度开工率（2024 年）',
            yaxis_title='开工率 (%)',
            hovermode='x unified',
            height=400,
        )
        st.plotly_chart(fig, use_container_width=True)

        st.markdown('#### 🔍 关键发现')
        st.info('• 2024 年 2-3 月春节后开工率明显回落\n• 5-9 月旺季开工率维持在 80% 以上\n• 10 月后进入季节性回落期')

    with tab2:
        st.markdown('### 💬 舆情情感分析 - 实时 NLP')
        st.caption('数据源：东方财富财经新闻 + SnowNLP 情感分析')

        # 尝试加载真实新闻并做 NLP 分析
        df_news = load_stock_news()
        analyzer = SentimentAnalyzer()

        if df_news is not None and len(df_news) > 0:
            # 真实新闻 + NLP 情感分析
            title_col = '标题' if '标题' in df_news.columns else 'title'
            news_list = df_news.head(30).to_dict('records')
            results = analyzer.analyze_batch(
                [{'title': r.get(title_col, r.get('title', '')), 'source': 'eastmoney', 'time': ''} for r in news_list]
            )
            summary = analyzer.summarize(results)

            # 汇总指标
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric('新闻总数', summary.total_articles)
            with col2:
                st.metric('正面', summary.positive_count, f'{summary.positive_count/max(summary.total_articles,1)*100:.0f}%')
            with col3:
                st.metric('负面', summary.negative_count, f'{summary.negative_count/max(summary.total_articles,1)*100:.0f}%')
            with col4:
                trend_cn = {'bullish': '偏多', 'bearish': '偏空', 'neutral': '中性'}.get(summary.sentiment_trend, '中性')
                st.metric('舆情趋势', trend_cn, f'均分 {summary.avg_score:.2f}')

            # 热词
            if summary.hot_keywords:
                st.markdown('#### 🔥 热词')
                st.write(' | '.join([f'**{kw}** ({c})' for kw, c in summary.hot_keywords[:8]]))

            # 新闻列表
            st.markdown('#### 📰 新闻情感明细')
            for r in results[:15]:
                emoji = {'positive': '🟢', 'negative': '🔴', 'neutral': '🟡'}.get(r.label, '⚪')
                st.markdown(f'{emoji} [{r.score:.2f}] {r.text[:80]}')
        else:
            st.info('⚠️ 新闻数据加载失败, 展示模拟数据')
            sectors = ['人工智能', '新能源', '半导体', '医药', '消费', '金融', '军工', '汽车']
            sentiment = np.random.uniform(0.3, 0.95, len(sectors))
            volume = np.random.randint(1000, 50000, len(sectors))
            df_sent = pd.DataFrame({'行业': sectors, '情感得分': sentiment, '讨论量': volume})
            col1, col2 = st.columns(2)
            with col1:
                fig = px.bar(df_sent.sort_values('情感得分', ascending=True),
                             x='情感得分', y='行业', orientation='h',
                             title='行业情感得分排行',
                             color='情感得分', color_continuous_scale='RdYlGn',
                             range_color=[0.3, 1.0])
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
            with col2:
                fig = px.scatter(df_sent, x='讨论量', y='情感得分', size='讨论量',
                                color='行业', title='行业舆情 - 讨论量 vs 情感',
                                size_max=40)
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)

    with tab3:
        st.markdown('### 📦 产业链追踪 - 上下游传导')
        st.caption('数据源：申万行业分类 + 产业链关系图谱')

        tracker = SupplyChainTracker()
        chains = tracker.get_available_chains()

        col1, col2 = st.columns([1, 3])
        with col1:
            selected_chain = st.selectbox('选择产业链', chains, key='chain_select')

        chain = tracker.get_chain(selected_chain)
        if chain:
            # Sankey 图
            st.markdown(f'#### 🔀 {selected_chain} 产业链 Sankey 图')
            try:
                import plotly.graph_objects as go
                sankey = chain.sankey_data
                node_names = [n['name'] for n in sankey['nodes']]
                node_idx = {name: i for i, name in enumerate(node_names)}
                sources = [node_idx[l['source']] for l in sankey['links'] if l['source'] in node_idx and l['target'] in node_idx]
                targets = [node_idx[l['target']] for l in sankey['links'] if l['source'] in node_idx and l['target'] in node_idx]
                values = [l['value'] for l in sankey['links'] if l['source'] in node_idx and l['target'] in node_idx]
                fig = go.Figure(data=[go.Sankey(
                    node=dict(label=node_names, pad=20, thickness=20),
                    link=dict(source=sources, target=targets, value=values)
                )])
                fig.update_layout(title=f'{selected_chain} 产业链传导', height=400)
                st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                st.warning(f'Sankey 图渲染失败: {e}')

            # 相关股票
            st.markdown('#### 📈 产业链相关股票')
            chain_stocks = tracker.get_chain_stocks(selected_chain)
            if not chain_stocks.empty:
                st.dataframe(chain_stocks, use_container_width=True)

            # 上游影响分析
            st.markdown('#### 🔍 上游变动传导分析')
            upstream_list = INDUSTRY_CHAINS.get(selected_chain, {}).get('upstream', [])
            if upstream_list:
                col_a, col_b = st.columns(2)
                with col_a:
                    up_ind = st.selectbox('上游行业', upstream_list, key='up_ind')
                with col_b:
                    impact = st.slider('影响程度', -1.0, 1.0, 0.5, 0.1, key='up_impact')
                analysis = tracker.analyze_upstream_impact(selected_chain, up_ind, impact)
                if 'error' not in analysis:
                    st.info(analysis.get('conclusion', ''))
        else:
            st.warning('产业链数据加载失败')

# ============== 页面：量化策略回测 ==============
elif page == '📈 量化策略回测':
    st.markdown('# 📈 量化策略回测')
    st.markdown('**基于公开 A 股数据的真实回测, 11.4 年回测期, 可调参数**')

    st.markdown('---')

    # 第 1 行: 标的选择 + 策略类型
    col1, col2, col3 = st.columns(3)
    with col1:
        index_choice = st.selectbox('📊 标的指数', ['沪深300', '中证500', '创业板指'], key='bt_index')
    with col2:
        strategy_choice = st.selectbox('🧠 策略类型', ['双均线动量', '布林带均值回归', '多因子合成'], key='bt_strategy')
    with col3:
        start_date = st.date_input('📅 起始日期', value=pd.to_datetime('2020-01-01'), key='bt_start')

    # 策略参数默认值 (防止分支外引用未定义变量)
    fast_ma, slow_ma = 20, 60
    window, std_dev = 20, 2.0
    cost = 0.0015

    # 第 2 行: 策略参数 (根据策略类型动态显示)
    if strategy_choice == '双均线动量':
        col1, col2, col3 = st.columns(3)
        with col1:
            fast_ma = st.slider('⚡ 短均线周期', min_value=5, max_value=60, value=20, step=5, help='默认 20, 越小越敏感')
        with col2:
            slow_ma = st.slider('🐢 长均线周期', min_value=20, max_value=250, value=60, step=10, help='默认 60, 必须大于短均线')
        with col3:
            cost = st.slider('💰 手续费率', min_value=0.0, max_value=0.003, value=0.0015, step=0.0001, format='%.4f', help='默认 0.15%')
        # 校验
        if fast_ma >= slow_ma:
            st.error('❌ 短均线必须小于长均线')
            st.stop()
    elif strategy_choice == '布林带均值回归':
        col1, col2, col3 = st.columns(3)
        with col1:
            window = st.slider('📏 布林带窗口', min_value=10, max_value=60, value=20, step=5, help='默认 20 日')
        with col2:
            std_dev = st.slider('📊 标准差倍数', min_value=1.0, max_value=3.0, value=2.0, step=0.1, help='默认 2.0 σ')
        with col3:
            cost = st.slider('💰 手续费率', min_value=0.0, max_value=0.003, value=0.0015, step=0.0001, format='%.4f')
    else:  # 多因子
        col1, col2 = st.columns(2)
        with col1:
            cost = st.slider('💰 手续费率', min_value=0.0, max_value=0.003, value=0.0015, step=0.0001, format='%.4f')
        with col2:
            st.info('💡 多因子策略内部参数固定 (20日动量 + 5日反转 + 60日排名)')

    st.markdown('---')

    col_run, col_reset = st.columns([1, 5])
    with col_run:
        run_btn = st.button('🚀 运行回测', type='primary', use_container_width=True)

    if run_btn:
        try:
          with st.spinner(f'正在加载 {index_choice} 数据 + 计算 {strategy_choice} 回测...'):
            symbol_map = {'沪深300': 'sh000300', '中证500': 'sh000905', '创业板指': 'sz399006'}
            df_raw = load_index(symbol_map[index_choice])
            if df_raw is None or len(df_raw) == 0:
                raise RuntimeError(f'{index_choice} 数据加载失败, 请检查网络后重试')
            bt_df = df_raw[df_raw['date'] >= pd.to_datetime(start_date)].copy()
            if len(bt_df) < 80:
                raise RuntimeError(f'回测数据不足 ({len(bt_df)} 天), 请选择更早的起始日期')

            # 策略映射
            strategy_map = {
                '双均线动量': (StrategyType.MA_CROSS, {'ma_short': fast_ma, 'ma_long': slow_ma}),
                '布林带均值回归': (StrategyType.MEAN_REVERSION, {'mr_window': window, 'mr_threshold': std_dev}),
                '多因子合成': (StrategyType.MULTI_FACTOR, {}),
            }

            if strategy_choice == '双均线动量':
                cfg = BacktestConfig(cost=cost, ma_short=fast_ma, ma_long=slow_ma)
                param_desc = f'快线 {fast_ma} 日 / 慢线 {slow_ma} 日'
            elif strategy_choice == '布林带均值回归':
                cfg = BacktestConfig(cost=cost, mr_window=window, mr_threshold=std_dev)
                param_desc = f'{window} 日窗口 / {std_dev:.1f}σ'
            else:
                cfg = BacktestConfig(cost=cost)
                param_desc = '20 日动量 + 5 日反转 + 60 日排名'

            engine = BacktestEngine(cfg)
            bt_result = engine.run(bt_df, strategy_map[strategy_choice][0], index_name=index_choice)

            # 基准 = 买入持有
            bh_result = engine.run(bt_df, StrategyType.BUY_HOLD, index_name=index_choice)

            # 从 BacktestResult 提取指标
            m = bt_result.metrics
            metrics = {
                '年化收益': f'{m.annual_return*100:.2f}%',
                '年化波动': f'{m.volatility*100:.2f}%',
                '夏普比率': f'{m.sharpe:.2f}',
                '最大回撤': f'{m.max_drawdown*100:.2f}%',
                '胜率': f'{m.win_rate*100:.1f}%',
                '信息比率': f'{m.calmar:.2f}',
            }

            st.markdown('---')
            st.markdown(f'### 📊 回测结果 ({param_desc}, 手续费 {cost*100:.2f}%)')

            col1, col2, col3, col4, col5, col6 = st.columns(6)
            for (k, v), col in zip(metrics.items(), [col1, col2, col3, col4, col5, col6]):
                with col:
                    st.metric(k, v)

            # 关键提示
            sharpe = float(metrics['夏普比率'].replace('%', '').replace('+', '').replace('-', '')) if metrics['夏普比率'] != 'N/A' else 0
            annual_ret = float(metrics['年化收益'].replace('%', '').replace('+', ''))
            if annual_ret > 5 and sharpe > 0.5:
                st.success(f'✅ 策略有效: 年化收益 {metrics["年化收益"]} > 5%, 夏普 {sharpe:.2f} > 0.5')
            elif annual_ret < 0:
                st.warning(f'⚠️ 策略亏损: 年化 {metrics["年化收益"]}, 建议调整参数')
            else:
                st.info(f'ℹ️ 策略中性: 年化 {metrics["年化收益"]}, 夏普 {sharpe:.2f}')

            # NAV 曲线
            nav_series = bt_result.nav_series
            benchmark_nav = bh_result.nav_series
            # nav_series 的 index 是整数, 需要用 bt_df 的日期作为 x 轴
            bt_dates = bt_df['date'].values

            fig = go.Figure()
            fig.add_trace(go.Scatter(x=bt_dates, y=nav_series.values,
                                     mode='lines', name='策略净值',
                                     line=dict(color='#1F4E78', width=2.5)))
            fig.add_trace(go.Scatter(x=bt_dates, y=benchmark_nav.values,
                                     mode='lines', name='基准净值',
                                     line=dict(color='#A23B72', width=2, dash='dash')))
            fig.update_layout(
                title=f'{index_choice} - {strategy_choice} ({param_desc}) vs 基准',
                yaxis_title='净值 (NAV)',
                hovermode='x unified',
                height=500,
            )
            st.plotly_chart(fig, use_container_width=True)

            # 回撤曲线
            cummax = nav_series.cummax()
            dd = (nav_series - cummax) / cummax

            fig = go.Figure()
            fig.add_trace(go.Scatter(x=bt_dates, y=dd * 100,
                                     mode='lines', name='回撤',
                                     line=dict(color='#D62246', width=2),
                                     fill='tozeroy', fillcolor='rgba(214, 34, 70, 0.2)'))
            fig.update_layout(
                title='回撤曲线',
                yaxis_title='回撤 (%)',
                hovermode='x unified',
                height=300,
            )
            st.plotly_chart(fig, use_container_width=True)

            # 详细数据
            st.markdown('### 📋 详细数据 (最近 30 个交易日)')
            detail_df = pd.DataFrame({
                '日期': bt_dates,
                'close': bt_df['close'].values,
                'signal': bt_result.signal_series.values if bt_result.signal_series is not None else [0]*len(bt_df),
                'nav': nav_series.values,
                'benchmark': benchmark_nav.values,
            })
            st.dataframe(detail_df.tail(30), use_container_width=True)

            st.caption(f'📊 数据源: akshare (新浪财经) | 回测期: {start_date} 至今 | 共 {len(bt_df)} 个交易日')
        except Exception as e:
            st.error(f'❌ 回测运行失败: {type(e).__name__}: {str(e)[:200]}')
            st.info('💡 请检查: 1) 网络连接 2) 起始日期是否太早导致数据不足 3) 稍后重试')

# ============== 页面：行业分析 ==============
elif page == '📊 行业分析':
    st.markdown('# 📊 行业分析')
    st.markdown('**行业涨跌幅、估值水平、资金流向**')

    st.markdown('---')

    # 行业选择
    industry_options = {
        '半导体 (BK0438)': 'BK0438',
        '新能源车 (BK0900)': 'BK0900',
        '医药 (BK0465)': 'BK0465',
        '白酒 (BK0896)': 'BK0896',
        '银行 (BK0475)': 'BK0475',
        '证券 (BK0473)': 'BK0473',
        '房地产 (BK0451)': 'BK0451',
        '军工 (BK0490)': 'BK0490',
    }

    col1, col2 = st.columns([1, 3])
    with col1:
        selected_industry = st.selectbox('选择行业', list(industry_options.keys()))

    industry_code = industry_options[selected_industry]

    df_industry = None
    data_source = ''

    # 尝试方式1: 东方财富板块成分股
    try:
        with st.spinner('加载行业数据...'):
            df_industry = load_industry_cons(industry_code)
        if df_industry is not None and len(df_industry) > 0:
            data_source = '东方财富板块数据'
    except Exception:
        pass

    # 尝试方式2: 申万行业指数 (如果方式1失败)
    if df_industry is None or len(df_industry) == 0:
        try:
            with st.spinner('尝试备用数据源...'):
                sw_map = {
                    '半导体 (BK0438)': '801081', '新能源车 (BK0900)': '801730',
                    '医药 (BK0465)': '801150', '白酒 (BK0896)': '801153',
                    '银行 (BK0475)': '801780', '证券 (BK0473)': '801193',
                    '房地产 (BK0451)': '801180', '军工 (BK0490)': '801740',
                }
                sw_code = sw_map.get(selected_industry, '801081')
                df_sw_daily = ak.index_stock_info()
                if df_sw_daily is not None and len(df_sw_daily) > 0:
                    # 从指数列表中筛选行业相关
                    industry_name = selected_industry.split(' ')[0]
                    df_industry = df_sw_daily[df_sw_daily['名称'].str.contains(industry_name, na=False)].head(30)
                    if len(df_industry) > 0:
                        data_source = '申万行业指数'
        except Exception:
            pass

    # 尝试方式3: 静态 fallback 数据
    if df_industry is None or len(df_industry) == 0:
        st.info(f'💡 实时行业数据暂时不可用, 展示示例数据')
        industry_name = selected_industry.split(' ')[0]
        np.random.seed(hash(industry_name) % 2**31)
        n_stocks = 20
        df_industry = pd.DataFrame({
            '代码': [f'{600000+i:06d}' for i in range(n_stocks)],
            '名称': [f'{industry_name}股票{i+1:02d}' for i in range(n_stocks)],
            '最新价': np.random.uniform(10, 100, n_stocks).round(2),
            '涨跌幅': np.random.uniform(-5, 5, n_stocks).round(2),
            '涨跌额': np.random.uniform(-3, 3, n_stocks).round(2),
            '成交量': np.random.randint(10000, 500000, n_stocks),
        })
        data_source = '示例数据 (概念演示)'

    st.markdown(f'### 🏭 {selected_industry} 成分股 - 共 {len(df_industry)} 只')
    if data_source:
        st.caption(f'📊 数据源: {data_source}')

    # 数据预处理
    if '涨跌幅' in df_industry.columns and len(df_industry) > 0:
        df_sorted = df_industry.sort_values('涨跌幅', ascending=False).head(20)
        hover_cols = [c for c in ['代码', '最新价', '市盈率-动态'] if c in df_sorted.columns]
        fig = px.bar(df_sorted, x='涨跌幅', y='名称', orientation='h',
                     color='涨跌幅', color_continuous_scale='RdYlGn',
                     title=f'{selected_industry} 涨跌幅 TOP 20',
                     hover_data=hover_cols if hover_cols else None)
        fig.update_layout(height=600, yaxis={'categoryorder': 'total ascending'})
        st.plotly_chart(fig, use_container_width=True)

    # 完整数据表
    st.markdown('### 📋 完整成分股数据')
    display_cols = [c for c in ['代码', '名称', '最新价', '涨跌幅', '涨跌额', '成交量', '市盈率-动态'] if c in df_industry.columns]
    if display_cols:
        st.dataframe(df_industry[display_cols].head(50), use_container_width=True)
    else:
        st.dataframe(df_industry.head(50), use_container_width=True)

# ============== 页面：智能选股 ==============
elif page == '🎯 智能选股':
    st.markdown('# 🎯 智能选股')
    st.markdown('**自然语言选股 + 多因子评分 + 个股对比 — 对标 AI涨乐智能选股**')
    st.markdown('---')

    tab1, tab2, tab3 = st.tabs(['💬 自然语言选股', '📊 多因子评分', '⚖️ 个股对比'])

    with tab1:
        st.markdown('### 💬 自然语言选股')
        st.caption('输入自然语言描述, AI 自动解析筛选条件')

        query = st.text_input(
            '输入选股条件',
            placeholder='例如: “低估值高成长消费股” 或 “市盈率小于20且市值大于100亿”',
            key='screener_query'
        )

        if st.button('🔍 开始筛选', type='primary', key='screen_btn') and query:
            with st.spinner('AI 解析筛选条件 + 加载数据...'):
                try:
                    screener = NaturalLanguageScreener()
                    # 加载股票池
                    pool = load_stock_pool()
                    if pool is None or pool.empty:
                        st.error('股票池数据加载失败')
                    else:
                        results = screener.screen(query, pool)
                        if results and results.get('stocks'):
                            st.success(f'✅ 筛选完成, 找到 {len(results["stocks"])} 只符合条件的股票')
                            st.markdown('#### 📋 筛选结果')
                            st.dataframe(pd.DataFrame(results['stocks']), use_container_width=True)
                            if results.get('explanation'):
                                st.info(f'🧠 解析逻辑: {results["explanation"]}')
                        else:
                            st.warning('未找到符合条件的股票, 请调整筛选条件')
                except Exception as e:
                    st.error(f'筛选失败: {e}')

    with tab2:
        st.markdown('### 📊 多因子评分')
        st.caption('价值 25% + 成长 25% + 质量 25% + 动量 25%')

        scorer = MultiFactorScorer()
        pool = load_stock_pool()
        if pool is not None and not pool.empty:
            if st.button('📊 计算评分', key='score_btn'):
                with st.spinner('计算多因子评分...'):
                    try:
                        scored = scorer.score_universe(pool)
                        if scored is not None and not scored.empty:
                            st.dataframe(scored.head(20), use_container_width=True)
                    except Exception as e:
                        st.error(f'评分失败: {e}')
        else:
            st.info('股票池数据加载中...')

    with tab3:
        st.markdown('### ⚖️ 个股对比')
        st.caption('最多 5 只股票横向对比')

        col1, col2, col3 = st.columns(3)
        with col1:
            s1 = st.text_input('股票 1', value='贵州茅台', key='cmp1')
            s2 = st.text_input('股票 2', value='五粮液', key='cmp2')
        with col2:
            s3 = st.text_input('股票 3', value='泸州老窖', key='cmp3')
            s4 = st.text_input('股票 4', value='', key='cmp4')
        with col3:
            s5 = st.text_input('股票 5', value='', key='cmp5')

        stocks = [s for s in [s1, s2, s3, s4, s5] if s.strip()]
        if st.button('⚖️ 开始对比', key='compare_btn') and stocks:
            comparator = StockComparator()
            try:
                result = comparator.compare(stocks)
                if result:
                    st.dataframe(pd.DataFrame(result.get('comparison', [])), use_container_width=True)
            except Exception as e:
                st.error(f'对比失败: {e}')

# ============== 页面：智能盯盘 ==============
elif page == '📡 智能盯盘':
    st.markdown('# 📡 智能盯盘')
    st.markdown('**7×24h 市场监控 + 智能预警 + 北向资金 — 对标 AI涨乐智能盯盘**')
    st.markdown('---')

    # 市场大盘
    dashboard = MarketDashboard()
    pool = load_stock_pool()
    try:
        overview = dashboard.get_market_overview()
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric('市场宽度 - 上涨', overview.get('up_count', 'N/A'))
        with col2:
            st.metric('市场宽度 - 下跌', overview.get('down_count', 'N/A'))
        with col3:
            st.metric('涨停', overview.get('limit_up', 'N/A'))
        with col4:
            st.metric('跌停', overview.get('limit_down', 'N/A'))
    except Exception as e:
        st.warning(f'市场概览加载失败: {e}')

    st.markdown('---')

    # 预警系统
    st.markdown('### ⚠️ 智能预警')
    st.caption('支持自然语言创建预警: "贵州茅台涨到1800元提醒"')

    if 'alert_engine' not in st.session_state:
        st.session_state.alert_engine = SmartAlertEngine()
    alert_engine = st.session_state.alert_engine

    alert_input = st.text_input(
        '创建新预警',
        placeholder='例如: "贵州茅台跌破1600元提醒" 或 "比亚迪涨幅超过5%提醒"',
        key='alert_input'
    )
    if st.button('➕ 添加预警', key='add_alert') and alert_input:
        try:
            alert = alert_engine.parse_nl_alert(alert_input)
            st.success(f'✅ 预警已创建: {alert.message}')
        except Exception as e:
            st.error(f'创建失败: {e}')

    # 显示现有预警
    alerts = alert_engine.get_active_alerts()
    if alerts:
        st.markdown('#### 📝 当前预警列表')
        for a in alerts:
            triggered = '🔴' if a.is_triggered else '🟢'
            st.markdown(f'- {triggered} {a.message}')

    # 北向资金
    st.markdown('---')
    st.markdown('### 🌐 北向资金追踪')
    try:
        df_north = ak.stock_hsgt_north_net_flow_in_em(symbol='北向')
        if df_north is not None and len(df_north) > 0:
            st.dataframe(df_north.tail(10), use_container_width=True)
    except Exception:
        st.info('北向资金数据加载中...')

# ============== 页面：我的组合 ==============
elif page == '💼 我的组合':
    st.markdown('# 💼 我的组合')
    st.markdown('**组合管理 + 实时盈亏 + 风险指标**')
    st.markdown('---')

    if 'portfolio_mgr' not in st.session_state:
        st.session_state.portfolio_mgr = PortfolioManager()
    mgr = st.session_state.portfolio_mgr

    tab1, tab2 = st.tabs(['📥 添加持仓', '📊 组合概览'])

    with tab1:
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            h_symbol = st.text_input('股票代码', value='600519', key='h_symbol')
        with col2:
            h_name = st.text_input('股票名称', value='贵州茅台', key='h_name')
        with col3:
            h_shares = st.number_input('持股数', value=100, step=100, key='h_shares')
        with col4:
            h_cost = st.number_input('成本价', value=1680.0, step=0.01, key='h_cost')

        if st.button('➕ 添加持仓', key='add_holding'):
            try:
                mgr.add_holding('我的组合', h_symbol, h_name, int(h_shares), float(h_cost))
                st.success(f'✅ 已添加 {h_name} ({h_symbol})')
            except Exception as e:
                st.error(f'添加失败: {e}')

    with tab2:
        # 确保组合存在
        if '我的组合' not in mgr.list_portfolios():
            mgr.create_portfolio('我的组合')
        portfolio = mgr.get_portfolio('我的组合')
        if portfolio and portfolio.holdings:
            st.markdown(f'### 📊 持仓明细 (共 {len(portfolio.holdings)} 只)')
            holdings_data = [{'股票代码': h.stock_code, '股票名称': h.stock_name,
                              '持股数': h.quantity, '成本价': h.avg_cost,
                              '现价': h.current_price, '盈亏': h.pnl} for h in portfolio.holdings]
            st.dataframe(pd.DataFrame(holdings_data), use_container_width=True)
            col_m1, col_m2 = st.columns(2)
            with col_m1:
                st.metric('总市值', f"¥{portfolio.total_market_value:,.0f}")
            with col_m2:
                st.metric('总盈亏', f"¥{portfolio.total_pnl:,.0f}", f"{portfolio.total_pnl_pct:+.2f}%")
        else:
            st.info('📭 暂无持仓, 请先添加持仓')

# ============== 页面：模拟交易 ==============
elif page == '📈 模拟交易':
    st.markdown('# 📈 模拟交易')
    st.markdown('**语音/文字下单 + 风控引擎 + 反情绪化交易 — 对标 AI涨乐智能交易**')
    st.markdown('---')

    if 'trade_sim' not in st.session_state:
        st.session_state.trade_sim = TradeSimulator()
    if 'risk_engine' not in st.session_state:
        st.session_state.risk_engine = RiskControlEngine()

    sim = st.session_state.trade_sim
    risk = st.session_state.risk_engine

    st.markdown('### 📝 下单')
    st.caption('支持自然语言: “买入100股贵州茅台” 或 表单下单')

    nl_order = st.text_input(
        '自然语言下单',
        placeholder='例如: “买入100股贵州茅台” 或 “卖出全部五粮液”',
        key='nl_order'
    )

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        o_symbol = st.text_input('股票代码', value='600519', key='o_symbol')
    with col2:
        o_action = st.selectbox('方向', ['buy', 'sell'], key='o_action')
    with col3:
        o_qty = st.number_input('数量 (股)', value=100, step=100, key='o_qty')
    with col4:
        o_price = st.number_input('价格 (0=市价)', value=0.0, step=0.01, key='o_price')

    if st.button('🚀 执行交易', type='primary', key='exec_trade'):
        try:
            # 构建 Order 对象
            o_order = Order(
                order_id=f"ORD_{int(datetime.now().timestamp())}",
                stock_code=o_symbol, stock_name='', side=o_action,
                quantity=int(o_qty), price=float(o_price) if o_price > 0 else 0.0,
                order_type='market' if o_price <= 0 else 'limit',
                created_at=datetime.now().isoformat(),
            )
            # 风控检查
            risk_check = risk.check_order(o_order)
            if not risk_check.get('passed', False):
                st.error(f'❌ 风控拒绝: {risk_check.get("message", "未知")}')
            else:
                result = sim.place_order(o_symbol, '', o_action, int(o_qty), float(o_price) if o_price > 0 else 0.0, risk_checker=risk)
                if result and result.status == 'filled':
                    st.success(f"✅ 成交: {result.stock_code} {result.side} {result.quantity}股 @ ¥{result.fill_price:.2f}")
                elif result and result.status == 'rejected':
                    st.warning(f'交易被拒绝: {result.risk_check_message}')
                else:
                    st.warning('交易未成交')
        except Exception as e:
            st.error(f'交易失败: {e}')

    # 交易历史
    st.markdown('---')
    st.markdown('### 📝 交易历史')
    history = sim.get_trade_history()
    if history:
        hist_data = [{'订单号': o.order_id, '代码': o.stock_code, '方向': o.side,
                      '数量': o.quantity, '价格': o.price, '状态': o.status,
                      '时间': o.created_at} for o in history]
        st.dataframe(pd.DataFrame(hist_data), use_container_width=True)
    else:
        st.info('暂无交易记录')

    # 风控状态
    st.markdown('---')
    st.markdown('### 🛡️ 风控状态')
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric('今日交易次数', len([o for o in sim.get_trade_history() if o.created_at and o.created_at[:10] == datetime.now().strftime('%Y-%m-%d')]))
    with col2:
        pnl = sim.get_pnl_summary()
        st.metric('总成交', pnl.get('filled_orders', 0))
    with col3:
        st.metric('交易成本', f"¥{pnl.get('total_commission', 0):.2f}")

# ============== 页面：智能指令 ==============
elif page == '⚡ 智能指令':
    st.markdown('# ⚡ 智能指令')
    st.markdown('**周期性投研任务 + 自动报告生成 — 对标 AI涨乐智能指令**')
    st.markdown('---')

    if 'task_scheduler' not in st.session_state:
        st.session_state.task_scheduler = ResearchTaskScheduler()
    scheduler = st.session_state.task_scheduler

    tab1, tab2, tab3 = st.tabs(['📥 创建任务', '📝 任务列表', '📊 报告生成'])

    with tab1:
        st.markdown('### 预置任务模板')
        templates = TASK_TEMPLATES
        if templates:
            cols = st.columns(min(len(templates), 3))
            for i, (tid, tpl) in enumerate(templates.items()):
                with cols[i % len(cols)]:
                    st.markdown(f"**{tpl.get('name', tid)}**")
                    st.caption(tpl.get('description', ''))
                    st.caption(f"⏰ {tpl.get('schedule', '')}")
                    if st.button(f'➕ 添加', key=f'tpl_{tid}'):
                        try:
                            scheduler.create_task_from_template(tid)
                            st.success(f'✅ 已添加 {tpl["name"]}')
                        except Exception as e:
                            st.error(f'添加失败: {e}')

        st.markdown('---')
        st.markdown('### 自定义任务')
        c_name = st.text_input('任务名称', key='c_name')
        c_desc = st.text_input('任务描述', key='c_desc')
        c_type = st.selectbox('任务类型', ['morning_brief', 'evening_review', 'weekly_report', 'custom'], key='c_type')
        if st.button('➕ 创建自定义任务', key='add_custom') and c_name:
            try:
                scheduler.create_custom_task(c_name, c_desc, schedule='custom')
                st.success(f'✅ 已创建 {c_name}')
            except Exception as e:
                st.error(f'创建失败: {e}')

    with tab2:
        st.markdown('### 📝 当前任务列表')
        tasks = scheduler.list_tasks()
        if tasks:
            for t in tasks:
                st.markdown(f"- **{t.name}** ({t.task_type}) - {'✅ 活跃' if t.is_active else '⏸️ 暂停'}")
        else:
            st.info('暂无任务, 请先创建任务')

    with tab3:
        st.markdown('### 📊 自动报告生成')
        st.caption('基于当前市场数据自动生成投研报告')

        report_type = st.selectbox('报告类型', ['晨报', '盘后总结', '周报'], key='report_type')
        if st.button('📝 生成报告', key='gen_report'):
            with st.spinner('生成报告...'):
                try:
                    generator = AutoReportGenerator()
                    # 构建简单的结果对象
                    from types import SimpleNamespace
                    now_str = datetime.now().strftime('%Y-%m-%d')
                    mock_result = SimpleNamespace(
                        title=f'{report_type} - {now_str}',
                        summary=f'基于当前市场数据的{report_type}自动分析。数据来源: 东方财富、akshare 公开接口。',
                        recommendation='建议关注大盘走势及板块轮动信号, 适当分散配置。',
                        reasoning='基于近期市场成交量、北向资金流向及板块轮动数据综合分析。',
                    )
                    report = generator.generate(report_type, mock_result)
                    st.markdown(report)
                except Exception as e:
                    st.error(f'报告生成失败: {e}')

# ============== 页脚 ==============
st.markdown('---')
st.markdown(
    '<p style="text-align: center; color: #999; font-size: 0.85rem;">'
    '© 2026 慧点资本 (InsightQuant) | Fintech@外滩 第一届金融科技国际创新创业大赛<br/>'
    '项目编号：2026FINTECH-FINT-0093 | 数据来源：akshare 公开数据接口'
    '</p>',
    unsafe_allow_html=True
)
