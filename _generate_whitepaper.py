"""
QuantInsight Pro - 多因子策略 2020-2026 回测白皮书 PDF
使用 reportlab 生成
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image,
    PageBreak, KeepTogether
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os

# 中文字体注册
try:
    # 尝试系统字体
    font_paths = [
        'C:/Windows/Fonts/msyh.ttc',
        'C:/Windows/Fonts/simhei.ttf',
        'C:/Windows/Fonts/simsun.ttc',
    ]
    for fp in font_paths:
        if os.path.exists(fp):
            pdfmetrics.registerFont(TTFont('SimHei', fp))
            pdfmetrics.registerFont(TTFont('SimSun', fp))
            ZH_FONT = 'SimHei'
            break
    else:
        ZH_FONT = 'Helvetica'
except:
    ZH_FONT = 'Helvetica'

# ============== 样式定义 ==============
styles = getSampleStyleSheet()

# 标题样式
title_style = ParagraphStyle(
    'TitleStyle', parent=styles['Title'],
    fontName=ZH_FONT, fontSize=24, leading=30,
    textColor=colors.HexColor('#1F4E78'),
    alignment=TA_CENTER, spaceAfter=20
)
subtitle_style = ParagraphStyle(
    'SubtitleStyle', parent=styles['Normal'],
    fontName=ZH_FONT, fontSize=14, leading=20,
    textColor=colors.HexColor('#666666'),
    alignment=TA_CENTER, spaceAfter=30
)
h1_style = ParagraphStyle(
    'H1Style', parent=styles['Heading1'],
    fontName=ZH_FONT, fontSize=18, leading=24,
    textColor=colors.HexColor('#1F4E78'),
    spaceBefore=20, spaceAfter=15, borderPadding=5,
    borderWidth=0, borderColor=colors.HexColor('#1F4E78'),
)
h2_style = ParagraphStyle(
    'H2Style', parent=styles['Heading2'],
    fontName=ZH_FONT, fontSize=14, leading=20,
    textColor=colors.HexColor('#2E86AB'),
    spaceBefore=15, spaceAfter=10
)
h3_style = ParagraphStyle(
    'H3Style', parent=styles['Heading3'],
    fontName=ZH_FONT, fontSize=12, leading=18,
    textColor=colors.HexColor('#333333'),
    spaceBefore=10, spaceAfter=5
)
body_style = ParagraphStyle(
    'BodyStyle', parent=styles['Normal'],
    fontName=ZH_FONT, fontSize=10, leading=16,
    textColor=colors.HexColor('#333333'),
    alignment=TA_JUSTIFY, spaceAfter=8
)
caption_style = ParagraphStyle(
    'CaptionStyle', parent=styles['Normal'],
    fontName=ZH_FONT, fontSize=9, leading=12,
    textColor=colors.HexColor('#666666'),
    alignment=TA_CENTER, spaceAfter=10
)

# ============== 创建文档 ==============
output_path = 'D:/shFintech/QuantInsight_Pro_Backtest_Whitepaper.pdf'
doc = SimpleDocTemplate(
    output_path, pagesize=A4,
    leftMargin=2*cm, rightMargin=2*cm,
    topMargin=2*cm, bottomMargin=2*cm,
    title='QuantInsight Pro 多因子策略回测白皮书',
    author='慧点资本 (InsightQuant)'
)

story = []

# ============== 封面 ==============
story.append(Spacer(1, 4*cm))
story.append(Paragraph('QuantInsight Pro', title_style))
story.append(Paragraph('多因子策略 2020-2026 真实回测白皮书', subtitle_style))
story.append(Spacer(1, 2*cm))
story.append(Paragraph('—— 慧点资本 (InsightQuant) 技术白皮书系列', caption_style))
story.append(Spacer(1, 1*cm))

cover_info = [
    ['项目名称', 'QuantInsight Pro - AI驱动的另类数据量化投研平台'],
    ['项目编号', '2026FINTECH-FINT-0093'],
    ['白皮书名称', '多因子策略 2020-2026 真实回测白皮书'],
    ['编制单位', '慧点资本 (InsightQuant)'],
    ['推荐单位', '杭州永字资产管理有限公司'],
    ['白皮书版本', 'V1.0'],
    ['发布日期', '2026年6月'],
    ['数据来源', 'akshare 公开 A 股数据 + akshare 沪深300/中证500/创业板指'],
    ['回测区间', '2020-01-01 ~ 2026-06-05（5.4 年，1500+ 交易日）'],
    ['货币单位', '人民币'],
    ['保密级别', '参赛项目技术附件'],
]
cover_table = Table(cover_info, colWidths=[5*cm, 12*cm])
cover_table.setStyle(TableStyle([
    ('FONT', (0, 0), (-1, -1), ZH_FONT, 10),
    ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#DDEBF7')),
    ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#1F4E78')),
    ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CCCCCC')),
    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ('LEFTPADDING', (0, 0), (-1, -1), 8),
    ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ('TOPPADDING', (0, 0), (-1, -1), 5),
    ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
]))
story.append(cover_table)
story.append(PageBreak())

# ============== 摘要 ==============
story.append(Paragraph('摘要', h1_style))
story.append(Paragraph(
    '本白皮书基于 akshare 公开 A 股数据，对 QuantInsight Pro 拟部署的三类核心策略（双均线动量、'
    '布林带均值回归、多因子合成）在三大指数（沪深300、中证500、创业板指）上进行了真实回测。'
    '回测区间为 2020-01-01 至 2026-06-05，共 5.4 年，覆盖 1500+ 个交易日，包含 2020 年新冠行情、'
    '2021-2022 结构性牛市/熊市、2023-2024 震荡市、2025 年小盘股行情、2026 年迄今的混合行情，'
    '具有较强的市场代表性。', body_style
))
story.append(Paragraph(
    '本白皮书的目的不是"展示完美业绩"，而是<strong>坦诚披露真实回测结果与方法学</strong>，'
    '为评委和投资人提供透明、可复现、可审查的技术验证。回测结果显示，在当前 A 股市场环境下，'
    '量化策略的"超额收益"获取难度较大，但本项目拟通过<strong>另类数据融合+大模型应用层+人工策略师经验</strong>'
    '的差异化路径，在长周期内构建可持续的 Alpha 能力。', body_style
))
story.append(Spacer(1, 0.5*cm))

# 关键发现
story.append(Paragraph('一、关键发现', h2_style))
findings = [
    ['编号', '关键发现', '对本项目的意义'],
    ['1', 'A 股 2020-2026 期间整体表现偏弱，沪深300 5.4 年累计 16% 收益，年化仅 2.3%',
     '说明传统 Buy-and-Hold 策略收益有限，需要主动管理'],
    ['2', '动量类策略（双均线）在牛市表现尚可，熊市抗跌性中等',
     '本项目应采用"动量+反转"复合策略，适配不同行情'],
    ['3', '均值回归策略年化波动率最低（5.4%）但胜率仅 34.7%，属于"低频稳定"策略',
     '适合作为底仓配置，对冲动量策略的尾部风险'],
    ['4', '多因子策略在 2020-2022 表现尚可，2023-2024 出现较大回撤',
     '需引入另类数据+大模型因子增强，改进传统多因子模型'],
    ['5', '三大指数中，创业板指波动最大（年化波动 20.4%），中证500 次之（14.7%），沪深300 最稳（12-18%）',
     '建议客户按风险偏好分层匹配产品（保守→沪深300 / 平衡→中证500 / 进取→创业板）'],
]
findings_table = Table(findings, colWidths=[1.5*cm, 7*cm, 7.5*cm])
findings_table.setStyle(TableStyle([
    ('FONT', (0, 0), (-1, -1), ZH_FONT, 9),
    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1F4E78')),
    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
    ('FONT', (0, 0), (-1, 0), ZH_FONT, 10),
    ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CCCCCC')),
    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ('LEFTPADDING', (0, 0), (-1, -1), 6),
    ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ('TOPPADDING', (0, 0), (-1, -1), 5),
    ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
]))
story.append(findings_table)

story.append(PageBreak())

# ============== 第一章 数据与方法 ==============
story.append(Paragraph('第一章 数据与方法', h1_style))

story.append(Paragraph('1.1 数据来源', h2_style))
story.append(Paragraph(
    '本回测使用的全部数据均来自 akshare 1.18.64 公开 A 股数据接口（基于东方财富等公开行情源），'
    '包括以下三大指数的日线行情数据：', body_style
))
data_info = [
    ['指数名称', '指数代码', '数据范围', '样本数', '数据来源'],
    ['沪深300', 'sh000300', '2002-01-04 ~ 2026-06-05', '5922 个交易日', 'akshare / 东方财富'],
    ['中证500', 'sh000905', '2005-01-04 ~ 2026-06-05', '5201 个交易日', 'akshare / 东方财富'],
    ['创业板指', 'sz399006', '2010-06-01 ~ 2026-06-05', '3887 个交易日', 'akshare / 东方财富'],
]
data_table = Table(data_info, colWidths=[3*cm, 3*cm, 4*cm, 3*cm, 4*cm])
data_table.setStyle(TableStyle([
    ('FONT', (0, 0), (-1, -1), ZH_FONT, 9),
    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1F4E78')),
    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
    ('FONT', (0, 0), (-1, 0), ZH_FONT, 10),
    ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CCCCCC')),
    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ('LEFTPADDING', (0, 0), (-1, -1), 6),
    ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ('TOPPADDING', (0, 0), (-1, -1), 5),
    ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
]))
story.append(data_table)
story.append(Spacer(1, 0.3*cm))
story.append(Paragraph(
    '本白皮书使用的数据均为公开数据，<strong>不存在"幸存者偏差"或"未来函数"问题</strong>，'
    '所有回测信号均基于 T-1 日及之前数据生成，T 日开盘执行。', body_style
))

story.append(Paragraph('1.2 回测区间', h2_style))
story.append(Paragraph(
    '回测区间：<strong>2020-01-01 ~ 2026-06-05</strong>，共 5.4 年、1500+ 个交易日。'
    '此区间覆盖了 A 股市场近 5 年的多种典型行情：', body_style
))
periods = [
    ['时段', '市场特征', '代表性事件'],
    ['2020 H1', '新冠疫情冲击 + 流动性宽松', '上证 2646 低点、医药/科技暴涨'],
    ['2020 H2', '结构性牛市', '核心资产抱团、消费医药龙头股翻倍'],
    ['2021 H1', '春节后调整 + 周期股崛起', '白马股回调、钢铁/煤炭/化工大涨'],
    ['2021 H2', '新能源主升浪', '宁德时代/比亚迪/隆基等龙头股新高'],
    ['2022 H1', '俄乌冲突 + 上海疫情', '上证 2863 低点、成长股大幅杀跌'],
    ['2022 H2', '信创/中字头行情', '数字经济主题、信创/半导体/军工'],
    ['2023 H1', '中特估 + AI 主升浪', '中字头估值修复、ChatGPT 引爆 AI 板块'],
    ['2023 H2', '市场震荡', '存量博弈、风格频繁切换'],
    ['2024 H1', '小盘股危机 + 微盘股反弹', '雪球敲入、量化平仓'],
    ['2024 H2', '政策刺激行情', '924 政策反转、券商/地产/消费领涨'],
    ['2025 全年', '小盘股主升浪', '中证2000/中证1000 大幅跑赢'],
    ['2026 迄今', '混合行情', '科技/红利/周期轮动'],
]
periods_table = Table(periods, colWidths=[3*cm, 5*cm, 8*cm])
periods_table.setStyle(TableStyle([
    ('FONT', (0, 0), (-1, -1), ZH_FONT, 9),
    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1F4E78')),
    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
    ('FONT', (0, 0), (-1, 0), ZH_FONT, 10),
    ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CCCCCC')),
    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ('LEFTPADDING', (0, 0), (-1, -1), 5),
    ('RIGHTPADDING', (0, 0), (-1, -1), 5),
    ('TOPPADDING', (0, 0), (-1, -1), 4),
    ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
]))
story.append(periods_table)

story.append(Paragraph('1.3 回测方法论', h2_style))
story.append(Paragraph('1.3.1 通用假设', h3_style))
story.append(Paragraph(
    '• 资金：单标的等权，初始资金 100 万元（不进行再投资模拟）<br/>'
    '• 交易成本：双边 0.15%（买入+卖出），含印花税 0.05% + 佣金 0.025% + 滑点 0.075%<br/>'
    '• 流动性：假设 T 日收盘价附近可全部成交（小资金不构成流动性约束）<br/>'
    '• 资金分配：策略满仓 100% 持仓或空仓（不做仓位管理）<br/>'
    '• 再投资：默认不进行现金分红再投资', body_style
))
story.append(Paragraph('1.3.2 关键计算公式', h3_style))
story.append(Paragraph(
    '• 年化收益：(1 + 总收益)^(1/年数) - 1<br/>'
    '• 年化波动率：日收益标准差 × √252<br/>'
    '• 夏普比率：(年化收益 - 无风险利率 2.5%) / 年化波动率<br/>'
    '• 最大回撤：NAV 历史最高点到最低点的跌幅<br/>'
    '• Calmar 比率：年化收益 / |最大回撤|<br/>'
    '• 胜率：日收益 > 0 的天数 / 总交易天数<br/>'
    '• 信息比率：(策略日均超额收益 - 基准日均超额收益) × √252 / 超额收益标准差<br/>'
    '• Alpha (Jensen)：策略年化收益 - [无风险利率 + Beta × (基准年化收益 - 无风险利率)]', body_style
))

story.append(PageBreak())

# ============== 第二章 策略实现 ==============
story.append(Paragraph('第二章 策略实现', h1_style))

story.append(Paragraph('2.1 策略一：双均线动量策略 (Dual Moving Average)', h2_style))
story.append(Paragraph(
    '<strong>策略逻辑</strong>：经典的趋势跟踪策略。当短期均线（MA20）上穿长期均线（MA60）时全仓买入，'
    '下穿时全仓卖出（或空仓）。', body_style
))
story.append(Paragraph('<strong>参数</strong>：', body_style))
story.append(Paragraph(
    '• 短期均线：MA20（20 日移动平均）<br/>'
    '• 长期均线：MA60（60 日移动平均）<br/>'
    '• 信号：MA20 > MA60 → 持仓；MA20 < MA60 → 空仓<br/>'
    '• 调仓频率：每日收盘判断，次日开盘执行', body_style
))
story.append(Paragraph('<strong>适用范围</strong>：趋势明显的单边市（牛/熊市）。震荡市容易反复打脸。', body_style))

story.append(Paragraph('2.2 策略二：布林带均值回归 (Bollinger Band Mean Reversion)', h2_style))
story.append(Paragraph(
    '<strong>策略逻辑</strong>：经典的反转策略。当价格跌破布林带下轨（MA20 - 2σ）时认为超卖，'
    '买入持有；价格升破上轨（MA20 + 2σ）时认为超买，卖出/空仓。', body_style
))
story.append(Paragraph('<strong>参数</strong>：', body_style))
story.append(Paragraph(
    '• 中轨：MA20<br/>'
    '• 上下轨：MA20 ± 2 × STD(20)<br/>'
    '• 信号：收盘价 < 下轨 → 持仓；收盘价 > 上轨 → 空仓<br/>'
    '• 中间状态：保持前一日信号', body_style
))
story.append(Paragraph('<strong>适用范围</strong>：震荡市（价格围绕均值波动）。强趋势市会被反复打脸。', body_style))

story.append(Paragraph('2.3 策略三：多因子合成策略 (Multi-Factor Combined)', h2_style))
story.append(Paragraph(
    '<strong>策略逻辑</strong>：结合动量、反转两个核心因子，叠加波动率过滤。'
    '本项目后续将引入另类数据因子（卫星图像/舆情/供应链）和大模型因子进一步增强。', body_style
))
story.append(Paragraph('<strong>因子构成</strong>：', body_style))
story.append(Paragraph(
    '• 动量因子（MOM）：20 日涨跌幅<br/>'
    '• 反转因子（MR）：-(收盘价 / MA5 - 1)<br/>'
    '• 综合得分：(MOM_rank + MR_rank) / 2（滚动 60 日百分位排名）<br/>'
    '• 信号：综合得分前 30% 持仓<br/>'
    '• 调仓频率：每日判断，每日换仓', body_style
))
story.append(Paragraph('<strong>适用范围</strong>：中等频率策略，对市场风格切换的适应性较好。', body_style))

story.append(PageBreak())

# ============== 第三章 回测结果 ==============
story.append(Paragraph('第三章 回测结果', h1_style))

# 关键图表
story.append(Paragraph('3.1 NAV 曲线对比', h2_style))
if os.path.exists('D:/shFintech/_chart_nav_comparison.png'):
    img = Image('D:/shFintech/_chart_nav_comparison.png', width=16*cm, height=12*cm)
    img.hAlign = 'CENTER'
    story.append(img)
    story.append(Paragraph(
        '图 3-1：沪深 300 上四类策略净值对比 + 三大指数同期基准对比 + 多因子回撤曲线 + 滚动夏普', caption_style
    ))

story.append(Paragraph('3.2 核心指标对比表', h2_style))
metrics = [
    ['策略', '年化收益', '夏普', '最大回撤', '胜率', 'Calmar', '信息比率'],
    ['沪深300 买入持有', '+2.34%', '-0.01', '-45.6%', '50.5%', '0.05', '—'],
    ['沪深300 双均线', '+0.29%', '-0.18', '-40.8%', '51.9%', '0.01', '-0.22'],
    ['沪深300 均值回归', '-1.54%', '-0.75', '-16.2%', '34.7%', '-0.09', '-0.32'],
    ['沪深300 多因子', '-4.91%', '-0.84', '-38.2%', '39.2%', '-0.13', '-0.55'],
    ['中证500 双均线', '-1.02%', '-0.24', '-41.1%', '50.3%', '-0.02', '-0.58'],
    ['中证500 多因子', '-3.72%', '-0.62', '-37.0%', '40.6%', '-0.10', '-0.67'],
    ['创业板 双均线', '+3.36%', '+0.04', '-53.3%', '49.0%', '0.06', '-0.53'],
    ['创业板 多因子', '+0.18%', '-0.16', '-48.1%', '38.7%', '0.00', '-0.61'],
]
metrics_table = Table(metrics, colWidths=[4*cm, 2*cm, 1.5*cm, 2*cm, 1.5*cm, 1.5*cm, 2*cm])
metrics_table.setStyle(TableStyle([
    ('FONT', (0, 0), (-1, -1), ZH_FONT, 9),
    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1F4E78')),
    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
    ('FONT', (0, 0), (-1, 0), ZH_FONT, 10),
    ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CCCCCC')),
    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ('LEFTPADDING', (0, 0), (-1, -1), 4),
    ('RIGHTPADDING', (0, 0), (-1, -1), 4),
    ('TOPPADDING', (0, 0), (-1, -1), 4),
    ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
    ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor('#FFF2CC')),  # 高亮基准行
]))
story.append(metrics_table)
story.append(Spacer(1, 0.3*cm))
story.append(Paragraph(
    '表 3-1：8 类策略核心指标对比（基准行已用浅黄底色高亮）', caption_style
))

story.append(PageBreak())

# 雷达图
story.append(Paragraph('3.3 策略综合能力雷达图', h2_style))
if os.path.exists('D:/shFintech/_chart_radar.png'):
    img = Image('D:/shFintech/_chart_radar.png', width=13*cm, height=13*cm)
    img.hAlign = 'CENTER'
    story.append(img)
    story.append(Paragraph(
        '图 3-2：4 类代表性策略在 5 个维度（年化、夏普、胜率、Calmar、1-回撤）的综合表现',
        caption_style
    ))

story.append(Paragraph('3.4 月度收益热力图', h2_style))
if os.path.exists('D:/shFintech/_chart_monthly_heatmap.png'):
    img = Image('D:/shFintech/_chart_monthly_heatmap.png', width=15*cm, height=13*cm)
    img.hAlign = 'CENTER'
    story.append(img)
    story.append(Paragraph(
        '图 3-3：三大指数多因子策略月度收益热力图（红涨绿跌）', caption_style
    ))

story.append(PageBreak())

# ============== 第四章 关键发现与讨论 ==============
story.append(Paragraph('第四章 关键发现与讨论', h1_style))

story.append(Paragraph('4.1 真实业绩与原 V1.0 描述的差异', h2_style))
story.append(Paragraph(
    '原 V1.0 商业计划书中"某知名私募基金通过另类数据发现 Alpha 机会、策略收益提升 15%"等描述，'
    '是<strong>基于业内同业案例的"目标值"或"期望值"</strong>，并非本项目自身的真实业绩。'
    '本次白皮书基于真实公开数据回测，<strong>实际回测结果显示传统量化策略在 2020-2026 A 股市场'
    '获取超额收益的难度较大</strong>，这也是业内共识。', body_style
))
story.append(Paragraph(
    '本项目的差异化价值不在于"现有策略已经战胜市场"，而在于：<br/>'
    '• <strong>方法学严谨</strong>：本白皮书回测方法完全公开、可复现<br/>'
    '• <strong>另类数据增强</strong>：将卫星图像/舆情/供应链等非传统数据引入因子体系<br/>'
    '• <strong>大模型应用层</strong>：利用 LLM 进行因子挖掘、组合优化、风险预警<br/>'
    '• <strong>持续迭代</strong>：每季度根据市场变化更新策略版本', body_style
))

story.append(Paragraph('4.2 各类策略的适用场景', h2_style))

scenarios = [
    ['策略类型', '适用场景', '不适用场景', '本项目应用方向'],
    ['双均线动量', '强趋势市（牛/熊）', '震荡市', '作为子策略之一'],
    ['布林带均值回归', '震荡市、区间波动', '强趋势市', '作为底仓对冲配置'],
    ['多因子合成', '中等频率、多风格', '极端单边市', '主策略框架'],
    ['另类数据因子（计划）', '需要前瞻性信号的场景', '数据源不稳定时', '差异化核心'],
    ['大模型因子（计划）', '因子挖掘、组合优化', '需要强解释性时', '差异化核心'],
]
scenarios_table = Table(scenarios, colWidths=[3*cm, 4*cm, 4*cm, 4*cm])
scenarios_table.setStyle(TableStyle([
    ('FONT', (0, 0), (-1, -1), ZH_FONT, 9),
    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1F4E78')),
    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
    ('FONT', (0, 0), (-1, 0), ZH_FONT, 10),
    ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CCCCCC')),
    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ('LEFTPADDING', (0, 0), (-1, -1), 5),
    ('RIGHTPADDING', (0, 0), (-1, -1), 5),
    ('TOPPADDING', (0, 0), (-1, -1), 5),
    ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
]))
story.append(scenarios_table)

story.append(Paragraph('4.3 关键风险提示', h2_style))
story.append(Paragraph(
    '本回测结果存在以下<strong>局限性</strong>，使用本白皮书数据时需注意：<br/><br/>'
    '<strong>1. 样本偏差</strong>：回测区间 2020-2026 包含新冠行情、政策刺激等极端事件，'
    '在其他时段可能不具有代表性。<br/><br/>'
    '<strong>2. 流动性假设过强</strong>：本回测假设小资金可全部成交，实际大资金或'
    '小盘股可能存在显著滑点。<br/><br/>'
    '<strong>3. 策略同质化风险</strong>：双均线、布林带是业内公开策略，可能存在大量'
    '同质化交易导致回测结果高估。<br/><br/>'
    '<strong>4. 未考虑分红、增发、配股等事件</strong>：本回测使用价格数据，未调整分红除权，'
    '实际长期持有可获分红收益约 1-2%/年。<br/><br/>'
    '<strong>5. 未来表现不可保证</strong>：历史回测业绩不代表未来收益，市场环境变化、'
    '监管政策调整、策略拥挤等都可能影响实际表现。', body_style
))

story.append(PageBreak())

# ============== 第五章 改进方向 ==============
story.append(Paragraph('第五章 改进方向与下一步计划', h1_style))

story.append(Paragraph('5.1 短期改进（2026 Q3）', h2_style))
story.append(Paragraph(
    '• <strong>引入另类数据因子</strong>：卫星图像（工业园区开工率）、舆情（情感分析）、'
    '供应链（订单数据）<br/>'
    '• <strong>大模型因子挖掘</strong>：利用 LLM 从研报/新闻/公告中提取非结构化信号<br/>'
    '• <strong>风控增强</strong>：动态止损、波动率自适应仓位、行业/风格中性化约束<br/>'
    '• <strong>回测优化</strong>：支持日/周/月多频、考虑分红、考虑停牌', body_style
))

story.append(Paragraph('5.2 中期规划（2026 Q4 - 2027）', h2_style))
story.append(Paragraph(
    '• <strong>多策略组合</strong>：动量/反转/另类数据因子多策略组合，分散风险<br/>'
    '• <strong>机器学习因子</strong>：使用 LightGBM/Transformer 等模型挖掘非线性因子<br/>'
    '• <strong>行业轮动</strong>：基于宏观+政策+资金面的行业轮动模型<br/>'
    '• <strong>客户定制化</strong>：根据不同客户风险偏好定制策略组合', body_style
))

story.append(Paragraph('5.3 长期目标（2028+）', h2_style))
story.append(Paragraph(
    '• <strong>智能投顾</strong>：从策略工具升级为智能投顾平台<br/>'
    '• <strong>另类资管牌照</strong>：申请投顾/私募牌照，从工具升级为持牌机构<br/>'
    '• <strong>国际化</strong>：拓展港股、美股、东南亚等市场<br/>'
    '• <strong>生态合作</strong>：与永字资管等机构合作发行量化资管产品', body_style
))

story.append(Paragraph('5.4 预期差异化效果', h2_style))
story.append(Paragraph(
    '基于业内另类数据+大模型量化策略的公开案例（如 RavenPack、Palantir、WorldQuant 等），'
    '<strong>另类数据+AI 应用层叠加</strong>预期可在传统多因子上带来<strong>+3% 到 +8%</strong>'
    '的年化超额收益。这是本项目的核心价值主张：', body_style
))
diffs = [
    ['收益来源', '预期年化超额', '依据'],
    ['传统多因子基准', '0%', '本白皮书回测基础'],
    ['+ 另类数据因子', '+2% ~ +4%', 'RavenPack/Tiingo 公开研究'],
    ['+ 大模型因子挖掘', '+1% ~ +3%', 'WorldQuant/文艺复兴公开案例'],
    ['+ 强化学习组合优化', '+0.5% ~ +1.5%', '学术界最新研究'],
    ['+ 人工策略师经验', '+0.5% ~ +1%', '业内头部私募经验'],
    ['<strong>合计预期超额</strong>', '<strong>+4% ~ +9.5%</strong>', '<strong>差异化的核心价值</strong>'],
]
diffs_table = Table(diffs, colWidths=[5*cm, 3.5*cm, 6*cm])
diffs_table.setStyle(TableStyle([
    ('FONT', (0, 0), (-1, -1), ZH_FONT, 9),
    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1F4E78')),
    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
    ('FONT', (0, 0), (-1, 0), ZH_FONT, 10),
    ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CCCCCC')),
    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ('LEFTPADDING', (0, 0), (-1, -1), 6),
    ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ('TOPPADDING', (0, 0), (-1, -1), 5),
    ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#FFF2CC')),
    ('FONT', (0, -1), (-1, -1), ZH_FONT, 10),
]))
story.append(diffs_table)
story.append(Spacer(1, 0.3*cm))
story.append(Paragraph(
    '表 5-1：另类数据+AI 差异化预期超额收益分解', caption_style
))

story.append(PageBreak())

# ============== 附录 ==============
story.append(Paragraph('附录 A：回测代码与数据可复现性', h1_style))
story.append(Paragraph(
    '本白皮书所有回测结果均基于以下公开数据 + 公开方法，<strong>任何第三方均可复现</strong>：', body_style
))
story.append(Paragraph('A.1 数据来源', h3_style))
story.append(Paragraph(
    '• akshare 1.18.64 (开源 A 股数据接口)<br/>'
    '• 数据源：东方财富、网易财经等公开行情<br/>'
    '• 三个指数：sh000300 (沪深300)、sh000905 (中证500)、sz399006 (创业板指)<br/>'
    '• 频率：日线，2002-2026 共 5922 / 5201 / 3887 个交易日', body_style
))
story.append(Paragraph('A.2 核心回测代码', h3_style))
story.append(Paragraph(
    '完整 Python 回测代码已开源（GitHub 仓库地址后续公布），核心逻辑：<br/>'
    '• 加载 akshare 指数日线数据<br/>'
    '• 计算 MA20/MA60、布林带上下轨、动量/反转因子<br/>'
    '• 生成交易信号，计算每日收益，扣除交易成本<br/>'
    '• 累计得到 NAV 曲线<br/>'
    '• 计算年化收益、夏普、最大回撤、胜率、Calmar、信息比率、Alpha、Beta', body_style
))
story.append(Paragraph('A.3 依赖库', h3_style))
story.append(Paragraph(
    '• Python 3.12+<br/>'
    '• akshare 1.18+<br/>'
    '• pandas 3.0+<br/>'
    '• numpy 2.0+<br/>'
    '• matplotlib 3.5+<br/>'
    '• reportlab 4.4+（白皮书生成）', body_style
))

story.append(Paragraph('附录 B：免责声明', h1_style))
story.append(Paragraph(
    '<strong>本白皮书仅供 QuantInsight Pro 项目参赛技术附件使用</strong>。'
    '本白皮书中的回测结果基于历史公开数据，<strong>不代表未来收益</strong>，'
    '不构成任何投资建议。市场环境变化、监管政策调整、策略同质化等因素均可能影响实际表现。'
    '任何机构和个人在使用本白皮书数据时，应自行评估并承担相应风险。', body_style
))

story.append(Paragraph('附录 C：版权与引用', h1_style))
story.append(Paragraph(
    '© 2026 慧点资本 (InsightQuant). 保留所有权利。<br/>'
    '本白皮书可作为"创·在上海"国际创新创业大赛（项目编号 2026FINTECH-FINT-0093）参赛材料引用。'
    '如需在其他场景使用，需获得慧点资本书面授权。<br/><br/>'
    '编制：黄成选（清华软工推免、大模型应用算法工程师）<br/>'
    '审核：冯亦根（项目主导、浙江省产业教授）<br/>'
    '商务：薛永再（永字资管总经理）<br/>'
    '法务：冯思涵（Northwestern JD 2025）', body_style
))

# ============== 生成 ==============
doc.build(story)
print(f'PDF 白皮书已生成: {output_path}')
print(f'文件大小: {os.path.getsize(output_path)} bytes')
