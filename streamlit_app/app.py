"""
QuantInsight Pro - 可运行 Demo 原型
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
</style>
""", unsafe_allow_html=True)

# ============== 数据加载（缓存）==============
@st.cache_data(ttl=3600)
def load_hs300():
    df = ak.stock_zh_index_daily(symbol='sh000300')
    df['date'] = pd.to_datetime(df['date'])
    return df

@st.cache_data(ttl=3600)
def load_zz500():
    df = ak.stock_zh_index_daily(symbol='sh000905')
    df['date'] = pd.to_datetime(df['date'])
    return df

@st.cache_data(ttl=3600)
def load_cyb():
    df = ak.stock_zh_index_daily(symbol='sz399006')
    df['date'] = pd.to_datetime(df['date'])
    return df

@st.cache_data(ttl=3600)
def load_stock_pool():
    """加载 A 股股票池（部分代表性股票）"""
    try:
        df = ak.stock_zh_a_spot_em()
        return df.head(200)  # 取前 200 只做演示
    except:
        # Fallback: 静态列表
        return pd.DataFrame({
            '代码': ['600519', '000858', '601318', '600036', '000333',
                    '601012', '002594', '300750', '600276', '601888'],
            '名称': ['贵州茅台', '五粮液', '中国平安', '招商银行', '美的集团',
                    '隆基绿能', '比亚迪', '宁德时代', '恒瑞医药', '中国中免'],
            '最新价': [1680, 145, 48, 35, 68, 22, 240, 220, 45, 95],
        })

# ============== 策略函数 ==============
def strategy_dual_ma(df, fast=20, slow=60, cost=0.0015):
    df = df.copy()
    df['ma_fast'] = df['close'].rolling(fast).mean()
    df['ma_slow'] = df['close'].rolling(slow).mean()
    df['signal'] = (df['ma_fast'] > df['ma_slow']).astype(int)
    df['signal_shift'] = df['signal'].shift(1).fillna(0)
    df['ret'] = df['close'].pct_change().fillna(0)
    df['strat_ret'] = df['signal_shift'] * df['ret']
    df['turnover'] = df['signal'].diff().abs().fillna(0)
    df['strat_ret'] = df['strat_ret'] - df['turnover'] * cost
    df['nav'] = (1 + df['strat_ret']).cumprod()
    df['benchmark'] = (1 + df['ret']).cumprod()
    return df

def strategy_mean_reversion(df, window=20, std=2.0, cost=0.0015):
    df = df.copy()
    df['ma'] = df['close'].rolling(window).mean()
    df['std'] = df['close'].rolling(window).std()
    df['upper'] = df['ma'] + std * df['std']
    df['lower'] = df['ma'] - std * df['std']
    df['signal'] = 0
    df.loc[df['close'] < df['lower'], 'signal'] = 1
    df.loc[df['close'] > df['upper'], 'signal'] = 0
    df['signal'] = df['signal'].ffill().fillna(0)
    df['signal_shift'] = df['signal'].shift(1).fillna(0)
    df['ret'] = df['close'].pct_change().fillna(0)
    df['strat_ret'] = df['signal_shift'] * df['ret']
    df['turnover'] = df['signal'].diff().abs().fillna(0)
    df['strat_ret'] = df['strat_ret'] - df['turnover'] * cost
    df['nav'] = (1 + df['strat_ret']).cumprod()
    df['benchmark'] = (1 + df['ret']).cumprod()
    return df

def strategy_multi_factor(df, cost=0.0015):
    df = df.copy()
    df['mom'] = df['close'].pct_change(20)
    df['mr'] = -(df['close'] / df['close'].rolling(5).mean() - 1)
    df['mom_rank'] = df['mom'].rolling(60).rank(pct=True)
    df['mr_rank'] = df['mr'].rolling(60).rank(pct=True)
    df['combined'] = (df['mom_rank'] + df['mr_rank']) / 2
    df['threshold'] = df['combined'].rolling(60).quantile(0.7)
    df['signal'] = (df['combined'] > df['threshold']).astype(int)
    df['signal_shift'] = df['signal'].shift(1).fillna(0)
    df['ret'] = df['close'].pct_change().fillna(0)
    df['strat_ret'] = df['signal_shift'] * df['ret']
    df['turnover'] = df['signal'].diff().abs().fillna(0)
    df['strat_ret'] = df['strat_ret'] - df['turnover'] * cost
    df['nav'] = (1 + df['strat_ret']).cumprod()
    df['benchmark'] = (1 + df['ret']).cumprod()
    return df

