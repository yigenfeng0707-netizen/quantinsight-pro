"""Render professional charts for AFAC BP PPT (matplotlib)."""
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib
import numpy as np

matplotlib.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'Arial Unicode MS', 'DejaVu Sans']
matplotlib.rcParams['axes.unicode_minus'] = False

ROOT = Path(r'd:\AFAC2026金融智能创新大赛\quantinsight-deploy')
OUT = ROOT / 'delivery' / '06_图表素材' / 'bp_charts'
OUT.mkdir(parents=True, exist_ok=True)

PRIMARY = '#1F77B4'
SUCCESS = '#2CA02C'
WARNING = '#FF7F0E'
DANGER = '#D62728'
GRAY = '#6B7280'


def save(fig, name: str):
    path = OUT / name
    fig.savefig(path, dpi=180, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    print(f'OK {path.name} ({path.stat().st_size // 1024} KB)')


def chart_tam_sam_som():
    fig, ax = plt.subplots(figsize=(10, 5.5))
    labels = ['TAM\n中国资管科技\n~2000亿', 'SAM\n中小私募长尾\n~300亿', 'SOM\n5年可触达\n~45亿']
    sizes = [2000, 300, 45]
    colors = [PRIMARY, WARNING, SUCCESS]
    y = np.arange(len(labels))
    bars = ax.barh(y, sizes, color=colors, height=0.55, edgecolor='white')
    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=12)
    ax.set_xlabel('市场规模（亿元）', fontsize=12)
    ax.set_title('市场规模：TAM / SAM / SOM', fontsize=16, fontweight='bold', pad=12)
    for bar, v in zip(bars, sizes):
        ax.text(v + 30, bar.get_y() + bar.get_height() / 2, f'{v} 亿',
                va='center', fontsize=12, fontweight='bold', color=GRAY)
    ax.set_xlim(0, 2400)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.grid(axis='x', linestyle='--', alpha=0.3)
    save(fig, '08_tam_sam_som.png')


def chart_revenue_profit():
    years = ['2026', '2027', '2028', '2029', '2030']
    revenue = [0.20, 0.73, 2.01, 4.30, 7.95]
    profit = [-0.184, -0.08, 0.2925, 0.931, 1.98]
    fig, ax1 = plt.subplots(figsize=(10, 5.5))
    x = np.arange(len(years))
    w = 0.35
    b1 = ax1.bar(x - w / 2, revenue, w, label='营收（亿元）', color=PRIMARY)
    b2 = ax1.bar(x + w / 2, profit, w, label='净利润（亿元）', color=SUCCESS)
    ax1.axhline(0, color='#999', linewidth=0.8)
    ax1.set_xticks(x)
    ax1.set_xticklabels(years, fontsize=12)
    ax1.set_ylabel('金额（亿元）', fontsize=12)
    ax1.set_title('5 年财务预测（基准场景）', fontsize=16, fontweight='bold', pad=12)
    ax1.legend(loc='upper left', fontsize=11)
    for bars in (b1, b2):
        for bar in bars:
            h = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width() / 2, h + (0.08 if h >= 0 else -0.18),
                     f'{h:.2f}', ha='center', va='bottom' if h >= 0 else 'top', fontsize=9)
    ax1.spines['top'].set_visible(False)
    ax1.spines['right'].set_visible(False)
    ax1.grid(axis='y', linestyle='--', alpha=0.3)
    save(fig, '09_revenue_profit.png')


def chart_funding_pie():
    labels = ['研发 40%', '团队 30%', '数据 20%', '营销 6%', '其他 4%']
    sizes = [40, 30, 20, 6, 4]
    colors = [PRIMARY, SUCCESS, WARNING, '#9467BD', GRAY]
    fig, ax = plt.subplots(figsize=(8, 5.5))
    wedges, texts, autotexts = ax.pie(
        sizes, labels=labels, colors=colors, autopct='%1.0f%%',
        startangle=90, pctdistance=0.7,
        wedgeprops=dict(width=0.45, edgecolor='white'))
    for t in texts:
        t.set_fontsize(11)
    for t in autotexts:
        t.set_fontsize(10)
        t.set_color('white')
        t.set_fontweight('bold')
    ax.set_title('天使轮 500 万用途分配', fontsize=16, fontweight='bold', pad=12)
    ax.text(0, 0, '500万\n天使轮', ha='center', va='center', fontsize=14, fontweight='bold', color=PRIMARY)
    save(fig, '10_angel_use_of_funds.png')


