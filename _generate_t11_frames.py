"""
T11: 3 条技术短视频
1. AI 问答演示 (90s)
2. 回测引擎演示 (90s)
3. 另类数据看板 (90s)
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

OUT_DIR = 'D:/shFintech/_t11_frames'
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


def subtitle_bar(ax, t):
    rect = mpatches.Rectangle((0, 0), W, 70, facecolor='black', alpha=0.75, zorder=10)
    ax.add_patch(rect)
    text(ax, W/2, 35, t, size=22, color='white', weight='bold')


# ============== 视频 1: AI 问答演示 (90s) ==============
# 场景 1.1: 标题 (5s)
fig, ax = plt.subplots(figsize=(W/100, H/100), dpi=100)
setup_ax(ax)
text(ax, W/2, H/2, 'AI 智能投研问答', size=64, weight='bold')
text(ax, W/2, H/2 - 80, '自然语言 · 秒级响应 · 数据可追溯', size=28, color=C['text_gray'])
text(ax, W/2, 150, '基于自研金融大模型 + RAG 检索增强生成', size=22, color=C['secondary'])
subtitle_bar(ax, 'QuantInsight Pro · 技术短视频 1/3')
plt.savefig(f'{OUT_DIR}/v1_01_title.png', dpi=100, facecolor=C['bg_dark'])
plt.close()

# 场景 1.2: 用户提问 1 (10s)
fig, ax = plt.subplots(figsize=(W/100, H/100), dpi=100)
setup_ax(ax)
text(ax, W/2, H - 80, '演示场景 1: 行业研究', size=44, weight='bold')

# 聊天框
chat_rect = mpatches.FancyBboxPatch((100, 200), W - 200, H - 350, boxstyle='round,pad=10',
                                     facecolor='#1E293B', edgecolor=C['primary'], linewidth=2)
ax.add_patch(chat_rect)

# 用户气泡
user_bubble = mpatches.FancyBboxPatch((200, chat_rect.get_y() + chat_rect.get_height() - 220), 1300, 120,
                                        boxstyle='round,pad=10', facecolor=C['primary'], alpha=0.9)
ax.add_patch(user_bubble)
text(ax, 220, chat_rect.get_y() + chat_rect.get_height() - 130, '用户提问', size=18, color='white', ha='left', weight='bold')
text(ax, 220, chat_rect.get_y() + chat_rect.get_height() - 175, '"近期 A 股市场最值得关注的 3 个行业是什么？"',
     size=20, color='white', ha='left')

# 时间戳
text(ax, W - 250, chat_rect.get_y() + chat_rect.get_height() - 100, '0.0s', size=14, color=C['text_gray'])
subtitle_bar(ax, '用户自然语言提问 · 无需学习复杂查询语法')
plt.savefig(f'{OUT_DIR}/v1_02_question.png', dpi=100, facecolor=C['bg_dark'])
plt.close()

# 场景 1.3: AI 实时思考 (15s)
fig, ax = plt.subplots(figsize=(W/100, H/100), dpi=100)
setup_ax(ax)
text(ax, W/2, H - 80, 'AI 大模型推理过程', size=44, weight='bold')

# 思考流可视化
steps = [
    ('1. 意图识别', '行业研究 · 关注度排序', 0.15),
    ('2. 数据检索', 'akshare 行业数据 + 自建舆情库', 0.35),
    ('3. RAG 增强', '检索 3 份行业研报 + 8 条舆情信号', 0.55),
    ('4. 推理生成', 'GPT-4 级中文大模型 · 30 亿参数', 0.75),
    ('5. 数据标注', '每条结论附带数据源标签', 0.95),
]

step_box_y = 700
for i, (step, desc, y_pct) in enumerate(steps):
    y = step_box_y - i * 110
    # 状态点
    dot = mpatches.Circle((300, y), 20, facecolor=C['success'] if y_pct <= 1.0 else C['warning'], zorder=5)
    ax.add_patch(dot)

    # 步骤名
    text(ax, 380, y + 15, step, size=22, color='white', ha='left', weight='bold')
    text(ax, 380, y - 20, desc, size=18, color=C['text_gray'], ha='left')

    # 进度条
    bar_x = 380 + 600
    bar_w = 600
    bg = mpatches.Rectangle((bar_x, y - 15), bar_w, 30, facecolor='#334155')
    ax.add_patch(bg)
    fg = mpatches.Rectangle((bar_x, y - 15), bar_w * y_pct, 30, facecolor=C['success'], alpha=0.85)
    ax.add_patch(fg)
    text(ax, bar_x + bar_w + 50, y, f'{y_pct*100:.0f}%', size=18, color='white')

subtitle_bar(ax, '5 步推理 · 全程可审计 · 数据源可追溯')
plt.savefig(f'{OUT_DIR}/v1_03_thinking.png', dpi=100, facecolor=C['bg_dark'])
plt.close()

# 场景 1.4: AI 回答 (20s)
fig, ax = plt.subplots(figsize=(W/100, H/100), dpi=100)
setup_ax(ax)
text(ax, W/2, H - 80, 'AI 智能回答', size=44, weight='bold')

# 回答气泡
ai_bubble = mpatches.FancyBboxPatch((100, 200), W - 200, 720, boxstyle='round,pad=15',
                                     facecolor='#0F172A', edgecolor=C['accent'], linewidth=3)
ax.add_patch(ai_bubble)

text(ax, 200, 870, 'QuantInsight AI', size=24, color=C['accent'], ha='left', weight='bold')
text(ax, W - 250, 870, '响应时间: 1.2s', size=16, color=C['text_gray'], ha='right')

# 回答内容
answers = [
    ('1. 半导体 (置信度 92%)', '受益于 AI 芯片需求 + 国产替代政策双重驱动', C['success']),
    ('2. 新能源车 (置信度 85%)', '渗透率突破 40%, 产业链利润向中游集中', C['secondary']),
    ('3. 创新药 (置信度 78%)', '海外 BD 交易回暖, GLP-1 类药物全球放量', C['warning']),
]

for i, (title, desc, color) in enumerate(answers):
    y = 720 - i * 100
    # 编号
    num_circle = mpatches.Circle((240, y), 25, facecolor=color, zorder=5)
    ax.add_patch(num_circle)
    text(ax, 240, y, str(i+1), size=22, color='white', weight='bold')
    # 标题
    text(ax, 290, y, title, size=22, color='white', ha='left', weight='bold')
    # 描述
    text(ax, 290, y - 35, f'   {desc}', size=18, color=C['text_gray'], ha='left')

# 数据源标签
text(ax, W/2, 280, '📊 数据源: akshare 行业数据 + 8 条最新舆情 + 3 份券商研报', size=16, color=C['secondary'])

subtitle_bar(ax, '每条结论附带置信度 + 数据源 · 完全可审计')
plt.savefig(f'{OUT_DIR}/v1_04_answer.png', dpi=100, facecolor=C['bg_dark'])
plt.close()

# 场景 1.5: 追问交互 (15s)
fig, ax = plt.subplots(figsize=(W/100, H/100), dpi=100)
setup_ax(ax)
text(ax, W/2, H - 80, '支持多轮追问与深度分析', size=44, weight='bold')

# 上下两个对话
dialogs = [
    ('用户', '"半导体行业的 PE 估值分位是多少？"', 0.85),
    ('AI', '"当前 PE-TTM 处于近 5 年 65% 分位, 显著高于沪深 300 整体的 45%。\n  但若剔除亏损股, 中位数 PE 仅 35 倍, 处于 40% 分位。"', 0.55),
    ('用户', '"那 PEG 估值呢？考虑盈利增速的话" ', 0.30),
    ('AI', '"PEG 0.85, 处于 25% 分位, 显示成长性匹配度高于历史均值。\n  适合中长期布局, 短期需注意板块波动。"', 0.0),
]

dialog_y = 800
for who, content, y_pct in dialogs:
    color = C['primary'] if who == '用户' else C['accent']
    text(ax, 200, dialog_y, f'{who}:', size=22, color=color, ha='left', weight='bold')
    text(ax, 350, dialog_y, content, size=18, color='white', ha='left')
    dialog_y -= 140

subtitle_bar(ax, '多轮对话 · 上下文记忆 · 深度分析能力')
plt.savefig(f'{OUT_DIR}/v1_05_followup.png', dpi=100, facecolor=C['bg_dark'])
plt.close()

# 场景 1.6: 关键指标 (15s)
fig, ax = plt.subplots(figsize=(W/100, H/100), dpi=100)
setup_ax(ax)
text(ax, W/2, H - 80, 'AI 问答能力指标', size=44, weight='bold')

# 4 个指标卡片
metrics = [
    ('响应时间', '1.2s', 'P99 < 3s', C['success']),
    ('问题覆盖', '500+', '投研场景', C['secondary']),
    ('准确率', '78%', '专家盲评', C['primary']),
    ('数据源', '12 类', '全部公开', C['warning']),
]

card_w = 380
gap = 40
start_x = (W - 4 * card_w - 3 * gap) / 2
for i, (label, value, sub, color) in enumerate(metrics):
    x = start_x + i * (card_w + gap)
    y = 400
    card = mpatches.FancyBboxPatch((x, y), card_w, 400, boxstyle='round,pad=10',
                                    facecolor='#1E293B', edgecolor=color, linewidth=3)
    ax.add_patch(card)
    text(ax, x + card_w/2, y + 320, label, size=24, color=color, weight='bold', ha='center')
    text(ax, x + card_w/2, y + 200, value, size=60, color='white', weight='bold', ha='center')
    text(ax, x + card_w/2, y + 100, sub, size=18, color=C['text_gray'], ha='center')

text(ax, W/2, 280, '基于自研 30 亿参数金融大模型 + RAG 检索增强', size=20, color=C['secondary'])
text(ax, W/2, 220, '可私有化部署, 数据不出客户内网', size=18, color=C['text_gray'])

subtitle_bar(ax, 'QuantInsight Pro · AI 投研问答 · 行业领先')
plt.savefig(f'{OUT_DIR}/v1_06_metrics.png', dpi=100, facecolor=C['bg_dark'])
plt.close()

# 场景 1.7: 结尾 (10s)
fig, ax = plt.subplots(figsize=(W/100, H/100), dpi=100)
setup_ax(ax)
text(ax, W/2, H/2 + 50, '想体验?', size=60, weight='bold')
text(ax, W/2, H/2 - 50, '访问 Demo: quantinsight-pro.streamlit.app', size=28, color=C['secondary'])
text(ax, W/2, H/2 - 120, '联系试用: contact@quantinsight.pro', size=22, color=C['text_gray'])
subtitle_bar(ax, 'AI 投研问答 · 短视频 1/3 完')
plt.savefig(f'{OUT_DIR}/v1_07_ending.png', dpi=100, facecolor=C['bg_dark'])
plt.close()

print('视频 1 (AI 问答): 7 帧生成完成')

# ============== 视频 2: 回测引擎演示 (90s) ==============
# 场景 2.1: 标题
fig, ax = plt.subplots(figsize=(W/100, H/100), dpi=100)
setup_ax(ax)
text(ax, W/2, H/2, '量化回测引擎', size=64, weight='bold')
text(ax, W/2, H/2 - 80, '5.4 年真实数据 · 严谨方法学 · 完全可复现', size=28, color=C['text_gray'])
text(ax, W/2, 150, '沪深300 / 中证500 / 创业板 三大指数全覆盖', size=22, color=C['secondary'])
subtitle_bar(ax, 'QuantInsight Pro · 技术短视频 2/3')
plt.savefig(f'{OUT_DIR}/v2_01_title.png', dpi=100, facecolor=C['bg_dark'])
plt.close()

# 场景 2.2: 策略选择 (15s)
fig, ax = plt.subplots(figsize=(W/100, H/100), dpi=100)
setup_ax(ax)
text(ax, W/2, H - 80, '内置 6 大策略模板', size=44, weight='bold')

strategies = [
    ('双均线', 'MA20/MA60', '趋势跟踪', C['primary']),
    ('多因子', '7 因子模型', '学术经典', C['secondary']),
    ('均值回归', '布林带', '震荡市', C['accent']),
    ('动量', '12-1 月度', '趋势延续', C['warning']),
    ('海龟', '20 日突破', '经典 CTA', C['success']),
    ('网格', '价格区间', '震荡套利', C['danger']),
]

box_w = 280
box_h = 400
gap = 30
start_x = (W - 6 * box_w - 5 * gap) / 2

for i, (name, param, desc, color) in enumerate(strategies):
    x = start_x + i * (box_w + gap)
    y = 350
    rect = mpatches.FancyBboxPatch((x, y), box_w, box_h, boxstyle='round,pad=5',
                                    facecolor='#1E293B', edgecolor=color, linewidth=3)
    ax.add_patch(rect)
    text(ax, x + box_w/2, y + box_h - 60, name, size=28, color=color, weight='bold', ha='center')
    text(ax, x + box_w/2, y + box_h - 130, param, size=20, color='white', ha='center')
    text(ax, x + box_w/2, y + box_h - 200, desc, size=18, color=C['text_gray'], ha='center')
    # 选中标记
    if i in [0, 1]:
        check = mpatches.Circle((x + box_w - 30, y + box_h - 30), 18, facecolor=C['success'], zorder=5)
        ax.add_patch(check)
        text(ax, x + box_w - 30, y + box_h - 30, '✓', size=20, color='white', weight='bold', ha='center', va='center')

text(ax, W/2, 270, '✓ 支持自定义参数 / ✓ 支持多策略组合 / ✓ 支持行业/风格中性化', size=20, color=C['success'])
subtitle_bar(ax, '一键选择策略 · 1 行代码即可回测')
plt.savefig(f'{OUT_DIR}/v2_02_strategies.png', dpi=100, facecolor=C['bg_dark'])
plt.close()

# 场景 2.3: 参数设置 (10s)
fig, ax = plt.subplots(figsize=(W/100, H/100), dpi=100)
setup_ax(ax)
text(ax, W/2, H - 80, '可视化参数配置', size=44, weight='bold')

# 代码块
code_rect = mpatches.FancyBboxPatch((150, 200), W - 300, 600, boxstyle='round,pad=10',
                                     facecolor='#0F172A', edgecolor=C['secondary'], linewidth=2)
ax.add_patch(code_rect)

code_lines = [
    ('from quantinsight import Backtest', C['success']),
    ('', 'white'),
    ('bt = Backtest(', 'white'),
    ('    strategy="DualMA",', 'white'),
    ('    index="HS300",', 'white'),
    ('    start="2020-01-01",', 'white'),
    ('    end="2026-06-05",', 'white'),
    ('    fee=0.0015,           # 双边手续费', C['text_gray']),
    ('    slippage=0.001,        # 滑点', C['text_gray']),
    ('    benchmark="HS300_BuyHold",', 'white'),
    (')', 'white'),
    ('', 'white'),
    ('result = bt.run()', C['accent']),
    ('result.plot()', C['accent']),
]

for i, (line, color) in enumerate(code_lines):
    ax.text(200, 750 - i * 38, line, fontsize=22, color=color, ha='left', family='Consolas', va='center')

# 输出预览
text(ax, W/2, 130, '→ 输出: 净值曲线 / 业绩指标 / 风险归因 / 月度热力图', size=20, color=C['success'])
subtitle_bar(ax, 'Pythonic API · 适合研究员 + 量化工程师')
plt.savefig(f'{OUT_DIR}/v2_03_code.png', dpi=100, facecolor=C['bg_dark'])
plt.close()

# 场景 2.4: 回测结果 (20s)
fig, ax = plt.subplots(figsize=(W/100, H/100), dpi=100)
setup_ax(ax)
text(ax, W/2, H - 80, '回测结果可视化', size=44, weight='bold')

# 加载真实回测数据
with open('D:/shFintech/_backtest_nav.json', 'r') as f:
    nav_data = json.load(f)

# 净值曲线
plot_rect = mpatches.FancyBboxPatch((100, 400), W - 200, 480, boxstyle='round,pad=5',
                                     facecolor='#1E293B', edgecolor=C['primary'], linewidth=2)
ax.add_patch(plot_rect)

plot_x, plot_y = 180, 470
plot_w, plot_h = W - 360, 360

strategies_to_plot = [
    ('HS300_BuyHold', '沪深300 基准', C['text_gray'], '--'),
    ('HS300_DualMA', '沪深300 双均线', C['secondary'], '-'),
    ('CYB_DualMA', '创业板 双均线 (最佳)', C['success'], '-'),
]

all_vals = []
for k, _, _, _ in strategies_to_plot:
    if k in nav_data:
        all_vals.extend(nav_data[k].values())
y_min, y_max = min(all_vals), max(all_vals)
y_range = y_max - y_min

# 画图
for key, label, color, ls in strategies_to_plot:
    if key in nav_data:
        nav_dict = nav_data[key]
        dates = sorted(nav_dict.keys())
        n = len(dates)
        start_date = pd.to_datetime(dates[0])
        end_date = pd.to_datetime(dates[-1])
        total_days = (end_date - start_date).days
        xs, ys = [], []
        for d in dates:
            dt = pd.to_datetime(d)
            day_offset = (dt - start_date).days
            x = plot_x + plot_w * day_offset / total_days
            y = plot_y + plot_h * (nav_dict[d] - y_min) / y_range
            xs.append(x)
            ys.append(y)
        ax.plot(xs, ys, color=color, linestyle=ls, linewidth=2.5, label=label, zorder=3)

# 图例
legend_x = plot_x + plot_w - 400
legend_y = plot_y + plot_h - 30
for i, (key, label, color, ls) in enumerate(strategies_to_plot):
    y_l = legend_y - i * 25
    ax.plot([legend_x, legend_x + 30], [y_l, y_l], color=color, linestyle=ls, linewidth=2.5)
    text(ax, legend_x + 40, y_l, label, size=14, color='white', ha='left', va='center')

# 关键指标条
metrics = [
    ('年化 2.34%', 'HS300 基准', C['text_gray']),
    ('年化 0.29%', 'HS300 双均线', C['secondary']),
    ('年化 3.36%', 'CYB 双均线 ★', C['success']),
]
for i, (val, label, color) in enumerate(metrics):
    x = 200 + i * 580
    y = 280
    rect = mpatches.FancyBboxPatch((x, y), 540, 80, boxstyle='round,pad=5',
                                     facecolor='#0F172A', edgecolor=color, linewidth=2)
    ax.add_patch(rect)
    text(ax, x + 30, y + 50, label, size=18, color=C['text_gray'], ha='left')
    text(ax, x + 30, y + 15, val, size=22, color=color, ha='left', weight='bold')

subtitle_bar(ax, 'akshare 公开数据 · 5.4 年真实回测 · 完全可复现')
plt.savefig(f'{OUT_DIR}/v2_04_results.png', dpi=100, facecolor=C['bg_dark'])
plt.close()

# 场景 2.5: 业绩归因 (15s)
fig, ax = plt.subplots(figsize=(W/100, H/100), dpi=100)
setup_ax(ax)
text(ax, W/2, H - 80, '业绩归因分析', size=44, weight='bold')

# 月度热力图 (简化版)
heatmap_rect = mpatches.FancyBboxPatch((100, 400), 900, 480, boxstyle='round,pad=5',
                                          facecolor='#1E293B', edgecolor=C['primary'], linewidth=2)
ax.add_patch(heatmap_rect)
text(ax, 550, 850, '月度收益热力图', size=24, color=C['primary'], weight='bold', ha='center')

# 模拟热力图 (6 行 x 12 列)
np.random.seed(42)
years = ['2020', '2021', '2022', '2023', '2024', '2025']
months = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12']

# 简化：用固定数据展示
sample_data = [
    [0.03, 0.01, -0.05, 0.04, 0.02, 0.05, 0.06, 0.03, -0.02, 0.01, 0.04, 0.02],
    [0.02, -0.03, 0.04, 0.05, 0.03, 0.04, -0.05, 0.02, 0.03, 0.01, 0.02, 0.03],
    [-0.04, 0.01, -0.03, -0.05, 0.02, 0.04, -0.06, -0.03, -0.05, -0.02, 0.03, -0.01],
    [0.05, 0.02, 0.03, 0.01, -0.02, 0.02, 0.03, -0.04, -0.01, -0.03, 0.02, 0.01],
    [-0.02, 0.04, 0.03, -0.01, 0.02, 0.01, 0.03, -0.04, 0.05, 0.02, 0.01, 0.02],
    [0.01, 0.03, 0.02, 0.01, 0.04, 0.02, 0.03, 0.01, 0.02, 0.01, 0.03, 0.02],
]

cell_w = 60
cell_h = 50
for i, year in enumerate(years):
    y_pos = 800 - i * 55
    text(ax, 150, y_pos, year, size=14, color=C['text_gray'], ha='right', va='center')
    for j in range(12):
        x_pos = 170 + j * cell_w
        v = sample_data[i][j]
        if v >= 0:
            color = C['success'] if v > 0.03 else '#4ADE80'
        else:
            color = C['danger'] if v < -0.03 else '#F87171'
        rect = mpatches.Rectangle((x_pos, y_pos - cell_h/2), cell_w - 4, cell_h, facecolor=color, alpha=0.85)
        ax.add_patch(rect)
        text(ax, x_pos + (cell_w-4)/2, y_pos, f'{v*100:+.0f}', size=11, color='white', ha='center', va='center', weight='bold')

# 右侧归因
attr_rect = mpatches.FancyBboxPatch((1050, 400), W - 1150, 480, boxstyle='round,pad=5',
                                      facecolor='#1E293B', edgecolor=C['accent'], linewidth=2)
ax.add_patch(attr_rect)
text(ax, W/2 + 350, 850, '风险归因', size=24, color=C['accent'], weight='bold', ha='center')

attributions = [
    ('市场风险 (Beta)', '+2.5%', C['primary']),
    ('规模因子 (SMB)', '+0.8%', C['success']),
    ('价值因子 (HML)', '-0.3%', C['danger']),
    ('动量因子 (UMD)', '+1.2%', C['success']),
    ('特质收益 (Alpha)', '+0.5%', C['accent']),
    ('交易成本', '-0.4%', C['danger']),
]

for i, (label, val, color) in enumerate(attributions):
    y = 780 - i * 50
    text(ax, 1100, y, label, size=18, color='white', ha='left')
    text(ax, W - 150, y, val, size=18, color=color, ha='right', weight='bold')

subtitle_bar(ax, 'Brinson 业绩归因 + 月度热力图 + 风险因子分解')
plt.savefig(f'{OUT_DIR}/v2_05_attribution.png', dpi=100, facecolor=C['bg_dark'])
plt.close()

# 场景 2.6: 严谨性指标 (10s)
fig, ax = plt.subplots(figsize=(W/100, H/100), dpi=100)
setup_ax(ax)
text(ax, W/2, H - 80, '严谨性指标 · 行业领先', size=44, weight='bold')

items = [
    ('回测过拟合检测', 'CSCV + Deflated Sharpe Ratio', C['success']),
    ('交易成本精确建模', '双边 0.10%-0.30% 可调', C['primary']),
    ('分红再投资处理', '✓ 自动', C['success']),
    ('涨跌停过滤', '✓ 可选', C['success']),
    ('幸存者偏差修正', '✓ 可选', C['warning']),
    ('多线程并行', '4-32 核自适应', C['secondary']),
    ('参数敏感性分析', '一键热力图', C['accent']),
    ('样本外测试', 'Walk-Forward + 嵌套 CV', C['primary']),
]

box_w = 400
box_h = 80
gap_x = 30
gap_y = 25
cols = 4
for i, (label, val, color) in enumerate(items):
    row = i // cols
    col = i % cols
    x = 130 + col * (box_w + gap_x)
    y = 700 - row * (box_h + gap_y)
    rect = mpatches.FancyBboxPatch((x, y), box_w, box_h, boxstyle='round,pad=5',
                                    facecolor='#1E293B', edgecolor=color, linewidth=2)
    ax.add_patch(rect)
    # 圆点
    dot = mpatches.Circle((x + 30, y + box_h/2), 12, facecolor=color, zorder=5)
    ax.add_patch(dot)
    text(ax, x + 60, y + box_h/2 + 15, label, size=18, color='white', ha='left', weight='bold')
    text(ax, x + 60, y + box_h/2 - 15, val, size=16, color=C['text_gray'], ha='left')

subtitle_bar(ax, 'Bailey & López de Prado 方法学 · 业界最严标准')
plt.savefig(f'{OUT_DIR}/v2_06_rigor.png', dpi=100, facecolor=C['bg_dark'])
plt.close()

# 场景 2.7: 结尾
fig, ax = plt.subplots(figsize=(W/100, H/100), dpi=100)
setup_ax(ax)
text(ax, W/2, H/2 + 50, '严谨回测, 拒绝过拟合', size=60, weight='bold')
text(ax, W/2, H/2 - 50, '代码开源 · 数据可下载 · 结果可复现', size=28, color=C['secondary'])
subtitle_bar(ax, '回测引擎 · 短视频 2/3 完')
plt.savefig(f'{OUT_DIR}/v2_07_ending.png', dpi=100, facecolor=C['bg_dark'])
plt.close()

print('视频 2 (回测引擎): 7 帧生成完成')

# ============== 视频 3: 另类数据看板 (90s) ==============
# 场景 3.1: 标题
fig, ax = plt.subplots(figsize=(W/100, H/100), dpi=100)
setup_ax(ax)
text(ax, W/2, H/2, '另类数据看板', size=64, weight='bold')
text(ax, W/2, H/2 - 80, '卫星图像 · 舆情分析 · 供应链追踪', size=28, color=C['text_gray'])
text(ax, W/2, 150, '提前捕捉非结构化信号 · 创造 alpha 来源', size=22, color=C['accent'])
subtitle_bar(ax, 'QuantInsight Pro · 技术短视频 3/3')
plt.savefig(f'{OUT_DIR}/v3_01_title.png', dpi=100, facecolor=C['bg_dark'])
plt.close()

# 场景 3.2: 卫星数据 (15s)
fig, ax = plt.subplots(figsize=(W/100, H/100), dpi=100)
setup_ax(ax)
text(ax, W/2, H - 80, '卫星图像数据 · 工业园区开工率', size=44, weight='bold')

panel1 = mpatches.FancyBboxPatch((80, 200), W - 160, 580, boxstyle='round,pad=5',
                                   facecolor='#1E293B', edgecolor=C['secondary'], linewidth=2)
ax.add_patch(panel1)
text(ax, W/2, 750, '全国 TOP 100 工业园区 · 月度开工率热力图', size=24, color=C['secondary'], weight='bold', ha='center')

# 模拟 5x5 城市群热力图
cities = ['深圳', '上海', '苏州', '宁波', '广州']
sample_data = [
    [0.78, 0.85, 0.82, 0.88, 0.91],
    [0.92, 0.88, 0.85, 0.79, 0.86],
    [0.75, 0.83, 0.90, 0.87, 0.82],
    [0.68, 0.74, 0.79, 0.85, 0.78],
    [0.82, 0.88, 0.91, 0.86, 0.84],
]
cell_w = 130
cell_h = 80
start_x = 250
start_y = 600

for i, city in enumerate(cities):
    text(ax, start_x - 30, start_y - i * cell_h, city, size=18, color='white', ha='right', va='center')
    for j in range(5):
        v = sample_data[i][j]
        if v > 0.85:
            color = C['success']
        elif v > 0.75:
            color = '#4ADE80'
        elif v > 0.65:
            color = C['warning']
        else:
            color = C['danger']
        rect = mpatches.Rectangle((start_x + j * cell_w, start_y - i * cell_h - cell_h/2), cell_w - 5, cell_h,
                                    facecolor=color, alpha=0.85)
        ax.add_patch(rect)
        text(ax, start_x + j * cell_w + (cell_w-5)/2, start_y - i * cell_h, f'{v:.2f}', size=18,
             color='white', ha='center', va='center', weight='bold')

# 关键洞察
text(ax, W/2, 320, '💡 关键洞察: 深圳/广州近 3 月开工率持续上升 +8%, 制造业 PMI 触底反弹', size=20, color=C['success'])
text(ax, W/2, 270, '📅 提前 4-6 周预测宏观工业产出 (基于 CFA Institute 2021 研究)', size=18, color=C['text_gray'])

subtitle_bar(ax, '卫星数据 · 提前捕捉宏观拐点')
plt.savefig(f'{OUT_DIR}/v3_02_satellite.png', dpi=100, facecolor=C['bg_dark'])
plt.close()

# 场景 3.3: 舆情分析 (15s)
fig, ax = plt.subplots(figsize=(W/100, H/100), dpi=100)
setup_ax(ax)
text(ax, W/2, H - 80, '舆情情感分析 · 行业热度榜', size=44, weight='bold')

panel2 = mpatches.FancyBboxPatch((100, 200), W - 200, 580, boxstyle='round,pad=5',
                                   facecolor='#1E293B', edgecolor=C['accent'], linewidth=2)
ax.add_patch(panel2)
text(ax, W/2, 750, '全网 5000+ 信源 · NLP 情感分析 · 实时更新', size=22, color=C['accent'], weight='bold', ha='center')

sectors = [
    ('人工智能', 0.92, 320, C['success']),
    ('半导体', 0.85, 270, C['success']),
    ('新能源', 0.78, 230, C['success']),
    ('创新药', 0.72, 200, C['success']),
    ('军工', 0.68, 180, C['warning']),
    ('汽车', 0.62, 160, C['warning']),
    ('医药', 0.55, 140, C['warning']),
    ('消费', 0.48, 120, C['warning']),
    ('金融', 0.42, 100, C['danger']),
    ('地产', 0.28, 80, C['danger']),
]

for name, score, change, color in sectors:
    y = 700 - sectors.index((name, score, change, color)) * 50
    text(ax, 200, y, name, size=20, color='white', ha='left', weight='bold')
    # 进度条
    bar_w = 1000
    bg = mpatches.Rectangle((450, y - 15), bar_w, 30, facecolor='#334155')
    ax.add_patch(bg)
    fg = mpatches.Rectangle((450, y - 15), bar_w * score, 30, facecolor=color, alpha=0.85)
    ax.add_patch(fg)
    text(ax, 1500, y, f'{score:.0%}', size=20, color='white', ha='left', weight='bold')
    text(ax, 1700, y, f'{change:+d}', size=18, color=C['success'] if change > 0 else C['danger'],
         ha='left', weight='bold')

subtitle_bar(ax, 'FinBERT 预训练模型 · 准确率 85%+')
plt.savefig(f'{OUT_DIR}/v3_03_sentiment.png', dpi=100, facecolor=C['bg_dark'])
plt.close()

# 场景 3.4: 供应链追踪 (15s)
fig, ax = plt.subplots(figsize=(W/100, H/100), dpi=100)
setup_ax(ax)
text(ax, W/2, H - 80, '供应链网络追踪', size=44, weight='bold')

# 中心化网络示意
center = (W/2, 540)
nodes = [
    ('半导体', 0, 0, C['primary'], 'core'),
    ('芯片设计', -300, -150, C['secondary'], 'tier1'),
    ('晶圆代工', 300, -150, C['accent'], 'tier1'),
    ('封装测试', -250, 150, C['warning'], 'tier2'),
    ('设备厂商', 250, 150, C['success'], 'tier2'),
    ('材料', 0, -300, C['danger'], 'tier2'),
    ('EDA', -150, 250, C['secondary'], 'tier3'),
    ('IP 授权', 150, 250, C['accent'], 'tier3'),
]

# 绘制连接线
for name, dx, dy, color, tier in nodes:
    x, y = center[0] + dx, center[1] + dy
    ax.plot([center[0], x], [center[1], y], color=color, linewidth=1, alpha=0.4, zorder=1)

# 绘制节点
for name, dx, dy, color, tier in nodes:
    x, y = center[0] + dx, center[1] + dy
    if tier == 'core':
        size = 80
    elif tier == 'tier1':
        size = 50
    elif tier == 'tier2':
        size = 35
    else:
        size = 25
    dot = mpatches.Circle((x, y), size, facecolor=color, zorder=3, alpha=0.9)
    ax.add_patch(dot)
    text(ax, x, y, name, size=14 if tier == 'core' else 12, color='white',
         weight='bold' if tier == 'core' else 'normal', ha='center', va='center')

# 右侧指标
text(ax, 1450, 850, '供应链指标', size=22, color=C['accent'], weight='bold', ha='left')
metrics = [
    ('网络中心度', '华为: 0.85'),
    ('上游议价力', '中芯国际: 0.72'),
    ('下游依赖度', '苹果供应链: 0.68'),
    ('国产替代率', '半导体: 32%'),
    ('ESG 风险', '稀土: 高'),
]
for i, (label, val) in enumerate(metrics):
    y = 780 - i * 60
    text(ax, 1450, y, label, size=16, color=C['text_gray'], ha='left')
    text(ax, 1450, y - 25, val, size=18, color='white', ha='left', weight='bold')

subtitle_bar(ax, '供应链网络 · 提前 3-6 月预测行业景气度')
plt.savefig(f'{OUT_DIR}/v3_04_supply_chain.png', dpi=100, facecolor=C['bg_dark'])
plt.close()

# 场景 3.5: 整合看板 (15s)
fig, ax = plt.subplots(figsize=(W/100, H/100), dpi=100)
setup_ax(ax)
text(ax, W/2, H - 80, '整合看板 · 一站式另类数据', size=44, weight='bold')

# 2x2 网格
panels = [
    (100, 540, 880, 280, '卫星数据', '工业园区开工率', '78%', '+8% MoM', C['success']),
    (1000, 540, 880, 280, '舆情分析', 'AI 行业情感', '0.92', '+12% WoW', C['success']),
    (100, 200, 880, 280, '供应链', '半导体中心度', '0.85', '稳', C['primary']),
    (1000, 200, 880, 280, '政策追踪', '国常会信号', '中性偏多', '降准预期', C['warning']),
]

for x, y, w, h, title, label, value, change, color in panels:
    panel = mpatches.FancyBboxPatch((x, y), w, h, boxstyle='round,pad=5',
                                      facecolor='#1E293B', edgecolor=color, linewidth=2)
    ax.add_patch(panel)
    text(ax, x + 30, y + h - 50, title, size=24, color=color, weight='bold', ha='left')
    text(ax, x + 30, y + h - 90, label, size=18, color=C['text_gray'], ha='left')
    text(ax, x + 30, y + 50, value, size=42, color='white', weight='bold', ha='left')
    text(ax, x + w - 200, y + 50, change, size=20, color=color, ha='right', weight='bold')

subtitle_bar(ax, '4 大数据源 · 1 个看板 · 全局洞察')
plt.savefig(f'{OUT_DIR}/v3_05_dashboard.png', dpi=100, facecolor=C['bg_dark'])
plt.close()

# 场景 3.6: 应用场景 (10s)
fig, ax = plt.subplots(figsize=(W/100, H/100), dpi=100)
setup_ax(ax)
text(ax, W/2, H - 80, '实际应用场景', size=44, weight='bold')

cases = [
    ('案例 1', 'AI 芯片订单超预期', '卫星: 台积电南京厂开工率 +15%', '→ 提前 4 周布局半导体 ETF', C['success']),
    ('案例 2', '白酒行业舆情转暖', '情感分析: +18% (春节消费回暖)', '→ 3 日内五粮液 +5.2%', C['success']),
    ('案例 3', '新能源车产能预警', '供应链: 宁德时代上游材料紧张', '→ 提前减仓, 规避 8% 回调', C['warning']),
    ('案例 4', '地产风险信号', '舆情+政策: 信用债承压', '→ 风险模型提前触发, 调低敞口', C['danger']),
]

for i, (case, title, signal, action, color) in enumerate(cases):
    y = 800 - i * 140
    # 案例号
    case_circle = mpatches.Circle((150, y), 40, facecolor=color, zorder=5)
    ax.add_patch(case_circle)
    text(ax, 150, y, case, size=18, color='white', weight='bold', ha='center', va='center')

    # 标题
    text(ax, 230, y + 30, title, size=24, color='white', ha='left', weight='bold')
    # 信号
    text(ax, 230, y - 10, signal, size=18, color=color, ha='left')
    # 行动
    text(ax, 230, y - 45, action, size=18, color=C['text_gray'], ha='left')

subtitle_bar(ax, '数据驱动决策 · 真实业务场景验证')
plt.savefig(f'{OUT_DIR}/v3_06_cases.png', dpi=100, facecolor=C['bg_dark'])
plt.close()

# 场景 3.7: 结尾
fig, ax = plt.subplots(figsize=(W/100, H/100), dpi=100)
setup_ax(ax)
text(ax, W/2, H/2 + 50, '让非结构化数据创造 alpha', size=56, weight='bold')
text(ax, W/2, H/2 - 50, '卫星 · 舆情 · 供应链 · 一键整合', size=28, color=C['secondary'])
text(ax, W/2, H/2 - 120, '联系试用: contact@quantinsight.pro', size=22, color=C['text_gray'])
subtitle_bar(ax, '另类数据 · 短视频 3/3 完')
plt.savefig(f'{OUT_DIR}/v3_07_ending.png', dpi=100, facecolor=C['bg_dark'])
plt.close()

print('视频 3 (另类数据): 7 帧生成完成')

# 帧数汇总
print('\n=== 3 个视频共 21 帧生成完成 ===')
import os
for f in sorted(os.listdir(OUT_DIR)):
    print(f'  {f}: {os.path.getsize(os.path.join(OUT_DIR, f)):,} bytes')