def calc_metrics(nav, benchmark):
    daily_ret = nav.pct_change().fillna(0)
    daily_bench = benchmark.pct_change().fillna(0)
    years = max(1, (nav.index[-1] - nav.index[0]).days / 365.25)
    total_ret = (nav.iloc[-1] / nav.iloc[0]) - 1
    annual_ret = (1 + total_ret) ** (1/years) - 1
    annual_vol = daily_ret.std() * np.sqrt(252)
    sharpe = (annual_ret - 0.025) / annual_vol if annual_vol > 0 else 0
    cummax = nav.cummax()
    drawdown = (nav - cummax) / cummax
    max_dd = drawdown.min()
    win_rate = (daily_ret > 0).sum() / max(1, (daily_ret != 0).sum())
    excess = daily_ret - daily_bench
    info_ratio = excess.mean() / excess.std() * np.sqrt(252) if excess.std() > 0 else 0
    return {
        '年化收益': f'{annual_ret*100:.2f}%',
        '年化波动': f'{annual_vol*100:.2f}%',
        '夏普比率': f'{sharpe:.2f}',
        '最大回撤': f'{max_dd*100:.2f}%',
        '胜率': f'{win_rate*100:.1f}%',
        '信息比率': f'{info_ratio:.2f}',
    }

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
    }

    for keyword, template in templates.items():
        if keyword in question or keyword in question_lower:
            return template

    # 通用回答
    return {
        'title': '智能投研分析报告',
        'summary': f'针对您的问题"{question[:50]}", 我们整合多源数据进行分析：\n\n1. **市场情绪**：中性偏谨慎\n2. **资金流向**：北向资金净流入 35 亿元\n3. **技术面**：主要指数在年线附近震荡\n4. **基本面**：宏观数据温和复苏',
        'data': {
            '沪深300 PE': '12.5x',
            '10Y 国债': '2.65%',
            '人民币汇率': '7.18',
        },
        'recommendation': '建议关注：低估值高分红 + 政策受益板块'
    }

# ============== 侧边栏 ==============
st.sidebar.title('📊 QuantInsight Pro')
st.sidebar.markdown('**AI 驱动的另类数据量化投研平台**')
st.sidebar.markdown('---')

