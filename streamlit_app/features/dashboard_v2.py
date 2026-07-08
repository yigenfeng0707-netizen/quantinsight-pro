# -*- coding: utf-8 -*-
"""
QuantInsight Pro - 升级版数据看板
==================================

替代数据看板 - 全新视觉:
  - 大盘指数卡片(渐变+迷你走势)
  - 北向资金热力图(时间序列)
  - 行业涨跌霓虹排行
  - 涨停板异动监控
  - 风险预警雷达
"""
from __future__ import annotations
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# 量化配色
COLORS = {
    'primary': '#0A1628',
    'accent': '#00D4FF',
    'gold': '#D4AF37',
    'green': '#00FF88',
    'red': '#FF3366',
    'gray': '#2A3441',
    'text': '#E8E8E8',
    'card_bg': '#FFFFFF',
    'card_border': '#E8ECF1',
}

from features.robust_utils import (
    get_sample_industries, get_sample_stocks, get_sample_news,
    safe_metric, retry_button, cached_with_ttl
)


# ============== 1. 大盘指数卡片 ==============

def render_index_cards(macro_data: Dict):
    """大盘指数卡片（渐变+颜色编码）"""
    cols = st.columns(3)
    indices = [
        ('sh_index', macro_data.get('sh_index', {'value': 0, 'change_pct': 0}), '🏛️', '#1F4E78'),
        ('sz_index', macro_data.get('sz_index', {'value': 0, 'change_pct': 0}), '🏢', '#2E86AB'),
        ('cyb_index', macro_data.get('cyb_index', {'value': 0, 'change_pct': 0}), '🚀', '#D4AF37'),
    ]
    display_names = {'sh_index': '沪深300', 'sz_index': '中证500', 'cyb_index': '创业板指'}

    for col, (key, data, icon, color) in zip(cols, indices):
        with col:
            name = display_names.get(key, key)
            change = data.get('change_pct', 0)
            color_class = 'green' if change > 0 else 'red' if change < 0 else 'gray'
            arrow = '▲' if change > 0 else '▼' if change < 0 else '—'
            value_color = COLORS['green'] if change > 0 else COLORS['red'] if change < 0 else COLORS['gray']

            st.markdown(f"""
            <div style="background: linear-gradient(135deg, {color} 0%, {COLORS['primary']} 100%);
                        padding: 20px; border-radius: 12px; color: white;
                        box-shadow: 0 4px 16px rgba(0,0,0,0.15);
                        border: 1px solid rgba(255,255,255,0.1); height: 130px;">
                <div style="display: flex; align-items: center; justify-content: space-between;">
                    <span style="font-size: 0.85rem; opacity: 0.8;">{icon} {name}</span>
                    <span style="font-size: 0.7rem; opacity: 0.6;">SH/SZ</span>
                </div>
                <div style="font-size: 1.8rem; font-weight: 800; margin: 8px 0; letter-spacing: 1px;">
                    {data.get('value', 0):.2f}
                </div>
                <div style="color: {value_color}; font-size: 1rem; font-weight: 600;">
                    {arrow} {change:+.2f}%
                </div>
            </div>
            """, unsafe_allow_html=True)


# ============== 2. 北向资金热力图 ==============

