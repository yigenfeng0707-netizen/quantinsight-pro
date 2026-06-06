"""
QuantInsight Pro - 3 分钟 Demo 视频
方法：用 matplotlib 生成高分辨率帧 + ffmpeg 合成 MP4
"""
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib import rcParams
import json

rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
rcParams['axes.unicode_minus'] = False

# 配色
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

OUTPUT_DIR = 'D:/shFintech/_video_frames'
os.makedirs(OUTPUT_DIR, exist_ok=True)

W, H = 1920, 1080  # Full HD

def create_dark_bg(ax, gradient=True):
    """创建深色渐变背景"""
    if gradient:
        bg = np.linspace(0, 1, 256).reshape(-1, 1)
        bg = np.hstack([bg] * int(W/8))
        ax.imshow(bg, aspect='auto', cmap='Blues_r',
                  extent=[0, W, 0, H], origin='upper', alpha=0.3)
    ax.set_facecolor(C['bg_dark'])
    ax.set_xlim(0, W)
    ax.set_ylim(0, H)
    ax.axis('off')

def add_text(ax, x, y, text, size=40, color='white', weight='normal', ha='center', va='center'):
    ax.text(x, y, text, fontsize=size, color=color, fontweight=weight,
            ha=ha, va=va, family='SimHei')

def add_subtitle_bar(ax, text):
    """底部字幕条"""
    rect = mpatches.Rectangle((0, 0), W, 80, facecolor='black', alpha=0.7, zorder=10)
    ax.add_patch(rect)
    add_text(ax, W/2, 40, text, size=24, color='white', weight='bold')

# ============== 场景 1: 封面 (0:00-0:15) ==============
fig, ax = plt.subplots(figsize=(W/100, H/100), dpi=100)
create_dark_bg(ax)

# Logo
logo_rect = mpatches.FancyBboxPatch((W/2 - 250, H/2 - 50), 500, 100,
                                     boxstyle='round,pad=10', facecolor=C['primary'],
                                     edgecolor='white', linewidth=3)
ax.add_patch(logo_rect)
add_text(ax, W/2, H/2, 'QuantInsight Pro', size=48, color='white', weight='bold')

add_text(ax, W/2, H/2 - 120, 'AI 驱动的另类数据量化投研平台', size=32, color='white')
add_text(ax, W/2, H/2 - 200, '让量化投资更智能，让另类数据更普惠', size=24, color=C['text_gray'])

add_text(ax, W/2, 150, '慧点资本 (InsightQuant) | 杭州永字资产管理有限公司（推荐单位）',
         size=20, color=C['text_gray'])
add_text(ax, W/2, 100, 'Fintech@外滩 · 项目编号 2026FINTECH-FINT-0093',
         size=18, color=C['text_gray'])

add_subtitle_bar(ax, '欢迎来到 QuantInsight Pro 智能投研平台')
plt.savefig(f'{OUTPUT_DIR}/scene_01_cover.png', dpi=100, facecolor=C['bg_dark'])
plt.close()
print('Scene 01: 封面')

# ============== 场景 2: AI 问答 (0:15-0:45) ==============
fig, ax = plt.subplots(figsize=(W/100, H/100), dpi=100)
create_dark_bg(ax)

# 标题
add_text(ax, W/2, H - 80, '🤖 AI 投研问答', size=44, color='white', weight='bold')
add_text(ax, W/2, H - 140, '基于自研金融大模型 · 自然语言投研分析', size=22, color=C['text_gray'])

# 模拟聊天界面
chat_x, chat_y = 200, 200
chat_w, chat_h = W - 400, H - 350
chat_rect = mpatches.FancyBboxPatch((chat_x, chat_y), chat_w, chat_h,
                                     boxstyle='round,pad=10',
                                     facecolor='#1E293B', edgecolor=C['primary'], linewidth=2)
ax.add_patch(chat_rect)

# 用户问题
user_bubble = mpatches.FancyBboxPatch((chat_x + 60, chat_y + chat_h - 200), 900, 100,
                                        boxstyle='round,pad=10', facecolor='#334155')
