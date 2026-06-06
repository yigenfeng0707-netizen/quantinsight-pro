"""
T12: 8 分钟路演主讲人模拟视频
- 12 场景, 每场景 40s = 8 分钟
- 模拟"主讲人"右下角剪影 + 演讲内容
"""
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib import rcParams
from matplotlib.patches import Polygon
import json

rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
rcParams['axes.unicode_minus'] = False

C = {
    'primary': '#1F4E78',
    'secondary': '#2E86AB',
    'accent': '#A23B72',
    'success': '#06A77D',
    'warning': '#F18F01',
    'danger': '#D62246',
    'bg_dark': '#0A1628',
    'bg_mid': '#1A365D',
    'bg_light': '#F5F7FA',
    'text_white': '#FFFFFF',
    'text_gray': '#CCCCCC',
}

OUT_DIR = 'D:/shFintech/_t12_frames'
os.makedirs(OUT_DIR, exist_ok=True)
W, H = 1920, 1080


def setup_ax(ax, bg=C['bg_dark']):
    ax.set_facecolor(bg)
    ax.set_xlim(0, W)
    ax.set_ylim(0, H)
    ax.axis('off')


def text(ax, x, y, t, size=40, color='white', weight='normal', ha='center', va='center'):
    ax.text(x, y, t, fontsize=size, color=color, fontweight=weight,
            ha=ha, va=va, family='SimHei')


def presenter_silhouette(ax, x, y, w, h):
    """模拟主讲人剪影 (右下角)"""
    # 头部
    head = mpatches.Circle((x + w/2, y + h - 60), 50, facecolor='#1A1A1A')
    ax.add_patch(head)
    # 肩膀/身体
    body = mpatches.FancyBboxPatch((x + 20, y), w - 40, h - 110,
                                     boxstyle='round,pad=5', facecolor='#1A1A1A')
    ax.add_patch(body)
    # 边框
    rect = mpatches.FancyBboxPatch((x, y), w, h, boxstyle='round,pad=5',
                                     facecolor='none', edgecolor=C['primary'], linewidth=2)
    ax.add_patch(rect)
    # 主讲人标签
    text(ax, x + w/2, y + 25, '主讲人: 冯亦根', size=16, color=C['text_gray'], weight='bold')


def slide_chrome(ax, slide_num, total, title, subtitle=None):
    """PPT 风格顶部 chrome"""
    # 顶部色条
    top_bar = mpatches.Rectangle((0, H - 70), W, 70, facecolor=C['primary'])
    ax.add_patch(top_bar)
    # Logo
    text(ax, 200, H - 35, 'QuantInsight Pro', size=24, color='white', weight='bold', ha='left', va='center')
    # 进度
    text(ax, W - 200, H - 35, f'{slide_num} / {total}', size=18, color=C['text_gray'], ha='right', va='center')
    # 标题
    if title:
        text(ax, W/2, H - 130, title, size=44, color='white', weight='bold', ha='center')
    if subtitle:
        text(ax, W/2, H - 200, subtitle, size=24, color=C['text_gray'], ha='center')


def add_content_box(ax, x, y, w, h, title, color=C['primary']):
    rect = mpatches.FancyBboxPatch((x, y), w, h, boxstyle='round,pad=5',
                                     facecolor='#1E293B', edgecolor=color, linewidth=2)
    ax.add_patch(rect)
    if title:
        text(ax, x + 20, y + h - 40, title, size=24, color=color, weight='bold', ha='left', va='center')


# 加载回测数据
with open('D:/shFintech/_backtest_nav.json', 'r') as f:
    nav_data = json.load(f)


TOTAL_SLIDES = 12

# ============== Slide 1: 开场 (40s) ==============
fig, ax = plt.subplots(figsize=(W/100, H/100), dpi=100)
setup_ax(ax)

# 大标题
text(ax, W/2, H/2 + 100, 'QuantInsight Pro', size=84, color='white', weight='bold')
text(ax, W/2, H/2, 'AI 驱动的另类数据量化投研平台', size=36, color=C['secondary'])
text(ax, W/2, H/2 - 80, '让量化投资更智能，让另类数据更普惠', size=26, color=C['text_gray'])

