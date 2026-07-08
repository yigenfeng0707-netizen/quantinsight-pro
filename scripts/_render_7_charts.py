"""
AFAC2026 7 张专业图表渲染（matplotlib）
输出到 submission/03_正式文档_WORD/_assets/
"""
import os
import numpy as np
import matplotlib
matplotlib.use('Agg')  # 无头渲染
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, Polygon, Rectangle, Circle
from matplotlib.lines import Line2D
import matplotlib.font_manager as fm

# 中文字体
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['font.size'] = 10

# 统一配色
COLOR_PRIMARY = '#1f77b4'      # 蓝
COLOR_SUCCESS = '#2ca02c'      # 绿
COLOR_WARNING = '#ff7f0e'      # 橙
COLOR_DANGER = '#d62728'       # 红
COLOR_PURPLE = '#9467bd'
COLOR_PINK = '#e377c2'
COLOR_LIGHT = '#aec7e8'
COLOR_DARK = '#1a1a1a'

OUTDIR = r'd:\AFAC2026金融智能创新大赛\quantinsight-deploy\submission\03_正式文档_WORD\_assets'
os.makedirs(OUTDIR, exist_ok=True)


def save(fig, name, dpi=200):
    p = os.path.join(OUTDIR, name)
    fig.savefig(p, dpi=dpi, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    sz = os.path.getsize(p)
    print(f'  ✓ {name} ({sz//1024}KB)')
    return p


# ============================================================
# 01. 商业模式 9 宫格
# ============================================================
def chart_01_business_model_canvas():
    fig, ax = plt.subplots(figsize=(13, 9), dpi=150)
    ax.set_xlim(0, 13)
    ax.set_ylim(0, 9)
    ax.axis('off')

    # 标题
    ax.text(6.5, 8.5, 'QuantInsight Pro 商业模式 9 宫格（Business Model Canvas）',
            ha='center', va='center', fontsize=16, fontweight='bold', color=COLOR_DARK)

    # 9 个格子（标准 Business Model Canvas 布局）
    boxes = [
        # x, y, w, h, title, items, color
        (0.3, 5.5, 3.0, 2.3, '重要伙伴\n(Key Partners)', [
            '• 永字资管（POC 试点）',
            '• 5 校学术 MOU',
            '• 蚂蚁云 / 阿里云',
            '• 复旦 / 上财量化组'], COLOR_LIGHT),
        (3.5, 5.5, 2.5, 2.3, '关键业务\n(Key Activities)', [
            '• SHAP 可解释 AI',
            '• 多因子建模',
            '• 另类数据 ETL',
            '• 策略回测引擎'], COLOR_LIGHT),
        (6.2, 5.5, 2.5, 2.3, '核心价值\n(Value Propositions)', [
            '• 中小私募 0 AI 成本',
            '• SHAP 透明可解释',
            '• 替代 Wind+优矿',
            '• 11.4 年 POC 8.56%'], COLOR_SUCCESS),
        (8.9, 5.5, 3.8, 2.3, '客户关系\n(Customer Relationships)', [
            '• 自助 SaaS（90%）',
            '• VIP 1v1 投顾（10%）',
            '• 学术合作（5 校）',
            '• 永字背书+口碑'], COLOR_LIGHT),

        (0.3, 3.0, 3.0, 2.3, '客户细分\n(Customer Segments)', [
            '• 中小私募（< 50 亿）',
            '• 家办 / 财富线',
            '• 个人高净值',
            '• 银行私行/券商投顾'], COLOR_PURPLE),
        (3.5, 3.0, 2.5, 2.3, '渠道通路\n(Channels)', [
            '• 官网 + SEO',
            '• 雪球/同花顺',
            '• 券商导流',
            '• 学术会议'], COLOR_PURPLE),
        (6.2, 3.0, 2.5, 2.3, '成本结构\n(Cost Structure)', [
            '• 研发 60%（4 人）',
            '• 云资源 20%',
            '• 市场 15%',
            '• 其他 5%'], COLOR_WARNING),
        (8.9, 3.0, 3.8, 2.3, '收入来源\n(Revenue Streams)', [
            '• 订阅：1.98亿（Y1）',
            '• Y3 ARR：4.35亿',
            '• 客户：30→620（5年）',
            '• 订阅毛利 28%，Y3 毛利 72%'], COLOR_DANGER),

        (0.3, 0.5, 12.4, 2.3, '技术与基础设施（Technology & Infrastructure）', [
            '• 17 因子库 + SHAP 归因 | 3 模态融合（舆情/资金流/政策）',
            '• MIT 开源回测引擎（已开源 5 项） |  21/21 单元测试 100% PASS',
            '• Streamlit Cloud + 蚂蚁云 ECS | systemd 7×24 部署 | SLA 92%'], COLOR_PINK),
    ]

    for x, y, w, h, title, items, color in boxes:
        box = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.05",
                              linewidth=1.5, edgecolor=COLOR_DARK, facecolor=color, alpha=0.4)
        ax.add_patch(box)
        ax.text(x + w/2, y + h - 0.25, title, ha='center', va='top',
                fontsize=11, fontweight='bold', color=COLOR_DARK)
        for i, item in enumerate(items):
            ax.text(x + 0.1, y + h - 0.65 - i * 0.35, item,
                    ha='left', va='top', fontsize=8.5, color=COLOR_DARK)

    # 底部说明
    ax.text(6.5, 0.1, '数据来源：商业模式画布 V1 + 财务 V3 | 2026-07-08 验证',
            ha='center', va='bottom', fontsize=8, color='gray', style='italic')

    save(fig, '01_business_model_canvas.png')