def chart_competition_matrix():
    # dimensions: AI能力, 可解释性, 价格友好, 中小私募适配, 另类数据, 开源透明
    dims = ['AI能力', '可解释性', '价格友好', '中小私募\n适配', '另类数据', '开源透明']
    players = {
        'QuantInsight': [9, 10, 9, 10, 8, 9],
        'Wind': [5, 3, 2, 3, 6, 2],
        '同花顺': [6, 3, 5, 5, 5, 2],
        '恒生': [4, 3, 4, 4, 4, 3],
    }
    colors = {k: c for k, c in zip(players, [PRIMARY, DANGER, WARNING, GRAY])}
    angles = np.linspace(0, 2 * np.pi, len(dims), endpoint=False).tolist()
    angles += angles[:1]
    fig, ax = plt.subplots(figsize=(8, 6.5), subplot_kw=dict(polar=True))
    for name, vals in players.items():
        data = vals + vals[:1]
        ax.plot(angles, data, linewidth=2, label=name, color=colors[name])
        ax.fill(angles, data, alpha=0.12, color=colors[name])
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(dims, fontsize=11)
    ax.set_ylim(0, 10)
    ax.set_yticks([2, 4, 6, 8, 10])
    ax.set_title('竞争对比雷达图', fontsize=16, fontweight='bold', pad=18)
    ax.legend(loc='upper right', bbox_to_anchor=(1.35, 1.1), fontsize=10)
    save(fig, '11_competition_radar.png')


def chart_backtest_table_visual():
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.axis('off')
    cols = ['策略', '年化收益', '夏普', '最大回撤', '交易次数']
    rows = [
        ['买入持有(基准)', '5.46%', '0.35', '-72.30%', '0'],
        ['双均线', '6.57%', '0.48', '-49.39%', '109'],
        ['多因子(核心)', '8.56%', '0.63', '-38.33%', '407'],
        ['动量', '8.13%', '0.57', '-39.66%', '255'],
    ]
    table = ax.table(cellText=rows, colLabels=cols, loc='center', cellLoc='center')
    table.auto_set_font_size(False)
    table.set_fontsize(12)
    table.scale(1.2, 2.0)
    for (r, c), cell in table.get_celld().items():
        cell.set_edgecolor('#E5E7EB')
        if r == 0:
            cell.set_facecolor(PRIMARY)
            cell.set_text_props(color='white', fontweight='bold')
        elif r == 3:  # multifactor row index in 1-based with header -> row 3 is multifactor
            cell.set_facecolor('#E8F4FC')
            if c == 0:
                cell.set_text_props(fontweight='bold', color=PRIMARY)
        else:
            cell.set_facecolor('white')
    ax.set_title('沪深300 · 11.4年回测（T35修正）', fontsize=16, fontweight='bold', pad=8)
    save(fig, '12_backtest_table.png')


def chart_milestones():
    fig, ax = plt.subplots(figsize=(11, 4.5))
    stages = ['种子期\n2026\n5–30客户', '成长期\n2027\n30–85', '扩张期\n2028\n85–200', '领先期\n2029\n200–380', '龙头期\n2030\n380–620']
    x = np.arange(len(stages))
    y = [30, 85, 200, 380, 620]
    ax.plot(x, y, '-o', color=PRIMARY, linewidth=3, markersize=12)
    ax.fill_between(x, y, alpha=0.15, color=PRIMARY)
    for i, (xi, yi, lab) in enumerate(zip(x, y, stages)):
        ax.annotate(lab, (xi, yi), textcoords='offset points', xytext=(0, 14),
                    ha='center', fontsize=10, fontweight='bold', color=PRIMARY)
    ax.set_xticks([])
    ax.set_ylabel('客户数（家）', fontsize=12)
    ax.set_title('客户拓展路线图 30 → 620', fontsize=16, fontweight='bold', pad=12)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.grid(axis='y', linestyle='--', alpha=0.3)
    save(fig, '13_milestone_roadmap.png')


if __name__ == '__main__':
    chart_tam_sam_som()
    chart_revenue_profit()
    chart_funding_pie()
    chart_competition_matrix()
    chart_backtest_table_visual()
    chart_milestones()
    print('ALL CHARTS DONE ->', OUT)