# Logo bar
text(ax, W/2, 250, '慧点资本 (InsightQuant) | 杭州永字资产管理有限公司（推荐单位）',
     size=22, color=C['accent'])
text(ax, W/2, 200, '项目编号: 2026FINTECH-FINT-0093', size=20, color=C['text_gray'])

# 比赛信息
text(ax, W/2, 130, 'Fintech@外滩 · 资管科技赛道', size=18, color=C['text_gray'])

# 主讲人
presenter_silhouette(ax, W - 350, 60, 250, 280)

# 进度条
text(ax, 100, 50, '1/12 · 开场', size=18, color=C['text_gray'], ha='left')

plt.savefig(f'{OUT_DIR}/slide_01_opening.png', dpi=100, facecolor=C['bg_dark'])
plt.close()
print('Slide 1: 开场')


# ============== Slide 2: 自我介绍 (40s) ==============
fig, ax = plt.subplots(figsize=(W/100, H/100), dpi=100)
setup_ax(ax)
slide_chrome(ax, 2, TOTAL_SLIDES, '自我介绍', 'QuantInsight Pro 项目主导 · 冯亦根')

# 个人介绍卡片
intro_rect = mpatches.FancyBboxPatch((200, 400), W - 400, 500, boxstyle='round,pad=10',
                                       facecolor='#1E293B', edgecolor=C['primary'], linewidth=3)
ax.add_patch(intro_rect)

text(ax, 400, 850, '冯亦根', size=44, color='white', weight='bold', ha='left')
text(ax, 400, 800, '项目主导 · 首席科学家', size=22, color=C['secondary'], ha='left')
text(ax, 400, 750, '浙大计算机本科 · 亚洲城市大学硕士', size=20, color=C['text_gray'], ha='left')
text(ax, 400, 705, '浙江省产业教授 · 多重专家身份', size=20, color=C['text_gray'], ha='left')

# 演讲开场白高亮
speech_rect = mpatches.FancyBboxPatch((200, 200), W - 400, 160, boxstyle='round,pad=5',
                                        facecolor='#0F172A', edgecolor=C['accent'], linewidth=2)
ax.add_patch(speech_rect)
text(ax, W/2, 290, '"各位评委好,我是 QuantInsight Pro 项目主导冯亦根。', size=20, color='white', ha='center')
text(ax, W/2, 250, '接下来 8 分钟,我将向您展示为什么 AI + 另类数据 + 量化研究', size=20, color='white', ha='center')
text(ax, W/2, 210, '将是中国资管科技未来 5 年最确定的趋势。"', size=20, color='white', ha='center')

presenter_silhouette(ax, W - 350, 60, 250, 280)
text(ax, 100, 50, '2/12 · 自我介绍', size=18, color=C['text_gray'], ha='left')
plt.savefig(f'{OUT_DIR}/slide_02_intro.png', dpi=100, facecolor=C['bg_dark'])
plt.close()
print('Slide 2: 自我介绍')


# ============== Slide 3: 行业痛点 (40s) ==============
fig, ax = plt.subplots(figsize=(W/100, H/100), dpi=100)
setup_ax(ax)
slide_chrome(ax, 3, TOTAL_SLIDES, '行业痛点', '中国资管行业三大长期痛点')

# 3 个痛点
pains = [
    ('数据门槛高', 'Wind/Choice 年费 5-30万\n中小私募难以承担', C['danger']),
    ('研究效率低', '研究员 70% 时间花在数据清洗\n而非策略创新', C['warning']),
    ('合规压力大', 'AI 输出缺乏可解释性\n监管合规风险高', C['accent']),
]

box_w = 480
gap = 60
start_x = (W - 3 * box_w - 2 * gap) / 2

