"""
QuantInsight Pro - Admin Dashboard
=====================================

Admin panel with 5 tabs:
1. User Analytics (DAU/WAU/MAU, registration trend)
2. Login History (timeline, IPs)
3. Usage Patterns (page visits, feature popularity)
4. Activation Codes (generate, revoke, list)
5. Marketing & Insights (conversion rates, user segments)

License: MIT
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime


def render_admin_dashboard(db):
    """Render the full admin dashboard with tabs"""
    st.markdown('# ⚙️ 管理后台')
    st.markdown('---')

    # Quick stats at top
    stats = db.get_dau_wau_mau()
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric('总用户数', stats['total_users'])
    with c2:
        st.metric('今日活跃 (DAU)', stats['dau'])
    with c3:
        st.metric('周活跃 (WAU)', stats['wau'])
    with c4:
        st.metric('月活跃 (MAU)', stats['mau'])

    st.markdown('---')

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        '📊 用户分析',
        '🔐 登录历史',
        '📈 使用模式',
        '🔑 激活码管理',
        '🎯 营销洞察',
    ])

    with tab1:
        _render_user_analytics(db)
    with tab2:
        _render_login_history(db)
    with tab3:
        _render_usage_patterns(db)
    with tab4:
        _render_activation_codes(db)
    with tab5:
        _render_marketing_insights(db)


def _render_user_analytics(db):
    """Tab 1: User analytics with charts"""
    st.markdown('### 📊 用户增长趋势')

    trend = db.get_registration_trend(days=30)
    if trend:
        df = pd.DataFrame(trend)
        df['day'] = pd.to_datetime(df['day'])
        fig = px.bar(df, x='day', y='cnt', title='近 30 天注册趋势',
                     labels={'day': '日期', 'cnt': '注册数'},
                     color_discrete_sequence=['#2E86AB'])
        fig.update_layout(bargap=0.2)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info('暂无注册数据')

    st.markdown('---')
    st.markdown('### 👥 用户列表')

    users = db.get_all_users()
    if users:
        df_users = pd.DataFrame(users)
        df_users.columns = ['ID', '用户名', '邮箱', '注册时间', '管理员', '体验已用', '状态']
        df_users['管理员'] = df_users['管理员'].map({1: '是', 0: '否'})
        df_users['体验已用'] = df_users['体验已用'].map({1: '是', 0: '否'})
        df_users['状态'] = df_users['状态'].map({1: '活跃', 0: '禁用'})
        st.dataframe(df_users, use_container_width=True, hide_index=True)
    else:
        st.info('暂无用户')


def _render_login_history(db):
    """Tab 2: Login history timeline"""
    st.markdown('### 🔐 最近登录记录')

    history = db.get_login_history_all(limit=200)
    if history:
        df = pd.DataFrame(history)
        df['login_time'] = pd.to_datetime(df['login_time'])

        # Display as table
        display_df = df[['username', 'login_time', 'ip_address', 'user_agent']].copy()
        display_df.columns = ['用户名', '登录时间', 'IP 地址', '浏览器']
        display_df['登录时间'] = display_df['登录时间'].dt.strftime('%Y-%m-%d %H:%M')
        display_df['浏览器'] = display_df['浏览器'].apply(
            lambda x: (x[:50] + '...') if x and len(str(x)) > 50 else x
        )
        st.dataframe(display_df, use_container_width=True, hide_index=True)

        # Login activity chart
        st.markdown('---')
        st.markdown('### 📈 登录活跃度 (按小时)')
        df['hour'] = df['login_time'].dt.hour
        hourly = df.groupby('hour').size().reset_index(name='count')
        fig = px.bar(hourly, x='hour', y='count',
                     title='登录时段分布',
                     labels={'hour': '时段 (小时)', 'count': '登录次数'},
                     color_discrete_sequence=['#1F4E78'])
        fig.update_xaxes(dtick=1)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info('暂无登录记录')


def _render_usage_patterns(db):
    """Tab 3: Page visit patterns and feature usage"""
    st.markdown('### 📈 页面访问热度')

    popularity = db.get_page_popularity()
    if popularity:
        df = pd.DataFrame(popularity)
        fig = px.bar(df, x='page', y='visits',
                     title='各页面访问次数',
                     labels={'page': '页面', 'visits': '访问次数'},
                     color='visits',
                     color_continuous_scale='Blues')
        fig.update_layout(xaxis_tickangle=-30)
        st.plotly_chart(fig, use_container_width=True)

        # Also show as table
        st.markdown('#### 详细数据')
        df.columns = ['页面', '访问次数']
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info('暂无使用数据')


def _render_activation_codes(db):
    """Tab 4: Activation code management"""
    st.markdown('### 🔑 激活码管理')

    # Generate new codes
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown('#### 生成新激活码')
        with st.form('gen_code_form'):
            note = st.text_input('备注 (可选)', placeholder='例如: VIP客户张三')
            quantity = st.number_input('生成数量', min_value=1, max_value=50, value=1)
            submitted = st.form_submit_button('🎫 生成激活码', type='primary')

        if submitted:
            codes_generated = []
            admin_id = st.session_state.get('auth_user_id', 1)
            for _ in range(quantity):
                code = db.create_activation_code(admin_id, note)
                codes_generated.append(code)
            st.success(f'✅ 已生成 {len(codes_generated)} 个激活码:')
            for c in codes_generated:
                st.code(c, language=None)

    with col2:
        st.markdown('#### 快速统计')
        all_codes = db.get_all_activation_codes()
        total = len(all_codes)
        used = sum(1 for c in all_codes if c['is_used'])
        unused = total - used
        st.metric('总激活码', total)
        st.metric('已使用', used)
        st.metric('未使用', unused)
        if total > 0:
            st.metric('使用率', f'{used/total*100:.1f}%')

    st.markdown('---')
    st.markdown('#### 激活码列表')

    if all_codes:
        df = pd.DataFrame(all_codes)
        display_cols = ['code', 'note', 'is_used', 'used_by_name', 'created_at', 'used_at']
        available_cols = [c for c in display_cols if c in df.columns]
        df_display = df[available_cols].copy()
        df_display.columns = ['激活码', '备注', '状态', '使用者', '创建时间', '使用时间']
        df_display['状态'] = df_display['状态'].map({1: '已使用', 0: '未使用'})
        df_display['创建时间'] = df_display['创建时间'].apply(lambda x: x[:16] if x else '')
        df_display['使用时间'] = df_display['使用时间'].apply(lambda x: x[:16] if x else '—')

        st.dataframe(df_display, use_container_width=True, hide_index=True)

        # Revoke unused codes
        st.markdown('---')
        st.markdown('#### 撤销未使用激活码')
        unused_codes = [c for c in all_codes if not c['is_used']]
        if unused_codes:
            code_to_revoke = st.selectbox(
                '选择要撤销的激活码',
                [c['code'] for c in unused_codes],
                key='revoke_select'
            )
            if st.button('❌ 撤销此激活码', key='revoke_btn'):
                code_obj = next(c for c in unused_codes if c['code'] == code_to_revoke)
                db.revoke_activation_code(code_obj['id'])
                st.success(f'已撤销激活码: {code_to_revoke}')
                st.rerun()
        else:
            st.info('没有未使用的激活码')
    else:
        st.info('暂无激活码记录')


def _render_marketing_insights(db):
    """Tab 5: Marketing analytics and user insights"""
    st.markdown('### 🎯 营销洞察')

    # Conversion funnel
    stats = db.get_dau_wau_mau()
    total_users = stats['total_users']
    users = db.get_all_users()

    if users:
        df = pd.DataFrame(users)
        activated = len(df[df['trial_used'] == 0])  # trial_used=0 means activated or fresh
        trial_exhausted = len(df[df['trial_used'] == 1])

        st.markdown('#### 📊 用户转化漏斗')
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric('总注册用户', total_users)
        with c2:
            st.metric('体验已用完', trial_exhausted)
        with c3:
            conversion = (activated / total_users * 100) if total_users > 0 else 0
            st.metric('已激活用户', activated, f'{conversion:.1f}%')

        # Funnel chart
        fig = go.Figure(go.Funnel(
            y=['注册用户', '体验用户', '激活用户'],
            x=[total_users, trial_exhausted + activated, activated],
            textposition='inside',
            marker={'color': ['#2E86AB', '#F4A261', '#2A9D8F']},
        ))
        fig.update_layout(title='用户转化漏斗', margin=dict(t=40, b=20))
        st.plotly_chart(fig, use_container_width=True)

        st.markdown('---')

        # User segments
        st.markdown('#### 🏷️ 用户画像分析')
        col1, col2 = st.columns(2)
        with col1:
            st.markdown('**用户类型分布**')
            admin_count = len(df[df['is_admin'] == 1])
            regular_count = len(df[df['is_admin'] == 0])
            segment_data = pd.DataFrame({
                '类型': ['管理员', '普通用户'],
                '数量': [admin_count, regular_count],
            })
            fig_pie = px.pie(segment_data, values='数量', names='类型',
                           color_discrete_sequence=['#E76F51', '#264653'])
            fig_pie.update_layout(margin=dict(t=20, b=20))
            st.plotly_chart(fig_pie, use_container_width=True)

        with col2:
            st.markdown('**活跃度指标**')
            dau = stats['dau']
            wau = stats['wau']
            mau = stats['mau']
            retention = (dau / mau * 100) if mau > 0 else 0
            st.metric('日活/月活比 (留存指标)', f'{retention:.1f}%')
            st.metric('周活跃率', f'{(wau/total_users*100) if total_users else 0:.1f}%')
            st.metric('月活跃率', f'{(mau/total_users*100) if total_users else 0:.1f}%')

        # Recent registration trend (last 7 days)
        st.markdown('---')
        st.markdown('#### 📅 近 7 天注册趋势')
        trend_7d = db.get_registration_trend(days=7)
        if trend_7d:
            df_trend = pd.DataFrame(trend_7d)
            df_trend['day'] = pd.to_datetime(df_trend['day'])
            fig_line = px.line(df_trend, x='day', y='cnt',
                              title='近 7 天每日注册数',
                              labels={'day': '日期', 'cnt': '注册数'},
                              markers=True,
                              color_discrete_sequence=['#E76F51'])
            fig_line.update_layout(margin=dict(t=40, b=20))
            st.plotly_chart(fig_line, use_container_width=True)
        else:
            st.info('暂无近 7 天注册数据')

        # Actionable insights
        st.markdown('---')
        st.markdown('#### 💡 运营建议')
        insights = []
        if total_users > 0 and trial_exhausted / total_users > 0.5:
            insights.append('⚠️ 超过半数用户体验已用完，建议加强激活码推广')
        if dau > 0 and dau / max(mau, 1) < 0.1:
            insights.append('📉 日活/月活比较低，建议增加每日推送或提醒功能')
        if total_users < 10:
            insights.append('📢 用户基数较小，建议通过社交媒体、投资社区推广')
        if not insights:
            insights.append('✅ 各项指标正常，继续保持')
        for ins in insights:
            st.markdown(f'- {ins}')
    else:
        st.info('暂无用户数据')