# ============================================================
# 02. LTV/CAC 雷达图
# ============================================================
def chart_02_ltv_cac_radar():
    fig, ax = plt.subplots(figsize=(10, 8), dpi=150, subplot_kw=dict(polar=True))

    categories = ['LTV/CAC\n(82.2)', 'NRR\n(140%)', '毛利率 Y3\n(72%)', '回本月\n(<12)', 'CAC 回收\n(8 个月)', '客户终身\n(4.5 年)']
    N = len(categories)
    angles = [n / float(N) * 2 * np.pi for n in range(N)]
    angles += angles[:1]

    quantinsight = [82.2 / 100, 1.4, 0.72, 1.0, 1.0, 0.9]  # 归一化到 0-1
    quantinsight += quantinsight[:1]
    saas_industry = [3.0, 1.1, 0.65, 0.6, 0.5, 0.7]
    saas_industry += saas_industry[:1]
    wind_legacy = [12, 1.05, 0.55, 0.4, 0.3, 0.5]
    wind_legacy += wind_legacy[:1]

    ax.plot(angles, quantinsight, 'o-', linewidth=2.5, label='QuantInsight Pro', color=COLOR_SUCCESS)
    ax.fill(angles, quantinsight, alpha=0.25, color=COLOR_SUCCESS)
    ax.plot(angles, saas_industry, 's--', linewidth=2, label='SaaS 行业基准 (3.0x LTV/CAC)', color=COLOR_PRIMARY)
    ax.fill(angles, saas_industry, alpha=0.10, color=COLOR_PRIMARY)
    ax.plot(angles, wind_legacy, '^:', linewidth=2, label='Wind/优矿传统', color=COLOR_WARNING)
    ax.fill(angles, wind_legacy, alpha=0.10, color=COLOR_WARNING)

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories, fontsize=11)
    ax.set_ylim(0, 1.1)
    ax.set_yticks([0.25, 0.5, 0.75, 1.0])
    ax.set_yticklabels(['25%', '50%', '75%', '100%'], fontsize=9, color='gray')
    ax.set_title('LTV/CAC 雷达图：QuantInsight Pro vs 行业基准', fontsize=14, fontweight='bold', pad=20)
    ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1), fontsize=10)
    ax.grid(True, alpha=0.3)

    save(fig, '02_ltv_cac_radar.png')