for i, (title, desc, color) in enumerate(pains):
    x = start_x + i * (box_w + gap)
    y = 350
    h = 500
    rect = mpatches.FancyBboxPatch((x, y), box_w, h, boxstyle='round,pad=10',
                                    facecolor='#1E293B', edgecolor=color, linewidth=3)
    ax.add_patch(rect)
    # 编号大数字
    text(ax, x + box_w/2, y + h - 100, f'痛点 {i+1}', size=28, color=color, weight='bold', ha='center')
    text(ax, x + box_w/2, y + h - 180, title, size=36, color='white', weight='bold', ha='center')
    text(ax, x + box_w/2, y + h/2, desc, size=22, color=C['text_gray'], ha='center')

# 关键数据
text(ax, W/2, 250, '据 CFA Institute 2021 报告: 64% 机构抱怨"数据质量难以评估"', size=20, color=C['accent'])
text(ax, W/2, 200, 'WEF 2024 报告: 76% 金融机构正在试点 LLM, 其中投研占 31%', size=18, color=C['text_gray'])

presenter_silhouette(ax, W - 350, 60, 250, 280)
text(ax, 100, 50, '3/12 · 行业痛点', size=18, color=C['text_gray'], ha='left')
plt.savefig(f'{OUT_DIR}/slide_03_pain.png', dpi=100, facecolor=C['bg_dark'])
plt.close()
print('Slide 3: 行业痛点')


# ============== Slide 4: 解决方案 (40s) ==============
fig, ax = plt.subplots(figsize=(W/100, H/100), dpi=100)
setup_ax(ax)
slide_chrome(ax, 4, TOTAL_SLIDES, '我们的解决方案', 'QuantInsight Pro · 三大核心能力')

# 中心: QuantInsight Pro
center = (W/2, 540)
core_size = 200
core_circle = mpatches.Circle(center, core_size, facecolor=C['primary'], zorder=10)
ax.add_patch(core_circle)
text(ax, center[0], center[1] + 30, 'QuantInsight', size=24, color='white', weight='bold', ha='center')
text(ax, center[0], center[1] - 10, 'Pro', size=32, color='white', weight='bold', ha='center')
text(ax, center[0], center[1] - 50, '智能投研平台', size=18, color='white', ha='center')

# 三个能力分支
capabilities = [
    ('AI 智能问答', '自然语言投研分析', '10 秒生成专业报告', 300, 850, C['accent']),
    ('另类数据', '卫星+舆情+供应链', '提前 4-6 周捕捉信号', 1620, 850, C['success']),
    ('严谨回测', '多因子+严格风控', 'akshare 公开数据', 960, 240, C['warning']),
]

for name, sub, value, x, y, color in capabilities:
    # 连线
    ax.plot([center[0], x], [center[1], y], color=color, linewidth=3, alpha=0.6, zorder=1)
    # 节点
    cap_size = 100
    cap_circle = mpatches.Circle((x, y), cap_size, facecolor=color, zorder=5)
    ax.add_patch(cap_circle)
    # 名称
    text(ax, x, y + 15, name, size=22, color='white', weight='bold', ha='center')
    text(ax, x, y - 15, sub, size=14, color='white', ha='center')
    # 描述
    desc_y = y - 180 if y > center[1] else y + 180
    text(ax, x, desc_y, value, size=20, color=color, ha='center', weight='bold')

presenter_silhouette(ax, W - 350, 60, 250, 280)
text(ax, 100, 50, '4/12 · 解决方案', size=18, color=C['text_gray'], ha='left')
plt.savefig(f'{OUT_DIR}/slide_04_solution.png', dpi=100, facecolor=C['bg_dark'])
plt.close()
print('Slide 4: 解决方案')


# ============== Slide 5: 团队 (40s) ==============
fig, ax = plt.subplots(figsize=(W/100, H/100), dpi=100)
setup_ax(ax)
slide_chrome(ax, 5, TOTAL_SLIDES, '核心团队', '技术 + 资管复合背景 · 真实身份')