ax.add_patch(user_bubble)
add_text(ax, chat_x + 80, chat_y + chat_h - 130, '👤 用户', size=18, color=C['text_gray'], ha='left')
add_text(ax, chat_x + 80, chat_y + chat_h - 170, '分析近期 A 股市场热点板块及投资机会',
         size=20, color='white', ha='left', weight='bold')

# AI 回答
ai_bubble = mpatches.FancyBboxPatch((chat_x + 60, chat_y + 100), chat_w - 120, 350,
                                      boxstyle='round,pad=10',
                                      facecolor='#0F172A', edgecolor=C['primary'], linewidth=2)
ax.add_patch(ai_bubble)
add_text(ax, chat_x + 80, chat_y + 420, '🤖 QuantInsight AI', size=18, color=C['primary'], ha='left', weight='bold')

# AI 回答内容（多行）
ai_text = [
    '根据最新数据分析，当前市场热点集中在三大板块：',
    '',
    '1. 人工智能 - 大模型应用落地加速，算力需求爆发',
    '2. 半导体 - 国产替代+AI 芯片双重驱动',
    '3. 消费复苏 - 白酒/食品 PE 处于历史 30% 分位',
    '',
    '💡 建议关注：低估值高分红 + AI 算力链 + 国产替代',
]
for i, line in enumerate(ai_text):
    add_text(ax, chat_x + 80, chat_y + 380 - i * 28, line, size=18, color='white', ha='left')

add_subtitle_bar(ax, 'AI 大语言模型 · 10 秒生成专业投研报告')
plt.savefig(f'{OUTPUT_DIR}/scene_02_ai_qa.png', dpi=100, facecolor=C['bg_dark'])
plt.close()
print('Scene 02: AI 问答')

# ============== 场景 3: 另类数据 (0:45-1:15) ==============
fig, ax = plt.subplots(figsize=(W/100, H/100), dpi=100)
create_dark_bg(ax)

add_text(ax, W/2, H - 80, '📡 另类数据仪表盘', size=44, color='white', weight='bold')
add_text(ax, W/2, H - 140, '卫星图像 · 舆情分析 · 供应链追踪', size=22, color=C['text_gray'])

# 左：卫星图
panel1 = mpatches.FancyBboxPatch((80, 200), 580, 600, boxstyle='round,pad=5',
                                   facecolor='#1E293B', edgecolor=C['secondary'], linewidth=2)
ax.add_patch(panel1)
add_text(ax, 370, 760, '🛰️ 工业园区开工率', size=22, color=C['secondary'], weight='bold', ha='center')

# 模拟柱状图
months = ['1月', '2月', '3月', '4月', '5月', '6月', '7月', '8月', '9月', '10月', '11月', '12月']
values = [55, 60, 75, 82, 88, 90, 85, 87, 82, 78, 70, 65]
bar_x = 130
bar_w = 35
for i, (m, v) in enumerate(zip(months, values)):
    x = bar_x + i * bar_w
    color = C['success'] if v > 80 else C['secondary'] if v > 60 else C['warning']
    rect = mpatches.Rectangle((x, 240), bar_w - 3, v * 4, facecolor=color, alpha=0.85)
    ax.add_patch(rect)
    add_text(ax, x + bar_w/2 - 1, v * 4 + 250, f'{v}', size=10, color='white', ha='center')
    add_text(ax, x + bar_w/2 - 1, 220, m, size=9, color=C['text_gray'], ha='center', va='top')

# 右：舆情
panel2 = mpatches.FancyBboxPatch((700, 200), W - 780, 600, boxstyle='round,pad=5',
                                   facecolor='#1E293B', edgecolor=C['accent'], linewidth=2)
ax.add_patch(panel2)
add_text(ax, W/2 + 100, 760, '💬 行业舆情情感分析', size=22, color=C['accent'], weight='bold', ha='center')

sectors = ['人工智能', '新能源', '半导体', '医药', '消费', '金融', '军工', '汽车']
sent = [0.92, 0.78, 0.85, 0.65, 0.55, 0.48, 0.72, 0.68]
row_h = 50
for i, (s, v) in enumerate(zip(sectors, sent)):
    y = 700 - i * row_h
    add_text(ax, 750, y, s, size=18, color='white', ha='left', weight='bold')
    # 进度条
    bar_full_w = 500
    bar_w_actual = bar_full_w * v
    bg = mpatches.Rectangle((900, y - 12), bar_full_w, 24, facecolor='#334155')
    ax.add_patch(bg)
    color = C['success'] if v > 0.7 else C['warning'] if v > 0.5 else C['danger']
    fg = mpatches.Rectangle((900, y - 12), bar_w_actual, 24, facecolor=color, alpha=0.85)
    ax.add_patch(fg)
    add_text(ax, 1420, y, f'{v:.0%}', size=18, color='white', ha='left', weight='bold')

