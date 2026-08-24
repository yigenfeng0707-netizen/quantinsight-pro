#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
合并 9 张 PNG 为 1 张 3×3 综合图，输出 PNG + PDF
- 8 张流程图 + 1 张核心数据图（HS300 回测曲线）
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import matplotlib.gridspec as gridspec
from matplotlib.patches import FancyBboxPatch
from matplotlib.backends.backend_pdf import PdfPages
import os
from pathlib import Path

SRC_DIR = Path("d:/AFAC2026金融智能创新大赛/quantinsight-deploy/delivery/06_图表素材/流程图")
SRC_DATA = Path("d:/AFAC2026金融智能创新大赛/quantinsight-deploy/delivery/06_图表素材/04_backtest_curve.png")
OUT_DIR = Path("d:/AFAC2026金融智能创新大赛/quantinsight-deploy/delivery/06_图表素材/综合图")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# 颜色
C_PRIMARY = "#0A1F44"
C_ACCENT  = "#1A558F"
C_RED     = "#C0392B"
C_GOLD    = "#E69F00"
C_LIGHT   = "#E8EEF7"
C_GRAY    = "#666666"
C_GREEN   = "#2E7D32"

# 9 张图（按逻辑顺序：架构 → 模块 → 算法 → 数据 → 业务）
figures = [
    ("01_六层技术架构.png",   "① 六层技术架构",     "L1基础设施 → L2算法 → L3数据 → L4服务 → L5智能体 → L6应用"),
    ("02_8大模块交互流程.png", "② 8大核心模块",       "智能选股 · SHAP · AI问答 · 回测 · 盯盘 · 模拟 · 报告 · 看板"),
    ("03_SHAP可解释算法.png",  "③ SHAP可解释算法",    "业内独家 · 17因子归因 · 满足监管算法备案"),
    ("04_RAG检索增强生成.png", "④ RAG检索增强",      "DeepSeek/Qwen + FAISS + ES · 中文金融80%+"),
    ("05_17因子多因子模型.png","⑤ 17因子多因子",      "6大类 · 价值/质量/动量/波动/情绪/技术"),
    ("06_商业模式画布.png",    "⑥ 商业模式画布",      "BMC 9区块 · 9类机构 · LTV/CAC 82.2"),
    ("07_客户旅程图.png",      "⑦ 客户旅程",         "5阶段 · 12-24月 · 5→50客户推荐"),
    ("08_永字资管合作5模块.png","⑧ 永字资管合作",     "5模块 × 4阶段 · 战略合作已签"),
    ("__BACKTEST__",           "⑨ HS300 回测曲线",   "11.4 年实测 · 8.56% 年化 · 超额 +3.10% · 夏普 0.63"),
]

# 字体设置
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# =================================================================
# 创建综合图
# =================================================================
fig = plt.figure(figsize=(20, 30), dpi=150)
# 5 行 × 3 列：标题 + 9 张子图(3×3) + 底部关键数字条
gs = gridspec.GridSpec(5, 3, figure=fig,
                       height_ratios=[1.0, 2.8, 2.8, 2.8, 0.8],
                       width_ratios=[1, 1, 1],
                       hspace=0.30, wspace=0.12,
                       left=0.05, right=0.95, top=0.97, bottom=0.03)

# ----- 顶部标题区（跨 3 列）-----
ax_title = fig.add_subplot(gs[0, :])
ax_title.axis('off')
ax_title.set_xlim(0, 100)
ax_title.set_ylim(0, 100)

# 标题横幅背景
title_bg = FancyBboxPatch((2, 5), 96, 90,
                          boxstyle="round,pad=2",
                          facecolor=C_PRIMARY, edgecolor=C_RED, linewidth=2)
ax_title.add_patch(title_bg)
# 副标题
title_bg2 = FancyBboxPatch((2, 5), 96, 38,
                           boxstyle="round,pad=2",
                           facecolor=C_ACCENT, edgecolor='none')
ax_title.add_patch(title_bg2)

ax_title.text(50, 85, "QuantInsight Pro · 9 张核心图综合",
              ha='center', va='center', fontsize=28,
              color='white', fontweight='bold')
