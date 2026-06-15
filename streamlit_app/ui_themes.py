"""
QuantInsight Pro - UI Themes
===============================

Light/Dark mode CSS injection for Streamlit.
Professional financial color scheme with glassmorphism effects.

License: MIT
"""

import streamlit as st

# Color palette
COLORS = {
    'primary': '#0A1628',       # Deep navy
    'secondary': '#1A2942',     # Navy blue
    'accent': '#00D4AA',        # Teal
    'accent_hover': '#00F0C0',  # Bright teal
    'warning': '#F4A261',       # Warm amber
    'danger': '#E76F51',        # Coral red
    'success': '#2A9D8F',       # Sea green
    'text_primary': '#E8ECF1',  # Light gray
    'text_secondary': '#8B95A5', # Muted gray
    'card_bg': 'rgba(26, 41, 66, 0.8)',  # Glassmorphism navy
    'sidebar_bg': '#0D1B2A',    # Dark sidebar
}

DARK_THEME_CSS = f"""
<style>
/* ===== Global Dark Theme ===== */
.stApp {{
    background: linear-gradient(135deg, {COLORS['primary']} 0%, #0F2236 50%, #0A1628 100%);
    color: {COLORS['text_primary']};
}}

/* ===== Sidebar ===== */
section[data-testid="stSidebar"] {{
    background: {COLORS['sidebar_bg']} !important;
    border-right: 1px solid rgba(0, 212, 170, 0.15);
}}
section[data-testid="stSidebar"] .stMarkdown p,
section[data-testid="stSidebar"] .stMarkdown li,
section[data-testid="stSidebar"] label {{
    color: {COLORS['text_primary']} !important;
}}
section[data-testid="stSidebar"] .stRadio label {{
    color: {COLORS['text_primary']} !important;
    font-size: 0.95rem;
}}
section[data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label {{
    padding: 0.4rem 0.8rem;
    border-radius: 8px;
    transition: all 0.2s;
}}
section[data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label:hover {{
    background: rgba(0, 212, 170, 0.1);
}}
section[data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label[data-baseweb="radio"]:has(div[aria-checked="true"]) {{
    background: rgba(0, 212, 170, 0.15);
}}

/* ===== Headers ===== */
.main-header {{
    font-size: 2.5rem;
    background: linear-gradient(135deg, {COLORS['accent']}, #00B8D4);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-weight: 800;
    text-align: center;
    padding: 1.5rem 0 0.5rem;
    letter-spacing: -0.5px;
}}
.sub-header {{
    font-size: 1.1rem;
    color: {COLORS['text_secondary']};
    text-align: center;
    padding-bottom: 1.5rem;
    font-weight: 300;
}}

/* ===== Cards ===== */
.metric-card {{
    background: {COLORS['card_bg']};
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    padding: 1.2rem;
    border-radius: 12px;
    border: 1px solid rgba(0, 212, 170, 0.15);
    color: {COLORS['text_primary']};
    text-align: center;
    transition: all 0.3s ease;
    position: relative;
    overflow: hidden;
}}
.metric-card::before {{
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    width: 4px;
    height: 100%;
    background: linear-gradient(180deg, {COLORS['accent']}, transparent);
}}
.metric-card:hover {{
    transform: translateY(-2px);
    border-color: rgba(0, 212, 170, 0.4);
    box-shadow: 0 8px 32px rgba(0, 212, 170, 0.1);
}}

.feature-card {{
    background: {COLORS['card_bg']};
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    padding: 1.5rem;
    border-radius: 12px;
    border: 1px solid rgba(255,255,255,0.06);
    border-left: 4px solid {COLORS['accent']};
    margin: 1rem 0;
    transition: all 0.3s ease;
    color: {COLORS['text_primary']};
}}
.feature-card:hover {{
    border-left-color: {COLORS['accent_hover']};
    box-shadow: 0 4px 24px rgba(0, 0, 0, 0.2);
}}
.feature-card h4 {{
    font-size: 1rem;
    margin: 0 0 0.5rem 0;
    color: {COLORS['accent']};
    font-weight: 600;
}}

/* ===== Streamlit Components ===== */
.stMarkdown h1 {{
    color: {COLORS['text_primary']} !important;
    font-weight: 700;
}}
.stMarkdown h2, .stMarkdown h3 {{
    color: {COLORS['text_primary']} !important;
}}
.stMarkdown p, .stMarkdown li {{
    color: {COLORS['text_secondary']} !important;
}}
.stMarkdown a {{
    color: {COLORS['accent']} !important;
}}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {{
    gap: 4px;
    background: transparent;
}}
.stTabs [data-baseweb="tab"] {{
    background: rgba(26, 41, 66, 0.6);
    border-radius: 8px 8px 0 0;
    color: {COLORS['text_secondary']};
    padding: 0.5rem 1rem;
}}
.stTabs [aria-selected="true"] {{
    background: {COLORS['card_bg']} !important;
    color: {COLORS['accent']} !important;
    border-bottom: 2px solid {COLORS['accent']};
}}

/* Buttons */
.stButton > button {{
    border-radius: 8px;
    font-weight: 500;
    transition: all 0.2s;
}}
.stButton > button[kind="primary"],
.stButton > button[data-testid="stFormSubmitButton"] {{
    background: linear-gradient(135deg, {COLORS['accent']}, #00B8D4) !important;
    color: {COLORS['primary']} !important;
    border: none !important;
    font-weight: 600;
}}
.stButton > button[kind="primary"]:hover {{
    box-shadow: 0 4px 16px rgba(0, 212, 170, 0.3);
    transform: translateY(-1px);
}}

/* Metric widgets */
[data-testid="stMetric"] {{
    background: {COLORS['card_bg']};
    border-radius: 10px;
    padding: 0.8rem 1rem;
    border: 1px solid rgba(255,255,255,0.05);
}}
[data-testid="stMetric"] label {{
    color: {COLORS['text_secondary']} !important;
    font-size: 0.85rem;
}}
[data-testid="stMetric"] [data-testid="stMetricValue"] {{
    color: {COLORS['text_primary']} !important;
    font-weight: 600;
}}

/* Expander */
.streamlit-expanderHeader {{
    background: rgba(26, 41, 66, 0.4) !important;
    border-radius: 8px !important;
    color: {COLORS['text_primary']} !important;
}}
.streamlit-expanderContent {{
    background: rgba(26, 41, 66, 0.2);
    border-radius: 0 0 8px 8px;
}}

/* Dataframe */
.stDataFrame {{
    border-radius: 8px;
    overflow: hidden;
}}

/* Alert boxes */
.stAlert {{
    border-radius: 8px;
    border-left-width: 4px;
}}

/* Text inputs */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea {{
    background: rgba(26, 41, 66, 0.6) !important;
    color: {COLORS['text_primary']} !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    border-radius: 8px;
}}
.stTextInput > div > div > input:focus {{
    border-color: {COLORS['accent']} !important;
    box-shadow: 0 0 0 2px rgba(0, 212, 170, 0.2) !important;
}}

/* Divider */
hr {{
    border-color: rgba(255,255,255,0.08) !important;
}}

/* Chat messages */
.stChatMessage {{
    background: {COLORS['card_bg']} !important;
    border-radius: 12px;
    border: 1px solid rgba(255,255,255,0.05);
}}

/* Selectbox */
.stSelectbox > div > div {{
    background: rgba(26, 41, 66, 0.6) !important;
    color: {COLORS['text_primary']} !important;
}}
</style>
"""

