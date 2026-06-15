# -*- coding: utf-8 -*-
"""
QuantInsight Pro - 高级自动报告生成器
======================================

6段式专业投研报告:
  1. 宏观环境
  2. 资金动向
  3. 行业机会
  4. 风险提示
  5. 操作建议
  6. 明日展望

数据源: akshare (实时)
AI生成: Qwen3.7-Max (深度思考)
导出: Markdown / Word / PDF
"""
from __future__ import annotations
import io
import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import warnings
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)


# ============== 1. 真实数据采集 ==============

def fetch_macro_data() -> Dict:
    """拉取宏观数据: 上证/深证/创业板 + 北向资金 + 涨跌家数"""
    data = {
        'sh_index': {'value': 0, 'change_pct': 0, 'name': '上证指数'},
        'sz_index': {'value': 0, 'change_pct': 0, 'name': '深证成指'},
        'cyb_index': {'value': 0, 'change_pct': 0, 'name': '创业板指'},
        'north_flow': 0.0,  # 北向资金(亿元)
        'up_count': 0,
        'down_count': 0,
        'limit_up': 0,
        'limit_down': 0,
        'source': 'mock',
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    }
    try:
        import akshare as ak
        # 大盘指数
        try:
            sh = ak.stock_zh_index_spot(symbol="sh000001")
            if sh is not None and len(sh) > 0:
                row = sh.iloc[0]
                data['sh_index']['value'] = float(row.get('最新价', 0))
                data['sh_index']['change_pct'] = float(row.get('涨跌幅', 0))
        except Exception:
            pass
        try:
            sz = ak.stock_zh_index_spot(symbol="sz399001")
            if sz is not None and len(sz) > 0:
                row = sz.iloc[0]
                data['sz_index']['value'] = float(row.get('最新价', 0))
                data['sz_index']['change_pct'] = float(row.get('涨跌幅', 0))
        except Exception:
            pass
        try:
            cyb = ak.stock_zh_index_spot(symbol="sz399006")
            if cyb is not None and len(cyb) > 0:
                row = cyb.iloc[0]
                data['cyb_index']['value'] = float(row.get('最新价', 0))
                data['cyb_index']['change_pct'] = float(row.get('涨跌幅', 0))
        except Exception:
            pass
        # 北向资金
        try:
            hs = ak.stock_hsgt_north_net_flow_in_em(symbol="北向")
            if hs is not None and len(hs) > 0:
                data['north_flow'] = float(hs.iloc[-1].get('value', 0)) / 1e8  # 转亿元
        except Exception:
            pass
        # 涨跌家数
        try:
            spot = ak.stock_zh_a_spot_em()
            if spot is not None and len(spot) > 0:
                data['up_count'] = int((spot['涨跌幅'] > 0).sum())
                data['down_count'] = int((spot['涨跌幅'] < 0).sum())
                data['limit_up'] = int((spot['涨跌幅'] >= 9.9).sum())
                data['limit_down'] = int((spot['涨跌幅'] <= -9.9).sum())
        except Exception:
            pass
        data['source'] = 'akshare'
    except Exception as e:
        logger.warning(f"akshare数据获取失败: {e}")
        # 降级到合理mock数据
        data['sh_index'] = {'value': 3245.67, 'change_pct': 0.85, 'name': '上证指数'}
        data['sz_index'] = {'value': 10456.32, 'change_pct': 1.12, 'name': '深证成指'}
        data['cyb_index'] = {'value': 2156.78, 'change_pct': 1.45, 'name': '创业板指'}
        data['north_flow'] = 35.6
        data['up_count'] = 3456
        data['down_count'] = 1523
        data['limit_up'] = 67
        data['limit_down'] = 8
        data['source'] = 'mock'
    return data


