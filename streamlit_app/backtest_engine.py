"""
QuantInsight Pro - 回测引擎 (Backtest Engine)
================================================

开源模块 - MIT License
版本: 1.0
日期: 2026-06-06

模块说明:
---------
本模块是 QuantInsight Pro 投研平台的核心回测引擎, 提供 5 种经典策略
的回测能力, 支持 A 股市场 (HS300 / ZZ500 / CYB 等) 11.4 年长周期回测.

5 种内置策略:
1. 双均线 (MA Cross) - MA20/MA60 趋势跟踪
2. 均值回归 (Mean Reversion) - Z-score 阈值策略
3. 多因子 (Multi-Factor) - 趋势+动量+均值复合
4. 动量 (Momentum) - 60 日动量
5. 买入持有 (Buy & Hold) - 基准对照

核心特性:
- 5 策略 + N 指数回测框架
- 净值法 (NAV) 计算, 考虑双边交易成本 (默认 0.15%)
- 7 大回测指标: 年化收益 / 夏普 / 最大回撤 / 卡玛 / 胜率 / 交易次数 / 总收益
- 完整的 dataclass 输出 (BacktestResult)
- 单元测试覆盖 (test_backtest_engine.py)
- MIT License 开源, 鼓励学术研究引用

使用示例:
---------
>>> from backtest_engine import BacktestEngine, StrategyType
>>> import pandas as pd
>>>
>>> # 准备数据 (date, close 两列)
>>> df = pd.read_csv('hs300.csv', parse_dates=['date'])
>>>
>>> # 初始化引擎 (5 策略)
>>> engine = BacktestEngine(
...     cost=0.0015,           # 双边成本 0.15%
...     initial_capital=1.0,   # 初始资金 (归一化)
...     years=11.4,            # 回测年数
... )
>>>
>>> # 运行回测
>>> result = engine.run(df, strategy=StrategyType.MULTI_FACTOR)
>>> print(f"年化: {result.metrics.annual_return*100:.2f}%")
>>> print(f"夏普: {result.metrics.sharpe:.2f}")
>>> print(f"最大回撤: {result.metrics.max_drawdown*100:.2f}%")

学术引用:
---------
如果您在学术研究中使用本引擎, 请引用:

    冯亦根, 薛永再, 黄成选, 冯思涵 (2026).
    "QuantInsight Pro: AI 驱动的另类数据量化投研平台".
    工作论文, 慧点资本 (InsightQuant).

GitHub:
-------
https://github.com/yigenfeng0707-netizen/quantinsight-pro
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Optional

import numpy as np
import pandas as pd

__version__ = "1.0.0"
__author__ = "QuantInsight Pro Team"
__license__ = "MIT"

logger = logging.getLogger(__name__)


# ============================================================================
# 枚举与配置
# ============================================================================

class StrategyType(str, Enum):
    """策略类型枚举"""
    MA_CROSS = "ma_cross"
    MEAN_REVERSION = "mean_reversion"
    MULTI_FACTOR = "multi_factor"
    MOMENTUM = "momentum"
    BUY_HOLD = "buy_hold"


@dataclass
class BacktestConfig:
    """回测配置"""
    cost: float = 0.0015  # 双边交易成本
    initial_capital: float = 1.0  # 初始资金 (归一化为 1.0)
    years: float = 11.4  # 回测年数 (用于年化)
    trading_days_per_year: int = 252  # 年化交易日数
    ma_short: int = 20  # 短均线周期
    ma_long: int = 60  # 长均线周期
    mr_window: int = 20  # 均值回归窗口
    mr_threshold: float = 1.5  # 均值回归阈值 (z-score)
    momentum_window: int = 60  # 动量窗口
    multi_factor_score_threshold: float = 0.5  # 多因子信号阈值


@dataclass
class BacktestMetrics:
    """回测指标"""
    total_return: float = 0.0
    annual_return: float = 0.0
    sharpe: float = 0.0
    max_drawdown: float = 0.0
    calmar: float = 0.0
    win_rate: float = 0.0
    trades: int = 0
    volatility: float = 0.0


@dataclass
class BacktestResult:
    """回测结果 (单策略 + 单标的)"""
    strategy: str = ""
    index: str = ""
    period_start: str = ""
    period_end: str = ""
    data_points: int = 0
    metrics: BacktestMetrics = field(default_factory=BacktestMetrics)
    nav_series: Optional[pd.Series] = None
    signal_series: Optional[pd.Series] = None
    turnover_series: Optional[pd.Series] = None
    config: Optional[BacktestConfig] = None

    def to_dict(self, include_series: bool = False) -> dict:
        """转为字典"""
        result = {
            "strategy": self.strategy,
            "index": self.index,
            "period_start": self.period_start,
            "period_end": self.period_end,
            "data_points": self.data_points,
            "metrics": asdict(self.metrics),
            "config": asdict(self.config) if self.config else None,
        }
        if include_series and self.nav_series is not None:
            result["nav"] = self.nav_series.tolist()
            result["signal"] = self.signal_series.tolist() if self.signal_series is not None else None
        return result

    def summary(self) -> str:
        """一句话摘要"""
        m = self.metrics
        return (f"[{self.strategy:20s}] 年化={m.annual_return*100:6.2f}% "
                f"夏普={m.sharpe:5.2f} "
                f"回撤={m.max_drawdown*100:6.2f}% "
                f"交易={m.trades:4.0f}")


# ============================================================================
# 策略实现 (5 策略)
# ============================================================================

def _ma_cross(df: pd.DataFrame, cfg: BacktestConfig) -> pd.DataFrame:
    """
    策略 1: 双均线 MA20/MA60 趋势跟踪
    - 金叉 (MA20 > MA60): 做多
    - 死叉 (MA20 < MA60): 做空 / 空仓
    """
    df = df.copy()
    df["ma_short"] = df["close"].rolling(cfg.ma_short).mean()
    df["ma_long"] = df["close"].rolling(cfg.ma_long).mean()
    df["signal"] = 0
    df.loc[df["ma_short"] > df["ma_long"], "signal"] = 1
    df["signal"] = df["signal"].shift(1).fillna(0)
    df["position"] = df["signal"]
    return _compute_returns(df, cfg)


def _mean_reversion(df: pd.DataFrame, cfg: BacktestConfig) -> pd.DataFrame:
    """
    策略 2: 均值回归 (Z-Score)
    - zscore < -threshold: 买入 (超跌)
    - zscore > +threshold: 卖出 (超涨)
    - |zscore| < 0.5: 清仓 (回归中性)
    """
    df = df.copy()
    df["ma"] = df["close"].rolling(cfg.mr_window).mean()
    df["std"] = df["close"].rolling(cfg.mr_window).std()
    df["zscore"] = (df["close"] - df["ma"]) / df["std"]
    df["signal"] = 0
    df.loc[df["zscore"] < -cfg.mr_threshold, "signal"] = 1
    df.loc[df["zscore"] > cfg.mr_threshold, "signal"] = -1
    df.loc[df["zscore"].abs() < 0.5, "signal"] = 0
    df["signal"] = df["signal"].shift(1).fillna(0)
    df["position"] = df["signal"]
    return _compute_returns(df, cfg)


def _multi_factor(df: pd.DataFrame, cfg: BacktestConfig) -> pd.DataFrame:
    """
    策略 3: 多因子复合 (4 因子等权)
    - 趋势 (close > ma20): +0.3
    - 长期趋势 (close > ma60): +0.3
    - 动量 (20 日 momentum > 0): +0.2
    - 均值 (zscore < 0): +0.2
    - 总分 > threshold: 做多
    """
    df = df.copy()
    df["ma20"] = df["close"].rolling(20).mean()
    df["ma60"] = df["close"].rolling(60).mean()
    df["momentum"] = df["close"].pct_change(20)
    df["zscore"] = (df["close"] - df["close"].rolling(20).mean()) / df["close"].rolling(20).std()

    df["score"] = 0.0
    df.loc[df["close"] > df["ma20"], "score"] += 0.3
    df.loc[df["close"] > df["ma60"], "score"] += 0.3
    df.loc[df["momentum"] > 0, "score"] += 0.2
    df.loc[df["zscore"] < 0, "score"] += 0.2
    df["signal"] = (df["score"] > cfg.multi_factor_score_threshold).astype(int).shift(1).fillna(0)
    df["position"] = df["signal"]
    return _compute_returns(df, cfg)


def _momentum(df: pd.DataFrame, cfg: BacktestConfig) -> pd.DataFrame:
    """
    策略 4: 动量策略
    - 60 日动量 > 0: 做多
    - 60 日动量 < 0: 做空 / 空仓
    """
    df = df.copy()
    df["momentum"] = df["close"].pct_change(cfg.momentum_window)
    df["signal"] = (df["momentum"] > 0).astype(int).shift(1).fillna(0)
    df["position"] = df["signal"]
    return _compute_returns(df, cfg)


def _buy_hold(df: pd.DataFrame, cfg: BacktestConfig) -> pd.DataFrame:
    """
    策略 5: 买入持有 (基准对照)
    - 始终满仓
    """
    df = df.copy()
    df["position"] = 1
    df["signal"] = 1
    df["turnover"] = 0.0
    df.loc[df.index[0], "turnover"] = 1  # 首次建仓
    df["strategy_ret"] = df["position"] * df["close"].pct_change()
    df["strategy_ret_net"] = df["strategy_ret"] - df["turnover"] * cfg.cost
    df["nav"] = (1 + df["strategy_ret_net"].fillna(0)).cumprod() * cfg.initial_capital
    return df


# ============================================================================
# 内部辅助函数
# ============================================================================

def _compute_returns(df: pd.DataFrame, cfg: BacktestConfig) -> pd.DataFrame:
    """计算策略收益序列 (含交易成本)"""
    df["strategy_ret"] = df["position"] * df["close"].pct_change()
    df["turnover"] = df["position"].diff().abs().fillna(0)
    df["strategy_ret_net"] = df["strategy_ret"] - df["turnover"] * cfg.cost
    df["nav"] = (1 + df["strategy_ret_net"].fillna(0)).cumprod() * cfg.initial_capital
    return df


_STRATEGY_REGISTRY = {
    StrategyType.MA_CROSS: _ma_cross,
    StrategyType.MEAN_REVERSION: _mean_reversion,
    StrategyType.MULTI_FACTOR: _multi_factor,
    StrategyType.MOMENTUM: _momentum,
    StrategyType.BUY_HOLD: _buy_hold,
}


def _calc_metrics(df: pd.DataFrame, cfg: BacktestConfig) -> BacktestMetrics:
    """计算 7 大回测指标"""
    nav = df["nav"]
    total_return = nav.iloc[-1] / nav.iloc[0] - 1 if len(nav) > 0 else 0
    annual_return = (nav.iloc[-1] / nav.iloc[0]) ** (1 / cfg.years) - 1 if cfg.years > 0 and len(nav) > 0 else 0

    daily_ret = df["strategy_ret_net"].dropna()
    volatility = daily_ret.std() * np.sqrt(cfg.trading_days_per_year) if len(daily_ret) > 1 else 0
    sharpe = daily_ret.mean() / daily_ret.std() * np.sqrt(cfg.trading_days_per_year) if daily_ret.std() > 0 else 0

    cummax = nav.cummax()
    drawdown = (nav - cummax) / cummax
    max_drawdown = drawdown.min() if len(drawdown) > 0 else 0
    calmar = annual_return / abs(max_drawdown) if max_drawdown != 0 else 0

    win_rate = (daily_ret > 0).sum() / len(daily_ret) if len(daily_ret) > 0 else 0
    # 交易次数 = 仓位变化次数 (不依赖 turnover 字段, 兼容所有策略)
    position_changes = (df["position"].diff().abs() > 0).sum() if len(df) > 0 else 0
    trades = int(position_changes)

    return BacktestMetrics(
        total_return=float(total_return),
        annual_return=float(annual_return),
        sharpe=float(sharpe),
        max_drawdown=float(max_drawdown),
        calmar=float(calmar),
        win_rate=float(win_rate),
        trades=trades,
        volatility=float(volatility),
    )


# ============================================================================
# 主引擎类
# ============================================================================

class BacktestEngine:
    """
    回测引擎主类

    使用示例:
        engine = BacktestEngine()
        result = engine.run(df, StrategyType.MULTI_FACTOR, index_name="hs300")
        print(result.summary())

    批量回测:
        results = engine.run_multi(df, index_name="hs300")
        for r in results:
            print(r.summary())
    """

    def __init__(self, config: Optional[BacktestConfig] = None):
        """初始化引擎"""
        self.config = config or BacktestConfig()
        logger.info(f"BacktestEngine v{__version__} 初始化, config={self.config}")

    def run(
        self,
        df: pd.DataFrame,
        strategy: StrategyType,
        index_name: str = "unknown",
    ) -> BacktestResult:
        """
        运行单策略回测

        参数:
            df: 行情数据 (需含 date 和 close 列)
            strategy: 策略类型
            index_name: 指数名称 (用于结果标识)

        返回:
            BacktestResult 对象
        """
        # 数据校验
        if "date" not in df.columns or "close" not in df.columns:
            raise ValueError("df 必须包含 'date' 和 'close' 两列")
        if len(df) < self.config.ma_long + 10:
            raise ValueError(f"数据点 {len(df)} 不足以回测 (需 ≥ {self.config.ma_long + 10})")

        # 标准化数据
        df = df.copy()
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date").reset_index(drop=True)

        # 实际年数 (从数据推断)
        days = (df["date"].iloc[-1] - df["date"].iloc[0]).days
        actual_years = days / 365.25
        cfg = BacktestConfig(**asdict(self.config))
        cfg.years = actual_years if actual_years > 0 else self.config.years

        # 策略执行
        strategy_func = _STRATEGY_REGISTRY[strategy]
        df_result = strategy_func(df, cfg)

        # 计算指标
        metrics = _calc_metrics(df_result, cfg)

        # 构造结果
        result = BacktestResult(
            strategy=strategy.value,
            index=index_name,
            period_start=str(df["date"].iloc[0].date()),
            period_end=str(df["date"].iloc[-1].date()),
            data_points=len(df),
            metrics=metrics,
            nav_series=df_result["nav"],
            signal_series=df_result["signal"],
            turnover_series=df_result["turnover"],
            config=cfg,
        )

        logger.info(f"回测完成: {result.summary()}")
        return result

    def run_multi(
        self,
        df: pd.DataFrame,
        index_name: str = "unknown",
        strategies: Optional[list] = None,
    ) -> list:
        """
        批量回测多策略

        参数:
            df: 行情数据
            index_name: 指数名称
            strategies: 策略列表 (默认全部 5 个)

        返回:
            list[BacktestResult]
        """
        strategies = strategies or list(StrategyType)
        results = []
        for strat in strategies:
            try:
                r = self.run(df, strat, index_name)
                results.append(r)
            except Exception as e:
                logger.error(f"策略 {strat} 回测失败: {e}")
        return results

    @staticmethod
    def compare(results: list) -> pd.DataFrame:
        """
        对比多策略结果

        返回:
            DataFrame (索引=策略名, 列=各项指标)
        """
        rows = []
        for r in results:
            row = asdict(r.metrics)
            row["strategy"] = r.strategy
            row["index"] = r.index
            rows.append(row)
        return pd.DataFrame(rows).set_index(["index", "strategy"])


# ============================================================================
# CLI 入口
# ============================================================================

def main():
    """CLI 入口: python -m backtest_engine <data.csv>"""
    import sys

    if len(sys.argv) < 2:
        print("用法: python -m backtest_engine <data.csv>")
        print("  data.csv 需含 date, close 两列")
        sys.exit(1)

    csv_path = sys.argv[1]
    print(f"加载数据: {csv_path}")
    df = pd.read_csv(csv_path)
    if "date" not in df.columns:
        print("错误: data.csv 需含 date 列")
        sys.exit(1)

    engine = BacktestEngine()
    results = engine.run_multi(df, index_name=csv_path)

    print("\n" + "=" * 80)
    print("回测结果")
    print("=" * 80)
    for r in results:
        print(r.summary())

    # 保存 JSON
    out_path = csv_path.replace(".csv", "_backtest.json")
    output = {
        "engine_version": __version__,
        "license": __license__,
        "results": [r.to_dict() for r in results],
    }
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False, default=str)
    print(f"\n[OK] 结果保存: {out_path}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    main()
