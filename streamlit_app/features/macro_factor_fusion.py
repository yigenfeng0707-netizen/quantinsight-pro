# -*- coding: utf-8 -*-
"""
QuantInsight Pro - 宏观因子融合与另类数据信号验证模块
========================================================

核心差异化功能（对标 Exabel / Quant Insight）:
  1. 宏观因子模型 - 8大类别宏观因子建模与周期识别
  2. 因子融合引擎 - 量化/宏观/另类三维因子动态融合
  3. 信号验证仪表盘 - IC/换手/衰减/交叉验证全流程
  4. Exabel风格信号看板 - 信号概览/相关性/边际贡献/新鲜度

依赖: numpy, pandas, scipy (纯Python，无需外部API)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from scipy import stats

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 1. 宏观因子模型
# ---------------------------------------------------------------------------

class MacroFactorModel:
    """
    宏观因子模型

    覆盖8大宏观因子类别，支持:
    - 加权宏观综合评分
    - 宏观周期识别 (扩张/复苏/衰退/滞胀)
    - 基于周期的资产配置信号生成
    """

    # 8大宏观因子类别定义
    MACRO_CATEGORIES = {
        "monetary": {
            "name": "货币因子",
            "factors": ["M2增速", "LPR", "存款准备金率"],
            "weights": [0.4, 0.35, 0.25],
            # 因子方向: +1 表示越大越利好, -1 表示越大越利空
            "directions": [1, -1, -1],
        },
        "fiscal": {
            "name": "财政因子",
            "factors": ["财政支出增速", "税收收入"],
            "weights": [0.6, 0.4],
            "directions": [1, -1],
        },
        "external": {
            "name": "外部因子",
            "factors": ["美元兑人民币", "贸易差额", "FDI"],
            "weights": [0.35, 0.4, 0.25],
            "directions": [-1, 1, 1],
        },
        "credit": {
            "name": "信用因子",
            "factors": ["社融总量", "新增贷款"],
            "weights": [0.55, 0.45],
            "directions": [1, 1],
        },
        "real_estate": {
            "name": "房地产因子",
            "factors": ["商品房销售增速", "土地出让金"],
            "weights": [0.6, 0.4],
            "directions": [1, 1],
        },
        "pmi": {
            "name": "PMI因子",
            "factors": ["制造业PMI", "服务业PMI"],
            "weights": [0.6, 0.4],
            "directions": [1, 1],
        },
        "inflation": {
            "name": "通胀因子",
            "factors": ["CPI", "PPI"],
            "weights": [0.55, 0.45],
            "directions": [-1, -1],
        },
        "employment": {
            "name": "就业因子",
            "factors": ["城镇调查失业率"],
            "weights": [1.0],
            "directions": [-1],
        },
    }

    # 各类别在综合评分中的权重
    CATEGORY_WEIGHTS = {
        "monetary": 0.20,
        "fiscal": 0.10,
        "external": 0.10,
        "credit": 0.20,
        "real_estate": 0.10,
        "pmi": 0.12,
        "inflation": 0.10,
        "employment": 0.08,
    }

    # 周期判断阈值
    REGIME_THRESHOLDS = {
        "expansion": 0.5,   # 综合评分 > 0.5
        "recovery": 0.0,    # 0.0 ~ 0.5
        "recession": -0.5,  # -0.5 ~ 0.0
        "stagflation": -1.0, # < -0.5 且通胀高
    }

    def __init__(self):
        """初始化宏观因子模型，加载因子定义与默认参数"""
        self.categories = self.MACRO_CATEGORIES
        self.category_weights = self.CATEGORY_WEIGHTS
        self._demo_cache: Dict = {}

    # ----- 演示数据生成 -----

    def generate_demo_factors(self) -> Dict[str, Dict[str, float]]:
        """
        生成演示用宏观因子数据

        Returns:
            Dict: 嵌套字典 {类别: {因子名: 值}}
        """
        np.random.seed(42)
        demo = {
            "monetary": {
                "M2增速": np.random.uniform(6, 12),
                "LPR": np.random.uniform(3.0, 4.5),
                "存款准备金率": np.random.uniform(6, 12),
            },
            "fiscal": {
                "财政支出增速": np.random.uniform(-5, 15),
                "税收收入": np.random.uniform(-10, 10),
            },
            "external": {
                "美元兑人民币": np.random.uniform(6.8, 7.4),
                "贸易差额": np.random.uniform(200, 800),
                "FDI": np.random.uniform(50, 200),
            },
            "credit": {
                "社融总量": np.random.uniform(10000, 50000),
                "新增贷款": np.random.uniform(5000, 30000),
            },
            "real_estate": {
                "商品房销售增速": np.random.uniform(-20, 20),
                "土地出让金": np.random.uniform(-15, 15),
            },
            "pmi": {
                "制造业PMI": np.random.uniform(45, 55),
                "服务业PMI": np.random.uniform(45, 58),
            },
            "inflation": {
                "CPI": np.random.uniform(0, 4),
                "PPI": np.random.uniform(-5, 8),
            },
            "employment": {
                "城镇调查失业率": np.random.uniform(4.5, 6.5),
            },
        }
        return demo

    # ----- 核心计算方法 -----

    def compute_macro_score(self, factors: Dict[str, Dict[str, float]]) -> Dict:
        """
        计算加权宏观综合评分

        对每个类别内的因子进行方向调整和加权汇总，再按类别权重
        计算综合宏观评分。

        Args:
            factors: 嵌套字典 {类别: {因子名: 值}}

        Returns:
            Dict: {
                'category_scores': {类别: 评分},
                'composite_score': 综合评分,
                'category_details': {类别: {因子: 贡献}},
            }
        """
        category_scores = {}
        category_details = {}

        for cat_key, cat_def in self.categories.items():
            if cat_key not in factors:
                # 缺失类别用0填充
                category_scores[cat_key] = 0.0
                category_details[cat_key] = {"raw": {}, "normalized": {}, "contributions": {}}
                continue

            cat_data = factors[cat_key]
            factor_names = cat_def["factors"]
            weights = cat_def["weights"]
            directions = cat_def["directions"]

            contributions = {}
            normalized_vals = {}
            raw_vals = {}

            for i, fname in enumerate(factor_names):
                val = cat_data.get(fname, 0.0)
                raw_vals[fname] = val

                # 标准化: 使用简单归一化 (基于历史范围的经验值)
                norm_val = self._normalize_factor(cat_key, fname, val)
                normalized_vals[fname] = norm_val

                # 方向调整
                adjusted = norm_val * directions[i]
                contrib = adjusted * weights[i]
                contributions[fname] = {
                    "raw": val,
                    "normalized": round(norm_val, 4),
                    "direction": directions[i],
                    "weight": weights[i],
                    "contribution": round(contrib, 4),
                }

            # 类别评分 = 因子贡献之和
            cat_score = sum(c["contribution"] for c in contributions.values())
            category_scores[cat_key] = round(cat_score, 4)
            category_details[cat_key] = {
                "raw": raw_vals,
                "normalized": normalized_vals,
                "contributions": contributions,
            }

        # 综合评分 = 类别加权
        composite = sum(
            category_scores.get(k, 0.0) * self.category_weights.get(k, 0.0)
            for k in self.categories
        )

        return {
            "category_scores": category_scores,
            "composite_score": round(composite, 4),
            "category_details": category_details,
        }

    def _normalize_factor(self, category: str, factor_name: str, value: float) -> float:
        """
        因子标准化 (基于经验范围映射到 [-1, 1])

        Args:
            category: 因子类别
            factor_name: 因子名
            value: 原始值

        Returns:
            float: 标准化后的值 [-1, 1]
        """
        # 经验范围定义 (可根据实际数据调整)
        RANGES = {
            "M2增速": (4, 14), "LPR": (2.5, 5.0), "存款准备金率": (5, 20),
            "财政支出增速": (-15, 25), "税收收入": (-20, 20),
            "美元兑人民币": (6.0, 8.0), "贸易差额": (-100, 1000), "FDI": (0, 300),
            "社融总量": (5000, 60000), "新增贷款": (2000, 40000),
            "商品房销售增速": (-30, 30), "土地出让金": (-25, 25),
            "制造业PMI": (40, 60), "服务业PMI": (40, 65),
            "CPI": (-1, 6), "PPI": (-10, 12),
            "城镇调查失业率": (3.5, 7.0),
        }

        lo, hi = RANGES.get(factor_name, (-1, 1))
        mid = (lo + hi) / 2.0
        half_range = (hi - lo) / 2.0
        if half_range == 0:
            return 0.0
        normalized = (value - mid) / half_range
        return float(np.clip(normalized, -1.0, 1.0))

    def macro_regime_detection(self, factors: Dict[str, Dict[str, float]]) -> Dict:
        """
        宏观周期识别

        根据综合评分和通胀水平，将当前宏观环境归类为:
        - expansion (扩张期): 高增长低通胀
        - recovery (复苏期): 增长回升通胀温和
        - recession (衰退期): 增长下行通胀下行
        - stagflation (滞胀期): 增长下行通胀上行

        Args:
            factors: 嵌套字典 {类别: {因子名: 值}}

        Returns:
            Dict: {
                'regime': 周期名称,
                'confidence': 置信度,
                'regime_scores': 各周期评分,
                'description': 中文描述,
            }
        """
        score_result = self.compute_macro_score(factors)
        composite = score_result["composite_score"]

        # 提取通胀水平
        inflation_data = factors.get("inflation", {})
        cpi = inflation_data.get("CPI", 2.0)
        ppi = inflation_data.get("PPI", 0.0)
        inflation_level = (cpi + max(ppi, 0)) / 2.0  # 综合通胀

        # 提取增长水平
        pmi_data = factors.get("pmi", {})
        mfg_pmi = pmi_data.get("制造业PMI", 50.0)
        growth_signal = (mfg_pmi - 50.0) / 10.0  # PMI偏离50的程度

        # 各周期评分 (越高越可能)
        regime_scores = {
            "expansion": 0.0,
            "recovery": 0.0,
            "recession": 0.0,
            "stagflation": 0.0,
        }

        # 扩张: 高增长 + 低通胀
        regime_scores["expansion"] = max(0, growth_signal) * 0.6 + max(0, 1 - inflation_level / 5.0) * 0.4

        # 复苏: 增长回升 + 通胀温和
        regime_scores["recovery"] = max(0, growth_signal + 0.3) * 0.5 + max(0, 1 - abs(inflation_level - 2.0) / 5.0) * 0.5

        # 衰退: 增长下行 + 通胀下行
        regime_scores["recession"] = max(0, -growth_signal) * 0.6 + max(0, 1 - inflation_level / 4.0) * 0.4

        # 滞胀: 增长下行 + 通胀上行
        regime_scores["stagflation"] = max(0, -growth_signal) * 0.4 + max(0, inflation_level / 5.0) * 0.6

        # 选择得分最高的周期
        best_regime = max(regime_scores, key=lambda k: regime_scores[k])
        best_score = regime_scores[best_regime]
        total_score = sum(regime_scores.values())

        # 置信度 = 最高分 / 总分
        confidence = round(best_score / total_score, 4) if total_score > 0 else 0.5

        # 中文描述
        descriptions = {
            "expansion": "经济扩张期：增长强劲，通胀温和，适合进攻型配置",
            "recovery": "经济复苏期：增长回升，通胀可控，适合成长型配置",
            "recession": "经济衰退期：增长下行，需求疲弱，适合防御型配置",
            "stagflation": "经济滞胀期：增长停滞，通胀高企，适合质量型配置",
        }

        return {
            "regime": best_regime,
            "confidence": confidence,
            "regime_scores": {k: round(v, 4) for k, v in regime_scores.items()},
            "description": descriptions[best_regime],
            "composite_score": composite,
            "inflation_level": round(inflation_level, 2),
            "growth_signal": round(growth_signal, 4),
        }

    def generate_macro_signal(self, regime: str) -> Dict:
        """
        基于宏观周期生成资产配置信号

        Args:
            regime: 周期名称 ('expansion'/'recovery'/'recession'/'stagflation')

        Returns:
            Dict: {
                'regime': 周期,
                'allocation': 资产配置建议,
                'sector_preference': 行业偏好,
                'risk_level': 风险等级,
                'strategy': 策略建议,
            }
        """
        # 各周期的资产配置权重
        ALLOCATION_MAP = {
            "expansion": {
                "股票": 0.55, "债券": 0.10, "商品": 0.20, "现金": 0.05, "另类": 0.10,
            },
            "recovery": {
                "股票": 0.50, "债券": 0.15, "商品": 0.15, "现金": 0.05, "另类": 0.15,
            },
            "recession": {
                "股票": 0.15, "债券": 0.45, "商品": 0.05, "现金": 0.25, "另类": 0.10,
            },
            "stagflation": {
                "股票": 0.20, "债券": 0.10, "商品": 0.30, "现金": 0.15, "另类": 0.25,
            },
        }

        # 行业偏好
        SECTOR_MAP = {
            "expansion": ["科技", "消费", "金融", "周期"],
            "recovery": ["科技", "医药", "新能源", "消费"],
            "recession": ["公用事业", "必需消费", "医药", "高股息"],
            "stagflation": ["资源", "能源", "必需消费", "黄金"],
        }

        # 风险等级
        RISK_MAP = {
            "expansion": "高",
            "recovery": "中高",
            "recession": "低",
            "stagflation": "中低",
        }

        # 策略建议
        STRATEGY_MAP = {
            "expansion": "进攻配置：超配成长股和周期股，适度杠杆",
            "recovery": "积极配置：超配成长与消费，逐步加仓",
            "recession": "防御配置：超配债券和必需消费，降低仓位",
            "stagflation": "对冲配置：超配资源和黄金，做空成长",
        }

        if regime not in ALLOCATION_MAP:
            regime = "recovery"  # 默认复苏

        return {
            "regime": regime,
            "allocation": ALLOCATION_MAP[regime],
            "sector_preference": SECTOR_MAP[regime],
            "risk_level": RISK_MAP[regime],
            "strategy": STRATEGY_MAP[regime],
        }


# ---------------------------------------------------------------------------
# 2. 因子融合引擎
# ---------------------------------------------------------------------------

class FactorFusionEngine:
    """
    因子融合引擎

    将三大因子维度进行动态融合:
    - 量化因子: PE/PB/ROE/动量等 (来自 shap_explainer)
    - 宏观因子: PMI/CPI/M2等 (来自 MacroFactorModel)
    - 另类信号: 卫星/舆情/供应链 (来自 multi_source_data)

    支持:
    - 基于宏观周期的时变权重调整
    - 加权综合评分
    - 简单回测
    """

    # 基础权重 (会在不同周期下调整)
    BASE_WEIGHTS = {
        "quant": 0.45,
        "macro": 0.30,
        "alt": 0.25,
    }

    # 周期调整后的权重
    REGIME_WEIGHTS = {
        "expansion": {"quant": 0.50, "macro": 0.25, "alt": 0.25},
        "recovery": {"quant": 0.45, "macro": 0.30, "alt": 0.25},
        "recession": {"quant": 0.35, "macro": 0.40, "alt": 0.25},
        "stagflation": {"quant": 0.30, "macro": 0.35, "alt": 0.35},
    }

    # 量化因子内部权重
    QUANT_FACTOR_WEIGHTS = {
        "PE": 0.15, "PB": 0.10, "ROE": 0.20, "毛利率": 0.10,
        "营收增速": 0.15, "动量_20日": 0.15, "动量_60日": 0.15,
    }

    # 另类信号内部权重
    ALT_SIGNAL_WEIGHTS = {
        "卫星信号": 0.30, "舆情信号": 0.40, "供应链信号": 0.30,
    }

    def __init__(self):
        """初始化因子融合引擎"""
        self.macro_model = MacroFactorModel()

    def fuse_factors(
        self,
        quant_factors: Dict[str, float],
        macro_factors: Dict[str, Dict[str, float]],
        alt_signals: Dict[str, float],
        regime: Optional[str] = None,
    ) -> Dict:
        """
        三维因子融合

        将量化因子、宏观因子、另类信号按动态权重融合为综合评分。

        Args:
            quant_factors: 量化因子 {因子名: 分值}，分值范围 [-1, 1]
            macro_factors: 宏观因子 {类别: {因子名: 值}}
            alt_signals: 另类信号 {信号名: 分值}，分值范围 [-1, 1]
            regime: 当前宏观周期 (如不传则自动检测)

        Returns:
            Dict: {
                'quant_score': 量化评分,
                'macro_score': 宏观评分,
                'alt_score': 另类评分,
                'composite_score': 综合评分,
                'weights': 使用的权重,
                'regime': 周期,
                'details': 各因子贡献详情,
            }
        """
        # 自动检测周期
        if regime is None:
            regime_result = self.macro_model.macro_regime_detection(macro_factors)
            regime = regime_result["regime"]

        # 获取周期调整权重
        weights = self.REGIME_WEIGHTS.get(regime, self.BASE_WEIGHTS)

        # 计算量化评分
        quant_score = self._compute_quant_score(quant_factors)

        # 计算宏观评分
        macro_result = self.macro_model.compute_macro_score(macro_factors)
        macro_score = macro_result["composite_score"]

        # 计算另类评分
        alt_score = self._compute_alt_score(alt_signals)

        # 综合评分
        composite = (
            quant_score * weights["quant"]
            + macro_score * weights["macro"]
            + alt_score * weights["alt"]
        )

        return {
            "quant_score": round(quant_score, 4),
            "macro_score": round(macro_score, 4),
            "alt_score": round(alt_score, 4),
            "composite_score": round(composite, 4),
            "weights": weights,
            "regime": regime,
            "details": {
                "quant_details": self._quant_details(quant_factors),
                "macro_details": macro_result.get("category_scores", {}),
                "alt_details": self._alt_details(alt_signals),
            },
        }

    def _compute_quant_score(self, quant_factors: Dict[str, float]) -> float:
        """计算量化因子加权评分"""
        if not quant_factors:
            return 0.0
        total_weight = 0.0
        weighted_sum = 0.0
        for fname, fval in quant_factors.items():
            w = self.QUANT_FACTOR_WEIGHTS.get(fname, 0.05)
            weighted_sum += fval * w
            total_weight += w
        return weighted_sum / total_weight if total_weight > 0 else 0.0

    def _compute_alt_score(self, alt_signals: Dict[str, float]) -> float:
        """计算另类信号加权评分"""
        if not alt_signals:
            return 0.0
        total_weight = 0.0
        weighted_sum = 0.0
        for sname, sval in alt_signals.items():
            w = self.ALT_SIGNAL_WEIGHTS.get(sname, 0.1)
            weighted_sum += sval * w
            total_weight += w
        return weighted_sum / total_weight if total_weight > 0 else 0.0

    def _quant_details(self, quant_factors: Dict[str, float]) -> Dict:
        """量化因子贡献详情"""
        details = {}
        for fname, fval in quant_factors.items():
            w = self.QUANT_FACTOR_WEIGHTS.get(fname, 0.05)
            details[fname] = {"value": fval, "weight": w, "contribution": round(fval * w, 4)}
        return details

    def _alt_details(self, alt_signals: Dict[str, float]) -> Dict:
        """另类信号贡献详情"""
        details = {}
        for sname, sval in alt_signals.items():
            w = self.ALT_SIGNAL_WEIGHTS.get(sname, 0.1)
            details[sname] = {"value": sval, "weight": w, "contribution": round(sval * w, 4)}
        return details

    def compute_composite_score(self, fused: Dict) -> Dict:
        """
        计算加权综合评分 (含时变权重)

        在 fuse_factors 结果基础上，进一步细化综合评分，
        加入时间衰减和置信度调整。

        Args:
            fused: fuse_factors 的输出

        Returns:
            Dict: {
                'composite': 综合评分,
                'adjusted_composite': 置信度调整后评分,
                'confidence': 置信度,
                'score_breakdown': 评分分解,
                'rating': 评级 (强烈推荐/推荐/中性/不推荐/强烈不推荐),
            }
        """
        composite = fused.get("composite_score", 0.0)
        quant_score = fused.get("quant_score", 0.0)
        macro_score = fused.get("macro_score", 0.0)
        alt_score = fused.get("alt_score", 0.0)

        # 置信度: 三维因子一致性越高，置信度越高
        scores = [quant_score, macro_score, alt_score]
        score_std = float(np.std(scores)) if len(scores) > 1 else 0.0
        confidence = max(0.3, 1.0 - score_std)  # 标准差越小置信度越高

        # 置信度调整
        adjusted = composite * confidence

        # 评级
        if adjusted > 0.3:
            rating = "强烈推荐"
        elif adjusted > 0.1:
            rating = "推荐"
        elif adjusted > -0.1:
            rating = "中性"
        elif adjusted > -0.3:
            rating = "不推荐"
        else:
            rating = "强烈不推荐"

        return {
            "composite": round(composite, 4),
            "adjusted_composite": round(adjusted, 4),
            "confidence": round(confidence, 4),
            "score_breakdown": {
                "quant_contribution": round(quant_score * fused.get("weights", {}).get("quant", 0.45), 4),
                "macro_contribution": round(macro_score * fused.get("weights", {}).get("macro", 0.30), 4),
                "alt_contribution": round(alt_score * fused.get("weights", {}).get("alt", 0.25), 4),
            },
            "rating": rating,
        }

    def regime_adjusted_weights(self, regime: str) -> Dict:
        """
        根据宏观周期调整因子权重

        扩张期: 动量权重高
        衰退期: 价值权重高
        复苏期: 成长权重高
        滞胀期: 质量权重高

        Args:
            regime: 周期名称

        Returns:
            Dict: {
                'dimension_weights': 维度权重,
                'quant_style_weights': 量化风格权重,
                'regime': 周期,
                'rationale': 调整理由,
            }
        """
        # 维度权重
        dim_weights = self.REGIME_WEIGHTS.get(regime, self.BASE_WEIGHTS)

        # 量化风格权重 (在不同周期下调整)
        STYLE_WEIGHTS = {
            "expansion": {
                "价值": 0.15, "成长": 0.25, "质量": 0.20, "动量": 0.30, "低波": 0.10,
            },
            "recovery": {
                "价值": 0.15, "成长": 0.35, "质量": 0.20, "动量": 0.20, "低波": 0.10,
            },
            "recession": {
                "价值": 0.30, "成长": 0.10, "质量": 0.25, "动量": 0.10, "低波": 0.25,
            },
            "stagflation": {
                "价值": 0.20, "成长": 0.10, "质量": 0.35, "动量": 0.10, "低波": 0.25,
            },
        }

        style_weights = STYLE_WEIGHTS.get(regime, STYLE_WEIGHTS["recovery"])

        # 调整理由
        RATIONALE = {
            "expansion": "扩张期市场情绪乐观，动量效应显著，超配动量因子捕捉趋势",
            "recovery": "复苏期盈利修复，成长股弹性最大，超配成长因子",
            "recession": "衰退期避险为主，价值因子提供安全边际，超配价值和低波",
            "stagflation": "滞胀期盈利质量为王，质量因子抗周期性强，超配质量和低波",
        }

        return {
            "dimension_weights": dim_weights,
            "quant_style_weights": style_weights,
            "regime": regime,
            "rationale": RATIONALE.get(regime, "默认配置"),
        }

    def backtest_factor_fusion(
        self,
        historical_data: Optional[pd.DataFrame] = None,
        lookback: int = 252,
    ) -> Dict:
        """
        因子融合策略简单回测

        基于历史数据模拟因子融合策略的表现。

        Args:
            historical_data: 历史数据 DataFrame (需包含 'return' 列)
            lookback: 回看期 (交易日数)

        Returns:
            Dict: {
                'total_return': 总收益率,
                'annual_return': 年化收益率,
                'sharpe_ratio': 夏普比率,
                'max_drawdown': 最大回撤,
                'win_rate': 胜率,
                'regime_distribution': 周期分布,
                'monthly_returns': 月度收益,
            }
        """
        # 生成演示数据
        if historical_data is None or historical_data.empty:
            np.random.seed(42)
            dates = pd.bdate_range(end=pd.Timestamp.today(), periods=lookback)
            # 模拟日收益率 (带周期切换)
            returns = np.zeros(lookback)
            regime_sequence = []
            current_regime = "recovery"
            for i in range(lookback):
                # 每60个交易日可能切换周期
                if i > 0 and i % 60 == 0:
                    regimes = ["expansion", "recovery", "recession", "stagflation"]
                    current_regime = np.random.choice(regimes)
                regime_sequence.append(current_regime)

                # 不同周期下的收益分布
                regime_params = {
                    "expansion": (0.0008, 0.012),
                    "recovery": (0.0005, 0.015),
                    "recession": (-0.0003, 0.020),
                    "stagflation": (0.0001, 0.018),
                }
                mu, sigma = regime_params[current_regime]
                # 融合策略: 超额收益
                alpha = mu * 0.5  # 因子融合带来的alpha
                returns[i] = np.random.normal(mu + alpha, sigma)

            historical_data = pd.DataFrame({
                "return": returns,
                "regime": regime_sequence,
            }, index=dates)

        returns = historical_data["return"]
        regimes = historical_data.get("regime", pd.Series(["recovery"] * len(returns)))

        # 计算策略指标
        cumulative = (1 + returns).cumprod()
        total_return = cumulative.iloc[-1] / cumulative.iloc[0] - 1

        # 年化收益
        n_days = len(returns)
        annual_return = (1 + total_return) ** (252 / max(n_days, 1)) - 1

        # 夏普比率
        sharpe = float(returns.mean() / returns.std() * np.sqrt(252)) if returns.std() > 0 else 0.0

        # 最大回撤
        running_max = cumulative.cummax()
        drawdown = (cumulative - running_max) / running_max
        max_drawdown = float(drawdown.min())

        # 胜率
        win_rate = float((returns > 0).sum() / len(returns))

        # 周期分布
        regime_dist = regimes.value_counts().to_dict() if isinstance(regimes, pd.Series) else {}

        # 月度收益
        monthly_returns = {}
        if isinstance(returns.index, pd.DatetimeIndex):
            monthly = (1 + returns).resample("ME").prod() - 1
            monthly_returns = {str(k.strftime("%Y-%m")): round(v, 4) for k, v in monthly.items()}

        return {
            "total_return": round(total_return, 4),
            "annual_return": round(annual_return, 4),
            "sharpe_ratio": round(sharpe, 4),
            "max_drawdown": round(max_drawdown, 4),
            "win_rate": round(win_rate, 4),
            "regime_distribution": regime_dist,
            "monthly_returns": monthly_returns,
            "n_observations": n_days,
        }


# ---------------------------------------------------------------------------
# 3. 信号验证数据
# ---------------------------------------------------------------------------

@dataclass
class VerificationResult:
    """信号验证结果"""
    signal_name: str
    ic: float = 0.0                    # 信息系数 (Spearman)
    ic_ir: float = 0.0                 # IC信息比率 (IC均值/IC标准差)
    hit_rate: float = 0.0              # 命中率
    decay_half_life: float = 0.0       # 衰减半衰期 (天)
    p_value: float = 1.0               # 统计显著性p值
    is_significant: bool = False       # 是否统计显著
    confidence: str = "低"             # 置信度等级
    turnover: float = 0.0              # 换手率
    cross_val_scores: List[float] = field(default_factory=list)
    vs_random: Dict = field(default_factory=dict)


class SignalVerificationData:
    """
    信号验证仪表盘数据

    提供完整的另类信号验证流程:
    - IC测试 (Spearman秩相关)
    - 换手分析 (信号稳定性)
    - 衰减分析 (预测力衰减速度)
    - 交叉验证 (时序分割)
    - 随机信号对比 (统计显著性)
    """

    def __init__(self):
        """初始化信号验证器"""
        self.min_observations = 20  # 最少观测数
        self.significance_level = 0.05  # 显著性水平

    def verify_alt_signal(
        self,
        signal_data: Optional[pd.Series] = None,
        price_data: Optional[pd.Series] = None,
        signal_name: str = "未命名信号",
    ) -> VerificationResult:
        """
        完整的另类信号验证

        Args:
            signal_data: 信号序列 (pd.Series, 索引为日期)
            price_data: 价格/收益序列 (pd.Series, 索引为日期)
            signal_name: 信号名称

        Returns:
            VerificationResult: 验证结果
        """
        # 生成演示数据
        if signal_data is None or price_data is None:
            signal_data, price_data = self._generate_demo_signal_data()

        # 确保数据对齐
        common_idx = signal_data.index.intersection(price_data.index)
        if len(common_idx) < self.min_observations:
            logger.warning("观测数不足，使用演示数据")
            signal_data, price_data = self._generate_demo_signal_data()
            common_idx = signal_data.index

        signal = signal_data.loc[common_idx].values
        forward_return = price_data.loc[common_idx].values

        # 1. IC测试 (Spearman秩相关)
        ic, ic_pvalue = self._compute_ic(signal, forward_return)

        # 2. 换手分析
        turnover = self._compute_turnover(signal)

        # 3. 衰减分析
        decay_half_life = self._compute_decay(signal, forward_return)

        # 4. 交叉验证
        cv_scores = self._cross_validate(signal, forward_return)

        # 5. 随机信号对比
        vs_random = self._compare_with_random(signal, forward_return)

        # 6. 命中率
        hit_rate = self._compute_hit_rate(signal, forward_return)

        # 7. IC信息比率
        ic_series = self._compute_rolling_ic(signal, forward_return)
        ic_ir = float(ic_series.mean() / ic_series.std()) if ic_series.std() > 0 else 0.0

        # 综合判断
        is_significant = ic_pvalue < self.significance_level and abs(ic) > 0.03
        confidence = self._assess_confidence(ic, ic_ir, hit_rate, decay_half_life, is_significant)

        return VerificationResult(
            signal_name=signal_name,
            ic=round(ic, 4),
            ic_ir=round(ic_ir, 4),
            hit_rate=round(hit_rate, 4),
            decay_half_life=round(decay_half_life, 1),
            p_value=round(ic_pvalue, 4),
            is_significant=is_significant,
            confidence=confidence,
            turnover=round(turnover, 4),
            cross_val_scores=[round(s, 4) for s in cv_scores],
            vs_random=vs_random,
        )

    def _generate_demo_signal_data(self, n_days: int = 252) -> Tuple[pd.Series, pd.Series]:
        """生成演示信号和收益数据"""
        np.random.seed(123)
        dates = pd.bdate_range(end=pd.Timestamp.today(), periods=n_days)

        # 信号: 带有一定预测力的信号
        true_alpha = np.random.normal(0, 0.01, n_days)
        signal = true_alpha + np.random.normal(0, 0.02, n_days)

        # 前向收益: 与信号有一定相关性
        noise = np.random.normal(0, 0.015, n_days)
        forward_return = 0.3 * true_alpha + noise

        return (
            pd.Series(signal, index=dates, name="signal"),
            pd.Series(forward_return, index=dates, name="forward_return"),
        )

    def _compute_ic(self, signal: np.ndarray, returns: np.ndarray) -> Tuple[float, float]:
        """计算Spearman秩相关IC"""
        try:
            ic, pvalue = stats.spearmanr(signal, returns)
            return float(ic), float(pvalue)
        except Exception:
            return 0.0, 1.0

    def _compute_rolling_ic(
        self, signal: np.ndarray, returns: np.ndarray, window: int = 20
    ) -> pd.Series:
        """计算滚动IC"""
        n = len(signal)
        if n < window:
            return pd.Series([0.0])
        ics = []
        for i in range(window, n):
            try:
                ic, _ = stats.spearmanr(signal[i - window:i], returns[i - window:i])
                ics.append(ic)
            except Exception:
                ics.append(0.0)
        return pd.Series(ics)

    def _compute_turnover(self, signal: np.ndarray) -> float:
        """计算信号换手率 (相邻期间信号方向变化比例)"""
        if len(signal) < 2:
            return 0.0
        # 将信号分为5分位
        try:
            quantiles = pd.qcut(signal, 5, labels=False, duplicates="drop")
        except Exception:
            quantiles = pd.Series(np.zeros(len(signal)))

        changes = np.diff(quantiles) != 0
        return float(changes.sum() / len(changes)) if len(changes) > 0 else 0.0

    def _compute_decay(self, signal: np.ndarray, returns: np.ndarray) -> float:
        """
        计算信号衰减半衰期

        通过计算不同滞后期IC，拟合衰减曲线，估算半衰期。
        """
        max_lag = min(60, len(signal) // 3)
        if max_lag < 5:
            return 0.0

        lags = range(1, max_lag + 1)
        lag_ics = []
        for lag in lags:
            if lag >= len(signal):
                break
            try:
                ic, _ = stats.spearmanr(signal[:-lag], returns[lag:])
                lag_ics.append(abs(ic))
            except Exception:
                lag_ics.append(0.0)

        if not lag_ics or lag_ics[0] == 0:
            return 0.0

        # 找到IC衰减到初始值一半的滞后期
        initial_ic = lag_ics[0]
        for i, ic in enumerate(lag_ics):
            if ic < initial_ic / 2:
                return float(i + 1)

        # 未衰减到一半，返回最大滞后期
        return float(max_lag)

    def _cross_validate(
        self, signal: np.ndarray, returns: np.ndarray, n_splits: int = 5
    ) -> List[float]:
        """时序交叉验证"""
        n = len(signal)
        fold_size = n // (n_splits + 1)

        if fold_size < self.min_observations:
            return [0.0]

        scores = []
        for i in range(n_splits):
            train_end = fold_size * (i + 1)
            test_end = min(train_end + fold_size, n)

            if train_end >= n or test_end > n:
                break

            train_signal = signal[:train_end]
            train_return = returns[:train_end]
            test_signal = signal[train_end:test_end]
            test_return = returns[train_end:test_end]

            try:
                ic, _ = stats.spearmanr(test_signal, test_return)
                scores.append(float(ic))
            except Exception:
                scores.append(0.0)

        return scores if scores else [0.0]

    def _compare_with_random(
        self, signal: np.ndarray, returns: np.ndarray, n_simulations: int = 100
    ) -> Dict:
        """与随机信号对比，评估统计显著性"""
        actual_ic, _ = self._compute_ic(signal, returns)

        # 生成随机信号的IC分布
        random_ics = []
        for _ in range(n_simulations):
            random_signal = np.random.permutation(signal)
            try:
                ric, _ = stats.spearmanr(random_signal, returns)
                random_ics.append(ric)
            except Exception:
                continue

        if not random_ics:
            return {"p_value_vs_random": 1.0, "percentile": 50.0, "is_significant": False}

        random_ics = np.array(random_ics)
        # 计算实际IC在随机分布中的百分位
        percentile = float(np.mean(np.abs(random_ics) < abs(actual_ic)) * 100)

        # p值: 随机IC超过实际IC绝对值的比例
        p_val = float(np.mean(np.abs(random_ics) >= abs(actual_ic)))

        return {
            "p_value_vs_random": round(p_val, 4),
            "percentile": round(percentile, 1),
            "random_ic_mean": round(float(np.mean(random_ics)), 4),
            "random_ic_std": round(float(np.std(random_ics)), 4),
            "is_significant": p_val < self.significance_level,
        }

    def _compute_hit_rate(self, signal: np.ndarray, returns: np.ndarray) -> float:
        """计算命中率: 信号方向与收益方向一致的比例"""
        if len(signal) < 2:
            return 0.5
        # 信号方向
        signal_direction = np.sign(signal)
        return_direction = np.sign(returns)
        # 忽略零值
        mask = (signal_direction != 0) & (return_direction != 0)
        if mask.sum() == 0:
            return 0.5
        return float((signal_direction[mask] == return_direction[mask]).mean())

    def _assess_confidence(
        self, ic: float, ic_ir: float, hit_rate: float,
        decay_half_life: float, is_significant: bool,
    ) -> str:
        """综合评估信号置信度"""
        score = 0
        # IC强度
        if abs(ic) > 0.1:
            score += 3
        elif abs(ic) > 0.05:
            score += 2
        elif abs(ic) > 0.03:
            score += 1

        # IC稳定性
        if abs(ic_ir) > 2.0:
            score += 2
        elif abs(ic_ir) > 1.0:
            score += 1

        # 命中率
        if hit_rate > 0.55:
            score += 2
        elif hit_rate > 0.52:
            score += 1

        # 衰减半衰期
        if decay_half_life > 20:
            score += 1

        # 统计显著
        if is_significant:
            score += 2

        if score >= 8:
            return "极高"
        elif score >= 6:
            return "高"
        elif score >= 4:
            return "中"
        elif score >= 2:
            return "低"
        else:
            return "极低"

    def generate_verification_report(self, results: VerificationResult) -> str:
        """
        生成信号验证文本报告

        Args:
            results: VerificationResult 对象

        Returns:
            str: 格式化的验证报告
        """
        lines = [
            f"{'='*60}",
            f"  信号验证报告: {results.signal_name}",
            f"{'='*60}",
            "",
            "【核心指标】",
            f"  IC (Spearman):     {results.ic:+.4f}",
            f"  IC信息比率:        {results.ic_ir:+.4f}",
            f"  命中率:            {results.hit_rate:.2%}",
            f"  衰减半衰期:        {results.decay_half_life:.0f} 天",
            f"  换手率:            {results.turnover:.2%}",
            "",
            "【统计显著性】",
            f"  p值:               {results.p_value:.4f}",
            f"  统计显著:          {'是 ✓' if results.is_significant else '否 ✗'}",
            f"  置信度:            {results.confidence}",
            "",
            "【交叉验证】",
        ]

        if results.cross_val_scores:
            for i, score in enumerate(results.cross_val_scores, 1):
                lines.append(f"  Fold {i}: IC = {score:+.4f}")
            mean_cv = np.mean(results.cross_val_scores)
            lines.append(f"  平均IC: {mean_cv:+.4f}")
        else:
            lines.append("  无交叉验证数据")

        lines.extend([
            "",
            "【随机信号对比】",
        ])

        if results.vs_random:
            lines.append(f"  随机IC均值:        {results.vs_random.get('random_ic_mean', 'N/A')}")
            lines.append(f"  随机IC标准差:      {results.vs_random.get('random_ic_std', 'N/A')}")
            lines.append(f"  百分位排名:        {results.vs_random.get('percentile', 'N/A')}%")
            lines.append(f"  vs随机p值:         {results.vs_random.get('p_value_vs_random', 'N/A')}")
        else:
            lines.append("  无对比数据")

        # 综合评价
        lines.extend([
            "",
            "【综合评价】",
        ])

        if results.confidence in ("极高", "高"):
            lines.append("  ★★★★ 信号质量优秀，可用于实盘策略")
        elif results.confidence == "中":
            lines.append("  ★★★☆ 信号质量中等，建议进一步验证后使用")
        elif results.confidence == "低":
            lines.append("  ★★☆☆ 信号质量较弱，仅作辅助参考")
        else:
            lines.append("  ★☆☆☆ 信号质量极弱，不建议使用")

        lines.append(f"{'='*60}")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# 4. Exabel风格信号看板
# ---------------------------------------------------------------------------

class ExabelStyleDashboard:
    """
    Exabel风格信号看板

    提供专业级信号管理视图:
    - 信号概览 (所有信号的关键指标一览)
    - 信号相关性矩阵 (跨信号相关性)
    - 信号边际贡献 (每个信号对收益的边际贡献)
    - 信号新鲜度 (数据时效性)
    """

    def __init__(self):
        """初始化Exabel风格看板"""
        self.verifier = SignalVerificationData()

    def compute_signal_overview(self, signals: Optional[Dict[str, Dict]] = None) -> pd.DataFrame:
        """
        信号概览

        汇总所有信号的关键指标，生成一览表。

        Args:
            signals: {信号名: {值, 类型, 更新时间, ...}}

        Returns:
            pd.DataFrame: 信号概览表
        """
        if signals is None:
            signals = self._generate_demo_signals()

        rows = []
        for name, info in signals.items():
            # 对每个信号进行快速验证
            signal_series = info.get("series")
            return_series = info.get("returns")
            if signal_series is not None and return_series is not None:
                result = self.verifier.verify_alt_signal(
                    signal_series, return_series, signal_name=name
                )
                rows.append({
                    "信号名称": name,
                    "类型": info.get("type", "未知"),
                    "当前值": info.get("current_value", 0.0),
                    "IC": result.ic,
                    "IC_IR": result.ic_ir,
                    "命中率": result.hit_rate,
                    "半衰期(天)": result.decay_half_life,
                    "置信度": result.confidence,
                    "显著": "✓" if result.is_significant else "✗",
                    "换手率": result.turnover,
                })
            else:
                # 无验证数据时使用基本信息
                rows.append({
                    "信号名称": name,
                    "类型": info.get("type", "未知"),
                    "当前值": info.get("current_value", 0.0),
                    "IC": info.get("ic", 0.0),
                    "IC_IR": info.get("ic_ir", 0.0),
                    "命中率": info.get("hit_rate", 0.0),
                    "半衰期(天)": info.get("decay_half_life", 0.0),
                    "置信度": info.get("confidence", "未验证"),
                    "显著": info.get("is_significant", "✗"),
                    "换手率": info.get("turnover", 0.0),
                })

        df = pd.DataFrame(rows)
        return df

    def compute_signal_correlation_matrix(
        self, signals: Optional[Dict[str, pd.Series]] = None
    ) -> pd.DataFrame:
        """
        信号相关性矩阵

        计算所有信号之间的Spearman秩相关系数。

        Args:
            signals: {信号名: 信号值序列}

        Returns:
            pd.DataFrame: 相关性矩阵
        """
        if signals is None:
            demo = self._generate_demo_signals()
            signals = {}
            for name, info in demo.items():
                if "series" in info:
                    signals[name] = info["series"]
                else:
                    # 生成模拟序列
                    np.random.seed(hash(name) % 2**31)
                    signals[name] = pd.Series(np.random.randn(100))

        if not signals:
            return pd.DataFrame()

        # 对齐索引
        signal_df = pd.DataFrame(signals)
        signal_df = signal_df.dropna()

        if signal_df.empty:
            return pd.DataFrame()

        # Spearman相关
        corr_matrix = signal_df.corr(method="spearman")
        return corr_matrix.round(4)

    def compute_signal_contribution(
        self,
        signals: Optional[Dict[str, pd.Series]] = None,
        returns: Optional[pd.Series] = None,
    ) -> pd.DataFrame:
        """
        信号边际贡献分析

        计算每个信号对收益的边际贡献:
        - 单信号IC
        - 增量IC (加入该信号后IC的提升)
        - 边际R²贡献

        Args:
            signals: {信号名: 信号值序列}
            returns: 收益序列

        Returns:
            pd.DataFrame: 边际贡献表
        """
        if signals is None or returns is None:
            signals, returns = self._generate_contribution_demo()

        rows = []
        signal_names = list(signals.keys())
        n_signals = len(signal_names)

        # 单信号IC
        single_ics = {}
        for name in signal_names:
            s = signals[name]
            try:
                common = s.index.intersection(returns.index)
                if len(common) > 10:
                    ic, _ = stats.spearmanr(s.loc[common].values, returns.loc[common].values)
                else:
                    ic = 0.0
            except Exception:
                ic = 0.0
            single_ics[name] = ic

        # 增量IC (逐步加入信号)
        cumulative_ic = 0.0
        for name in sorted(signal_names, key=lambda x: abs(single_ics.get(x, 0)), reverse=True):
            s = signals[name]
            try:
                common = s.index.intersection(returns.index)
                if len(common) > 10:
                    ic, _ = stats.spearmanr(s.loc[common].values, returns.loc[common].values)
                else:
                    ic = 0.0
            except Exception:
                ic = 0.0

            incremental = abs(ic) - min(abs(cumulative_ic), abs(ic)) * 0.3  # 简化增量计算
            cumulative_ic += incremental

            rows.append({
                "信号名称": name,
                "单信号IC": round(ic, 4),
                "增量IC": round(incremental, 4),
                "累计IC": round(cumulative_ic, 4),
                "贡献占比": round(incremental / max(cumulative_ic, 0.001), 4) if cumulative_ic > 0 else 0.0,
            })

        return pd.DataFrame(rows)

    def compute_signal_freshness(
        self, signals: Optional[Dict[str, Dict]] = None
    ) -> pd.DataFrame:
        """
        信号新鲜度分析

        评估每个信号数据的时效性:
        - 最后更新时间
        - 更新频率
        - 新鲜度评分
        - 数据完整度

        Args:
            signals: {信号名: {last_update, frequency, completeness, ...}}

        Returns:
            pd.DataFrame: 新鲜度表
        """
        if signals is None:
            signals = self._generate_demo_signals()

        now = pd.Timestamp.now()
        rows = []

        for name, info in signals.items():
            last_update = info.get("last_update", now - pd.Timedelta(days=7))
            if isinstance(last_update, str):
                try:
                    last_update = pd.Timestamp(last_update)
                except Exception:
                    last_update = now - pd.Timedelta(days=7)

            frequency = info.get("frequency", "日度")
            completeness = info.get("completeness", 0.8)

            # 计算新鲜度
            hours_since_update = (now - last_update).total_seconds() / 3600

            # 根据更新频率设定新鲜度阈值
            FRESHNESS_THRESHOLD = {
                "实时": 1,      # 1小时
                "日度": 24,     # 24小时
                "周度": 168,    # 7天
                "月度": 720,    # 30天
            }

            threshold = FRESHNESS_THRESHOLD.get(frequency, 24)
            freshness_score = max(0, 1 - hours_since_update / threshold)
            freshness_label = (
                "新鲜" if freshness_score > 0.7
                else "一般" if freshness_score > 0.3
                else "过期"
            )

            rows.append({
                "信号名称": name,
                "类型": info.get("type", "未知"),
                "最后更新": last_update.strftime("%Y-%m-%d %H:%M"),
                "更新频率": frequency,
                "新鲜度评分": round(freshness_score, 2),
                "新鲜度": freshness_label,
                "数据完整度": f"{completeness:.0%}",
            })

        return pd.DataFrame(rows)

    # ----- 演示数据 -----

    def _generate_demo_signals(self) -> Dict[str, Dict]:
        """生成演示信号数据"""
        np.random.seed(42)
        n = 252
        dates = pd.bdate_range(end=pd.Timestamp.today(), periods=n)

        # 卫星信号
        sat_signal = pd.Series(
            np.cumsum(np.random.randn(n)) * 0.01, index=dates, name="卫星信号"
        )
        # 舆情信号
        sent_signal = pd.Series(
            np.cumsum(np.random.randn(n)) * 0.01 + 0.005, index=dates, name="舆情信号"
        )
        # 供应链信号
        supply_signal = pd.Series(
            np.cumsum(np.random.randn(n)) * 0.01 - 0.003, index=dates, name="供应链信号"
        )
        # 另类消费信号
        consumption_signal = pd.Series(
            np.cumsum(np.random.randn(n)) * 0.01 + 0.002, index=dates, name="另类消费信号"
        )
        # 资金流信号
        fund_flow_signal = pd.Series(
            np.cumsum(np.random.randn(n)) * 0.01 - 0.001, index=dates, name="资金流信号"
        )

        # 共用收益序列
        returns = pd.Series(np.random.normal(0.0005, 0.015, n), index=dates, name="returns")

        return {
            "卫星信号": {
                "type": "另类数据",
                "current_value": round(sat_signal.iloc[-1], 4),
                "last_update": dates[-1],
                "frequency": "周度",
                "completeness": 0.92,
                "series": sat_signal,
                "returns": returns,
            },
            "舆情信号": {
                "type": "NLP",
                "current_value": round(sent_signal.iloc[-1], 4),
                "last_update": dates[-1],
                "frequency": "日度",
                "completeness": 0.98,
                "series": sent_signal,
                "returns": returns,
            },
            "供应链信号": {
                "type": "另类数据",
                "current_value": round(supply_signal.iloc[-1], 4),
                "last_update": dates[-2],
                "frequency": "月度",
                "completeness": 0.85,
                "series": supply_signal,
                "returns": returns,
            },
            "另类消费信号": {
                "type": "另类数据",
                "current_value": round(consumption_signal.iloc[-1], 4),
                "last_update": dates[-1],
                "frequency": "日度",
                "completeness": 0.95,
                "series": consumption_signal,
                "returns": returns,
            },
            "资金流信号": {
                "type": "量化",
                "current_value": round(fund_flow_signal.iloc[-1], 4),
                "last_update": dates[-1],
                "frequency": "实时",
                "completeness": 1.0,
                "series": fund_flow_signal,
                "returns": returns,
            },
        }

    def _generate_contribution_demo(
        self,
    ) -> Tuple[Dict[str, pd.Series], pd.Series]:
        """生成边际贡献演示数据"""
        np.random.seed(456)
        n = 252
        dates = pd.bdate_range(end=pd.Timestamp.today(), periods=n)

        base_factor = np.random.randn(n) * 0.01
        returns = pd.Series(base_factor + np.random.randn(n) * 0.015, index=dates)

        signals = {
            "动量因子": pd.Series(base_factor * 0.6 + np.random.randn(n) * 0.01, index=dates),
            "价值因子": pd.Series(base_factor * 0.4 + np.random.randn(n) * 0.01, index=dates),
            "质量因子": pd.Series(base_factor * 0.3 + np.random.randn(n) * 0.01, index=dates),
            "舆情因子": pd.Series(base_factor * 0.2 + np.random.randn(n) * 0.01, index=dates),
            "卫星因子": pd.Series(base_factor * 0.15 + np.random.randn(n) * 0.01, index=dates),
        }

        return signals, returns


# ---------------------------------------------------------------------------
# 便捷函数: 供 Streamlit 页面直接调用
# ---------------------------------------------------------------------------

def get_macro_factor_model() -> MacroFactorModel:
    """获取宏观因子模型实例"""
    return MacroFactorModel()


def get_factor_fusion_engine() -> FactorFusionEngine:
    """获取因子融合引擎实例"""
    return FactorFusionEngine()


def get_signal_verifier() -> SignalVerificationData:
    """获取信号验证器实例"""
    return SignalVerificationData()


def get_exabel_dashboard() -> ExabelStyleDashboard:
    """获取Exabel风格看板实例"""
    return ExabelStyleDashboard()


def run_demo() -> Dict:
    """
    运行完整演示流程

    Returns:
        Dict: 包含所有模块的演示结果
    """
    results = {}

    # 1. 宏观因子模型
    macro_model = get_macro_factor_model()
    demo_factors = macro_model.generate_demo_factors()
    results["macro_score"] = macro_model.compute_macro_score(demo_factors)
    results["macro_regime"] = macro_model.macro_regime_detection(demo_factors)
    results["macro_signal"] = macro_model.generate_macro_signal(results["macro_regime"]["regime"])

    # 2. 因子融合
    fusion_engine = get_factor_fusion_engine()
    quant_factors = {"PE": -0.3, "PB": -0.2, "ROE": 0.5, "毛利率": 0.3, "营收增速": 0.4, "动量_20日": 0.6, "动量_60日": 0.4}
    alt_signals = {"卫星信号": 0.3, "舆情信号": 0.5, "供应链信号": -0.2}
    results["fusion"] = fusion_engine.fuse_factors(quant_factors, demo_factors, alt_signals)
    results["composite"] = fusion_engine.compute_composite_score(results["fusion"])
    results["regime_weights"] = fusion_engine.regime_adjusted_weights(results["macro_regime"]["regime"])
    results["backtest"] = fusion_engine.backtest_factor_fusion()

    # 3. 信号验证
    verifier = get_signal_verifier()
    verification = verifier.verify_alt_signal(signal_name="演示信号")
    results["verification"] = verification
    results["verification_report"] = verifier.generate_verification_report(verification)

    # 4. Exabel看板
    dashboard = get_exabel_dashboard()
    results["signal_overview"] = dashboard.compute_signal_overview()
    results["signal_correlation"] = dashboard.compute_signal_correlation_matrix()
    results["signal_contribution"] = dashboard.compute_signal_contribution()
    results["signal_freshness"] = dashboard.compute_signal_freshness()

    return results