LIGHT_THEME_CSS = f"""
<style>
/* ===== Light Theme (Professional Financial) ===== */
.main-header {{
    font-size: 2.5rem;
    color: #1F4E78;
    font-weight: 800;
    text-align: center;
    padding: 1.5rem 0 0.5rem;
    letter-spacing: -0.5px;
}}
.sub-header {{
    font-size: 1.1rem;
    color: #666;
    text-align: center;
    padding-bottom: 1.5rem;
    font-weight: 300;
}}
.metric-card {{
    background: linear-gradient(135deg, #1F4E78 0%, #2E86AB 100%);
    padding: 1.2rem;
    border-radius: 12px;
    color: white;
    text-align: center;
    transition: all 0.3s ease;
    position: relative;
    overflow: hidden;
    box-shadow: 0 2px 12px rgba(31, 78, 120, 0.15);
}}
.metric-card::before {{
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    width: 4px;
    height: 100%;
    background: linear-gradient(180deg, #00D4AA, transparent);
}}
.metric-card:hover {{
    transform: translateY(-2px);
    box-shadow: 0 8px 24px rgba(31, 78, 120, 0.2);
}}

.feature-card {{
    background: #FFFFFF;
    padding: 1.5rem;
    border-radius: 12px;
    border: 1px solid #E8ECF1;
    border-left: 4px solid #2E86AB;
    margin: 1rem 0;
    transition: all 0.3s ease;
    box-shadow: 0 1px 4px rgba(0,0,0,0.04);
}}
.feature-card:hover {{
    border-left-color: #D4AF37;
    box-shadow: 0 4px 16px rgba(0,0,0,0.08);
    transform: translateY(-2px);
}}
.feature-card h4 {{
    font-size: 1rem;
    margin: 0 0 0.5rem 0;
    color: #1F4E78;
    font-weight: 600;
}}

/* ===== 上海金融中心风格：金色高亮 + 霓虹青数据条 ===== */
.gold-accent {{
    color: #D4AF37 !important;
    font-weight: 700;
}}
.neon-text {{
    color: #00D4FF !important;
    text-shadow: 0 0 8px rgba(0, 212, 255, 0.4);
}}
.data-pulse {{
    background: linear-gradient(90deg, #00D4FF 0%, #D4AF37 100%);
    height: 3px;
    border-radius: 2px;
    animation: pulse 2s ease-in-out infinite;
}}
@keyframes pulse {{
    0%, 100% {{ opacity: 0.6; }}
    50% {{ opacity: 1; }}
}}

/* ===== 侧边栏对比度增强（关键修复） ===== */
section[data-testid="stSidebar"] {{
    background: linear-gradient(180deg, #0A1628 0%, #0F2236 100%) !important;
    border-right: 2px solid rgba(0, 212, 255, 0.2);
    box-shadow: 4px 0 24px rgba(0, 0, 0, 0.3);
}}
section[data-testid="stSidebar"] * {{
    color: #FFFFFF !important;
    font-weight: 500;
}}
section[data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label {{
    padding: 0.5rem 1rem !important;
    border-radius: 8px;
    margin: 2px 0;
    border-left: 3px solid transparent;
    transition: all 0.2s;
}}
section[data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label:hover {{
    background: rgba(0, 212, 255, 0.15);
    border-left-color: #00D4FF;
}}
section[data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label[data-baseweb="radio"]:has(input:checked),
section[data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label:has(input:checked) {{
    background: linear-gradient(90deg, rgba(0, 212, 255, 0.2), rgba(212, 175, 55, 0.1)) !important;
    border-left: 3px solid #D4AF37 !important;
    color: #D4AF37 !important;
    font-weight: 600 !important;
}}
section[data-testid="stSidebar"] h1, section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3, section[data-testid="stSidebar"] h4 {{
    color: #D4AF37 !important;
    letter-spacing: 0.5px;
}}
section[data-testid="stSidebar"] .stMarkdown {{
    color: #FFFFFF !important;
}}
section[data-testid="stSidebar"] .stMarkdown p {{
    color: #E8ECF1 !important;
    font-size: 0.9rem;
}}

/* ===== Tabs 升级：金色下划线 ===== */
.stTabs [data-baseweb="tab-list"] {{
    background: linear-gradient(90deg, rgba(0, 212, 255, 0.05), rgba(212, 175, 55, 0.05));
    border-radius: 8px;
    padding: 4px;
}}
.stTabs [data-baseweb="tab"] {{
    background: transparent;
    color: #1F4E78 !important;
    font-weight: 500;
    border-radius: 6px;
    padding: 0.6rem 1.2rem;
}}
.stTabs [aria-selected="true"] {{
    background: linear-gradient(135deg, #1F4E78 0%, #2E86AB 100%) !important;
    color: #FFFFFF !important;
    font-weight: 700;
    box-shadow: 0 2px 12px rgba(31, 78, 120, 0.3);
}}

/* ===== 按钮升级：金色描边主按钮 ===== */
.stButton > button[kind="primary"] {{
    background: linear-gradient(135deg, #1F4E78 0%, #D4AF37 100%) !important;
    color: #FFFFFF !important;
    border: 1px solid #D4AF37 !important;
    font-weight: 700;
    letter-spacing: 0.5px;
    box-shadow: 0 4px 16px rgba(31, 78, 120, 0.2);
}}
.stButton > button[kind="primary"]:hover {{
    transform: translateY(-1px);
    box-shadow: 0 6px 24px rgba(212, 175, 55, 0.4);
}}

/* ===== 数据卡片升级 ===== */
[data-testid="stMetric"] {{
    background: linear-gradient(135deg, #FFFFFF 0%, #F5F7FA 100%);
    border: 1px solid #E8ECF1;
    border-left: 4px solid #00D4FF;
    border-radius: 10px;
    padding: 1rem;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}}
[data-testid="stMetric"] label {{
    color: #1F4E78 !important;
    font-weight: 600;
}}
[data-testid="stMetric"] [data-testid="stMetricValue"] {{
    color: #0A1628 !important;
    font-weight: 800;
    font-size: 1.4rem;
}}
</style>
"""

