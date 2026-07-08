"""
QuantInsight Pro - Auth Pages (Login / Register / Trial Gate / Profile)
=========================================================================

Streamlit UI components for authentication flow.

License: MIT
"""

import streamlit as st


def render_login_page(session_mgr):
    """Render login form. Returns True if login successful."""
    st.markdown("""
    <div style="text-align:center; padding: 2rem 0 1rem;">
        <h1 style="color:#1F4E78; font-size:2.2rem;">QuantInsight Pro</h1>
        <p style="color:#666; font-size:1.1rem;">AI 驱动的另类数据量化投研平台</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown('### 🔐 用户登录')

        with st.form('login_form'):
            username = st.text_input('用户名', placeholder='请输入用户名')
            password = st.text_input('密码', type='password', placeholder='请输入密码')
            submitted = st.form_submit_button('登录', type='primary', use_container_width=True)

        if submitted:
            if not username or not password:
                st.error('请输入用户名和密码')
            else:
                result = session_mgr.login(st.session_state, username, password)
                if result['ok']:
                    st.success(f'✅ 欢迎回来, {username}!')
                    st.rerun()
                else:
                    st.error(f'❌ {result["error"]}')

        st.markdown('---')
        st.markdown('还没有账号? 请在下方切换到 **注册** 页面')

    return False


def render_register_page(session_mgr, db):
    """Render registration form. Returns True if registered."""
    st.markdown("""
    <div style="text-align:center; padding: 2rem 0 1rem;">
        <h1 style="color:#1F4E78; font-size:2.2rem;">QuantInsight Pro</h1>
        <p style="color:#666; font-size:1.1rem;">创建您的专属投研账号</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown('### 📝 用户注册')

        with st.form('register_form'):
            username = st.text_input('用户名 *', placeholder='4-20 位字母数字')
            email = st.text_input('邮箱 (可选)', placeholder='your@email.com')
            password = st.text_input('密码 *', type='password', placeholder='至少 6 位')
            confirm = st.text_input('确认密码 *', type='password', placeholder='再次输入密码')
            submitted = st.form_submit_button('注册', type='primary', use_container_width=True)

        if submitted:
            # Validation
            errors = []
            if not username or len(username) < 4:
                errors.append('用户名至少 4 个字符')
            if not password or len(password) < 6:
                errors.append('密码至少 6 个字符')
            if password != confirm:
                errors.append('两次密码不一致')

            if errors:
                for e in errors:
                    st.error(f'❌ {e}')
            else:
                # Rate limit check (use placeholder IP for now)
                ip = '0.0.0.0'
                if not db.check_registration_rate(ip):
                    st.error('❌ 注册频率过高, 请明天再试')
                else:
                    result = db.create_user(username, password, email)
                    if result['ok']:
                        st.success(f'✅ 注册成功! 用户名: {username}')
                        st.info('👉 请切换到 **登录** 页面登录')
                        st.session_state.auth_show_login = True
                        st.rerun()
                    else:
                        st.error(f'❌ {result["error"]}')

        st.markdown('---')
        st.markdown('已有账号? 请在上方切换到 **登录** 页面')

    return False


def render_trial_gate(session_mgr, db):
    """Render activation code page when trial is exhausted."""
    st.markdown("""
    <div style="text-align:center; padding: 2rem 0 1rem;">
        <h1 style="color:#1F4E78; font-size:2.2rem;">QuantInsight Pro</h1>
        <p style="color:#666; font-size:1.1rem;">您的免费体验已结束</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.warning('⚠️ **免费体验已结束** — 每个用户仅可享受一次免费体验, 请输入激活码继续使用')

        st.markdown('### 🔑 输入激活码')
        with st.form('activation_form'):
            code = st.text_input(
                '激活码',
                placeholder='请输入 16 位激活码 (例如: A1B2C3D4E5F6G7H8)',
            ).strip().upper()
            submitted = st.form_submit_button('激活', type='primary', use_container_width=True)

        if submitted:
            if not code:
                st.error('请输入激活码')
            else:
                result = db.redeem_activation_code(code, st.session_state.auth_user_id)
                if result['ok']:
                    st.success('✅ 激活成功! 正在跳转...')
                    st.session_state.auth_trial_used = False
                    st.rerun()
                else:
                    st.error(f'❌ {result["error"]}')

        st.markdown('---')
        st.markdown("""
        ### 📞 获取激活码
        
        请联系管理员获取激活码:
        - **微信**: 扫码联系客服
        - **邮箱**: support@insightquant.com
        - **电话**: 400-XXX-XXXX
        
        > 💡 激活码由管理员在后台生成, 每个激活码仅限使用一次
        """)

    # Logout option
    st.markdown('---')
    if st.button('🚪 退出登录', use_container_width=True, key='trial_gate_logout'):
        session_mgr.logout(st.session_state)
        st.rerun()


def render_auth_selector():
    """Render login/register tab selector. Returns 'login' or 'register'."""
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        tab1, tab2 = st.tabs(['🔐 登录', '📝 注册'])
        with tab1:
            return 'login'
        with tab2:
            return 'register'


def render_profile_page(session_mgr, db):
    """Render user profile page"""
    if not session_mgr.is_authenticated(st.session_state):
        st.warning('请先登录')
        return

    user = session_mgr.get_current_user(st.session_state)
    if not user:
        return

    st.markdown('# 👤 个人中心')
    st.markdown('---')

    col1, col2 = st.columns(2)
    with col1:
        st.markdown('### 📋 账户信息')
        st.markdown(f'- **用户名**: {user["username"]}')
        st.markdown(f'- **邮箱**: {user.get("email", "未设置")}')
        st.markdown(f'- **注册时间**: {user["created_at"][:10]}')
        st.markdown(f'- **账户类型**: {"管理员" if user["is_admin"] else "普通用户"}')
        st.markdown(f'- **体验状态**: {"已激活" if not user["trial_used"] else "免费体验中"}')

    with col2:
        st.markdown('### 📊 使用统计')
        stats = db.get_user_stats(user['id'])
        st.markdown(f'- **登录次数**: {stats["login_count"]}')
        st.markdown(f'- **操作次数**: {stats["action_count"]}')
        st.markdown(f'- **最近登录**: {stats["last_login"][:16] if stats["last_login"] else "无记录"}')

    st.markdown('---')
    if st.button('🚪 退出登录', use_container_width=True, key='profile_logout'):
        session_mgr.logout(st.session_state)
        st.rerun()