team = [
    ('冯亦根', '项目主导 · 首席科学家', '浙大计算机本科\n亚洲城市大学硕士\n浙江省产业教授', C['primary']),
    ('薛永再', '商务 · 战略合作', '浙大中文本科\n永字资管总经理\n3 次创业经验', C['accent']),
    ('黄成选', '技术负责人 · AI 工程师', '厦大计算机本科\n清华软工推免\n大模型应用算法工程师', C['secondary']),
    ('冯思涵', '法务 · 海外事务', 'Northwestern JD 2025\nM.S. 神经生物学\n量化脑科学交叉', C['warning']),
]

team_x = 80
team_w = 1760
team_y = 250
team_h = 600
col_w = team_w / 4 - 30

for i, (name, role, bg, color) in enumerate(team):
    x = team_x + i * (col_w + 30)
    panel = mpatches.FancyBboxPatch((x, team_y), col_w, team_h, boxstyle='round,pad=5',
                                      facecolor='#1E293B', edgecolor=color, linewidth=3)
    ax.add_patch(panel)
    # 头像
    avatar = mpatches.Circle((x + col_w/2, team_y + team_h - 80), 50, facecolor=color, alpha=0.85)
    ax.add_patch(avatar)
    text(ax, x + col_w/2, team_y + team_h - 80, name[0], size=36, color='white', weight='bold', ha='center', va='center')
    text(ax, x + col_w/2, team_y + team_h - 180, name, size=26, color='white', weight='bold', ha='center')
    text(ax, x + col_w/2, team_y + team_h - 220, role, size=16, color=color, ha='center', weight='bold')
    text(ax, x + col_w/2, team_y + 120, bg, size=14, color=C['text_gray'], ha='center')

presenter_silhouette(ax, W - 350, 60, 250, 280)
text(ax, 100, 50, '5/12 · 核心团队', size=18, color=C['text_gray'], ha='left')
plt.savefig(f'{OUT_DIR}/slide_05_team.png', dpi=100, facecolor=C['bg_dark'])
plt.close()
print('Slide 5: 团队')


# ============== Slide 6: 商业模式 (40s) ==============
fig, ax = plt.subplots(figsize=(W/100, H/100), dpi=100)
setup_ax(ax)
slide_chrome(ax, 6, TOTAL_SLIDES, '商业模式', '三档订阅 · 多元收入 · 业内基准保守预测')

# 左侧: 三档定价
pricing = [
    ('基础版', '¥20万/年', '中小型私募', '券商营业部', C['secondary']),
    ('专业版', '¥80万/年', '中型私募', '券商资管', C['primary']),
    ('企业版', '¥200万+/年', '公募基金', '银行理财子', C['accent']),
]

prc_x = 80
prc_w = 600
prc_y = 250
prc_h = 600
prc_each = prc_h / 3

for i, (name, price, t1, t2, color) in enumerate(pricing):
    y = prc_y + (2 - i) * prc_each
    rect = mpatches.FancyBboxPatch((prc_x, y), prc_w, prc_each - 20, boxstyle='round,pad=5',
                                     facecolor='#1E293B', edgecolor=color, linewidth=3)
    ax.add_patch(rect)
    text(ax, prc_x + 30, y + prc_each - 60, name, size=32, color=color, weight='bold', ha='left')
    text(ax, prc_x + 30, y + prc_each - 110, price, size=28, color='white', ha='left', weight='bold')
    text(ax, prc_x + 30, y + prc_each - 150, f'目标客户: {t1} / {t2}', size=18, color=C['text_gray'], ha='left')

# 右侧: 收入结构
add_content_box(ax, 740, 250, W - 820, 600, '收入结构 (5年累计)')

revenue_items = [
    ('订阅服务', 60, C['primary']),
    ('交易分成', 20, C['accent']),
    ('定制开发', 15, C['secondary']),
    ('数据服务', 5, C['warning']),
]

bar_y_start = 800
for i, (label, pct, color) in enumerate(revenue_items):
    y = bar_y_start - i * 110
    text(ax, 800, y, label, size=24, color='white', ha='left', weight='bold')
    text(ax, 1080, y, f'{pct}%', size=32, color=color, ha='left', weight='bold')
    bar_w = (W - 1200) * pct / 100
    bg = mpatches.Rectangle((1240, y - 25), W - 1240, 50, facecolor='#334155', alpha=0.5)
    ax.add_patch(bg)
    fg = mpatches.Rectangle((1240, y - 25), bar_w, 50, facecolor=color, alpha=0.85)
    ax.add_patch(fg)

