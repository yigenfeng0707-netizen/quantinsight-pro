"""
QuantInsight Pro - 回测图表生成
生成 NAV 曲线、回撤、月度收益分布、滚动夏普
"""
import pandas as pd
import numpy as np
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib import rcParams

# 中文字体
rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
rcParams['axes.unicode_minus'] = False

# 加载数据
with open('D:/shFintech/_backtest_nav.json', 'r', encoding='utf-8') as f:
    nav_data = json.load(f)
with open('D:/shFintech/_backtest_results.json', 'r', encoding='utf-8') as f:
    results = json.load(f)

# 转换 NAV 为 DataFrame
def nav_to_df(nav_dict):
    s = pd.Series(nav_dict)
    s.index = pd.to_datetime(s.index)
    s.sort_index(inplace=True)
    return s

nav_dfs = {k: nav_to_df(v) for k, v in nav_data.items()}

# ============== 图表 1: 沪深 300 三策略 NAV 对比 ==============
fig, axes = plt.subplots(2, 2, figsize=(16, 12))

# 子图 1: HS300 策略 NAV
ax = axes[0, 0]
for key in ['HS300_Benchmark', 'HS300_DualMA', 'HS300_MeanRev', 'HS300_MultiFactor']:
    label = {
        'HS300_Benchmark': '沪深300 买入持有',
        'HS300_DualMA': '双均线 (20/60)',
        'HS300_MeanRev': '均值回归 (布林带)',
        'HS300_MultiFactor': '多因子 (动量+反转)',
    }[key]
    nav_dfs[key].plot(ax=ax, label=label, linewidth=1.5)
ax.set_title('沪深 300 策略净值对比 (2020-01 ~ 2026-06)', fontsize=14, fontweight='bold')
ax.set_ylabel('净值 (NAV)')
ax.legend(loc='best', fontsize=9)
ax.grid(True, alpha=0.3)
ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
ax.xaxis.set_major_locator(mdates.MonthLocator(interval=6))

# 子图 2: 三大指数双均线对比
ax = axes[0, 1]
for key in ['HS300_Benchmark', 'ZZ500_Benchmark', 'CYB_Benchmark']:
    label = {
        'HS300_Benchmark': '沪深300',
        'ZZ500_Benchmark': '中证500',
        'CYB_Benchmark': '创业板指',
    }[key]
    nav_dfs[key].plot(ax=ax, label=label, linewidth=1.5)
ax.set_title('三大指数同期表现对比 (基准)', fontsize=14, fontweight='bold')
ax.set_ylabel('净值 (NAV)')
ax.legend(loc='best', fontsize=9)
ax.grid(True, alpha=0.3)
ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
ax.xaxis.set_major_locator(mdates.MonthLocator(interval=6))

# 子图 3: HS300 多因子回撤曲线
ax = axes[1, 0]
df_mf = nav_dfs['HS300_MultiFactor']
cummax = df_mf.cummax()
dd = (df_mf - cummax) / cummax
dd.plot(ax=ax, color='red', linewidth=1.2, label='多因子最大回撤')
ax.fill_between(dd.index, dd.values, 0, color='red', alpha=0.2)
ax.set_title('沪深300 多因子策略 - 回撤曲线', fontsize=14, fontweight='bold')
ax.set_ylabel('回撤 (%)')
ax.legend(loc='best', fontsize=9)
ax.grid(True, alpha=0.3)
ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
ax.xaxis.set_major_locator(mdates.MonthLocator(interval=6))

# 子图 4: 滚动夏普 (252日)
ax = axes[1, 1]
for key in ['HS300_DualMA', 'HS300_MultiFactor', 'ZZ500_DualMA']:
    label = {
        'HS300_DualMA': 'HS300 双均线',
        'HS300_MultiFactor': 'HS300 多因子',
        'ZZ500_DualMA': 'ZZ500 双均线',
    }[key]
    nav = nav_dfs[key]
    daily_ret = nav.pct_change().fillna(0)
    rolling_sharpe = (daily_ret.rolling(252).mean() * 252 - 0.025) / (daily_ret.rolling(252).std() * np.sqrt(252))
    rolling_sharpe.plot(ax=ax, label=label, linewidth=1.2)
ax.axhline(y=0, color='black', linestyle='--', alpha=0.5)
ax.axhline(y=1, color='green', linestyle='--', alpha=0.3, label='夏普=1')
ax.set_title('滚动 252 日夏普比率', fontsize=14, fontweight='bold')
ax.set_ylabel('夏普比率')
ax.legend(loc='best', fontsize=9)
ax.grid(True, alpha=0.3)
ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
ax.xaxis.set_major_locator(mdates.MonthLocator(interval=6))

plt.tight_layout()
plt.savefig('D:/shFintech/_chart_nav_comparison.png', dpi=150, bbox_inches='tight', facecolor='white')
plt.close()
print('Chart 1 saved: NAV 对比')

# ============== 图表 2: 三大指数多因子策略 ==============
fig, ax = plt.subplots(figsize=(12, 7))
for key in ['HS300_MultiFactor', 'ZZ500_MultiFactor', 'CYB_MultiFactor']:
    label = {
        'HS300_MultiFactor': '沪深300 多因子',
        'ZZ500_MultiFactor': '中证500 多因子',
        'CYB_MultiFactor': '创业板 多因子',
    }[key]
    nav_dfs[key].plot(ax=ax, label=label, linewidth=2)
