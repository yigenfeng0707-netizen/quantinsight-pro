# -*- coding: utf-8 -*-
"""AFAC2026 提交材料 — 专业图表渲染（matplotlib）"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
CHART_DIR = ROOT / "submission" / "03_正式文档_WORD" / "_charts"
POC_JSON = ROOT / "submission" / "02_Demo交付" / "POC实验数据" / "t35_hs300_summary.json"

# 品牌色
DARK = "#0A0E27"
CYAN = "#00D4FF"
GOLD = "#FFB800"
VIOLET = "#7B61FF"
GREEN = "#00FF88"
RED = "#FF4D6A"

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False


def _ensure_dir() -> Path:
    CHART_DIR.mkdir(parents=True, exist_ok=True)
    return CHART_DIR


def chart_strategy_comparison(out_name: str = "chart_strategy_comparison.png") -> Path:
    """五策略年化收益 / 夏普 / 最大回撤对比"""
    with open(POC_JSON, encoding="utf-8") as f:
        poc = json.load(f)
    strategies = list(poc["strategies"].values())
    names = [s["name"] for s in strategies]
    annual = [s["annual_return_pct"] for s in strategies]
    sharpe = [s["sharpe"] for s in strategies]
    mdd = [abs(s["max_drawdown_pct"]) for s in strategies]

    x = np.arange(len(names))
    w = 0.25
    fig, ax1 = plt.subplots(figsize=(10, 5.5), facecolor="white")
    ax1.bar(x - w, annual, w, label="年化收益(%)", color=CYAN, edgecolor=DARK, linewidth=0.5)
    ax1.bar(x, sharpe, w, label="夏普比率", color=GOLD, edgecolor=DARK, linewidth=0.5)
    ax1.bar(x + w, [-v for v in mdd], w, label="最大回撤(%)", color=VIOLET, alpha=0.85, edgecolor=DARK, linewidth=0.5)
    ax1.axhline(0, color="#999", linewidth=0.8)
    ax1.set_xticks(x)
    ax1.set_xticklabels(names, fontsize=10)
    ax1.set_ylabel("数值", fontsize=10)
    ax1.set_title("HS300 五策略回测对比（T35 修正 · 2015-2026）", fontsize=13, fontweight="bold", color=DARK, pad=12)
    ax1.legend(loc="upper left", fontsize=9, framealpha=0.9)
    ax1.grid(axis="y", alpha=0.25, linestyle="--")
    fig.tight_layout()
    path = _ensure_dir() / out_name
    fig.savefig(path, dpi=180, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return path


def chart_afac_scoring_radar(out_name: str = "chart_afac_scoring.png") -> Path:
    """AFAC 初筛五维评分雷达图"""
    labels = ["项目创新性", "技术成熟度", "商业模式\n与落地", "团队综合\n素质", "社会效益"]
    scores = [23, 24, 21, 16, 14]
    max_scores = [25, 25, 25, 20, 15]
    angles = np.linspace(0, 2 * np.pi, len(labels), endpoint=False).tolist()
    scores_plot = scores + [scores[0]]
    max_plot = max_scores + [max_scores[0]]
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(6.5, 6.5), subplot_kw=dict(polar=True), facecolor="white")
    ax.fill(angles, max_plot, color=CYAN, alpha=0.08)
    ax.plot(angles, max_plot, color=CYAN, linewidth=1, linestyle="--", label="满分")
    ax.fill(angles, scores_plot, color=GOLD, alpha=0.35)
    ax.plot(angles, scores_plot, color=GOLD, linewidth=2.5, marker="o", markersize=7, label="自评分")
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels, fontsize=9)
    ax.set_ylim(0, 28)
    ax.set_title("AFAC2026 初筛五维评分自评（加权 88/100）", fontsize=12, fontweight="bold", color=DARK, pad=20)
    ax.legend(loc="upper right", bbox_to_anchor=(1.25, 1.1), fontsize=9)
    fig.tight_layout()
    path = _ensure_dir() / out_name
    fig.savefig(path, dpi=180, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return path


def chart_architecture_layers(out_name: str = "chart_architecture.png") -> Path:
    """六层技术架构示意图"""
    layers = [
        ("L6 部署层", "ECS · Nginx · systemd · HTTPS", DARK),
        ("L5 应用层", "Streamlit 多页 Demo · 管理后台", "#1E3A5F"),
        ("L4 智能体层", "Qwen/DeepSeek + RAG 投研问答", VIOLET),
        ("L3 模型层", "XGBoost 多因子 + SHAP 可解释", GOLD),
        ("L2 特征层", "17 因子工程 · pandas/numpy", CYAN),
        ("L1 数据层", "SQLite · 东方财富 · akshare · 另类数据", GREEN),
    ]
    fig, ax = plt.subplots(figsize=(9, 6), facecolor="white")
    ax.set_xlim(0, 10)
    ax.set_ylim(0, len(layers) + 1)
    ax.axis("off")
    for i, (title, desc, color) in enumerate(layers):
        y = len(layers) - i
        rect = plt.Rectangle((1, y - 0.35), 8, 0.7, facecolor=color, edgecolor="white", linewidth=2, alpha=0.92)
        ax.add_patch(rect)
        ax.text(1.3, y, title, va="center", ha="left", fontsize=11, fontweight="bold", color="white")
        ax.text(5.5, y, desc, va="center", ha="left", fontsize=9.5, color="white")
    ax.set_title("QuantInsight Pro 六层技术架构", fontsize=13, fontweight="bold", color=DARK, pad=10)
    fig.tight_layout()
    path = _ensure_dir() / out_name
    fig.savefig(path, dpi=180, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return path


def chart_data_flow(out_name: str = "chart_data_flow.png") -> Path:
    """数据流：多源 → 缓存 → 应用"""
    boxes = [
        ("外部数据源", "akshare / 东方财富 / Baostock"),
        ("SQLite 缓存层", "refresh_data.py 定时刷新"),
        ("特征 & 因子", "17 因子 · 另类数据融合"),
        ("AI + 回测", "SHAP · MIT 回测引擎"),
        ("用户界面", "https://3blue1brownlab.cn"),
    ]
    fig, ax = plt.subplots(figsize=(8, 4.5), facecolor="white")
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 2)
    ax.axis("off")
    xs = np.linspace(0.8, 9.2, len(boxes))
    for i, (x, (title, sub)) in enumerate(zip(xs, boxes)):
        color = [CYAN, GOLD, VIOLET, GREEN, DARK][i]
        rect = plt.Rectangle((x - 0.75, 0.55), 1.5, 0.9, facecolor=color, edgecolor="white", linewidth=1.5, alpha=0.9)
        ax.add_patch(rect)
        ax.text(x, 1.05, title, ha="center", va="center", fontsize=8.5, fontweight="bold", color="white")
        ax.text(x, 0.75, sub, ha="center", va="center", fontsize=6.5, color="white", wrap=True)
        if i < len(boxes) - 1:
            ax.annotate("", xy=(xs[i + 1] - 0.78, 1.0), xytext=(x + 0.78, 1.0),
                        arrowprops=dict(arrowstyle="->", color=DARK, lw=1.5))
    ax.set_title("数据链路：SQLite 优先 · 后台定时刷新", fontsize=12, fontweight="bold", color=DARK)
    fig.tight_layout()
    path = _ensure_dir() / out_name
    fig.savefig(path, dpi=180, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return path


def render_all_charts() -> dict[str, Path]:
    return {
        "strategy": chart_strategy_comparison(),
        "scoring": chart_afac_scoring_radar(),
        "architecture": chart_architecture_layers(),
        "data_flow": chart_data_flow(),
    }


if __name__ == "__main__":
    paths = render_all_charts()
    for k, p in paths.items():
        print(f"{k}: {p} ({p.stat().st_size:,} bytes)")
