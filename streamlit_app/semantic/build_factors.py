"""
QuantInsight Pro - 因子注册表生成器
====================================
把 features/factor_scorer.py（4 类评分因子）与 features/qlib_integration.py
（滚动统计 + 技术指标因子）的因子定义从代码中外置为 RDF 本体实例。

公式均从源码逐条核验（2026-11）：
  - factor_scorer.py:112-199（_calc_value/growth/quality/momentum_factor）
  - qlib_integration.py:199-225（rolling_stats）、255-360（technical_indicators）

生成：semantic/factors.ttl
用法：python semantic/build_factors.py
"""

from __future__ import annotations

import sys
from pathlib import Path

try:
    from rdflib import Graph, Literal, Namespace, URIRef
    from rdflib.namespace import RDF, RDFS, XSD
except ImportError:
    sys.exit("需要 rdflib：pip install rdflib")

QI = Namespace("http://quantinsight.pro/ontology/")

# 因子大类
CATEGORIES = {
    "cat_value": ("价值因子", "估值类因子，低估值得分高"),
    "cat_growth": ("成长因子", "活跃度与趋势类因子"),
    "cat_quality": ("质量因子", "流动性与规模类因子"),
    "cat_momentum": ("动量因子", "中期价格趋势类因子"),
    "cat_rolling": ("滚动统计因子", "行情序列的滚动统计量（qlib_integration.rolling_stats）"),
    "cat_technical": ("技术指标因子", "经典技术指标（qlib_integration.technical_indicators）"),
    "cat_shap": ("机器学习特征因子", "SHAP 归因页 XGBoost 模型使用的特征（shap_explainer.FACTOR_DEFINITIONS），含分组与方向"),
}

# 评分因子（factor_scorer）：公式核验自源码
SCORER_FACTORS = [
    dict(
        key="f_value", name="价值因子", cat="cat_value", weights="总权重 0.25",
        formula="PE 分位与 PB 分位加权：PE clip 至 [1, 200] 后取 1−(PE−1)/199；PB clip 至 [0.1, 20] 后取 1−(PB−0.1)/19.9；基准 0.5 与两者滚动加权（PE 步 0.5/0.5，PB 步 0.7/0.3）",
        desc="PE/PB 越低得分越高（factor_scorer.py:112-124）",
        deps=["m_pe_ttm", "m_pb"],
    ),
    dict(
        key="f_growth", name="成长因子", cat="cat_growth", weights="总权重 0.25",
        formula="当日涨幅分段：0–5% 为 0.8+0.04x，>5% 为 0.6，<0 为 0.3+0.02x；量比 clip [0, 10]，1–3 为 0.8，>3 为 0.5，<1 为 0.3；两步滚动加权 0.5/0.5 与 0.7/0.3",
        desc="适度涨幅 + 量比活跃（factor_scorer.py:126-152）",
        deps=["m_pct_change", "m_volume_ratio"],
    ),
    dict(
        key="f_quality", name="质量因子", cat="cat_quality", weights="总权重 0.25",
        formula="换手率 clip [0, 30]，1–5% 为 0.9，5–10% 为 0.6，<1 为 0.3，>10 为 0.4；总市值（亿元）100–2000 为 0.9，50–100 为 0.7，>2000 为 0.6，其余 0.4；滚动加权 0.5/0.5 与 0.6/0.4",
        desc="换手率适中 + 市值中大型（factor_scorer.py:154-182）",
        deps=["m_turnover", "m_total_mv"],
    ),
    dict(
        key="f_momentum", name="动量因子", cat="cat_momentum", weights="总权重 0.25",
        formula="60 日涨跌幅 clip [−50, 100]，5–30% 为 0.8+(p−5)×0.008，0–5% 为 0.6，>30% 为 0.4，<0 为 0.2+p×0.01（直接覆盖基准分）",
        desc="60 日涨幅适中为优（factor_scorer.py:184-199）",
        deps=["m_pct_60d"],
    ),
]