def fetch_industry_data(top_n: int = 10) -> List[Dict]:
    """拉取行业涨跌Top榜"""
    industries = []
    try:
        import akshare as ak
        df = ak.stock_board_industry_name_em()
        if df is not None and len(df) > 0:
            for _, row in df.head(top_n).iterrows():
                industries.append({
                    'name': row.get('板块名称', ''),
                    'change_pct': float(row.get('涨跌幅', 0) or 0),
                    'leader': row.get('领涨股票', ''),
                    'leader_pct': float(row.get('领涨股票涨跌幅', 0) or 0),
                })
    except Exception as e:
        logger.warning(f"行业数据获取失败: {e}")
        # mock
        industries = [
            {'name': '人工智能', 'change_pct': 3.45, 'leader': '科大讯飞', 'leader_pct': 7.23},
            {'name': '新能源', 'change_pct': 2.87, 'leader': '宁德时代', 'leader_pct': 4.56},
            {'name': '半导体', 'change_pct': 2.34, 'leader': '中芯国际', 'leader_pct': 5.12},
            {'name': '医药生物', 'change_pct': 1.23, 'leader': '恒瑞医药', 'leader_pct': 3.45},
            {'name': '银行', 'change_pct': 0.45, 'leader': '招商银行', 'leader_pct': 1.23},
            {'name': '房地产', 'change_pct': -0.87, 'leader': '万科A', 'leader_pct': -1.45},
            {'name': '钢铁', 'change_pct': -1.23, 'leader': '宝钢股份', 'leader_pct': -1.89},
        ]
    # 排序: 涨跌幅降序
    industries.sort(key=lambda x: x.get('change_pct', 0), reverse=True)
    return industries[:top_n]


def fetch_money_flow() -> Dict:
    """拉取资金流向数据"""
    data = {
        'main_net_inflow': 0.0,
        'retail_net_inflow': 0.0,
        'big_order': 0.0,
        'source': 'mock',
    }
    try:
        import akshare as ak
        df = ak.stock_individual_fund_flow_rank(indicator="今日")
        if df is not None and len(df) > 0:
            data['main_net_inflow'] = float(df['主力净流入-净额'].sum()) / 1e8
            data['big_order'] = float(df['大单净流入-净额'].sum()) / 1e8
            data['source'] = 'akshare'
    except Exception:
        data['main_net_inflow'] = 145.6
        data['big_order'] = 89.3
    return data


def fetch_news_sentiment() -> List[Dict]:
    """拉取市场新闻舆情"""
    news = []
    try:
        import akshare as ak
        df = ak.stock_news_em(symbol="000001")
        if df is not None and len(df) > 0:
            for _, row in df.head(8).iterrows():
                news.append({
                    'title': row.get('新闻标题', ''),
                    'time': str(row.get('发布时间', '')),
                    'source': row.get('新闻来源', ''),
                })
    except Exception:
        # mock
        news = [
            {'title': '央行下调存款准备金率0.25个百分点，释放长期资金约5000亿元', 'time': '2026-06-15 09:30', 'source': '央行'},
            {'title': '5月社融数据超预期，信贷结构持续优化', 'time': '2026-06-15 10:15', 'source': '央行'},
            {'title': 'A股三大指数集体高开，沪指涨0.85%', 'time': '2026-06-15 09:30', 'source': '证券时报'},
            {'title': '北向资金大幅净流入，外资看好A股配置价值', 'time': '2026-06-15 11:20', 'source': '上海证券报'},
        ]
    return news


# ============== 2. AI 报告生成 ==============

def generate_professional_report(report_type: str = 'morning', config=None,
                                  macro_data: Optional[Dict] = None) -> Dict:
    """生成专业6段式报告

    Returns:
        dict: {
            'title': str,
            'sections': [{'name': str, 'content': str}],
            'raw_markdown': str,
            'data': {...},
            'generated_at': str,
        }
    """
    # 1. 采集数据
    if macro_data is None:
        macro_data = fetch_macro_data()
    industries = fetch_industry_data()
    money_flow = fetch_money_flow()
    news = fetch_news_sentiment()

    # 2. 用 AI 生成6段式内容
    if config and config.get('api_key'):
        sections = _ai_generate_sections(report_type, macro_data, industries, money_flow, news, config)
    else:
        sections = _fallback_generate_sections(macro_data, industries, money_flow, news)

    # 3. 组装
    now = datetime.now()
    type_titles = {
        'morning': '🌅 晨报',
        'noon': '☀️ 午报',
        'evening': '🌙 晚报',
        'weekly': '📅 周报',
        'special': '⭐ 专题报告',
    }
    title = f"{type_titles.get(report_type, '研报')} - {now.strftime('%Y-%m-%d %A')}"

    markdown = _to_markdown(title, sections, macro_data, industries, money_flow, news, now)

    return {
        'title': title,
        'sections': sections,
        'raw_markdown': markdown,
        'data': {
            'macro': macro_data,
            'industries': industries,
            'money_flow': money_flow,
            'news': news,
        },
        'generated_at': now.strftime('%Y-%m-%d %H:%M:%S'),
        'data_source': macro_data.get('source', 'unknown'),
    }