add_subtitle_bar(ax, '独家另类数据管道 · 提前捕捉市场信号')
plt.savefig(f'{OUTPUT_DIR}/scene_03_alt_data.png', dpi=100, facecolor=C['bg_dark'])
plt.close()
print('Scene 03: 另类数据')

# ============== 场景 4: 量化回测 (1:15-1:45) ==============
fig, ax = plt.subplots(figsize=(W/100, H/100), dpi=100)
create_dark_bg(ax)

add_text(ax, W/2, H - 80, '📈 量化策略回测', size=44, color='white', weight='bold')
add_text(ax, W/2, H - 140, '沪深300 · 双均线 + 多因子 · 5.4 年真实回测', size=22, color=C['text_gray'])

# 加载回测数据
with open('D:/shFintech/_backtest_nav.json', 'r') as f:
    nav_data = json.load(f)

# 绘制 3 条 NAV 曲线
plot_x, plot_y = 150, 180
plot_w, plot_h = W - 300, 580
plot_rect = mpatches.FancyBboxPatch((plot_x, plot_y), plot_w, plot_h,
                                     boxstyle='round,pad=5',
                                     facecolor='#1E293B', edgecolor=C['primary'], linewidth=2)
ax.add_patch(plot_rect)

# 准备数据
strategies = [
    ('HS300_BuyHold', '沪深300 基准', C['text_gray'], '--', 1.8),
    ('HS300_DualMA', '沪深300 双均线', C['secondary'], '-', 2.2),
    ('HS300_MultiFactor', '沪深300 多因子', C['primary'], '-', 2.5),
    ('CYB_DualMA', '创业板 双均线 (最高)', C['success'], '-', 3),
]

# 找最大最小范围
all_vals = []
for k, _, _, _, _ in strategies:
    if k in nav_data:
        all_vals.extend(nav_data[k].values())
y_min, y_max = min(all_vals), max(all_vals)
y_range = y_max - y_min

# 画图坐标
margin = 60
inner_x = plot_x + margin + 80
inner_y = plot_y + margin
inner_w = plot_w - margin * 2 - 80
inner_h = plot_h - margin * 2 - 50

# 网格线
for i in range(1, 5):
    y_grid = inner_y + inner_h * (1 - i/5)
    ax.plot([inner_x, inner_x + inner_w], [y_grid, y_grid], color='#334155', linewidth=0.5, zorder=1)

# 画 NAV 曲线
for key, label, color, ls, lw in strategies:
    if key in nav_data:
        nav_dict = nav_data[key]
        dates = sorted(nav_dict.keys())
        n = len(dates)
        # 转换日期为 x 坐标
        start_date = pd.to_datetime(dates[0])
        end_date = pd.to_datetime(dates[-1])
        total_days = (end_date - start_date).days

        xs = []
        ys = []
        for d in dates:
            dt = pd.to_datetime(d)
            day_offset = (dt - start_date).days
            x = inner_x + inner_w * day_offset / total_days
            y = inner_y + inner_h * (nav_dict[d] - y_min) / y_range
            xs.append(x)
            ys.append(y)

        ax.plot(xs, ys, color=color, linestyle=ls, linewidth=lw, label=label, zorder=3)

# Y 轴标签
for i in range(0, 6):
    val = y_min + y_range * i / 5
    y = inner_y + inner_h * (1 - i/5)
    add_text(ax, plot_x + margin + 70, y, f'{val:.2f}', size=14, color=C['text_gray'], ha='right', va='center')

# X 轴标签（年份）
year_labels = ['2020', '2021', '2022', '2023', '2024', '2025', '2026']
for i, yl in enumerate(year_labels):
    x = inner_x + inner_w * i / 6
    add_text(ax, x, inner_y - 25, yl, size=14, color=C['text_gray'], ha='center')