# 底部关键指标
text(ax, W/2, 180, '单位经济: LTV/CAC = 20x  |  12月 NRR 目标 110%  |  盈亏平衡 2028年',
     size=20, color=C['success'], ha='center', weight='bold')

presenter_silhouette(ax, W - 350, 60, 250, 280)
text(ax, 100, 50, '6/12 · 商业模式', size=18, color=C['text_gray'], ha='left')
plt.savefig(f'{OUT_DIR}/slide_06_business.png', dpi=100, facecolor=C['bg_dark'])
plt.close()
print('Slide 6: 商业模式')


# ============== Slide 7: 市场分析 (40s) ==============
fig, ax = plt.subplots(figsize=(W/100, H/100), dpi=100)
setup_ax(ax)
slide_chrome(ax, 7, TOTAL_SLIDES, '市场分析', '资管科技 SaaS · 蓝海高增长赛道')

# 柱状图: 6 大细分市场
categories = ['传统数据\n(Wind)', '量化平台\n(聚宽/米筐)', '智能投研\n(AI 问答)',
              '另类数据\n(卫星/舆情)', '智能风控', '资管科技 SaaS\n(本项目赛道)']
market = [85, 32, 18, 12, 25, 8]
growth = [8, 35, 65, 80, 45, 75]

bar_x = 200
bar_w = 200
gap = 80

for i, (cat, m, g) in enumerate(zip(categories, market, growth)):
    x = bar_x + i * (bar_w + gap)
    # 市场规模柱
    m_height = m * 4
    m_rect = mpatches.Rectangle((x, 280), bar_w, m_height, facecolor=C['primary'], alpha=0.85)
    ax.add_patch(m_rect)
    text(ax, x + bar_w/2, 280 + m_height + 20, f'{m}亿', size=20, color=C['primary'], ha='center', weight='bold')
    # 增速柱
    g_height = g * 3
    g_rect = mpatches.Rectangle((x, 280), bar_w, g_height, facecolor=C['warning'], alpha=0.4)
    ax.add_patch(g_rect)

    # 类别名
    text(ax, x + bar_w/2, 200, cat, size=16, color='white', ha='center', weight='bold')

# 突出本项目赛道
i = len(categories) - 1
x = bar_x + i * (bar_w + gap)
highlight = mpatches.FancyBboxPatch((x - 5, 275), bar_w + 10, max(market[i] * 4, growth[i] * 3) + 60,
                                     boxstyle='round,pad=2', facecolor='none',
                                     edgecolor=C['accent'], linewidth=4)
ax.add_patch(highlight)

# 图例
legend_y = 950
ax.add_patch(mpatches.Rectangle((1200, legend_y - 20), 40, 25, facecolor=C['primary'], alpha=0.85))
text(ax, 1260, legend_y - 8, '2025 年市场规模（亿元）', size=18, color='white', ha='left')
ax.add_patch(mpatches.Rectangle((1200, legend_y - 60), 40, 25, facecolor=C['warning'], alpha=0.4))
text(ax, 1260, legend_y - 48, '年同比增速 (%)', size=18, color='white', ha='left')

# 关键洞察
text(ax, W/2, 130, '聚焦: 75% 增速 + 8亿规模 = 蓝海高增长机会', size=24, color=C['accent'], weight='bold', ha='center')

presenter_silhouette(ax, W - 350, 60, 250, 280)
text(ax, 100, 50, '7/12 · 市场分析', size=18, color=C['text_gray'], ha='left')
plt.savefig(f'{OUT_DIR}/slide_07_market.png', dpi=100, facecolor=C['bg_dark'])
plt.close()
print('Slide 7: 市场分析')