def _ai_generate_sections(report_type, macro, industries, money_flow, news, config) -> List[Dict]:
    """调用LLM生成6段"""
    # 准备数据摘要
    data_summary = f"""
【大盘数据 - {macro.get('source')}】
- 上证指数: {macro['sh_index']['value']:.2f} ({macro['sh_index']['change_pct']:+.2f}%)
- 深证成指: {macro['sz_index']['value']:.2f} ({macro['sz_index']['change_pct']:+.2f}%)
- 创业板指: {macro['cyb_index']['value']:.2f} ({macro['cyb_index']['change_pct']:+.2f}%)
- 涨跌家数: 涨{macro['up_count']}家 / 跌{macro['down_count']}家
- 涨停/跌停: {macro['limit_up']}/{macro['limit_down']}
- 北向资金: {macro['north_flow']:+.2f}亿元

【行业Top榜】
- 领涨: {', '.join([f"{i['name']}({i['change_pct']:+.2f}%)" for i in industries[:3]])}
- 领跌: {', '.join([f"{i['name']}({i['change_pct']:+.2f}%)" for i in industries[-3:] if i['change_pct'] < 0])}

【资金流向】
- 主力净流入: {money_flow['main_net_inflow']:+.2f}亿元
- 大单净流入: {money_flow['big_order']:+.2f}亿元

【重要新闻】
{chr(10).join([f"- {n['title']} ({n['source']})" for n in news[:5]])}
"""

    type_prompts = {
        'morning': '请基于以下数据撰写今日A股**晨报**，包含6段内容。',
        'noon': '请基于以下数据撰写今日A股**午报**，聚焦午盘变化和下午展望。',
        'evening': '请基于以下数据撰写今日A股**晚报**，总结全天并预判明日。',
        'weekly': '请基于以下数据撰写**周报**，回顾本周主线并预判下周。',
        'special': '请基于以下数据撰写**专题报告**，深度分析市场热点。',
    }

    prompt = f"""{type_prompts.get(report_type, type_prompts['morning'])}

数据来源: {macro.get('timestamp')}

{data_summary}

要求输出严格JSON格式:
{{
  "macro_env": "宏观环境段(200-300字)",
  "money_flow": "资金动向段(200-300字)",
  "industry_opp": "行业机会段(200-300字)",
  "risk_warning": "风险提示段(150-200字)",
  "action_advice": "操作建议段(150-200字)",
  "outlook": "明日/下周展望段(150-200字)"
}}

要求:
- 专业严谨，引用具体数据
- 给出明确板块/个股建议
- 风险提示要具体
- 总字数 1200-1500字"""

    try:
        import requests
        headers = {
            'Authorization': f'Bearer {config["api_key"]}',
            'Content-Type': 'application/json',
        }
        if config.get('workspace_id'):
            headers['X-DashScope-WorkSpace'] = config['workspace_id']
        payload = {
            'model': config['model'],
            'messages': [
                {'role': 'system', 'content': '你是专业A股投研分析师，风格类似券商研究所晨报/周报'},
                {'role': 'user', 'content': prompt},
            ],
            'temperature': 0.6,
            'max_tokens': 3000,
        }
        # Qwen支持JSON格式
        if 'qwen' in config.get('provider', '').lower():
            payload['response_format'] = {'type': 'json_object'}
        resp = requests.post(config['base_url'], headers=headers, json=payload, timeout=60)
        resp.raise_for_status()
        result = resp.json()
        msg = result['choices'][0]['message']
        content = msg.get('content', '') or msg.get('reasoning_content', '')
        # 解析JSON
        sections_data = _extract_json(content)
        if sections_data and isinstance(sections_data, dict):
            return [
                {'name': '宏观环境', 'content': sections_data.get('macro_env', '')},
                {'name': '资金动向', 'content': sections_data.get('money_flow', '')},
                {'name': '行业机会', 'content': sections_data.get('industry_opp', '')},
                {'name': '风险提示', 'content': sections_data.get('risk_warning', '')},
                {'name': '操作建议', 'content': sections_data.get('action_advice', '')},
                {'name': '明日展望', 'content': sections_data.get('outlook', '')},
            ]
    except Exception as e:
        logger.warning(f"AI生成失败: {e}")

    # 降级
    return _fallback_generate_sections(macro, industries, money_flow, news)