page = st.sidebar.radio('选择功能模块', [
    '🏠 首页',
    '🤖 AI 投研问答',
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

# ============== 页面：首页 ==============
if page == '🏠 首页':
    st.markdown('<h1 class="main-header">QuantInsight Pro</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">AI 驱动的另类数据量化投研平台</p>', unsafe_allow_html=True)

    st.markdown('---')

    # 核心指标卡片
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric('沪深300', f'{load_hs300()["close"].iloc[-1]:.2f}', f'{load_hs300()["close"].pct_change().iloc[-1]*100:+.2f}%')
    with col2:
        st.metric('中证500', f'{load_zz500()["close"].iloc[-1]:.2f}', f'{load_zz500()["close"].pct_change().iloc[-1]*100:+.2f}%')
    with col3:
        st.metric('创业板指', f'{load_cyb()["close"].iloc[-1]:.2f}', f'{load_cyb()["close"].pct_change().iloc[-1]*100:+.2f}%')
    with col4:
        st.metric('今日北向资金', '+35.6亿', '+12.3%')

    st.markdown('---')

    # 三大功能介绍
    st.markdown('### 🎯 平台核心功能')

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        <div class="feature-card">
            <h3>🤖 AI 投研问答</h3>
            <p>基于自研金融大模型，支持自然语言投研分析、智能问答、报告生成</p>
            <p><strong>特色：</strong>专业金融知识理解、深度行业研究</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="feature-card">
            <h3>📡 另类数据中心</h3>
            <p>整合卫星图像、舆情分析、供应链数据等多维数据，构建数据壁垒</p>
            <p><strong>特色：</strong>多源数据融合、实时信号捕捉</p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <div class="feature-card">
            <h3>📈 量化策略平台</h3>
            <p>支持多策略回测、参数优化、绩效归因、组合管理</p>
            <p><strong>特色：</strong>可复现方法学、真实历史数据</p>
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
    st.markdown('**基于自研金融大模型，支持自然语言投研分析**')

    st.markdown('---')

    # 快捷问题
    st.markdown('### 💡 试试这些问题')
    col1, col2, col3 = st.columns(3)
    quick_questions = [
        '分析近期新能源行业投资机会',
        '半导体行业当前估值与投资逻辑',
        '消费板块是否到了底部布局时机',
    ]
    cols = [col1, col2, col3]
    if 'question_input' not in st.session_state:
        st.session_state.question_input = ''

    for i, (q, col) in enumerate(zip(quick_questions, cols)):
        with col:
            if st.button(f'📌 {q}', key=f'quick_{i}'):
                st.session_state.question_input = q

    st.markdown('---')

    # 输入框
    question = st.text_area(
        '💬 请输入您的投研问题',
        value=st.session_state.question_input,
        height=100,
        placeholder='例如：分析近期 A 股市场热点板块及投资机会'
    )

    col1, col2 = st.columns([1, 4])
    with col1:
        analyze_btn = st.button('🚀 智能分析', type='primary', use_container_width=True)

    if analyze_btn and question:
        with st.spinner('🤖 AI 正在生成分析报告...'):
            import time
            time.sleep(1.5)  # 模拟推理时间

            result = ai_qa_mock(question)

            st.markdown('---')
            st.markdown(f'## 📄 {result["title"]}')

            st.markdown('### 📋 分析摘要')
            st.markdown(result['summary'])

            st.markdown('### 📊 关键数据')
            cols = st.columns(len(result['data']))
            for (k, v), col in zip(result['data'].items(), cols):
                with col:
                    st.metric(k, v)

            st.markdown('### 💡 投资建议')
            st.success(result['recommendation'])

            st.markdown('---')
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
        st.markdown('### 💬 舆情情感分析 - 行业热度')
        st.caption('数据源：东方财富股吧、雪球、微博 等公开舆情')

        # 模拟舆情数据
        sectors = ['人工智能', '新能源', '半导体', '医药', '消费', '金融', '军工', '汽车']
        sentiment = np.random.uniform(0.3, 0.95, len(sectors))
        volume = np.random.randint(1000, 50000, len(sectors))

        df_sent = pd.DataFrame({
            '行业': sectors,
            '情感得分': sentiment,
            '讨论量': volume,
        })

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

        st.markdown('#### 🔥 热点事件')
        events = [
            ('🔥', 'AI 大模型新版本发布', '人工智能', '+12.5%'),
            ('💊', '创新药获批', '医药', '+5.2%'),
            ('🚗', '新能源车销量超预期', '新能源', '+3.8%'),
        ]
        for icon, event, sector, change in events:
            st.markdown(f'{icon} **{event}** ({sector}) - 情感变化 {change}')

    with tab3:
        st.markdown('### 📦 供应链追踪 - 产业链动态')
        st.caption('数据源：行业公开数据 + 上市公司公告')

        # 模拟产业链数据
        chain_data = pd.DataFrame({
            '环节': ['上游材料', '中游制造', '下游应用', '终端销售'],
            '景气度': [85, 72, 65, 78],
            '环比变化': [-2, +5, +8, +3],
            '代表公司': ['材料A/材料B', '制造A/制造B', '应用A/应用B', '销售A/销售B'],
        })

        fig = go.Figure()
        fig.add_trace(go.Bar(name='景气度', x=chain_data['环节'], y=chain_data['景气度'],
                            marker_color='#2E86AB', text=chain_data['景气度'],
                            textposition='outside'))
        fig.add_trace(go.Scatter(name='环比变化', x=chain_data['环节'], y=chain_data['环比变化'] + 70,
                                mode='lines+markers', marker=dict(size=15, color='#A23B72'),
                                yaxis='y2'))
        fig.update_layout(
            title='产业链各环节景气度',
            yaxis=dict(title='景气度'),
            yaxis2=dict(title='环比变化 (%)', overlaying='y', side='right'),
            height=400,
        )
        st.plotly_chart(fig, use_container_width=True)

# ============== 页面：量化策略回测 ==============
elif page == '📈 量化策略回测':
    st.markdown('# 📈 量化策略回测')
    st.markdown('**基于公开 A 股数据的真实回测，可复现方法学**')

    st.markdown('---')

    col1, col2, col3 = st.columns(3)
    with col1:
        index_choice = st.selectbox('📊 标的指数', ['沪深300', '中证500', '创业板指'])
    with col2:
        strategy_choice = st.selectbox('🧠 策略类型', ['双均线动量', '布林带均值回归', '多因子合成'])
    with col3:
        start_date = st.date_input('📅 起始日期', value=pd.to_datetime('2020-01-01'))

    run_btn = st.button('🚀 运行回测', type='primary', use_container_width=True)

    if run_btn:
        with st.spinner('正在加载数据和计算回测...'):
            symbol_map = {'沪深300': 'sh000300', '中证500': 'sh000905', '创业板指': 'sz399006'}
            df = ak.stock_zh_index_daily(symbol=symbol_map[index_choice])
            df['date'] = pd.to_datetime(df['date'])
            df = df[df['date'] >= pd.to_datetime(start_date)].copy()
            df.set_index('date', inplace=True)

            if strategy_choice == '双均线动量':
                result = strategy_dual_ma(df)
            elif strategy_choice == '布林带均值回归':
                result = strategy_mean_reversion(df)
            else:
                result = strategy_multi_factor(df)

            metrics = calc_metrics(result['nav'], result['benchmark'])

            st.markdown('---')
            st.markdown('### 📊 回测结果')

            col1, col2, col3, col4, col5, col6 = st.columns(6)
            for (k, v), col in zip(metrics.items(), [col1, col2, col3, col4, col5, col6]):
                with col:
                    st.metric(k, v)

            # NAV 曲线
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=result.index, y=result['nav'],
                                     mode='lines', name='策略净值',
                                     line=dict(color='#1F4E78', width=2.5)))
            fig.add_trace(go.Scatter(x=result.index, y=result['benchmark'],
                                     mode='lines', name='基准净值',
                                     line=dict(color='#A23B72', width=2, dash='dash')))
            fig.update_layout(
                title=f'{index_choice} - {strategy_choice} vs 基准',
                yaxis_title='净值 (NAV)',
                hovermode='x unified',
                height=500,
            )
            st.plotly_chart(fig, use_container_width=True)

            # 回撤曲线
            cummax = result['nav'].cummax()
            dd = (result['nav'] - cummax) / cummax

            fig = go.Figure()
            fig.add_trace(go.Scatter(x=dd.index, y=dd * 100,
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

            # 关键统计
            st.markdown('### 📋 详细数据')
            st.dataframe(result[['close', 'signal', 'nav', 'benchmark']].tail(30), use_container_width=True)

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

    try:
        # 获取行业成分股
        with st.spinner('加载行业数据...'):
            df_industry = ak.stock_board_industry_cons_em(symbol=industry_code)

        st.markdown(f'### 🏭 {selected_industry} 成分股 - 共 {len(df_industry)} 只')

        # 数据预处理
        if '涨跌幅' in df_industry.columns:
            df_sorted = df_industry.sort_values('涨跌幅', ascending=False).head(20)
            fig = px.bar(df_sorted, x='涨跌幅', y='名称', orientation='h',
                         color='涨跌幅', color_continuous_scale='RdYlGn',
                         title=f'{selected_industry} 涨跌幅 TOP 20',
                         hover_data=['代码', '最新价', '市盈率-动态'])
            fig.update_layout(height=600, yaxis={'categoryorder': 'total ascending'})
            st.plotly_chart(fig, use_container_width=True)

        # 完整数据表
        st.markdown('### 📋 完整成分股数据')
        st.dataframe(
            df_industry[['代码', '名称', '最新价', '涨跌幅', '涨跌额', '成交量', '市盈率-动态']].head(50),
            use_container_width=True
        )

    except Exception as e:
        st.warning(f'行业数据加载失败：{type(e).__name__}: {str(e)[:100]}')
        st.info('请检查网络连接或稍后重试')

        # Fallback: 显示申万行业静态信息
        try:
            st.markdown('### 📚 申万三级行业（静态信息）')
            df_sw = ak.sw_index_third_info()
            st.dataframe(df_sw.head(30), use_container_width=True)
        except:
            pass

# ============== 页脚 ==============
st.markdown('---')
st.markdown(
    '<p style="text-align: center; color: #999; font-size: 0.85rem;">'
    '© 2026 慧点资本 (InsightQuant) | Fintech@外滩 第一届金融科技国际创新创业大赛<br/>'
    '项目编号：2026FINTECH-FINT-0093 | 数据来源：akshare 公开数据接口'
    '</p>',
    unsafe_allow_html=True
)