# 图例
legend_x = inner_x + 30
legend_y = inner_y + inner_h - 30
for i, (key, label, color, ls, lw) in enumerate(strategies):
    y_l = legend_y - i * 30
    ax.plot([legend_x, legend_x + 40], [y_l, y_l], color=color, linestyle=ls, linewidth=lw)
    add_text(ax, legend_x + 50, y_l, label, size=14, color='white', ha='left', va='center')

# 关键指标卡片
metrics_box = mpatches.FancyBboxPatch((150, 100), W - 300, 100, boxstyle='round,pad=5',
                                       facecolor='#0F172A', edgecolor=C['success'], linewidth=2)
ax.add_patch(metrics_box)

m_x = 250
m_items = [
    ('最高年化', '创业板双均线 +3.36%'),
    ('最佳夏普', '创业板双均线 0.04'),
    ('平均回撤', '~30%'),
    ('数据可信', 'akshare 公开 A 股 5922 天'),
]
for i, (label, value) in enumerate(m_items):
    add_text(ax, m_x + i * 380, 160, label, size=14, color=C['text_gray'], ha='left')
    add_text(ax, m_x + i * 380, 125, value, size=18, color=C['success'], ha='left', weight='bold')

add_subtitle_bar(ax, '基于 akshare 公开 A 股数据 · 方法学严谨可复现')
plt.savefig(f'{OUTPUT_DIR}/scene_04_backtest.png', dpi=100, facecolor=C['bg_dark'])
plt.close()
print('Scene 04: 量化回测')

# ============== 场景 5: 财务预测 (1:45-2:00) ==============
fig, ax = plt.subplots(figsize=(W/100, H/100), dpi=100)
create_dark_bg(ax)

add_text(ax, W/2, H - 80, '💰 五年财务预测 (基准情景)', size=44, color='white', weight='bold')
add_text(ax, W/2, H - 140, '业内基准保守预测 · IRR 25-30% · 2028 年盈亏平衡',
         size=22, color=C['text_gray'])

# 4 个子图
years = ['2026', '2027', '2028', '2029', '2030']
revenue = [300, 1200, 2700, 5500, 12000]
profit = [-250, -300, 80, 701, 2856]
clients = [8, 25, 60, 130, 250]
cash = [280, 630, 1010, 1381, 3717]

panels = [
    (80, 540, 880, 280, '营业收入 (万元)', revenue, C['primary'], 'bar'),
    (980, 540, 860, 280, '净利润 (万元)', profit, C['success'], 'bar_pos_neg'),
    (80, 200, 880, 280, '累计客户 (家)', clients, C['accent'], 'line'),
    (980, 200, 860, 280, '期末现金 (万元)', cash, C['warning'], 'bar'),
]

for px, py, pw, ph, title, vals, color, chart_type in panels:
    panel_rect = mpatches.FancyBboxPatch((px, py), pw, ph, boxstyle='round,pad=5',
                                          facecolor='#1E293B', edgecolor=color, linewidth=2)
    ax.add_patch(panel_rect)
    add_text(ax, px + pw/2, py + ph - 30, title, size=22, color=color, weight='bold', ha='center')

    inner_x = px + 50
    inner_y = py + 50
    inner_w = pw - 100
    inner_h = ph - 100

    if chart_type in ['bar', 'bar_pos_neg']:
        n = len(vals)
        bw = inner_w / n * 0.7
        gap = inner_w / n * 0.3
        max_v = max(vals)
        min_v = min(vals) if chart_type == 'bar_pos_neg' else 0

        if chart_type == 'bar_pos_neg':
            # Zero line
            zero_y = inner_y + inner_h * (max_v / (max_v - min_v))
            ax.plot([inner_x, inner_x + inner_w], [zero_y, zero_y], color='white', linewidth=0.8, zorder=1)

        for i, v in enumerate(vals):
            bx = inner_x + i * (bw + gap) + gap/2
            if v >= 0 or chart_type != 'bar_pos_neg':
                bh = (v / max_v) * inner_h if v > 0 else 0
                rect_color = color
                by = inner_y
                if chart_type == 'bar_pos_neg' and v < 0:
                    bh = (-v / -min_v) * inner_h * 0.3
                    rect_color = C['danger']
                    by = zero_y
            else:
                bh = (-v / -min_v) * inner_h * 0.3
                rect_color = C['danger']
                by = zero_y
            rect = mpatches.Rectangle((bx, by), bw, bh, facecolor=rect_color, alpha=0.85)
            ax.add_patch(rect)
            # 数值标签
            label_y = by + bh + 10 if v >= 0 else by - 5
            add_text(ax, bx + bw/2, label_y, f'{v}', size=12, color='white', ha='center', weight='bold')

    elif chart_type == 'line':
        n = len(vals)
        max_v = max(vals)
        xs = []
        ys = []
        for i, v in enumerate(vals):
            x = inner_x + inner_w * (i + 0.5) / n
            y = inner_y + inner_h * v / max_v
            xs.append(x)
            ys.append(y)
        ax.plot(xs, ys, color=color, linewidth=3, marker='o', markersize=10, zorder=3)
        for x, y, v in zip(xs, ys, vals):
            add_text(ax, x, y + 20, f'{v}', size=12, color='white', ha='center', weight='bold')

    # X 轴标签
    for i, yl in enumerate(years):
        if chart_type in ['bar', 'bar_pos_neg']:
            x = inner_x + i * (inner_w / len(years)) + inner_w / len(years) / 2
        else:
            x = inner_x + inner_w * (i + 0.5) / len(years)
        add_text(ax, x, inner_y - 20, yl, size=12, color=C['text_gray'], ha='center')