# ============== Slide 8: 竞争优势 (40s) ==============
fig, ax = plt.subplots(figsize=(W/100, H/100), dpi=100)
setup_ax(ax)
slide_chrome(ax, 8, TOTAL_SLIDES, '竞争优势', '差异化对标 vs 聚宽/米筐/同花顺/恒生')

# 对比矩阵
add_content_box(ax, 80, 250, W - 160, 600, '功能差异化对比', C['primary'])

# 表头
headers = ['功能', '同花顺', '聚宽', '米筐', '本项目']
col_widths = [380, 240, 240, 240, 320]
header_y = 800
header_x = 100
for i, (h, w) in enumerate(zip(headers, col_widths)):
    x = header_x + sum(col_widths[:i])
    rect = mpatches.Rectangle((x, header_y), w - 10, 50, facecolor=C['primary'])
    ax.add_patch(rect)
    text(ax, x + w/2, header_y + 25, h, size=22, color='white', weight='bold', ha='center', va='center')

# 数据行
rows = [
    ['基础数据', '✅', '✅', '✅', '✅'],
    ['量化回测', '⚠️', '✅', '✅', '✅'],
    ['多因子', '❌', '✅', '✅', '✅'],
    ['AI 问答', '⚠️', '❌', '❌', '✅ ★'],
    ['另类数据', '⚠️', '❌', '❌', '✅ ★'],
    ['行业研究', '✅', '❌', '❌', '✅'],
]

row_h = 60
for r, row in enumerate(rows):
    y = header_y - (r + 1) * row_h
    for i, (cell, w) in enumerate(zip(row, col_widths)):
        x = header_x + sum(col_widths[:i])
        if r % 2 == 0:
            bg = mpatches.Rectangle((x, y), w - 10, row_h, facecolor='#0F172A', alpha=0.5)
            ax.add_patch(bg)
        # ★ 标记
        color = C['accent'] if '★' in cell else 'white'
        text(ax, x + w/2, y + row_h/2, cell, size=20, color=color, weight='bold', ha='center', va='center')

presenter_silhouette(ax, W - 350, 60, 250, 280)
text(ax, 100, 50, '8/12 · 竞争优势', size=18, color=C['text_gray'], ha='left')
plt.savefig(f'{OUT_DIR}/slide_08_competitive.png', dpi=100, facecolor=C['bg_dark'])
plt.close()
print('Slide 8: 竞争优势')


# ============== Slide 9: 财务预测 (40s) ==============
fig, ax = plt.subplots(figsize=(W/100, H/100), dpi=100)
setup_ax(ax)
slide_chrome(ax, 9, TOTAL_SLIDES, '财务预测', '5 年财务预测 · 基准情景')

# 4 个核心指标
metrics = [
    ('第 5 年营收', '1.2 亿', '4 年 40x 增长', C['primary']),
    ('第 5 年净利', '2,856 万', '净利率 24%', C['success']),
    ('盈亏平衡', '2028 年', '2 年内实现', C['warning']),
    ('5 年 IRR', '25-30%', '业内基准', C['accent']),
]

box_w = 380
gap = 30
start_x = (W - 4 * box_w - 3 * gap) / 2

for i, (label, value, sub, color) in enumerate(metrics):
    x = start_x + i * (box_w + gap)
    y = 650
    h = 280
    card = mpatches.FancyBboxPatch((x, y), box_w, h, boxstyle='round,pad=10',
                                     facecolor='#1E293B', edgecolor=color, linewidth=3)
    ax.add_patch(card)
    text(ax, x + box_w/2, y + h - 50, label, size=22, color=color, weight='bold', ha='center')
    text(ax, x + box_w/2, y + 130, value, size=44, color='white', weight='bold', ha='center')
    text(ax, x + box_w/2, y + 50, sub, size=16, color=C['text_gray'], ha='center')

# 收入曲线示意
text(ax, W/2, 580, '收入增长曲线 (基准)', size=20, color=C['primary'], weight='bold', ha='center')

years = ['2026', '2027', '2028', '2029', '2030']
revenue = [300, 1200, 2700, 5500, 12000]
profit = [-250, -300, 80, 701, 2856]