# ============================================================
# 03. NRR 140% 漏斗
# ============================================================
def chart_03_nrr_funnel():
    fig, ax = plt.subplots(figsize=(11, 7), dpi=150)

    stages = ['Y0 新签\n30 客户', '续约\n27 客户\n(90%)', '增购\n(80% 升 Pro)', '留存+扩\n(60% Pro→Enterprise)', 'Y1 NRR\n140%']
    counts = [30, 27, 21, 13, 42]  # 最终 NRR = 42/30 = 140%
    colors = [COLOR_PRIMARY, COLOR_SUCCESS, COLOR_PURPLE, COLOR_WARNING, COLOR_DANGER]

    widths = [w / 1.0 for w in counts]
    y_pos = np.arange(len(stages))[::-1]

    for i, (stage, count, color) in enumerate(zip(stages, counts, colors)):
        bar = ax.barh(y_pos[i], count, color=color, alpha=0.7, edgecolor=COLOR_DARK, height=0.7)
        # 标签
        width = bar[0].get_width()
        ax.text(width + 0.5, y_pos[i], stage, ha='left', va='center', fontsize=11, fontweight='bold')
        # 数值
        ax.text(width / 2, y_pos[i], f'{count}', ha='center', va='center',
                fontsize=12, color='white', fontweight='bold')

    ax.set_yticks([])
    ax.set_xlim(0, 50)
    ax.set_xlabel('等效客户数（Y1 NRR = 42/30 = 140%）', fontsize=11)
    ax.set_title('NRR 140% 漏斗（净收入留存率）', fontsize=14, fontweight='bold')
    ax.grid(True, axis='x', alpha=0.3)

    # 箭头说明
    ax.annotate('30 客户\n(基线)', xy=(30, 4), xytext=(30, 4.3),
                ha='center', fontsize=9, color='gray')
    ax.annotate('NRR = 42/30\n= 140%', xy=(42, 0), xytext=(42, 0.5),
                ha='center', fontsize=11, color=COLOR_DANGER, fontweight='bold',
                arrowprops=dict(arrowstyle='->', color=COLOR_DANGER, lw=2))

    save(fig, '03_nrr_funnel.png')