# Shared responsive CSS - injected regardless of theme
RESPONSIVE_CSS = """
<style>
/* ===== Responsive Design: Mobile / Tablet / Desktop ===== */

/* Base: ensure containers are flexible */
.block-container {
    padding: 1rem !important;
    max-width: 100% !important;
}

/* DataFrames: horizontal scroll on small screens */
[data-testid="stDataFrame"] {
    max-width: 100% !important;
    overflow-x: auto !important;
}

/* Tabs: wrap on small screens */
.stTabs [data-baseweb="tab-list"] {
    flex-wrap: wrap !important;
    gap: 4px !important;
}
.stTabs [data-baseweb="tab"] {
    padding: 0.4rem 0.8rem !important;
    font-size: 0.85rem !important;
    min-width: auto !important;
}

/* Plotly charts: responsive */
.js-plotly-plot, .js-plotly-plot .plotly {
    width: 100% !important;
}

/* ===== Tablet (768px - 1024px) ===== */
@media (min-width: 768px) and (max-width: 1024px) {
    .block-container {
        padding: 1rem 2rem !important;
    }
    .main-header { font-size: 2rem !important; }
    .sub-header { font-size: 1rem !important; }
    .stMarkdown h1 { font-size: 1.6rem !important; }
    .stMarkdown h2 { font-size: 1.3rem !important; }
    [data-testid="column"] { min-width: 45% !important; }
    .metric-card { padding: 0.8rem !important; }
    .feature-card { padding: 1.2rem !important; }
    [data-testid="stSidebar"] { min-width: 220px !important; max-width: 280px !important; }
}

/* ===== Mobile (max-width: 767px) ===== */
@media (max-width: 767px) {
    .block-container {
        padding: 0.5rem 0.8rem !important;
    }
    .main-header {
        font-size: 1.4rem !important;
        padding: 0.8rem 0 0.3rem !important;
    }
    .sub-header {
        font-size: 0.85rem !important;
        padding-bottom: 0.8rem !important;
    }
    .stMarkdown h1 { font-size: 1.3rem !important; }
    .stMarkdown h2 { font-size: 1.1rem !important; }
    .stMarkdown h3 { font-size: 1rem !important; }
    /* Stack columns vertically */
    [data-testid="column"] {
        width: 100% !important;
        flex: 100% !important;
        min-width: 100% !important;
        margin-bottom: 0.3rem !important;
    }
    /* Full width buttons */
    .stButton > button {
        width: 100% !important;
        font-size: 0.85rem !important;
    }
    /* Compact cards */
    .metric-card { padding: 0.6rem !important; font-size: 0.85rem !important; }
    .feature-card { padding: 0.8rem !important; margin: 0.5rem 0 !important; }
    /* Compact sidebar */
    [data-testid="stSidebar"] { min-width: 180px !important; max-width: 240px !important; }
    [data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label {
        font-size: 0.85rem !important;
        padding: 0.3rem 0.5rem !important;
    }
    /* Smaller metrics */
    [data-testid="stMetricValue"] { font-size: 1.2rem !important; }
    /* Compact chat */
    .stChatMessage [data-testid="stMarkdownContainer"] p { font-size: 0.85rem !important; }
    /* Smaller tabs */
    .stTabs [data-baseweb="tab"] { padding: 0.3rem 0.5rem !important; font-size: 0.8rem !important; }
    /* Reduce spacing */
    .stMarkdown { margin-bottom: 0.5rem !important; }
    hr { margin: 0.5rem 0 !important; }
}

/* ===== Small Mobile (max-width: 480px) ===== */
@media (max-width: 480px) {
    .block-container { padding: 0.3rem 0.5rem !important; }
    .main-header { font-size: 1.2rem !important; }
    .stMarkdown h1 { font-size: 1.1rem !important; }
    .stButton > button { font-size: 0.8rem !important; }
    [data-testid="stMetricValue"] { font-size: 1rem !important; }
}

/* ===== Desktop (min-width: 1025px) ===== */
@media (min-width: 1025px) {
    .block-container { padding: 1rem 3rem !important; }
}

/* ===== Large Desktop (min-width: 1440px) ===== */
@media (min-width: 1440px) {
    .block-container {
        padding: 1rem 5rem !important;
        max-width: 1400px !important;
        margin: 0 auto !important;
    }
}

/* ===== Print styles ===== */
@media print {
    [data-testid="stSidebar"] { display: none !important; }
    .stButton { display: none !important; }
}
</style>
"""


def apply_theme():
    """Inject theme CSS based on session state preference + shared responsive CSS"""
    theme = st.session_state.get('theme_mode', 'dark')
    if theme == 'dark':
        st.markdown(DARK_THEME_CSS, unsafe_allow_html=True)
    else:
        st.markdown(LIGHT_THEME_CSS, unsafe_allow_html=True)
    # Always inject responsive CSS (shared across themes)
    st.markdown(RESPONSIVE_CSS, unsafe_allow_html=True)


def render_theme_toggle():
    """Render a theme toggle in the sidebar"""
    if 'theme_mode' not in st.session_state:
        st.session_state.theme_mode = 'dark'

    current = st.session_state.theme_mode
    new_theme = '☀️ 浅色' if current == 'dark' else '🌙 深色'
    if st.sidebar.button(new_theme, key='theme_toggle', width='stretch'):
        st.session_state.theme_mode = 'light' if current == 'dark' else 'dark'
        st.rerun()