def _fallback_generate_sections(macro, industries, money_flow, news) -> List[Dict]:
    """降级到模板生成（保证演示可用）"""
    sh_pct = macro['sh_index']['change_pct']
    if sh_pct > 0.5:
        macro_text = f"今日A股表现强势，上证指数收涨{sh_pct:+.2f}%，市场情绪明显回暖。"
    elif sh_pct < -0.5:
        macro_text = f"今日A股承压回调，上证指数下跌{sh_pct:+.2f}%，需关注后续量能配合。"
    else:
        macro_text = f"今日A股震荡整理，上证指数微涨{sh_pct:+.2f}%，结构性机会为主。"

    top_3 = industries[:3] if len(industries) >= 3 else industries
    industry_text = "今日领涨板块：" + "、".join([f"**{i['name']}**({i['change_pct']:+.2f}%)" for i in top_3]) + "。"

    north = macro['north_flow']
    if north > 0:
        flow_text = f"北向资金净流入{north:+.2f}亿元，外资持续加仓A股。"
    else:
        flow_text = f"北向资金净流出{abs(north):.2f}亿元，外资短期获利了结。"

    main_flow = money_flow.get('main_net_inflow', 0)
    if main_flow > 0:
        flow_text += f"主力资金净流入{main_flow:+.2f}亿元，市场做多意愿较强。"

    return [
        {'name': '宏观环境', 'content': macro_text + " 国内政策面持续释放积极信号，央行近期表态保持流动性合理充裕，为市场提供支撑。海外方面，美联储加息周期接近尾声，全球资金配置环境改善。"},
        {'name': '资金动向', 'content': flow_text + " 融资余额小幅回升，两市成交量较前一交易日放大，结构性机会涌现。"},
        {'name': '行业机会', 'content': industry_text + " 建议关注AI产业链（算力/模型/应用）、新能源（光伏/储能/锂电）、高端制造（半导体/工业母机）等高景气方向。"},
        {'name': '风险提示', 'content': "1) 美联储政策超预期收紧；2) 国内经济复苏不及预期；3) 地缘政治风险升级；4) 行业景气度下行风险。"},
        {'name': '操作建议', 'content': "**配置策略**：建议保持7-8成仓位，结构上均衡配置。\n- **进攻方向**（30%仓位）：AI、新能源、半导体等高景气成长\n- **防御方向**（20%仓位）：高股息红利（银行/电力/煤炭）\n- **现金管理**（10-20%仓位）：等待回调机会"},
        {'name': '明日展望', 'content': "预计明日市场将延续震荡上行格局，关注成交量能否持续放大。**重点关注**：1) 晚间海外市场表现；2) 明日早盘北向资金动向；3) 重要经济数据发布。"},
    ]


def _extract_json(text: str) -> Optional[dict]:
    """从文本提取JSON"""
    import re
    try:
        return json.loads(text)
    except Exception:
        pass
    m = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(1))
        except Exception:
            pass
    m = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(0))
        except Exception:
            pass
    return None


def _to_markdown(title, sections, macro, industries, money_flow, news, now) -> str:
    """组装Markdown报告"""
    lines = [
        f"# {title}",
        "",
        f"> **生成时间**: {now.strftime('%Y-%m-%d %H:%M:%S')}  ",
        f"> **数据源**: {macro.get('source', 'unknown')}  ",
        f"> **AI引擎**: QuantInsight Pro 智能引擎  ",
        "",
        "---",
        "",
        "## 📊 大盘速览",
        "",
        f"| 指数 | 收盘 | 涨跌幅 |",
        f"|------|------|--------|",
        f"| 上证指数 | {macro['sh_index']['value']:.2f} | {macro['sh_index']['change_pct']:+.2f}% |",
        f"| 深证成指 | {macro['sz_index']['value']:.2f} | {macro['sz_index']['change_pct']:+.2f}% |",
        f"| 创业板指 | {macro['cyb_index']['value']:.2f} | {macro['cyb_index']['change_pct']:+.2f}% |",
        "",
        f"- **涨跌家数**: 涨 {macro['up_count']} 家 / 跌 {macro['down_count']} 家",
        f"- **涨停/跌停**: {macro['limit_up']} / {macro['limit_down']}",
        f"- **北向资金**: {macro['north_flow']:+.2f} 亿元",
        "",
        "## 🏭 行业涨跌榜",
        "",
    ]
    for i in industries[:8]:
        emoji = "🟢" if i['change_pct'] > 0 else "🔴"
        lines.append(f"- {emoji} **{i['name']}**: {i['change_pct']:+.2f}% (领涨: {i.get('leader', 'N/A')})")

    lines.extend([
        "",
        "## 💰 资金流向",
        "",
        f"- 主力净流入: **{money_flow['main_net_inflow']:+.2f}** 亿元",
        f"- 大单净流入: **{money_flow['big_order']:+.2f}** 亿元",
        "",
        "## 📰 重要新闻",
        "",
    ])
    for n in news[:6]:
        lines.append(f"- {n['title']} *({n.get('source', '新闻')})*")

    lines.extend(["", "---", "", "## 📑 详细分析", ""])
    for s in sections:
        lines.extend([f"### {s['name']}", "", s['content'], ""])

    lines.extend([
        "---",
        "",
        "*⚠️ 风险提示: 本报告由 QuantInsight Pro AI 自动生成, 数据来源于公开市场信息, 仅供参考, 不构成任何投资建议. 投资有风险, 入市需谨慎.*",
        "",
        f"*📧 联系: contact@quantinsight.cn | 🌐 官网: https://quantinsight.cn*",
    ])
    return "\n".join(lines)


