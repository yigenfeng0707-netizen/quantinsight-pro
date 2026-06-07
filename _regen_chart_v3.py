"""用 V3 数据更新财务图表"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.font_manager as fm

# 字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

years = ['2026', '2027', '2028', '2029', '2030']
revenue = [2000, 7300, 20100, 42960, 79500]  # 万元
net_profit = [-1840, -800, 2925, 9310, 19800]  # 万元
net_margin = [-92, -11, 15, 22, 25]  # %
gross_margin = [38, 58, 71, 75, 78]  # %
customers = [30, 85, 200, 380, 620]
team_size = [26, 58, 117, 201, 284]

fig, axes = plt.subplots(2, 2, figsize=(16, 12))
fig.suptitle('QuantInsight Pro - 财务模型 V3.0 关键指标 (5 年)', fontsize=18, fontweight='bold', y=0.98)

# 1. 营收 vs 净利润
ax = axes[0, 0]
x = np.arange(len(years))
width = 0.35
bars1 = ax.bar(x - width/2, [r/1000 for r in revenue], width, label='营业收入 (千万)', color='#2E86AB', edgecolor='black')
bars2 = ax.bar(x + width/2, [n/1000 for n in net_profit], width, label='净利润 (千万)', color='#A23B72', edgecolor='black')
ax.axhline(y=0, color='black', linewidth=0.8)
ax.set_xlabel('年份', fontsize=12)
ax.set_ylabel('金额 (千万元)', fontsize=12)
ax.set_title('营业收入与净利润', fontsize=14, fontweight='bold')
ax.set_xticks(x)
ax.set_xticklabels(years)
ax.legend(loc='upper left', fontsize=11)
ax.grid(True, alpha=0.3)
for bars in [bars1, bars2]:
    for bar in bars:
        h = bar.get_height()
        va = 'bottom' if h >= 0 else 'top'
        offset = 0.3 if h >= 0 else -0.6
        ax.text(bar.get_x() + bar.get_width()/2, h + offset, f'{h:.1f}',
                ha='center', va=va, fontsize=9, fontweight='bold')

# 2. 毛利率与净利率
ax = axes[0, 1]
ax.plot(years, gross_margin, marker='o', linewidth=2.5, markersize=10, label='毛利率', color='#2E86AB')
ax.plot(years, net_margin, marker='s', linewidth=2.5, markersize=10, label='净利率', color='#A23B72')
ax.axhline(y=0, color='black', linewidth=0.5, linestyle='--')
ax.set_xlabel('年份', fontsize=12)
ax.set_ylabel('百分比 (%)', fontsize=12)
ax.set_title('毛利率与净利率', fontsize=14, fontweight='bold')
ax.legend(loc='lower right', fontsize=11)
ax.grid(True, alpha=0.3)
for i, (g, n) in enumerate(zip(gross_margin, net_margin)):
    ax.text(i, g+1.5, f'{g}%', ha='center', fontsize=9, color='#2E86AB', fontweight='bold')
    ax.text(i, n+1.5, f'{n}%', ha='center', fontsize=9, color='#A23B72', fontweight='bold')

# 3. 客户数与团队规模
ax = axes[1, 0]
ax2 = ax.twinx()
line1 = ax.plot(years, customers, marker='o', linewidth=2.5, markersize=10, color='#5A4FCF', label='客户数 (家)')
line2 = ax2.plot(years, team_size, marker='s', linewidth=2.5, markersize=10, color='#F18F01', label='团队规模 (人)')
ax.set_xlabel('年份', fontsize=12)
ax.set_ylabel('客户数 (家)', fontsize=12, color='#5A4FCF')
ax2.set_ylabel('团队规模 (人)', fontsize=12, color='#F18F01')
ax.set_title('客户数与团队规模', fontsize=14, fontweight='bold')
lines = line1 + line2
labels = [l.get_label() for l in lines]
ax.legend(lines, labels, loc='upper left', fontsize=11)
ax.grid(True, alpha=0.3)
for i, c in enumerate(customers):
    ax.text(i, c+15, f'{c}', ha='center', fontsize=9, color='#5A4FCF', fontweight='bold')
for i, t in enumerate(team_size):
    ax2.text(i, t+8, f'{t}', ha='center', fontsize=9, color='#F18F01', fontweight='bold')

# 4. 关键比率
ax = axes[1, 1]
metrics = ['LTV/CAC', '回收期(月)', '续约率(%)', 'NRR(%)']
v3_values = [40, 5, 92, 120]
bench_values = [3, 18, 85, 100]
x = np.arange(len(metrics))
width = 0.35
bars1 = ax.bar(x - width/2, v3_values, width, label='QuantInsight Pro', color='#2E86AB', edgecolor='black')
bars2 = ax.bar(x + width/2, bench_values, width, label='行业基准', color='#999999', edgecolor='black')
ax.set_ylabel('数值', fontsize=12)
ax.set_title('单位经济指标 vs 行业基准', fontsize=14, fontweight='bold')
ax.set_xticks(x)
ax.set_xticklabels(metrics, rotation=15)
ax.legend(loc='upper right', fontsize=11)
ax.grid(True, alpha=0.3)
for bars, vals in [(bars1, v3_values), (bars2, bench_values)]:
    for bar, v in zip(bars, vals):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1, f'{v}',
                ha='center', fontsize=9, fontweight='bold')

plt.tight_layout()
plt.savefig('D:/shFintech/QuantInsight_Pro_Chart_01_Financial.png', dpi=150, bbox_inches='tight', facecolor='white')
import os
size = os.path.getsize('D:/shFintech/QuantInsight_Pro_Chart_01_Financial.png') / 1024
print(f'[OK] 财务图表 V3 已更新: {size:.0f} KB')