# 营收柱
rev_x_start = 250
rev_w = 250
rev_h_max = 350
for i, (y, r) in enumerate(zip(years, revenue)):
    x = rev_x_start + i * 280
    h = (r / max(revenue)) * rev_h_max
    rect = mpatches.Rectangle((x, 200), rev_w - 30, h, facecolor=C['primary'], alpha=0.85)
    ax.add_patch(rect)
    text(ax, x + rev_w/2 - 15, 200 + h + 20, f'{r}', size=20, color='white', weight='bold', ha='center')
    text(ax, x + rev_w/2 - 15, 180, y, size=16, color=C['text_gray'], ha='center')

# 净利折线
profit_y_start = 180
profit_max = max(profit)
profit_min = min(profit)
for i, p in enumerate(profit):
    pct = (p - profit_min) / (profit_max - profit_min) if profit_max > profit_min else 0.5
    h = pct * 200
    if p >= 0:
        # 正值
        color = C['success']
    else:
        # 负值
        h = abs(p / profit_min) * 100
        color = C['danger']
    # 不画在主图上, 只在标题栏说明
    pass

# 关键数据
text(ax, W/2, 150, '5 年累计融资 ¥1,800 万 → 5 年累计净利 ¥3,087 万 → NPV 净现值为正',
     size=18, color=C['success'], ha='center', weight='bold')

presenter_silhouette(ax, W - 350, 60, 250, 280)
text(ax, 100, 50, '9/12 · 财务预测', size=18, color=C['text_gray'], ha='left')
plt.savefig(f'{OUT_DIR}/slide_09_financial.png', dpi=100, facecolor=C['bg_dark'])
plt.close()
print('Slide 9: 财务预测')


# ============== Slide 10: 客户验证 (40s) ==============
fig, ax = plt.subplots(figsize=(W/100, H/100), dpi=100)
setup_ax(ax)
slide_chrome(ax, 10, TOTAL_SLIDES, '客户验证', '行业基线 + 模拟试点 · 100% 续约率')

# 左侧: 行业基线
add_content_box(ax, 80, 250, 880, 600, '行业基线 (公开案例)', C['primary'])
baselines = [
    ('聚宽', 'B 轮 15 亿', '5 年 8 万用户'),
    ('米筐', 'B+ 轮 20 亿', '5 年 5 万用户'),
    ('通联数据', 'D 轮 50 亿', '当前最完整对标'),
    ('本项目目标', '5 年 1.2 亿营收', '1800 万累计融资'),
]
for i, (name, fund, sub) in enumerate(baselines):
    y = 780 - i * 130
    text(ax, 140, y, name, size=22, color='white', ha='left', weight='bold')
    text(ax, 140, y - 35, fund, size=18, color=C['secondary'], ha='left')
    text(ax, 600, y, sub, size=18, color=C['text_gray'], ha='left')

# 右侧: 模拟试点
add_content_box(ax, 980, 250, W - 1060, 600, '模拟试点 (3 客户, 18 月)', C['accent'])

pilot_data = [
    ('客户 A', '百亿量化私募', '+9.2%', '续约'),
    ('客户 B', '券商资管', '+14.7%', '续约 + 升级'),
    ('客户 C', '中型私募', '+6.5%', '续约'),
    ('续约率', '100%', 'NPS 52', '平台稳定 99.95%'),
]
for i, (name, target, val, status) in enumerate(pilot_data):
    y = 780 - i * 130
    text(ax, 1040, y, name, size=22, color='white', ha='left', weight='bold')
    text(ax, 1040, y - 35, target, size=18, color=C['accent'], ha='left')
    text(ax, 1320, y, val, size=22, color=C['success'], ha='left', weight='bold')
    text(ax, 1540, y, status, size=18, color=C['text_gray'], ha='left')

# 底部
text(ax, W/2, 180, '所有客户标识为模拟代号 · 数据基于 akshare 真实历史反演',
     size=16, color=C['text_gray'], ha='center', weight='bold')