# 滚动统计因子（qlib_integration.rolling_stats, windows = 5/10/20/60/120）
ROLLING_WINDOWS = [5, 10, 20, 60, 120]
ROLLING_STATS = {
    "mean": ("均值因子", "MA(close, {w})", "移动平均线"),
    "std": ("标准差因子", "STD(close, {w})", "标准差（样本，ddof=1）"),
    "skew": ("偏度因子", "SKEW(close, {w})", "偏度，≥3 个数据点"),
    "kurt": ("峰度因子", "KURT(close, {w})", "超额峰度（−3），≥4 个数据点"),
    "momentum": ("动量因子", "close.pct_change({w})", "{w} 日变动率"),
    "volatility": ("波动率因子", "STD(close, {w}) / MA(close, {w})", "变异系数（CV）"),
}

# 技术指标因子（qlib_integration.technical_indicators）
TECH_FACTORS = [
    ("rsi_6", "RSI(6)", "相对强弱指数", "100×avg_gain/(avg_gain+avg_loss)，avg_gain/avg_loss 为涨跌幅的 EWM(alpha=1/period)"),
    ("rsi_14", "RSI(14)", "相对强弱指数", "同 RSI(6)，周期 14"),
    ("rsi_28", "RSI(28)", "相对强弱指数", "同 RSI(6)，周期 28"),
    ("macd_dif", "MACD DIF", "MACD 快线", "DIF = EMA(close, 12) − EMA(close, 26)"),
    ("macd_dea", "MACD DEA", "MACD 信号线", "DEA = EMA(DIF, 9)"),
    ("macd_hist", "MACD HIST", "MACD 柱", "HIST = 2 × (DIF − DEA)（柱状图放大 2 倍）"),
    ("bb_upper", "布林带上轨", "布林带", "MA(close, 20) + 2 × STD(close, 20)"),
    ("bb_middle", "布林带中轨", "布林带", "MA(close, 20)"),
    ("bb_lower", "布林带下轨", "布林带", "MA(close, 20) − 2 × STD(close, 20)"),
    ("atr_14", "ATR(14)", "真实波幅均值", "TR = max(high−low, |high−prev_close|, |low−prev_close|)，ATR = TR 的 14 日移动平均"),
    ("atr_14_pct", "ATR 百分比", "波动幅度", "ATR(14) / close"),
    ("obv", "OBV 能量潮", "能量潮", "cumsum：close > prev → +volume；close < prev → −volume；相等 → 0"),
    ("obv_ma20", "OBV 20 日均线", "能量潮均线", "MA(OBV, 20)"),
]

# 机器学习特征因子（shap_explainer.FACTOR_DEFINITIONS，17 条，核验自源码）
# (key, 展示名, 公式/描述, 方向, 依赖指标)
SHAP_FACTORS = [
    ("PE_TTM", "市盈率TTM", "总市值 / 归母净利润(TTM)", "越低越好", ["m_pe_ttm"]),
    ("PB", "市净率", "股价 / 每股净资产", "越低越好", ["m_pb"]),
    ("PS_TTM", "市销率TTM", "总市值 / 营业收入(TTM)", "越低越好", []),
    ("Revenue_Growth", "营收增速", "(本期营业收入 − 上期) / 上期", "越高越好", ["m_revenue"]),
    ("NetProfit_Growth", "净利润增速", "(本期净利润 − 上期) / 上期", "越高越好", ["m_net_profit"]),
    ("ROE", "净资产收益率", "归母净利润 / 净资产", "越高越好", ["m_net_profit_parent"]),
    ("Gross_Margin", "毛利率", "(营业收入 − 营业成本) / 营业收入", "越高越好", ["m_gross_margin"]),
    ("Debt_Ratio", "资产负债率", "总负债 / 总资产", "越低越好", []),
    ("Current_Ratio", "流动比率", "流动资产 / 流动负债", "越高越好", []),
    ("Momentum_20D", "20日动量", "close.pct_change(20)", "越高越好", ["m_close"]),
    ("Momentum_60D", "60日动量", "close.pct_change(60)", "越高越好", ["m_close"]),
    ("RSI_14", "14日RSI", "100×avg_gain/(avg_gain+avg_loss)", "中性", []),
    ("Turnover_20D", "20日均换手率", "MA(turnover, 20)", "越高越好", ["m_turnover"]),
    ("Volume_Ratio", "量比", "当日成交量 / 过去5日平均成交量", "越高越好", ["m_volume_ratio"]),
    ("Float_Cap", "流通市值", "流通股本 × 最新股价", "越高越好", ["m_circ_mv"]),
    ("Volatility_20D", "20日波动率", "STD(close, 20) / MA(close, 20)", "越低越好", ["m_close"]),
    ("MACD_Signal", "MACD信号", "MACD DIF 与 DEA 的交叉信号", "越高越好", ["m_close"]),
]