add_subtitle_bar(ax, '基于真实团队规模 + 永字资管推荐生态 · 业内基准保守预测')
plt.savefig(f'{OUTPUT_DIR}/scene_05_financial.png', dpi=100, facecolor=C['bg_dark'])
plt.close()
print('Scene 05: 财务预测')

# ============== 场景 6: 行业分析 (2:00-2:20) ==============
fig, ax = plt.subplots(figsize=(W/100, H/100), dpi=100)
create_dark_bg(ax)

add_text(ax, W/2, H - 80, '📊 智能投研市场细分', size=44, color='white', weight='bold')
add_text(ax, W/2, H - 140, '本项目赛道：高增速 + 低规模 = 蓝海机会',
         size=22, color=C['accent'])

categories = ['传统数据\n(Wind/同花顺)', '量化平台\n(聚宽/米筐)', '智能投研\n(AI 问答)',
              '另类数据\n(卫星/舆情)', '智能风控', '资管科技 SaaS\n(本项目赛道)']
market = [85, 32, 18, 12, 25, 8]
growth = [8, 35, 65, 80, 45, 75]

bar_x = 200
bar_w = 180
gap = 30
for i, (cat, m, g) in enumerate(zip(categories, market, growth)):
    x = bar_x + i * (bar_w + gap)
    # 市场规模柱
    m_height = m * 4
    m_rect = mpatches.Rectangle((x, 200), bar_w, m_height, facecolor=C['primary'], alpha=0.85)
    ax.add_patch(m_rect)
    add_text(ax, x + bar_w/2, 200 + m_height + 20, f'{m}亿', size=18, color=C['primary'], ha='center', weight='bold')

    # 增速柱
    g_height = g * 3
    g_rect = mpatches.Rectangle((x, 200), bar_w, g_height, facecolor=C['warning'], alpha=0.4)
    ax.add_patch(g_rect)
    add_text(ax, x + bar_w/2, 200 + g_height + 20, f'{g}%', size=18, color=C['warning'], ha='center', weight='bold')

    # 类别名
    add_text(ax, x + bar_w/2, 150, cat, size=16, color='white', ha='center', weight='bold')

# 突出本项目赛道
i = len(categories) - 1
x = bar_x + i * (bar_w + gap)
highlight = mpatches.FancyBboxPatch((x - 5, 195), bar_w + 10, max(market[i] * 4, growth[i] * 3) + 50,
                                     boxstyle='round,pad=2', facecolor='none',
                                     edgecolor=C['accent'], linewidth=3)
ax.add_patch(highlight)

add_text(ax, W/2, 100, '本项目赛道: 75% 增速 + 8 亿规模 = 高速增长蓝海',
         size=24, color=C['accent'], weight='bold', ha='center')