def render_northbound_heatmap(north_flow: float = 0.0):
    """北向资金热力图 - 优先使用真实时序数据"""
    st.markdown("""
    <h3 style="color: #0A1628; margin-bottom: 8px;">
        💰 北向资金流向 <span style="color: #D4AF37; font-size: 0.7em; font-weight: 400;">— 外资态度</span>
    </h3>
    """, unsafe_allow_html=True)

    dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
    flows = None
    data_source = "demo"

    try:
        from features.extended_data_sources import fetch_northbound_series
        res = fetch_northbound_series(days=30)
        if res.ok and isinstance(res.data, pd.DataFrame) and not res.data.empty:
            df = res.data.copy()
            data_source = res.source
            # 兼容多种列名
            date_col = next((c for c in df.columns if '日期' in str(c) or c.lower() == 'date'), df.columns[0])
            flow_col = next((c for c in df.columns if '净流入' in str(c) or 'net' in str(c).lower()), df.columns[-1])
            df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
            df = df.dropna(subset=[date_col]).sort_values(date_col).tail(30)
            dates = df[date_col]
            flows = pd.to_numeric(df[flow_col], errors='coerce').fillna(0).values
    except Exception as e:
        logger = __import__('logging').getLogger(__name__)
        logger.debug("northbound series: %s", e)

    if flows is None:
        np.random.seed(int(north_flow * 10) % 100)
        flows = np.random.normal(north_flow, 30, 30).cumsum()
        st.caption("⚠️ 实时接口暂不可用，展示模拟序列")
    else:
        st.caption(f"数据来源: {data_source} · 近 {len(flows)} 个交易日")

    # 颜色：流入绿色，流出红色
    colors = [COLORS['green'] if f > 0 else COLORS['red'] for f in flows]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=dates, y=flows,
        marker_color=colors,
        text=[f'{v:+.0f}' for v in flows],
        textposition='outside',
        textfont=dict(size=9, color=COLORS['text']),
        hovertemplate='<b>%{x|%m-%d}</b><br>净流入: %{y:+.2f}亿<extra></extra>',
    ))

    fig.update_layout(
        plot_bgcolor='#F8F9FB',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#1F4E78', family='Arial'),
        height=250,
        margin=dict(l=20, r=20, t=20, b=20),
        showlegend=False,
        xaxis=dict(gridcolor='rgba(0,0,0,0.05)', showgrid=False),
        yaxis=dict(gridcolor='rgba(0,0,0,0.05)', title='净流入(亿元)'),
    )

    col1, col2 = st.columns([3, 1])
    with col1:
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #1F4E78 0%, #0A1628 100%);
                    padding: 16px; border-radius: 12px; color: white; height: 250px;
                    display: flex; flex-direction: column; justify-content: center;">
            <div style="font-size: 0.85rem; opacity: 0.8;">今日北向</div>
            <div style="font-size: 2rem; font-weight: 800; color: {COLORS['green'] if north_flow > 0 else COLORS['red']};
                        margin: 8px 0;">
                {north_flow:+.2f}<span style="font-size: 1rem; opacity: 0.7;">亿</span>
            </div>
            <div style="font-size: 0.8rem; opacity: 0.7;">
                30日累计: <b style="color: {COLORS['gold']};">{flows.sum():+.1f}亿</b>
            </div>
            <div style="font-size: 0.8rem; opacity: 0.7; margin-top: 4px;">
                状态: <b style="color: {COLORS['green'] if north_flow > 0 else COLORS['red']};">
                {'看多' if north_flow > 0 else '看空' if north_flow < -10 else '观望'}
                </b>
            </div>
        </div>
        """, unsafe_allow_html=True)


# ============== 3. 行业涨跌霓虹排行 ==============

def render_industry_neon_ranking(industries: Optional[List[Dict]] = None):
    """行业涨跌霓虹排行 - 彩色横条"""
    if not industries:
        industries = get_sample_industries()

    st.markdown("""
    <h3 style="color: #0A1628; margin-bottom: 8px;">
        🏭 行业涨跌榜 <span style="color: #D4AF37; font-size: 0.7em; font-weight: 400;">— 资金偏好</span>
    </h3>
    """, unsafe_allow_html=True)

    # 排序
    industries = sorted(industries, key=lambda x: x.get('change_pct', 0), reverse=True)

    # 渐变条形图
    names = [ind['name'] for ind in industries[:10]]
    changes = [ind['change_pct'] for ind in industries[:10]]
    colors = [COLORS['green'] if c > 0 else COLORS['red'] for c in changes]

    fig = go.Figure(go.Bar(
        x=changes,
        y=names,
        orientation='h',
        marker=dict(
            color=changes,
            colorscale=[[0, COLORS['red']], [0.5, '#666666'], [1, COLORS['green']]],
            line=dict(color='rgba(255,255,255,0.3)', width=1),
        ),
        text=[f'{c:+.2f}%' for c in changes],
        textposition='outside',
        textfont=dict(color='#0A1628', size=11, family='Arial Black'),
        hovertemplate='<b>%{y}</b><br>涨跌幅: %{x:+.2f}%<extra></extra>',
    ))

    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#1F4E78'),
        height=400,
        margin=dict(l=80, r=60, t=20, b=20),
        showlegend=False,
        xaxis=dict(
            title='涨跌幅(%)',
            gridcolor='rgba(0,0,0,0.05)',
            zerolinecolor='#D4AF37',
            zerolinewidth=2,
        ),
        yaxis=dict(autorange='reversed', gridcolor='rgba(0,0,0,0.05)'),
    )

    st.plotly_chart(fig, use_container_width=True)


# ============== 4. 涨跌停监控 ==============

def render_limit_monitor(macro: Dict):
    """涨跌停监控面板"""
    st.markdown("""
    <h3 style="color: #0A1628; margin-bottom: 8px;">
        ⚡ 涨停板异动监控 <span style="color: #D4AF37; font-size: 0.7em; font-weight: 400;">— 实时</span>
    </h3>
    """, unsafe_allow_html=True)

    limit_up = macro.get('limit_up', 0)
    limit_down = macro.get('limit_down', 0)
    up_count = macro.get('up_count', 0)
    down_count = macro.get('down_count', 0)
    total = up_count + down_count

    col1, col2, col3, col4 = st.columns(4)
    metrics = [
        ('涨停', limit_up, COLORS['green'], '🚀'),
        ('跌停', limit_down, COLORS['red'], '💥'),
        ('上涨家数', up_count, COLORS['green'], '📈'),
        ('下跌家数', down_count, COLORS['red'], '📉'),
    ]
    for col, (label, value, color, icon) in zip([col1, col2, col3, col4], metrics):
        with col:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, {color}33 0%, {color}11 100%);
                        padding: 16px; border-radius: 10px; text-align: center;
                        border: 1px solid {color};">
                <div style="color: {color}; font-size: 0.8rem; font-weight: 600;">{icon} {label}</div>
                <div style="color: {color}; font-size: 1.6rem; font-weight: 800; margin-top: 4px;">{value}</div>
            </div>
            """, unsafe_allow_html=True)

    # 涨跌比可视化
    if total > 0:
        up_pct = up_count / total * 100
        st.markdown(f"""
        <div style="margin-top: 16px;">
            <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                <span style="color: {COLORS['green']}; font-size: 0.85rem; font-weight: 600;">上涨 {up_pct:.1f}%</span>
                <span style="color: {COLORS['red']}; font-size: 0.85rem; font-weight: 600;">下跌 {100-up_pct:.1f}%</span>
            </div>
            <div style="background: #E8ECF1; height: 12px; border-radius: 6px; overflow: hidden;">
                <div style="background: linear-gradient(90deg, {COLORS['green']} 0%, #00FFB3 100%);
                            width: {up_pct}%; height: 100%; float: left; box-shadow: 0 0 8px {COLORS['green']}77;"></div>
                <div style="background: linear-gradient(90deg, #FF6680 0%, {COLORS['red']} 100%);
                            width: {100-up_pct}%; height: 100%; float: left; box-shadow: 0 0 8px {COLORS['red']}77;"></div>
            </div>
        </div>
        """, unsafe_allow_html=True)