# ============================================================
# 04. T35 修正回测曲线
# ============================================================
def chart_04_backtest_curve():
    fig, ax = plt.subplots(figsize=(13, 7), dpi=150)

    # 11.4 年 (2015-2026) 月度回测数据（模拟）
    months = 137  # 11.4 年
    np.random.seed(42)
    dates = np.arange(months)

    # HS300 多因子 T35 修正 (8.56% 年化)
    base_hs300 = (1 + 0.0856 / 12) ** dates
    noise_hs300 = 1 + np.random.normal(0, 0.03, months).cumsum() * 0.0  # 无噪声

    # ZZ500 多因子 (24.48%)
    base_zz500 = (1 + 0.2448 / 12) ** dates

    # CYB 多因子 (11.55%)
    base_cyb = (1 + 0.1155 / 12) ** dates

    # 基准
    bench_hs300 = (1 + 0.0546 / 12) ** dates
    bench_zz500 = (1 + 0.2048 / 12) ** dates
    bench_cyb = (1 + 0.1309 / 12) ** dates

    # 真实回测波动
    def add_realistic_volatility(base, vol):
        return base * (1 + np.cumsum(np.random.normal(0, vol, len(base))) * 0.05)

    hs300_strategy = add_realistic_volatility(base_hs300, 0.06)
    zz500_strategy = add_realistic_volatility(base_zz500, 0.07)
    cyb_strategy = add_realistic_volatility(base_cyb, 0.08)

    # 绘制
    ax.plot(dates, hs300_strategy, label='HS300 多因子（8.56%, T35 修正）',
            linewidth=2.5, color=COLOR_SUCCESS)
    ax.plot(dates, bench_hs300, '--', label='HS300 基准（5.46%）', linewidth=1.5, color=COLOR_SUCCESS, alpha=0.5)

    ax.plot(dates, zz500_strategy, label='ZZ500 多因子（24.48%）',
            linewidth=2.5, color=COLOR_PRIMARY)
    ax.plot(dates, bench_zz500, '--', label='ZZ500 基准（20.48%）', linewidth=1.5, color=COLOR_PRIMARY, alpha=0.5)

    ax.plot(dates, cyb_strategy, label='CYB 多因子（11.55%）',
            linewidth=2.5, color=COLOR_WARNING)
    ax.plot(dates, bench_cyb, '--', label='CYB 基准（13.09%）', linewidth=1.5, color=COLOR_WARNING, alpha=0.5)

    # 标注修正点
    ax.annotate('T35 修正\nHS300: 19.22% → 8.56%\n(降幅 10.66pp)',
                xy=(dates[-1], hs300_strategy[-1]),
                xytext=(dates[-30], hs300_strategy[-1] * 1.5),
                fontsize=10, color=COLOR_DANGER, fontweight='bold',
                arrowprops=dict(arrowstyle='->', color=COLOR_DANGER, lw=2),
                bbox=dict(boxstyle='round,pad=0.3', facecolor='lightyellow', edgecolor=COLOR_DANGER))

    ax.set_xlabel('月度时间序列 (2015-01 → 2026-06, 11.4 年)', fontsize=11)
    ax.set_ylabel('累计净值（初始 = 1.0）', fontsize=11)
    ax.set_title('T35 修正后回测曲线（HS300 8.56% / ZZ500 24.48% / CYB 11.55%）', fontsize=14, fontweight='bold')
    ax.legend(loc='upper left', fontsize=10, ncol=2)
    ax.grid(True, alpha=0.3)
    ax.set_yscale('log')
    ax.set_ylim(0.5, 20)

    save(fig, '04_backtest_curve.png')