ax_title.text(50, 65, "AI 驱动的另类数据量化投研平台",
              ha='center', va='center', fontsize=18,
              color='white', style='italic')
ax_title.text(50, 45, "·  SHAP 可解释（业内独家） ·  5 类另类数据  ·  17 因子多因子  ·  MIT 开源回测  ·",
              ha='center', va='center', fontsize=12, color='white')
ax_title.text(50, 25, "HS300 多因子 11.4 年 8.56% 年化  ·  超额 +3.10%  ·  夏普 0.63  ·  中文金融 80%+",
              ha='center', va='center', fontsize=12, color=C_GOLD, fontweight='bold')
ax_title.text(50, 10, "Demo: 3blue1brownlab.cn  ·  GitHub: github.com/yigenfeng0707-netizen/quantinsight-pro-afac2026",
              ha='center', va='center', fontsize=10, color='white', style='italic')

# ----- 9 张子图（3×3 网格，填满 gs[1:4, 0:3]）-----
for idx, (filename, title, subtitle) in enumerate(figures):
    row = idx // 3 + 1   # 1, 1, 1, 2, 2, 2, 3, 3, 3
    col = idx % 3        # 0, 1, 2, 0, 1, 2, 0, 1, 2
    ax = fig.add_subplot(gs[row, col])
    ax.axis('off')

    # 子图标题
    ax.text(0.5, 1.02, title, transform=ax.transAxes,
            ha='center', va='bottom', fontsize=14,
            color=C_PRIMARY, fontweight='bold')
    ax.text(0.5, -0.02, subtitle, transform=ax.transAxes,
            ha='center', va='top', fontsize=9,
            color=C_GRAY, style='italic')

    # 加载并显示图片（特殊 __BACKTEST__ 走 SRC_DATA 路径）
    img_path = SRC_DATA if filename == "__BACKTEST__" else (SRC_DIR / filename)
    if img_path.exists():
        img = mpimg.imread(img_path)
        ax.imshow(img, aspect='auto')

# ----- 底部关键数字条（横跨 3 列）-----
ax_kpi = fig.add_subplot(gs[4, :])
ax_kpi.axis('off')
ax_kpi.set_xlim(0, 100)
ax_kpi.set_ylim(0, 100)

kpi_bg = FancyBboxPatch((0, 0), 100, 100,
                        boxstyle="round,pad=2",
                        facecolor=C_GOLD, edgecolor=C_PRIMARY, linewidth=1.5)
ax_kpi.add_patch(kpi_bg)

# 7 个关键数字 + 1 个标签
kpis = [
    ("★ HS300 年化",  "8.56%", C_RED),
    ("★ 超额收益",    "+3.10%", C_RED),
    ("★ 夏普比率",    "0.63", C_PRIMARY),
    ("★ 中文金融",    "80%+",  C_PRIMARY),
    ("★ 投研效率",    "+65%",  C_GREEN),
    ("★ LTV/CAC",    "82.2",  C_PRIMARY),
    ("★ NRR",        "140%",  C_PRIMARY),
]
cell_w = 100 / len(kpis)
for i, (label, val, color) in enumerate(kpis):
    cx = cell_w * (i + 0.5)
    ax_kpi.text(cx, 65, label, ha='center', va='center',
                fontsize=10, color=C_PRIMARY)
    ax_kpi.text(cx, 30, val, ha='center', va='center',
                fontsize=18, color=color, fontweight='bold')

# ----- 保存 PNG -----
png_path = OUT_DIR / "QuantInsight_Pro_9图综合_V1.png"
fig.savefig(png_path, dpi=150, bbox_inches='tight', facecolor='white')
print(f"  [OK] PNG: {png_path} ({png_path.stat().st_size:,} bytes)")

# ----- 保存 PDF（用 PdfPages 保证兼容性）-----
pdf_path = OUT_DIR / "QuantInsight_Pro_9图综合_V1.pdf"
with PdfPages(pdf_path) as pdf:
    pdf.savefig(fig, bbox_inches='tight', facecolor='white')
print(f"  [OK] PDF: {pdf_path} ({pdf_path.stat().st_size:,} bytes)")

# 关闭
plt.close(fig)
print("\nDone.")