# ============== 5. 主入口 ==============

def render_dashboard():
    """数据看板主入口"""
    st.markdown("""
    <div style="background: linear-gradient(135deg, #0A1628 0%, #1E3A5F 100%);
                padding: 24px; border-radius: 12px; margin-bottom: 24px;
                border: 1px solid rgba(0, 212, 255, 0.3);
                box-shadow: 0 8px 24px rgba(0, 212, 255, 0.15);">
        <h2 style="color: #00D4FF; margin: 0; font-weight: 800;">📊 实时数据看板</h2>
        <p style="color: #B8C5D6; margin: 8px 0 0 0;">AFAC2026 Demo · 大盘指数 · 北向资金 · 涨跌停 · 行业排行 · SQLite 优先</p>
    </div>
    """, unsafe_allow_html=True)

    # 拉取数据
    from features.report_generator import fetch_macro_data, fetch_industry_data, fetch_money_flow
    macro = fetch_macro_data()
    industries = fetch_industry_data(top_n=10)
    money_flow = fetch_money_flow()

    # ---- 格式转换：将 macro['indices'] 列表转为 render_index_cards 期望的 dict 格式 ----
    index_key_map = {'沪深300': 'sh_index', '中证500': 'sz_index', '创业板指': 'cyb_index'}
    index_dict = {}
    for item in macro.get('indices', []):
        key = index_key_map.get(item.get('name', ''))
        if key:
            index_dict[key] = {'value': item.get('price', 0), 'change_pct': item.get('change_pct', 0)}
    macro.update(index_dict)

    # ---- 格式转换：将 macro['breadth'] 展开为 render_limit_monitor 期望的字段 ----
    breadth = macro.get('breadth', {})
    macro['up_count'] = breadth.get('advance', 0)
    macro['down_count'] = breadth.get('decline', 0)

    # 数据源标识
    source = macro.get('source', 'unknown')
    badge = '🟢 真实akshare数据' if source == 'akshare' else '🟡 演示数据(高质量模拟)'
    st.caption(f"数据源: {badge} | 更新时间: {datetime.now().strftime('%H:%M:%S')}")

    # 1. 大盘指数卡片
    render_index_cards(macro)

    st.markdown("<br/>", unsafe_allow_html=True)

    # 2. 北向资金热力图（优先使用 money_flow 中的 north_flow，更完整）
    north_flow = money_flow.get('north_flow', macro.get('north_flow', 0))
    render_northbound_heatmap(north_flow)

    st.markdown("<br/>", unsafe_allow_html=True)

    # 3. 涨跌停监控
    render_limit_monitor(macro)

    st.markdown("<br/>", unsafe_allow_html=True)

    # 4. 行业涨跌霓虹排行
    render_industry_neon_ranking(industries)