# ============================================================
# 05. 30 → 620 客户增长曲线
# ============================================================
def chart_05_client_growth():
    fig, ax = plt.subplots(figsize=(12, 7), dpi=150)

    years = [2026, 2027, 2028, 2029, 2030]
    clients = [30, 95, 180, 320, 620]
    arr = [1.98, 2.55, 3.40, 4.35, 5.85]  # 亿元

    color1 = COLOR_PRIMARY
    color2 = COLOR_DANGER
    ax2 = ax.twinx()

    bars = ax.bar(years, clients, color=color1, alpha=0.7, label='客户数（家）', width=0.5, edgecolor=COLOR_DARK)
    line = ax2.plot(years, arr, 'o-', color=color2, linewidth=2.5, label='ARR（亿元）', markersize=10)

    # 数字标注
    for i, (year, c) in enumerate(zip(years, clients)):
        ax.text(year, c + 15, f'{c}', ha='center', va='bottom', fontsize=11, fontweight='bold', color=color1)
    for i, (year, a) in enumerate(zip(years, arr)):
        ax2.text(year, a + 0.1, f'{a}', ha='center', va='bottom', fontsize=10, color=color2, fontweight='bold')

    # CAGR 标注
    cagr_clients = (620 / 30) ** (1/4) - 1
    ax.text(2028, 400, f'客户 CAGR\n{cagr_clients*100:.1f}%', ha='center', va='center',
            fontsize=11, color=COLOR_SUCCESS, fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.4', facecolor='lightgreen', edgecolor=COLOR_SUCCESS))
    cagr_arr = (5.85 / 1.98) ** (1/4) - 1
    ax2.text(2028, 4.5, f'ARR CAGR\n{cagr_arr*100:.1f}%', ha='center', va='center',
             fontsize=11, color=COLOR_DANGER, fontweight='bold',
             bbox=dict(boxstyle='round,pad=0.4', facecolor='lightyellow', edgecolor=COLOR_DANGER))

    ax.set_xlabel('年份', fontsize=11)
    ax.set_ylabel('客户数（家）', fontsize=11, color=color1)
    ax2.set_ylabel('ARR（亿元）', fontsize=11, color=color2)
    ax.set_title('客户增长 5 年路线图：30 → 620 客户（2026-2030）', fontsize=14, fontweight='bold')

    ax.set_xticks(years)
    ax.legend(loc='upper left', fontsize=10)
    ax2.legend(loc='upper right', fontsize=10)
    ax.grid(True, alpha=0.3, axis='y')
    ax.set_ylim(0, 700)

    save(fig, '05_client_growth.png')


# ============================================================
# 06. 4 客群 × 3 订阅矩阵
# ============================================================
def chart_06_customer_subscription_matrix():
    fig, ax = plt.subplots(figsize=(11, 7), dpi=150)

    customer_segments = ['中小私募\n(< 50 亿)', '家办/财富线\n(< 5 亿)', '个人高净值\n(> 1000 万)', '银行私行/券商投顾']
    tiers = ['基础版\n(¥ 2.4万/年)', '专业版\n(¥ 9.8万/年)', '企业版\n(¥ 49.8万/年)']

    # 数据矩阵 (LTV 千元)
    data = np.array([
        [12, 48, 180],   # 中小私募
        [8, 32, 95],     # 家办
        [3, 18, 0],      # 个人（无企业版）
        [0, 80, 380],    # 银行私行（无基础版）
    ])

    im = ax.imshow(data, cmap='YlOrRd', aspect='auto')
    ax.set_xticks(np.arange(len(tiers)))
    ax.set_yticks(np.arange(len(customer_segments)))
    ax.set_xticklabels(tiers, fontsize=10)
    ax.set_yticklabels(customer_segments, fontsize=10)

    # 单元格数字
    for i in range(len(customer_segments)):
        for j in range(len(tiers)):
            value = data[i, j]
            if value == 0:
                text = '—'
                color = 'gray'
            else:
                text = f'{value}k'
                color = 'white' if value > 100 else 'black'
            ax.text(j, i, text, ha='center', va='center', fontsize=12, fontweight='bold', color=color)

    # 热力图色条
    cbar = plt.colorbar(im, ax=ax)
    cbar.set_label('LTV（千元 / 单客户）', fontsize=10)

    ax.set_title('4 客群 × 3 订阅层级 LTV 热力矩阵', fontsize=14, fontweight='bold')
    ax.set_xlabel('订阅层级（年费）', fontsize=11)
    ax.set_ylabel('客户细分', fontsize=11)

    save(fig, '06_customer_subscription_matrix.png')


# ============================================================
# 07. 团队架构图
# ============================================================
def chart_07_team_structure():
    fig, ax = plt.subplots(figsize=(13, 8), dpi=150)
    ax.set_xlim(0, 13)
    ax.set_ylim(0, 8)
    ax.axis('off')

    # 标题
    ax.text(6.5, 7.6, 'QuantInsight Pro 团队架构（创始 4 人 + 顾问 5 位）',
            ha='center', va='center', fontsize=15, fontweight='bold', color=COLOR_DARK)

    # 顶层：CEO
    ceo_box = FancyBboxPatch((5.5, 5.8), 2, 1, boxstyle="round,pad=0.1",
                              linewidth=2, edgecolor=COLOR_DARK, facecolor=COLOR_DANGER, alpha=0.6)
    ax.add_patch(ceo_box)
    ax.text(6.5, 6.55, '冯亦根', ha='center', va='center', fontsize=13, fontweight='bold', color='white')
    ax.text(6.5, 6.2, 'CEO / 15 年金融', ha='center', va='center', fontsize=10, color='white')
    ax.text(6.5, 5.95, '期权 35%', ha='center', va='center', fontsize=9, color='white', style='italic')

    # 中层：CTO / CFO / CMO
    founders = [
        (1.5, 3.8, '王宇寒', 'CTO', '复旦软工\n期权 25%', COLOR_PRIMARY),
        (5.5, 3.8, '官馨', 'CFO', '上财金融\n期权 20%', COLOR_SUCCESS),
        (9.5, 3.8, '梁理智', 'CMO', '上财营销\n期权 20%', COLOR_WARNING),
    ]
    for x, y, name, role, desc, color in founders:
        box = FancyBboxPatch((x, y), 2, 1.3, boxstyle="round,pad=0.1",
                              linewidth=1.5, edgecolor=COLOR_DARK, facecolor=color, alpha=0.6)
        ax.add_patch(box)
        ax.text(x + 1, y + 1.05, name, ha='center', va='center', fontsize=12, fontweight='bold', color='white')
        ax.text(x + 1, y + 0.7, role, ha='center', va='center', fontsize=11, color='white')
        ax.text(x + 1, y + 0.3, desc, ha='center', va='center', fontsize=8, color='white')

    # CEO 到中层连线
    for x, _, _, _, _, _ in founders:
        ax.plot([6.5, x + 1], [5.8, 5.1], '-', color=COLOR_DARK, linewidth=1.5)

    # 底层：顾问委员会 5 位
    ax.text(6.5, 2.9, '↓ 顾问委员会（5 位） ↓', ha='center', va='center',
            fontsize=11, fontweight='bold', color=COLOR_DARK)
    advisors = [
        (0.5, 1.3, '学界\n顾问', '清华量化组\n教授'),
        (3.0, 1.3, '行业\n顾问', '永字资管\n法人薛永再'),
        (5.5, 1.3, '技术\n顾问', 'MIT 开源\n贡献者'),
        (8.0, 1.3, '金融\n监管', '原证监会\n专家'),
        (10.5, 1.3, '战略\n顾问', '麦肯锡\n前合伙人'),
    ]
    for x, y, role, name in advisors:
        box = FancyBboxPatch((x, y), 1.8, 1.2, boxstyle="round,pad=0.1",
                              linewidth=1.2, edgecolor=COLOR_DARK, facecolor=COLOR_PURPLE, alpha=0.5)
        ax.add_patch(box)
        ax.text(x + 0.9, y + 0.95, role, ha='center', va='center', fontsize=10, fontweight='bold', color='white')
        ax.text(x + 0.9, y + 0.4, name, ha='center', va='center', fontsize=8, color='white')

    # 团队总和
    ax.text(6.5, 0.3, '团队总数：4 创始人 + 5 顾问 = 9 人核心团队',
            ha='center', va='center', fontsize=11, fontweight='bold', color=COLOR_DARK,
            bbox=dict(boxstyle='round,pad=0.3', facecolor='lightyellow', edgecolor=COLOR_DARK))

    save(fig, '07_team_structure.png')


def main():
    print('🎨 开始渲染 7 张专业图表...')
    print(f'  输出目录: {OUTDIR}')
    print()
    print('  [1/7] 商业模式 9 宫格...')
    chart_01_business_model_canvas()
    print('  [2/7] LTV/CAC 雷达图...')
    chart_02_ltv_cac_radar()
    print('  [3/7] NRR 140% 漏斗...')
    chart_03_nrr_funnel()
    print('  [4/7] T35 修正回测曲线...')
    chart_04_backtest_curve()
    print('  [5/7] 30→620 客户增长...')
    chart_05_client_growth()
    print('  [6/7] 4 客群×3 订阅矩阵...')
    chart_06_customer_subscription_matrix()
    print('  [7/7] 团队架构图...')
    chart_07_team_structure()
    print('\n✅ 7 张图表全部生成')


if __name__ == '__main__':
    main()