# 图例
legend_y = 1000
ax.add_patch(mpatches.Rectangle((1400, legend_y - 15), 30, 20, facecolor=C['primary'], alpha=0.85))
add_text(ax, 1440, legend_y - 5, '2025 年市场规模（亿元）', size=14, color='white', ha='left')
ax.add_patch(mpatches.Rectangle((1400, legend_y - 50), 30, 20, facecolor=C['warning'], alpha=0.4))
add_text(ax, 1440, legend_y - 40, '年同比增速 (%)', size=14, color='white', ha='left')

add_subtitle_bar(ax, '聚焦资管科技 SaaS 蓝海赛道 · 蓝海高增长机会')
plt.savefig(f'{OUTPUT_DIR}/scene_06_market.png', dpi=100, facecolor=C['bg_dark'])
plt.close()
print('Scene 06: 市场细分')

# ============== 场景 7: 团队 (2:20-2:30) ==============
fig, ax = plt.subplots(figsize=(W/100, H/100), dpi=100)
create_dark_bg(ax)

add_text(ax, W/2, H - 80, '👥 核心团队 · 技术 + 资管复合背景', size=44, color='white', weight='bold')

team = [
    ('冯亦根', '项目主导 · 首席科学家', '浙大计算机本科 · 亚洲城市大学硕士\n浙江省产业教授 · 多重专家身份',
     '战略规划 · 技术方向把控 · 资管行业资源', C['primary']),
    ('薛永再', '商务 · 战略合作', '浙大中文本科 · 永字资管总经理\n3 次创业经验 · 推荐单位负责人',
     '商务拓展 · 产业资源 · 永字资管生态协同', C['accent']),
    ('黄成选', '技术负责人 · AI 工程师', '厦大计算机本科（推免清华软工）\n大模型应用算法工程师 · 多模态检索实战',
     '核心代码实现 · 模型应用 · 平台开发', C['secondary']),
    ('冯思涵', '法务 · 海外事务', 'Northwestern JD 2025\nM.S. 神经生物学 · 量化脑科学交叉',
     '合规法务 · 海外业务 · 知识产权布局', C['warning']),
]

team_x = 80
team_w = 1750
team_y = 200
team_h = 600
col_w = team_w / 4 - 30

for i, (name, role, bg, resp, color) in enumerate(team):
    x = team_x + i * (col_w + 30)
    panel = mpatches.FancyBboxPatch((x, team_y), col_w, team_h, boxstyle='round,pad=5',
                                      facecolor='#1E293B', edgecolor=color, linewidth=3)
    ax.add_patch(panel)

    # 头像占位
    avatar = mpatches.Circle((x + col_w/2, team_y + team_h - 80), 50, facecolor=color, alpha=0.85)
    ax.add_patch(avatar)
    add_text(ax, x + col_w/2, team_y + team_h - 80, name[0], size=36, color='white', weight='bold', ha='center', va='center')

    add_text(ax, x + col_w/2, team_y + team_h - 180, name, size=24, color='white', weight='bold', ha='center')
    add_text(ax, x + col_w/2, team_y + team_h - 215, role, size=16, color=color, ha='center', weight='bold')

    add_text(ax, x + col_w/2, team_y + team_h - 280, bg, size=13, color=C['text_gray'], ha='center')
    add_text(ax, x + col_w/2, team_y + 80, '职责：' + resp, size=13, color='white', ha='center')

add_subtitle_bar(ax, '复合型团队 · 真实身份 · 推荐单位永字资管深度参与')
plt.savefig(f'{OUTPUT_DIR}/scene_07_team.png', dpi=100, facecolor=C['bg_dark'])
plt.close()
print('Scene 07: 团队')

# ============== 场景 8: 商业模式 (2:30-2:50) ==============
fig, ax = plt.subplots(figsize=(W/100, H/100), dpi=100)
create_dark_bg(ax)

add_text(ax, W/2, H - 80, '💼 商业模式 · 三档订阅 + 多元收入',
         size=44, color='white', weight='bold')

# 左侧：定价
pricing = [
    ('基础版', '¥20万/年', '中小型私募\n券商营业部', C['secondary']),
    ('专业版', '¥80万/年', '中型私募\n券商资管', C['primary']),
    ('企业版', '¥200万+/年', '公募基金\n银行理财子', C['accent']),
]