presenter_silhouette(ax, W - 350, 60, 250, 280)
text(ax, 100, 50, '10/12 · 客户验证', size=18, color=C['text_gray'], ha='left')
plt.savefig(f'{OUT_DIR}/slide_10_evidence.png', dpi=100, facecolor=C['bg_dark'])
plt.close()
print('Slide 10: 客户验证')


# ============== Slide 11: 风险与对策 (40s) ==============
fig, ax = plt.subplots(figsize=(W/100, H/100), dpi=100)
setup_ax(ax)
slide_chrome(ax, 11, TOTAL_SLIDES, '风险与对策', '诚实面对 + 严格缓释')

risks = [
    ('技术风险', '回测过拟合/AI 黑箱', 'CSCV 检测 + RAG 增强 + 完整审计', C['danger']),
    ('合规风险', '越界投顾业务', '严守"研究工具"定位 + 法律审查 (冯思涵)', C['warning']),
    ('市场风险', '大厂入局/同业竞争', 'AI + 另类数据差异化 + 客户深度绑定', C['accent']),
    ('执行风险', '团队规模小/扩张慢', '推荐单位永字资管 + 校园招聘', C['secondary']),
]

risk_y = 780
for i, (name, desc, mitigation, color) in enumerate(risks):
    y = risk_y - i * 130
    # 风险名
    rect = mpatches.FancyBboxPatch((80, y - 90), W - 160, 110, boxstyle='round,pad=5',
                                     facecolor='#1E293B', edgecolor=color, linewidth=2)
    ax.add_patch(rect)
    # 标题
    text(ax, 150, y, name, size=26, color=color, weight='bold', ha='left')
    text(ax, 400, y, desc, size=20, color='white', ha='left')
    text(ax, 1000, y, mitigation, size=18, color=C['success'], ha='left')

presenter_silhouette(ax, W - 350, 60, 250, 280)
text(ax, 100, 50, '11/12 · 风险与对策', size=18, color=C['text_gray'], ha='left')
plt.savefig(f'{OUT_DIR}/slide_11_risk.png', dpi=100, facecolor=C['bg_dark'])
plt.close()
print('Slide 11: 风险与对策')


# ============== Slide 12: 收尾 (40s) ==============
fig, ax = plt.subplots(figsize=(W/100, H/100), dpi=100)
setup_ax(ax)

# 大标题
text(ax, W/2, H/2 + 150, '让量化投资更智能', size=64, color='white', weight='bold')
text(ax, W/2, H/2 + 50, '让另类数据更普惠', size=64, color=C['secondary'], weight='bold')

# CTA
cta_y = H/2 - 80
text(ax, W/2, cta_y, '诚邀合作 · 立即体验', size=36, color=C['accent'], weight='bold')

# 联系方式
text(ax, W/2, cta_y - 80, '📧 contact@quantinsight.pro', size=22, color='white', ha='center')
text(ax, W/2, cta_y - 130, '🌐 www.quantinsight.pro', size=22, color='white', ha='center')
text(ax, W/2, cta_y - 180, '📊 quantinsight-pro.streamlit.app', size=22, color=C['secondary'], ha='center')

# 结束语
text(ax, W/2, 200, '感谢各位评委的耐心聆听!', size=32, color=C['success'], weight='bold')
text(ax, W/2, 130, '项目编号: 2026FINTECH-FINT-0093', size=20, color=C['text_gray'])

presenter_silhouette(ax, W - 350, 60, 250, 280)
text(ax, 100, 50, '12/12 · 收尾', size=18, color=C['text_gray'], ha='left')

plt.savefig(f'{OUT_DIR}/slide_12_ending.png', dpi=100, facecolor=C['bg_dark'])
plt.close()
print('Slide 12: 收尾')

print('\n=== 12 张路演 PPT 帧生成完成 ===')
import os
total_size = 0
for f in sorted(os.listdir(OUT_DIR)):
    size = os.path.getsize(os.path.join(OUT_DIR, f))
    total_size += size
    print(f'  {f}: {size:,} bytes')
print(f'  总计: {total_size:,} bytes ({total_size/1024/1024:.1f} MB)')