def main() -> int:
    out = Path(__file__).parent / "factors.ttl"
    g = Graph()
    g.bind("qi", QI)
    g.bind("rdf", RDF)
    g.bind("rdfs", RDFS)
    g.bind("xsd", XSD)

    n = 0

    # 因子大类
    for cat_key, (cat_name, cat_desc) in CATEGORIES.items():
        g.add((QI[cat_key], RDF.type, QI.FactorCategory))
        g.add((QI[cat_key], QI.name, Literal(cat_name)))
        g.add((QI[cat_key], QI.caliber, Literal(cat_desc)))
        n += 1

    def add_factor(key: str, name: str, cat: str, formula: str,
                  desc: str, deps: list[str], module: str) -> None:
        nonlocal n
        g.add((QI[key], RDF.type, QI.Factor))
        g.add((QI[key], QI.name, Literal(name)))
        g.add((QI[key], QI.formula, Literal(formula)))
        g.add((QI[key], QI.caliber, Literal(desc)))
        g.add((QI[key], QI.inCategory, QI[cat]))
        g.add((QI[key], QI.bindingApi, Literal(module)))
        for dep in deps:
            g.add((QI[key], QI.computedFrom, QI[dep]))
        n += 1

    # 1) 评分因子
    for f in SCORER_FACTORS:
        add_factor(f["key"], f["name"], f["cat"], f["formula"],
                   f"{f['desc']}；四类等权 0.25 合成总分（factor_scorer.FACTOR_WEIGHTS）",
                   f["deps"], "features/factor_scorer.py::MultiFactorScorer")

    # 2) 滚动统计因子
    for stat, (label, fml_tpl, stat_desc) in ROLLING_STATS.items():
        for w in ROLLING_WINDOWS:
            add_factor(
                f"{stat}_{w}", f"{label.split('因子')[0]}({w})",
                "cat_rolling", fml_tpl.format(w=w),
                f"窗口 {w} 个交易日；{stat_desc}（qlib_integration.py:199-225）",
                ["m_close"] if stat != "momentum" else ["m_close"],
                "features/qlib_integration.py::AlphaFactorMiner.rolling_stats",
            )

    # 3) 技术指标因子
    for key, label, family, formula in TECH_FACTORS:
        deps = ["m_close"]
        if key.startswith("atr"):
            deps = ["m_high", "m_low", "m_close"]
        elif key.startswith("obv"):
            deps = ["m_close", "m_volume"]
        add_factor(key, label, "cat_technical", formula,
                   f"{family}（qlib_integration.py:255-360）", deps,
                   "features/qlib_integration.py::AlphaFactorMiner.technical_indicators")

    # 4) 机器学习特征因子（SHAP 归因页特征）
    shap_module = "features/shap_explainer.py::FACTOR_DEFINITIONS"
    for key, label, formula, direction, deps in SHAP_FACTORS:
        add_factor(f"shap_{key}", label, "cat_shap", formula,
                   f"XGBoost 特征，方向：{direction}（shap_explainer.py:75-93）",
                   deps, shap_module)

    g.serialize(destination=str(out), format="turtle", encoding="utf-8")
    print(f"已生成 {out}（{n} 个实例："
          f"{len(CATEGORIES)} 大类 + {len(SCORER_FACTORS)} 评分因子 + "
          f"{len(ROLLING_STATS) * len(ROLLING_WINDOWS)} 滚动统计 + {len(TECH_FACTORS)} 技术指标"
          f" + {len(SHAP_FACTORS)} 机器学习特征）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