ax.set_title('多因子策略在三大指数的表现 (2020-01 ~ 2026-06)', fontsize=15, fontweight='bold')
ax.set_ylabel('净值 (NAV)')
ax.legend(loc='best', fontsize=11)
ax.grid(True, alpha=0.3)
ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
ax.xaxis.set_major_locator(mdates.MonthLocator(interval=6))
plt.tight_layout()
plt.savefig('D:/shFintech/_chart_multifactor.png', dpi=150, bbox_inches='tight', facecolor='white')
plt.close()
print('Chart 2 saved: 多因子策略')

# ============== 图表 3: 月度收益热力图 ==============
fig, axes = plt.subplots(3, 1, figsize=(14, 12))

for idx, key in enumerate(['HS300_MultiFactor', 'ZZ500_MultiFactor', 'CYB_MultiFactor']):
    nav = nav_dfs[key]
    monthly_ret = nav.resample('ME').last().pct_change().dropna()

    # 构建年-月矩阵
    monthly_ret.index = pd.to_datetime(monthly_ret.index)
    years = monthly_ret.index.year
    months = monthly_ret.index.month
    matrix = pd.DataFrame(monthly_ret.values, index=[years, months], columns=['return'])

    pivot = matrix.unstack(level=1)
    pivot.columns = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'][:len(pivot.columns)]

    label = {
        'HS300_MultiFactor': '沪深300 多因子',
        'ZZ500_MultiFactor': '中证500 多因子',
        'CYB_MultiFactor': '创业板 多因子',
    }[key]

    ax = axes[idx]
    im = ax.imshow(pivot.values * 100, cmap='RdYlGn', aspect='auto', vmin=-15, vmax=15)
    ax.set_xticks(range(len(pivot.columns)))
    ax.set_xticklabels(pivot.columns)
    ax.set_yticks(range(len(pivot.index)))
    ax.set_yticklabels(pivot.index)
    ax.set_title(f'{label} - 月度收益率热力图 (%)', fontsize=12, fontweight='bold')

    # 标注数字
    for i in range(len(pivot.index)):
        for j in range(len(pivot.columns)):
            val = pivot.values[i, j] * 100
            if not np.isnan(val):
                color = 'white' if abs(val) > 8 else 'black'
                ax.text(j, i, f'{val:.1f}', ha='center', va='center', fontsize=8, color=color)

plt.tight_layout()
plt.savefig('D:/shFintech/_chart_monthly_heatmap.png', dpi=150, bbox_inches='tight', facecolor='white')
plt.close()
print('Chart 3 saved: 月度收益热力图')

# ============== 图表 4: 综合指标雷达图 ==============
fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(polar=True))

# 选取 4 个代表性策略 + 基准
selected = ['HS300_BuyHold', 'HS300_DualMA', 'HS300_MultiFactor', 'CYB_MultiFactor']
categories = ['年化收益', '夏普比率', '胜率', 'Calmar', '1-最大回撤']

# 归一化到 0-1
for key in selected:
    m = results[key]
    # 归一化指标
    norm_vals = [
        max(0, min(1, (m['annual_return'] + 0.1) / 0.3)),  # 年化 -10%~20% 归一
        max(0, min(1, (m['sharpe'] + 1) / 2)),  # 夏普 -1~1 归一
        m['win_rate'],  # 胜率 0-1
        max(0, min(1, (m['calmar'] + 0.5) / 1.5)),  # Calmar
        max(0, min(1, 1 + m['max_drawdown'])),  # 1-回撤
    ]
    angles = np.linspace(0, 2 * np.pi, len(categories), endpoint=False).tolist()
    norm_vals += norm_vals[:1]
    angles += angles[:1]
    label = {
        'HS300_BuyHold': '沪深300 基准',
        'HS300_DualMA': '沪深300 双均线',
        'HS300_MultiFactor': '沪深300 多因子',
        'CYB_MultiFactor': '创业板 多因子',
    }[key]
    ax.plot(angles, norm_vals, linewidth=2, label=label)
    ax.fill(angles, norm_vals, alpha=0.1)

ax.set_xticks(angles[:-1])
ax.set_xticklabels(categories, fontsize=11)
ax.set_ylim(0, 1)
ax.set_title('策略综合能力雷达图', fontsize=15, fontweight='bold', pad=20)
ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1), fontsize=10)
ax.grid(True)

plt.tight_layout()
plt.savefig('D:/shFintech/_chart_radar.png', dpi=150, bbox_inches='tight', facecolor='white')
plt.close()
print('Chart 4 saved: 雷达图')

# ============== 图表 5: 累计收益对比柱状图 ==============
fig, ax = plt.subplots(figsize=(12, 7))

strategies = list(results.keys())
annual_rets = [results[k]['annual_return'] * 100 for k in strategies]
sharpes = [results[k]['sharpe'] for k in strategies]
max_dds = [results[k]['max_drawdown'] * 100 for k in strategies]

x = np.arange(len(strategies))
width = 0.25

ax.bar(x - width, annual_rets, width, label='年化收益 (%)', color='#2E86AB')
ax.bar(x, sharpes, width, label='夏普比率', color='#A23B72')
ax.bar(x + width, max_dds, width, label='最大回撤 (%)', color='#F18F01')

ax.set_xticks(x)
ax.set_xticklabels([k.replace('_', '\n') for k in strategies], rotation=0, fontsize=8)
ax.set_ylabel('数值')
ax.set_title('所有策略核心指标对比', fontsize=14, fontweight='bold')
ax.legend()
ax.grid(True, alpha=0.3, axis='y')
ax.axhline(y=0, color='black', linewidth=0.5)
plt.tight_layout()
plt.savefig('D:/shFintech/_chart_metrics_bar.png', dpi=150, bbox_inches='tight', facecolor='white')
plt.close()
print('Chart 5 saved: 指标柱状图')

print('\n所有图表生成完成！')