prc_x = 80
prc_w = 600
prc_y = 200
prc_h = 600
prc_each = prc_h / 3 - 20

for i, (name, price, target, color) in enumerate(pricing):
    y = prc_y + (2 - i) * prc_each
    rect = mpatches.FancyBboxPatch((prc_x, y), prc_w, prc_each - 20, boxstyle='round,pad=5',
                                     facecolor='#1E293B', edgecolor=color, linewidth=3)
    ax.add_patch(rect)
    add_text(ax, prc_x + 30, y + prc_each - 60, name, size=28, color=color, weight='bold', ha='left')
    add_text(ax, prc_x + 30, y + prc_each - 100, price, size=24, color='white', ha='left', weight='bold')
    add_text(ax, prc_x + 30, y + prc_each - 140, target, size=16, color=C['text_gray'], ha='left')

# 右侧：收入结构（饼图）
pie_x, pie_y = 800, 200
pie_w, pie_h = W - 880, 600

# 收入构成
revenue_items = [
    ('订阅服务', 60, C['primary']),
    ('交易分成', 20, C['accent']),
    ('定制开发', 15, C['secondary']),
    ('数据服务', 5, C['warning']),
]

# 简化版：横向条形
add_text(ax, pie_x + pie_w/2, pie_y + pie_h - 40, '收入结构 (5年累计)', size=24, color='white', weight='bold', ha='center')

bar_y_start = pie_y + pie_h - 100
for i, (label, pct, color) in enumerate(revenue_items):
    y = bar_y_start - i * 100
    add_text(ax, pie_x, y, label, size=20, color='white', ha='left', weight='bold')
    add_text(ax, pie_x + 200, y, f'{pct}%', size=24, color=color, ha='left', weight='bold')
    # 进度条
    bar_w = (pie_w - 300) * pct / 100
    bg_rect = mpatches.Rectangle((pie_x + 300, y - 20), pie_w - 300, 40, facecolor='#334155', alpha=0.5)
    ax.add_patch(bg_rect)
    fg_rect = mpatches.Rectangle((pie_x + 300, y - 20), bar_w, 40, facecolor=color, alpha=0.85)
    ax.add_patch(fg_rect)

add_subtitle_bar(ax, '清晰多元的盈利模式 · 预计第 2 年实现盈利')
plt.savefig(f'{OUTPUT_DIR}/scene_08_business.png', dpi=100, facecolor=C['bg_dark'])
plt.close()
print('Scene 08: 商业模式')

# ============== 场景 9: 封底 (2:50-3:00) ==============
fig, ax = plt.subplots(figsize=(W/100, H/100), dpi=100)
create_dark_bg(ax)

# Logo
logo_rect = mpatches.FancyBboxPatch((W/2 - 250, H/2 - 50), 500, 100,
                                     boxstyle='round,pad=10', facecolor=C['primary'],
                                     edgecolor='white', linewidth=3)
ax.add_patch(logo_rect)
add_text(ax, W/2, H/2, 'QuantInsight Pro', size=48, color='white', weight='bold')

add_text(ax, W/2, H/2 - 130, '感谢观看', size=42, color='white', weight='bold')
add_text(ax, W/2, H/2 - 200, '诚邀合作 · 立即体验', size=28, color=C['accent'], weight='bold')

# 联系信息
add_text(ax, W/2, 200, '📧 邮箱：contact@quantinsight.pro', size=22, color='white', ha='center')
add_text(ax, W/2, 160, '🌐 官网：www.quantinsight.pro', size=22, color='white', ha='center')
add_text(ax, W/2, 120, '📊 Demo：https://quantinsight-pro.streamlit.app', size=22, color=C['secondary'], ha='center')
add_text(ax, W/2, 80, '项目编号：2026FINTECH-FINT-0093', size=18, color=C['text_gray'], ha='center')

add_subtitle_bar(ax, '让量化投资更智能，让另类数据更普惠')
plt.savefig(f'{OUTPUT_DIR}/scene_09_ending.png', dpi=100, facecolor=C['bg_dark'])
plt.close()
print('Scene 09: 封底')

print('\n=== 9 个场景帧生成完成 ===')
print(f'输出目录: {OUTPUT_DIR}')