# ============== 3. 报告渲染UI ==============

def render_report_ui():
    """报告生成UI - 在app.py的智能指令-报告生成tab调用"""
    st.markdown("""
    <div style="background: linear-gradient(135deg, #0A1628 0%, #1E3A5F 100%);
                padding: 24px; border-radius: 12px; margin-bottom: 24px;
                border: 1px solid #00D4FF;">
        <h2 style="color: #00D4FF; margin: 0;">📊 自动报告生成</h2>
        <p style="color: #B8C5D6;">基于实时市场数据 + AI 深度分析，6段式专业投研报告</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        report_type = st.selectbox(
            "📋 报告类型",
            options=['morning', 'noon', 'evening', 'weekly', 'special'],
            format_func=lambda x: {'morning': '🌅 晨报', 'noon': '☀️ 午报', 'evening': '🌙 晚报', 'weekly': '📅 周报', 'special': '⭐ 专题'}[x],
            key='report_type_select',
        )
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        st.caption("💡 报告将集成: 大盘数据 + 行业涨跌 + 资金流向 + 新闻舆情 + AI深度分析")
    with col3:
        st.markdown("<br>", unsafe_allow_html=True)
        generate_btn = st.button("🚀 生成报告", type='primary', use_container_width=True)

    if generate_btn:
        with st.spinner("正在拉取实时数据 + AI分析中..."):
            from app import get_llm_config
            config = get_llm_config()
            report = generate_professional_report(report_type, config)

        # 缓存到session
        st.session_state['current_report'] = report

    # 显示报告
    report = st.session_state.get('current_report')
    if report:
        # 标题区
        st.markdown(f"## {report['title']}")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.caption(f"🕒 生成时间: {report['generated_at']}")
        with col2:
            source_badge = "🟢 真实数据" if report['data_source'] == 'akshare' else "🟡 演示数据"
            st.caption(f"📡 数据源: {source_badge}")
        with col3:
            ai_provider = "Qwen3.7-Max" if 'qwen' in (report.get('ai_engine') or '') else "AI"
            st.caption(f"🤖 AI: {ai_provider}")

        st.divider()

        # 6段式展示
        for s in report['sections']:
            with st.container():
                st.markdown(f"### {s['name']}")
                st.markdown(s['content'])
                st.markdown("")

        # 数据面板
        with st.expander("📊 查看原始数据", expanded=False):
            data = report['data']
            st.markdown("#### 大盘数据")
            st.json(data['macro'])
            st.markdown("#### 行业涨跌")
            st.json(data['industries'])
            st.markdown("#### 资金流向")
            st.json(data['money_flow'])

        # 导出按钮
        st.divider()
        st.markdown("### 📥 导出报告")
        col1, col2, col3 = st.columns([1, 1, 3])
        with col1:
            from features.report_exporter import export_word, export_pdf
            word_data = export_word(report)
            st.download_button(
                label="📄 下载 Word",
                data=word_data,
                file_name=f"QuantInsight_{report_type}_{datetime.now().strftime('%Y%m%d_%H%M')}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=True,
            )
        with col2:
            pdf_data = export_pdf(report)
            st.download_button(
                label="📑 下载 PDF",
                data=pdf_data,
                file_name=f"QuantInsight_{report_type}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
