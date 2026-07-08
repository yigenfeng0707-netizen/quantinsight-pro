# -*- coding: utf-8 -*-
"""
QuantInsight Pro - Qlib风格因子挖掘与VectorBT回测集成
=========================================================

本模块提供三大核心能力:
1. AlphaFactorMiner  - Qlib风格Alpha因子挖掘 (无需安装Qlib)
2. VectorBTEngine    - VectorBT回测引擎 (优雅降级至内置引擎)
3. FactorICTester    - 因子IC测试 (信息系数分析)
4. SignalVerifier    - 另类数据信号验证

设计原则:
- 所有类均可独立使用, 仅依赖 pandas/numpy/scipy
- vectorbt 可选安装, 未安装时自动回退至 backtest_engine.py
- 深色主题 matplotlib 图表 (facecolor='#0A0E27')
- 全中文注释与文档字符串
- 完善的错误处理与降级策略
- 内置演示数据生成器

License: MIT
版本: 1.0.0
"""

from __future__ import annotations

import logging
import warnings
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Optional, Dict, List, Tuple, Union

import numpy as np
import pandas as pd

# 可选依赖: vectorbt
try:
    import vectorbt as vbt
    HAS_VBT = True
except ImportError:
    HAS_VBT = False

# 可选依赖: scipy
try:
    from scipy import stats as scipy_stats
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False

# 可选依赖: matplotlib
try:
    import matplotlib
    matplotlib.use('Agg')  # 非交互式后端
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    HAS_MPL = True
except ImportError:
    HAS_MPL = False

__version__ = "1.0.0"
__all__ = [
    "AlphaFactorMiner",
    "VectorBTEngine",
    "FactorICTester",
    "SignalVerifier",
    "generate_demo_data",
]

logger = logging.getLogger(__name__)

# ============================================================================
# 全局常量
# ============================================================================

# 深色主题配色 (与 ui_themes.py 一致)
DARK_BG = "#0A0E27"
DARK_BG2 = "#131938"
BRAND_CYAN = "#00D4FF"
BRAND_GOLD = "#FFB800"
BRAND_PURPLE = "#7B61FF"
BRAND_GREEN = "#00C896"
BRAND_RED = "#FF4D4F"
TEXT_WHITE = "#FFFFFF"
TEXT_GRAY = "#8A92B0"

# 默认滚动窗口
DEFAULT_WINDOWS = [5, 10, 20, 60, 120]


# ============================================================================
# 演示数据生成器
# ============================================================================

def generate_demo_data(
    n_days: int = 500,
    n_stocks: int = 10,
    start_date: str = "2024-01-02",
    seed: int = 42,
) -> pd.DataFrame:
    """
    生成模拟行情数据 (用于无真实数据时的演示)

    Args:
        n_days: 交易日数量
        n_stocks: 股票数量
        start_date: 起始日期
        seed: 随机种子

    Returns:
        DataFrame: 列=[date, stock, open, high, low, close, volume]
    """
    np.random.seed(seed)
    dates = pd.bdate_range(start_date, periods=n_days)
    stock_names = [f"STOCK{i:02d}" for i in range(n_stocks)]

    records = []
    for stock in stock_names:
        # 模拟价格路径 (几何布朗运动)
        price = 100.0
        mu = np.random.uniform(0.02, 0.12) / 252  # 日均收益率
        sigma = np.random.uniform(0.15, 0.40) / np.sqrt(252)  # 日波动率
        for d in dates:
            ret = mu + sigma * np.random.randn()
            price *= np.exp(ret)
            price = max(price, 1.0)  # 防止负价
            high = price * (1 + abs(np.random.randn() * 0.01))
            low = price * (1 - abs(np.random.randn() * 0.01))
            open_ = low + (high - low) * np.random.rand()
            vol = int(np.random.uniform(1e5, 5e7))
            records.append({
                "date": d,
                "stock": stock,
                "open": round(open_, 2),
                "high": round(high, 2),
                "low": round(low, 2),
                "close": round(price, 2),
                "volume": vol,
            })

    df = pd.DataFrame(records)
    logger.info(f"生成演示数据: {n_days}天 × {n_stocks}只 = {len(df)}条")
    return df


def _apply_dark_theme(ax=None):
    """应用深色主题到matplotlib图表"""
    if not HAS_MPL:
        return
    if ax is None:
        ax = plt.gca()
    fig = ax.get_figure()
    fig.patch.set_facecolor(DARK_BG)
    ax.set_facecolor(DARK_BG2)
    ax.tick_params(colors=TEXT_GRAY, labelsize=9)
    ax.xaxis.label.set_color(TEXT_WHITE)
    ax.yaxis.label.set_color(TEXT_WHITE)
    ax.title.set_color(TEXT_WHITE)
    for spine in ax.spines.values():
        spine.set_color(TEXT_GRAY)
        spine.set_linewidth(0.5)
    ax.grid(True, alpha=0.15, color=TEXT_GRAY, linestyle='--')


# ============================================================================
# 1. Alpha因子挖掘器
# ============================================================================

class AlphaFactorMiner:
    """
    Qlib风格Alpha因子挖掘器

    无需安装Qlib, 使用纯pandas/numpy实现因子计算。
    兼容Qlib数据格式 (若已安装Qlib可直接对接)。

    功能:
    - 滚动统计因子 (均值/标准差/偏度/峰度)
    - 技术指标因子 (RSI/MACD/布林带/ATR/OBV)
    - 截面标准化 (rank/zscore)
    - 因子换手率分析

    使用示例:
        >>> miner = AlphaFactorMiner()
        >>> factors = miner.mine_all_factors(df)
        >>> ranked = miner.cross_section_rank(factors, factor_col='rsi_14')
    """

    def __init__(self, windows: Optional[List[int]] = None):
        """
        初始化因子挖掘器

        Args:
            windows: 滚动窗口列表, 默认 [5, 10, 20, 60, 120]
        """
        self.windows = windows or DEFAULT_WINDOWS

    # ------------------------------------------------------------------
    # 滚动统计因子
    # ------------------------------------------------------------------

    def rolling_stats(self, df: pd.DataFrame, price_col: str = "close") -> pd.DataFrame:
        """
        计算滚动统计因子 (均值/标准差/偏度/峰度)

        Args:
            df: 行情数据, 需含 price_col 列
            price_col: 价格列名

        Returns:
            DataFrame: 原始数据 + 滚动统计因子列
        """
        df = df.copy()
        series = df[price_col]

        for w in self.windows:
            roll = series.rolling(w)
            df[f"mean_{w}"] = roll.mean()
            df[f"std_{w}"] = roll.std()
            # 偏度与峰度需要至少3/4个数据点
            df[f"skew_{w}"] = roll.apply(lambda x: self._safe_skew(x), raw=True)
            df[f"kurt_{w}"] = roll.apply(lambda x: self._safe_kurt(x), raw=True)
            # 动量因子
            df[f"momentum_{w}"] = series.pct_change(w)
            # 波动率因子
            df[f"volatility_{w}"] = roll.std() / roll.mean()  # 变异系数

        return df

    @staticmethod
    def _safe_skew(x) -> float:
        """安全计算偏度"""
        if len(x) < 3:
            return np.nan
        n = len(x)
        mean = np.mean(x)
        std = np.std(x, ddof=1)
        if std == 0:
            return 0.0
        return float(np.mean(((x - mean) / std) ** 3))

    @staticmethod
    def _safe_kurt(x) -> float:
        """安全计算峰度 (超额峰度)"""
        if len(x) < 4:
            return np.nan
        n = len(x)
        mean = np.mean(x)
        std = np.std(x, ddof=1)
        if std == 0:
            return 0.0
        return float(np.mean(((x - mean) / std) ** 4) - 3.0)

    # ------------------------------------------------------------------
    # 技术指标因子
    # ------------------------------------------------------------------

    def technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        计算技术指标因子 (RSI/MACD/布林带/ATR/OBV)

        Args:
            df: 行情数据, 需含 open/high/low/close/volume 列

        Returns:
            DataFrame: 原始数据 + 技术指标因子列
        """
        df = df.copy()

        # RSI (相对强弱指数)
        for period in [6, 14, 28]:
            df[f"rsi_{period}"] = self._calc_rsi(df["close"], period)

        # MACD
        macd_cols = self._calc_macd(df["close"])
        for col_name, col_data in macd_cols.items():
            df[col_name] = col_data

        # 布林带
        bb_cols = self._calc_bollinger(df["close"])
        for col_name, col_data in bb_cols.items():
            df[col_name] = col_data

        # ATR (真实波幅)
        if all(c in df.columns for c in ["high", "low", "close"]):
            df["atr_14"] = self._calc_atr(df["high"], df["low"], df["close"], 14)
            df["atr_14_pct"] = df["atr_14"] / df["close"]

        # OBV (能量潮)
        if "volume" in df.columns:
            df["obv"] = self._calc_obv(df["close"], df["volume"])
            df["obv_ma20"] = df["obv"].rolling(20).mean()

        return df

    @staticmethod
    def _calc_rsi(close: pd.Series, period: int = 14) -> pd.Series:
        """
        计算RSI (相对强弱指数)

        Args:
            close: 收盘价序列
            period: RSI周期

        Returns:
            Series: RSI值 (0-100)
        """
        delta = close.diff()
        gain = delta.where(delta > 0, 0.0)
        loss = (-delta).where(delta < 0, 0.0)

        # 使用指数移动平均
        avg_gain = gain.ewm(alpha=1.0 / period, min_periods=period).mean()
        avg_loss = loss.ewm(alpha=1.0 / period, min_periods=period).mean()

        rs = avg_gain / avg_loss.replace(0, np.nan)
        rsi = 100.0 - (100.0 / (1.0 + rs))
        return rsi

    @staticmethod
    def _calc_macd(
        close: pd.Series,
        fast: int = 12,
        slow: int = 26,
        signal: int = 9,
    ) -> Dict[str, pd.Series]:
        """
        计算MACD (移动平均收敛/发散)

        Args:
            close: 收盘价序列
            fast: 快线周期
            slow: 慢线周期
            signal: 信号线周期

        Returns:
            Dict: {macd_dif, macd_dea, macd_hist}
        """
        ema_fast = close.ewm(span=fast, adjust=False).mean()
        ema_slow = close.ewm(span=slow, adjust=False).mean()
        dif = ema_fast - ema_slow
        dea = dif.ewm(span=signal, adjust=False).mean()
        hist = 2 * (dif - dea)  # 柱状图放大2倍便于观察

        return {
            "macd_dif": dif,
            "macd_dea": dea,
            "macd_hist": hist,
        }

    @staticmethod
    def _calc_bollinger(
        close: pd.Series,
        period: int = 20,
        num_std: float = 2.0,
    ) -> Dict[str, pd.Series]:
        """
        计算布林带 (Bollinger Bands)

        Args:
            close: 收盘价序列
            period: 移动平均周期
            num_std: 标准差倍数

        Returns:
            Dict: {bb_mid, bb_upper, bb_lower, bb_width, bb_pct}
        """
        mid = close.rolling(period).mean()
        std = close.rolling(period).std()
        upper = mid + num_std * std
        lower = mid - num_std * std
        width = (upper - lower) / mid.replace(0, np.nan)
        # %B指标: 价格在布林带中的位置
        pct = (close - lower) / (upper - lower).replace(0, np.nan)

        return {
            "bb_mid": mid,
            "bb_upper": upper,
            "bb_lower": lower,
            "bb_width": width,
            "bb_pct": pct,
        }

    @staticmethod
    def _calc_atr(
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        period: int = 14,
    ) -> pd.Series:
        """
        计算ATR (平均真实波幅)

        Args:
            high: 最高价
            low: 最低价
            close: 收盘价
            period: ATR周期

        Returns:
            Series: ATR值
        """
        prev_close = close.shift(1)
        tr1 = high - low
        tr2 = (high - prev_close).abs()
        tr3 = (low - prev_close).abs()
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.ewm(alpha=1.0 / period, min_periods=period).mean()
        return atr

    @staticmethod
    def _calc_obv(close: pd.Series, volume: pd.Series) -> pd.Series:
        """
        计算OBV (能量潮指标)

        Args:
            close: 收盘价
            volume: 成交量

        Returns:
            Series: OBV值
        """
        direction = np.sign(close.diff())
        direction.iloc[0] = 0
        obv = (volume * direction).cumsum()
        return obv

    # ------------------------------------------------------------------
    # 截面标准化
    # ------------------------------------------------------------------

    @staticmethod
    def cross_section_rank(
        df: pd.DataFrame,
        factor_col: str,
        group_col: str = "date",
        ascending: bool = True,
    ) -> pd.Series:
        """
        截面排名标准化 (按日期分组排名)

        Args:
            df: 含因子列和分组列的DataFrame
            factor_col: 因子列名
            group_col: 分组列 (默认按日期)
            ascending: 是否升序排名

        Returns:
            Series: 排名百分比 (0-1)
        """
        ranked = df.groupby(group_col)[factor_col].rank(
            pct=True, ascending=ascending
        )
        return ranked

    @staticmethod
    def cross_section_zscore(
        df: pd.DataFrame,
        factor_col: str,
        group_col: str = "date",
    ) -> pd.Series:
        """
        截面Z-Score标准化 (按日期分组标准化)

        Args:
            df: 含因子列和分组列的DataFrame
            factor_col: 因子列名
            group_col: 分组列 (默认按日期)

        Returns:
            Series: Z-Score值
        """
        grouped = df.groupby(group_col)[factor_col]
        def _zscore(x):
            std = x.std()
            if std == 0 or np.isnan(std):
                return pd.Series(np.nan, index=x.index)
            return (x - x.mean()) / std
        zscore = grouped.transform(_zscore)
        return zscore

    # ------------------------------------------------------------------
    # 因子换手率分析
    # ------------------------------------------------------------------

    @staticmethod
    def factor_turnover(
        factor_series: pd.Series,
        group_col: Optional[pd.Series] = None,
        top_n: int = 50,
    ) -> pd.DataFrame:
        """
        因子换手率分析 (衡量因子排名的稳定性)

        Args:
            factor_series: 因子值序列 (需为多截面长格式, 含日期索引或分组列)
            group_col: 截面分组列 (如日期)
            top_n: 取Top N计算换手率

        Returns:
            DataFrame: 列=[date, turnover, retention]
                turnover: 换手率 (0-1)
                retention: 留存率 (0-1)
        """
        if group_col is None:
            if isinstance(factor_series.index, pd.MultiIndex):
                group_col = factor_series.index.get_level_values(0)
            else:
                # 假设为单时间序列, 无法计算截面换手率
                logger.warning("因子换手率分析需要截面数据, 当前为单序列")
                return pd.DataFrame()

        df = pd.DataFrame({"factor": factor_series.values, "group": group_col.values})

        results = []
        prev_top = None
        for name, group in df.groupby("group"):
            current_top = set(group.nlargest(min(top_n, len(group)), "factor").index)
            if prev_top is not None:
                # 换手率 = 新增占比
                new_entries = current_top - prev_top
                turnover = len(new_entries) / max(len(current_top), 1)
                retention = 1.0 - turnover
            else:
                turnover = np.nan
                retention = np.nan
            results.append({
                "date": name,
                "turnover": turnover,
                "retention": retention,
            })
            prev_top = current_top

        return pd.DataFrame(results).dropna()

    # ------------------------------------------------------------------
    # 一键挖掘所有因子
    # ------------------------------------------------------------------

    def mine_all_factors(self, df: pd.DataFrame, price_col: str = "close") -> pd.DataFrame:
        """
        一键挖掘所有因子 (滚动统计 + 技术指标)

        Args:
            df: 行情数据
            price_col: 价格列名

        Returns:
            DataFrame: 原始数据 + 所有因子列
        """
        logger.info(f"开始挖掘因子, 数据量={len(df)}, 窗口={self.windows}")
        df = self.rolling_stats(df, price_col)
        df = self.technical_indicators(df)
        # 清理无穷值
        df = df.replace([np.inf, -np.inf], np.nan)
        logger.info(f"因子挖掘完成, 共生成 {len(df.columns)} 列")
        return df


# ============================================================================
# 2. VectorBT回测引擎
# ============================================================================

class VBTStrategyType(str, Enum):
    """VectorBT策略类型枚举"""
    MA_CROSS = "ma_cross"            # 双均线
    MOMENTUM = "momentum"            # 动量
    MEAN_REVERSION = "mean_reversion"  # 均值回归
    MULTI_FACTOR = "multi_factor"    # 多因子
    PAIRS_TRADING = "pairs_trading"  # 配对交易


@dataclass
class VBTBacktestMetrics:
    """VectorBT回测指标"""
    total_return: float = 0.0       # 总收益
    annual_return: float = 0.0      # 年化收益
    sharpe: float = 0.0             # 夏普比率
    max_drawdown: float = 0.0       # 最大回撤
    calmar: float = 0.0             # 卡玛比率
    win_rate: float = 0.0           # 胜率
    turnover: float = 0.0           # 换手率
    volatility: float = 0.0         # 年化波动率
    total_trades: int = 0           # 总交易次数


@dataclass
class VBTBacktestResult:
    """VectorBT回测结果"""
    strategy: str = ""
    benchmark: str = ""
    metrics: VBTBacktestMetrics = field(default_factory=VBTBacktestMetrics)
    equity_curve: Optional[pd.Series] = None
    benchmark_curve: Optional[pd.Series] = None
    positions: Optional[pd.DataFrame] = None
    use_vectorbt: bool = False

    def summary(self) -> str:
        """一句话摘要"""
        m = self.metrics
        engine_tag = "VBT" if self.use_vectorbt else "内置"
        return (f"[{self.strategy:20s}][{engine_tag}] "
                f"年化={m.annual_return*100:6.2f}% "
                f"夏普={m.sharpe:5.2f} "
                f"回撤={m.max_drawdown*100:6.2f}% "
                f"胜率={m.win_rate*100:5.1f}% "
                f"交易={m.total_trades:4d}")


class VectorBTEngine:
    """
    VectorBT回测引擎

    优先使用vectorbt进行高性能向量化回测;
    若vectorbt未安装, 自动回退至内置backtest_engine.py逻辑。

    支持5+策略:
    1. MA Cross (双均线)
    2. Momentum (动量)
    3. Mean Reversion (均值回归)
    4. Multi-Factor (多因子)
    5. Pairs Trading (配对交易)

    使用示例:
        >>> engine = VectorBTEngine()
        >>> result = engine.run_backtest(data, strategy='ma_cross')
        >>> print(result.summary())
    """

    # 基准指数映射
    BENCHMARK_MAP = {
        "hs300": "沪深300",
        "zz500": "中证500",
        "cyb": "创业板指",
    }

    def __init__(
        self,
        cost: float = 0.0015,
        initial_capital: float = 1_000_000,
        risk_free_rate: float = 0.03,
        trading_days: int = 252,
    ):
        """
        初始化回测引擎

        Args:
            cost: 双边交易成本
            initial_capital: 初始资金
            risk_free_rate: 无风险利率 (年化)
            trading_days: 年化交易日数
        """
        self.cost = cost
        self.initial_capital = initial_capital
        self.risk_free_rate = risk_free_rate
        self.trading_days = trading_days
        self.has_vbt = HAS_VBT

        if self.has_vbt:
            logger.info("VectorBTEngine: 使用vectorbt加速回测")
        else:
            logger.info("VectorBTEngine: vectorbt未安装, 使用内置回测逻辑")

    def run_backtest(
        self,
        data: pd.DataFrame,
        strategy: str = "ma_cross",
        params: Optional[Dict] = None,
        benchmark_data: Optional[pd.DataFrame] = None,
    ) -> VBTBacktestResult:
        """
        运行回测

        Args:
            data: 行情数据, 需含 date/close 列, 可选 open/high/low/volume
            strategy: 策略名称, 见 VBTStrategyType
            params: 策略参数字典
            benchmark_data: 基准数据 (可选)

        Returns:
            VBTBacktestResult
        """
        params = params or {}
        strategy = strategy.lower().replace("-", "_").replace(" ", "_")

        # 数据校验与预处理
        data = self._validate_and_prepare(data)

        if self.has_vbt:
            result = self._run_with_vbt(data, strategy, params, benchmark_data)
        else:
            result = self._run_builtin(data, strategy, params, benchmark_data)

        return result

    def _validate_and_prepare(self, data: pd.DataFrame) -> pd.DataFrame:
        """数据校验与预处理"""
        data = data.copy()

        if "close" not in data.columns:
            raise ValueError("数据必须包含 'close' 列")

        # 确保有日期列
        if "date" in data.columns:
            data["date"] = pd.to_datetime(data["date"])
            data = data.sort_values("date").reset_index(drop=True)

        # 填充缺失的OHLCV列
        if "open" not in data.columns:
            data["open"] = data["close"]
        if "high" not in data.columns:
            data["high"] = data["close"]
        if "low" not in data.columns:
            data["low"] = data["close"]
        if "volume" not in data.columns:
            data["volume"] = 1_000_000

        # 前向填充
        data = data.ffill().dropna(subset=["close"])

        return data

    # ------------------------------------------------------------------
    # VectorBT回测
    # ------------------------------------------------------------------

    def _run_with_vbt(
        self,
        data: pd.DataFrame,
        strategy: str,
        params: Dict,
        benchmark_data: Optional[pd.DataFrame],
    ) -> VBTBacktestResult:
        """使用vectorbt进行回测"""
        try:
            close = data["close"]
            entries, exits = self._generate_signals_vbt(data, strategy, params)

            # 构建投资组合
            pf = vbt.Portfolio.from_signals(
                close=close,
                entries=entries,
                exits=exits,
                init_cash=self.initial_capital,
                fees=self.cost,
                freq="1D",
            )

            # 提取指标
            metrics = self._extract_vbt_metrics(pf)
            equity_curve = pf.value

            # 基准曲线
            benchmark_curve = None
            if benchmark_data is not None and "close" in benchmark_data.columns:
                bm_close = benchmark_data["close"].reindex(data.index, method="ffill")
                benchmark_curve = bm_close / bm_close.iloc[0] * self.initial_capital

            return VBTBacktestResult(
                strategy=strategy,
                benchmark=self.BENCHMARK_MAP.get(strategy, ""),
                metrics=metrics,
                equity_curve=equity_curve,
                benchmark_curve=benchmark_curve,
                use_vectorbt=True,
            )

        except Exception as e:
            logger.warning(f"VectorBT回测失败, 回退至内置引擎: {e}")
            return self._run_builtin(data, strategy, params, benchmark_data)

    def _generate_signals_vbt(
        self,
        data: pd.DataFrame,
        strategy: str,
        params: Dict,
    ) -> Tuple[pd.Series, pd.Series]:
        """生成vectorbt格式的入场/出场信号"""
        close = data["close"]

        if strategy == VBTStrategyType.MA_CROSS.value:
            short_w = params.get("short_window", 20)
            long_w = params.get("long_window", 60)
            ma_short = close.rolling(short_w).mean()
            ma_long = close.rolling(long_w).mean()
            entries = (ma_short > ma_long) & (ma_short.shift(1) <= ma_long.shift(1))
            exits = (ma_short < ma_long) & (ma_short.shift(1) >= ma_long.shift(1))

        elif strategy == VBTStrategyType.MOMENTUM.value:
            window = params.get("window", 60)
            mom = close.pct_change(window)
            entries = (mom > 0) & (mom.shift(1) <= 0)
            exits = (mom < 0) & (mom.shift(1) >= 0)

        elif strategy == VBTStrategyType.MEAN_REVERSION.value:
            window = params.get("window", 20)
            threshold = params.get("threshold", 1.5)
            ma = close.rolling(window).mean()
            std = close.rolling(window).std()
            zscore = (close - ma) / std.replace(0, np.nan)
            entries = zscore < -threshold
            exits = zscore > threshold

        elif strategy == VBTStrategyType.MULTI_FACTOR.value:
            # 多因子综合信号
            score_threshold = params.get("score_threshold", 0.5)
            score = self._compute_multi_factor_score(data)
            entries = (score > score_threshold) & (score.shift(1) <= score_threshold)
            exits = (score < -score_threshold) & (score.shift(1) >= -score_threshold)

        elif strategy == VBTStrategyType.PAIRS_TRADING.value:
            # 配对交易: 需要两只股票数据
            spread_window = params.get("spread_window", 20)
            spread_threshold = params.get("spread_threshold", 2.0)
            if "spread" not in data.columns:
                # 如果没有提供价差, 使用close与MA的偏离作为代理
                ma = close.rolling(spread_window).mean()
                spread = (close - ma) / close.rolling(spread_window).std().replace(0, np.nan)
            else:
                spread = data["spread"]
            entries = spread < -spread_threshold
            exits = spread > spread_threshold

        else:
            # 未知策略, 默认买入持有
            entries = pd.Series(True, index=data.index)
            entries.iloc[1:] = False
            exits = pd.Series(False, index=data.index)

        return entries.fillna(False), exits.fillna(False)

    def _compute_multi_factor_score(self, data: pd.DataFrame) -> pd.Series:
        """计算多因子综合得分"""
        close = data["close"]
        score = pd.Series(0.0, index=data.index)

        # 趋势因子
        ma20 = close.rolling(20).mean()
        ma60 = close.rolling(60).mean()
        score += ((close > ma20).astype(float) * 0.3)
        score += ((close > ma60).astype(float) * 0.3)

        # 动量因子
        momentum = close.pct_change(20)
        score += ((momentum > 0).astype(float) * 0.2)

        # 均值回归因子
        zscore = (close - close.rolling(20).mean()) / close.rolling(20).std().replace(0, np.nan)
        score += ((zscore < 0).astype(float) * 0.2)

        return score

    def _extract_vbt_metrics(self, pf) -> VBTBacktestMetrics:
        """从vectorbt Portfolio提取指标"""
        try:
            stats = pf.stats()
            total_return = stats.get("Total Return [%]", 0) / 100
            annual_return = stats.get("Annualized Return [%]", 0) / 100
            sharpe = stats.get("Sharpe Ratio", 0)
            max_dd = stats.get("Max Drawdown [%]", 0) / 100
            win_rate = stats.get("Win Rate [%]", 0) / 100
            total_trades = int(stats.get("Total Trades", 0))
        except Exception:
            total_return = annual_return = sharpe = max_dd = win_rate = 0.0
            total_trades = 0

        calmar = annual_return / abs(max_dd) if max_dd != 0 else 0
        volatility = 0.0

        return VBTBacktestMetrics(
            total_return=float(total_return),
            annual_return=float(annual_return),
            sharpe=float(sharpe),
            max_drawdown=float(max_dd),
            calmar=float(calmar),
            win_rate=float(win_rate),
            turnover=0.0,
            volatility=float(volatility),
            total_trades=total_trades,
        )

    # ------------------------------------------------------------------
    # 内置回测 (vectorbt不可用时的降级方案)
    # ------------------------------------------------------------------

    def _run_builtin(
        self,
        data: pd.DataFrame,
        strategy: str,
        params: Dict,
        benchmark_data: Optional[pd.DataFrame],
    ) -> VBTBacktestResult:
        """使用内置逻辑进行回测 (降级方案)"""
        close = data["close"]
        signals = self._generate_signals_builtin(data, strategy, params)

        # 计算策略净值
        position = signals.shift(1).fillna(0)  # T+1执行
        strategy_ret = position * close.pct_change()
        turnover = position.diff().abs().fillna(0)
        strategy_ret_net = strategy_ret - turnover * self.cost
        nav = (1 + strategy_ret_net.fillna(0)).cumprod() * self.initial_capital

        # 计算指标
        metrics = self._calc_builtin_metrics(strategy_ret_net, nav, position)

        # 基准曲线
        benchmark_curve = None
        if benchmark_data is not None and "close" in benchmark_data.columns:
            bm_close = benchmark_data["close"].reindex(data.index, method="ffill")
            benchmark_curve = bm_close / bm_close.iloc[0] * self.initial_capital
        else:
            # 使用买入持有作为基准
            benchmark_curve = close / close.iloc[0] * self.initial_capital

        return VBTBacktestResult(
            strategy=strategy,
            benchmark="买入持有",
            metrics=metrics,
            equity_curve=nav,
            benchmark_curve=benchmark_curve,
            use_vectorbt=False,
        )

    def _generate_signals_builtin(
        self,
        data: pd.DataFrame,
        strategy: str,
        params: Dict,
    ) -> pd.Series:
        """生成内置策略信号"""
        close = data["close"]

        if strategy == VBTStrategyType.MA_CROSS.value:
            short_w = params.get("short_window", 20)
            long_w = params.get("long_window", 60)
            ma_short = close.rolling(short_w).mean()
            ma_long = close.rolling(long_w).mean()
            signals = (ma_short > ma_long).astype(float)

        elif strategy == VBTStrategyType.MOMENTUM.value:
            window = params.get("window", 60)
            mom = close.pct_change(window)
            signals = (mom > 0).astype(float)

        elif strategy == VBTStrategyType.MEAN_REVERSION.value:
            window = params.get("window", 20)
            threshold = params.get("threshold", 1.5)
            ma = close.rolling(window).mean()
            std = close.rolling(window).std()
            zscore = (close - ma) / std.replace(0, np.nan)
            signals = pd.Series(0.0, index=data.index)
            signals[zscore < -threshold] = 1.0
            signals[zscore > threshold] = -1.0

        elif strategy == VBTStrategyType.MULTI_FACTOR.value:
            score = self._compute_multi_factor_score(data)
            threshold = params.get("score_threshold", 0.5)
            signals = (score > threshold).astype(float)

        elif strategy == VBTStrategyType.PAIRS_TRADING.value:
            spread_window = params.get("spread_window", 20)
            spread_threshold = params.get("spread_threshold", 2.0)
            ma = close.rolling(spread_window).mean()
            std = close.rolling(spread_window).std().replace(0, np.nan)
            spread = (close - ma) / std
            signals = pd.Series(0.0, index=data.index)
            signals[spread < -spread_threshold] = 1.0
            signals[spread > spread_threshold] = -1.0

        else:
            signals = pd.Series(1.0, index=data.index)

        return signals

    def _calc_builtin_metrics(
        self,
        strategy_ret_net: pd.Series,
        nav: pd.Series,
        position: pd.Series,
    ) -> VBTBacktestMetrics:
        """计算内置回测指标"""
        daily_ret = strategy_ret_net.dropna()

        if len(daily_ret) < 2 or len(nav) < 2:
            return VBTBacktestMetrics()

        # 总收益
        total_return = nav.iloc[-1] / nav.iloc[0] - 1

        # 年化收益
        n_days = len(nav)
        years = n_days / self.trading_days
        annual_return = (1 + total_return) ** (1 / max(years, 0.01)) - 1 if years > 0 else 0

        # 夏普比率
        if daily_ret.std() > 0:
            sharpe = (daily_ret.mean() - self.risk_free_rate / self.trading_days) / daily_ret.std() * np.sqrt(self.trading_days)
        else:
            sharpe = 0.0

        # 最大回撤
        cummax = nav.cummax()
        drawdown = (nav - cummax) / cummax
        max_drawdown = drawdown.min()

        # 卡玛比率
        calmar = annual_return / abs(max_drawdown) if max_drawdown != 0 else 0

        # 胜率
        win_rate = (daily_ret > 0).sum() / len(daily_ret) if len(daily_ret) > 0 else 0

        # 换手率 (日均)
        turnover = position.diff().abs().mean() if len(position) > 1 else 0

        # 波动率
        volatility = daily_ret.std() * np.sqrt(self.trading_days)

        # 交易次数
        total_trades = int((position.diff().abs() > 0).sum())

        return VBTBacktestMetrics(
            total_return=float(total_return),
            annual_return=float(annual_return),
            sharpe=float(sharpe),
            max_drawdown=float(max_drawdown),
            calmar=float(calmar),
            win_rate=float(win_rate),
            turnover=float(turnover),
            volatility=float(volatility),
            total_trades=total_trades,
        )

    # ------------------------------------------------------------------
    # 批量回测
    # ------------------------------------------------------------------

    def run_multi_strategy(
        self,
        data: pd.DataFrame,
        strategies: Optional[List[str]] = None,
        params: Optional[Dict[str, Dict]] = None,
        benchmark_data: Optional[pd.DataFrame] = None,
    ) -> List[VBTBacktestResult]:
        """
        批量回测多策略

        Args:
            data: 行情数据
            strategies: 策略列表 (默认全部5种)
            params: 各策略参数 {strategy_name: {param: value}}
            benchmark_data: 基准数据

        Returns:
            List[VBTBacktestResult]
        """
        strategies = strategies or [s.value for s in VBTStrategyType]
        params = params or {}

        results = []
        for strat in strategies:
            try:
                strat_params = params.get(strat, {})
                r = self.run_backtest(data, strat, strat_params, benchmark_data)
                results.append(r)
            except Exception as e:
                logger.error(f"策略 {strat} 回测失败: {e}")

        return results

    def compare_strategies(self, results: List[VBTBacktestResult]) -> pd.DataFrame:
        """
        对比多策略回测结果

        Args:
            results: 回测结果列表

        Returns:
            DataFrame: 策略对比表
        """
        rows = []
        for r in results:
            m = r.metrics
            rows.append({
                "策略": r.strategy,
                "引擎": "VectorBT" if r.use_vectorbt else "内置",
                "年化收益": f"{m.annual_return*100:.2f}%",
                "夏普比率": f"{m.sharpe:.2f}",
                "最大回撤": f"{m.max_drawdown*100:.2f}%",
                "卡玛比率": f"{m.calmar:.2f}",
                "胜率": f"{m.win_rate*100:.1f}%",
                "换手率": f"{m.turnover:.4f}",
                "交易次数": m.total_trades,
            })
        return pd.DataFrame(rows)

    # ------------------------------------------------------------------
    # 净值曲线绘图
    # ------------------------------------------------------------------

    def plot_equity_curve(
        self,
        results: List[VBTBacktestResult],
        title: str = "策略净值曲线对比",
        figsize: Tuple[int, int] = (14, 7),
    ) -> Optional[object]:
        """
        绘制净值曲线对比图

        Args:
            results: 回测结果列表
            title: 图表标题
            figsize: 图表尺寸

        Returns:
            matplotlib Figure (若matplotlib可用)
        """
        if not HAS_MPL:
            logger.warning("matplotlib未安装, 无法绘图")
            return None

        fig, ax = plt.subplots(figsize=figsize)
        _apply_dark_theme(ax)

        colors = [BRAND_CYAN, BRAND_GOLD, BRAND_GREEN, BRAND_PURPLE, BRAND_RED]

        for i, r in enumerate(results):
            if r.equity_curve is not None:
                color = colors[i % len(colors)]
                label = r.strategy
                # 归一化净值
                curve = r.equity_curve / r.equity_curve.iloc[0] if len(r.equity_curve) > 0 else r.equity_curve
                ax.plot(curve.values, label=label, color=color, linewidth=1.5, alpha=0.9)

        # 基准曲线
        for r in results:
            if r.benchmark_curve is not None:
                curve = r.benchmark_curve / r.benchmark_curve.iloc[0] if len(r.benchmark_curve) > 0 else r.benchmark_curve
                ax.plot(curve.values, label="基准(买入持有)", color=TEXT_GRAY, linewidth=1, linestyle="--", alpha=0.6)
                break  # 只画一次基准

        ax.set_title(title, fontsize=14, fontweight='bold', pad=15)
        ax.set_xlabel("交易日", fontsize=11)
        ax.set_ylabel("归一化净值", fontsize=11)
        ax.legend(
            loc="upper left",
            fontsize=9,
            facecolor=DARK_BG2,
            edgecolor=TEXT_GRAY,
            labelcolor=TEXT_WHITE,
        )

        fig.tight_layout()
        return fig


# ============================================================================
# 3. 因子IC测试器
# ============================================================================

class FactorICTester:
    """
    因子IC (Information Coefficient) 测试器

    核心功能:
    - compute_ic: 计算Spearman秩相关IC
    - compute_ic_series: 滚动IC序列
    - ic_summary: IC汇总统计
    - plot_ic_heatmap: IC热力图

    使用示例:
        >>> tester = FactorICTester()
        >>> ic = tester.compute_ic(factor_values, forward_returns)
        >>> ic_series = tester.compute_ic_series(factor_values, forward_returns)
        >>> summary = tester.ic_summary(ic_series)
    """

    def __init__(self, method: str = "spearman"):
        """
        初始化IC测试器

        Args:
            method: IC计算方法, 'spearman'(秩相关) 或 'pearson'(线性相关)
        """
        self.method = method

    def compute_ic(
        self,
        factor_values: pd.Series,
        forward_returns: pd.Series,
    ) -> float:
        """
        计算单期IC (Information Coefficient)

        使用Spearman秩相关 (默认) 或Pearson线性相关。

        Args:
            factor_values: 因子值序列 (截面)
            forward_returns: 远期收益率序列 (与因子值对齐)

        Returns:
            float: IC值 (-1 到 1)
        """
        # 对齐数据, 去除NaN
        valid = pd.DataFrame({
            "factor": factor_values,
            "return": forward_returns,
        }).dropna()

        if len(valid) < 5:
            logger.warning(f"有效数据不足 ({len(valid)}), IC不可靠")
            return 0.0

        if HAS_SCIPY:
            if self.method == "spearman":
                ic, _ = scipy_stats.spearmanr(valid["factor"], valid["return"])
            else:
                ic, _ = scipy_stats.pearsonr(valid["factor"], valid["return"])
        else:
            # 降级: 使用pandas内置相关
            if self.method == "spearman":
                ic = valid["factor"].rank().corr(valid["return"].rank())
            else:
                ic = valid["factor"].corr(valid["return"])

        return float(ic) if not np.isnan(ic) else 0.0

    def compute_ic_series(
        self,
        factor_values: pd.DataFrame,
        forward_returns: pd.DataFrame,
        periods: int = 20,
        date_col: str = "date",
    ) -> pd.Series:
        """
        计算滚动IC序列

        Args:
            factor_values: 多期因子值, 需含日期列
            forward_returns: 多期远期收益率, 需含日期列
            periods: 滚动窗口期数
            date_col: 日期列名

        Returns:
            Series: 滚动IC序列, 索引为日期
        """
        # 确保输入为DataFrame
        if isinstance(factor_values, pd.Series):
            factor_values = factor_values.to_frame("factor")
        if isinstance(forward_returns, pd.Series):
            forward_returns = forward_returns.to_frame("return")

        # MultiIndex (date, stock) from stack() — flatten for IC 序列
        if isinstance(factor_values.index, pd.MultiIndex):
            factor_values = factor_values.reset_index()
            if "level_0" in factor_values.columns:
                factor_values = factor_values.rename(columns={"level_0": "date", "level_1": "stock"})
        if isinstance(forward_returns.index, pd.MultiIndex):
            forward_returns = forward_returns.reset_index()
            if "level_0" in forward_returns.columns:
                forward_returns = forward_returns.rename(columns={"level_0": "date", "level_1": "stock"})

        # 获取因子列和收益列 (排除日期列)
        factor_cols = [c for c in factor_values.columns if c != date_col]
        return_cols = [c for c in forward_returns.columns if c != date_col]

        if not factor_cols or not return_cols:
            logger.warning("因子值或远期收益列为空")
            return pd.Series(dtype=float)

        # 按日期分组计算IC
        if date_col in factor_values.columns:
            dates = factor_values[date_col].unique()
        else:
            # 假设索引为日期
            dates = factor_values.index.unique()

        ic_list = []
        for d in dates:
            if date_col in factor_values.columns:
                f_slice = factor_values[factor_values[date_col] == d][factor_cols[0]]
                r_slice = forward_returns[forward_returns[date_col] == d][return_cols[0]] if date_col in forward_returns.columns else forward_returns.loc[f_slice.index, return_cols[0]]
            else:
                f_slice = factor_values.loc[d, factor_cols[0]] if isinstance(factor_values.index, pd.MultiIndex) else factor_values[factor_cols[0]]
                r_slice = forward_returns.loc[d, return_cols[0]] if isinstance(forward_returns.index, pd.MultiIndex) else forward_returns[return_cols[0]]

            ic = self.compute_ic(f_slice, r_slice)
            ic_list.append({"date": d, "ic": ic})

        ic_df = pd.DataFrame(ic_list)
        if len(ic_df) == 0:
            return pd.Series(dtype=float)

        ic_series = ic_df.set_index("date")["ic"]

        # 滚动平均
        if periods > 1 and len(ic_series) >= periods:
            ic_series = ic_series.rolling(periods, min_periods=max(periods // 2, 1)).mean()

        return ic_series

    def ic_summary(self, ic_series: pd.Series) -> Dict[str, float]:
        """
        IC汇总统计

        Args:
            ic_series: IC序列 (来自 compute_ic_series)

        Returns:
            Dict: {
                mean_ic: 均值IC,
                ic_ir: IC信息比率 (均值/标准差),
                ic_positive_ratio: IC>0占比,
                t_stat: t统计量,
                p_value: p值,
                ic_std: IC标准差,
            }
        """
        ic_clean = ic_series.dropna()
        if len(ic_clean) < 3:
            return {
                "mean_ic": 0.0,
                "ic_ir": 0.0,
                "ic_positive_ratio": 0.0,
                "t_stat": 0.0,
                "p_value": 1.0,
                "ic_std": 0.0,
            }

        mean_ic = ic_clean.mean()
        ic_std = ic_clean.std()
        ic_ir = mean_ic / ic_std if ic_std > 0 else 0.0
        ic_positive_ratio = (ic_clean > 0).mean()

        # t检验
        if HAS_SCIPY:
            t_stat, p_value = scipy_stats.ttest_1samp(ic_clean, 0)
        else:
            # 近似t统计量
            n = len(ic_clean)
            t_stat = mean_ic / (ic_std / np.sqrt(n)) if ic_std > 0 and n > 0 else 0.0
            # 近似p值 (正态近似)
            p_value = 2 * (1 - self._norm_cdf(abs(t_stat))) if t_stat != 0 else 1.0

        return {
            "mean_ic": float(mean_ic),
            "ic_ir": float(ic_ir),
            "ic_positive_ratio": float(ic_positive_ratio),
            "t_stat": float(t_stat),
            "p_value": float(p_value),
            "ic_std": float(ic_std),
        }

    @staticmethod
    def _norm_cdf(x: float) -> float:
        """标准正态CDF近似 (无scipy时使用)"""
        # Abramowitz and Stegun 近似
        a1 = 0.254829592
        a2 = -0.284496736
        a3 = 1.421413741
        a4 = -1.453152027
        a5 = 1.061405429
        p = 0.3275911
        sign = 1 if x >= 0 else -1
        x = abs(x) / np.sqrt(2)
        t = 1.0 / (1.0 + p * x)
        y = 1.0 - (((((a5 * t + a4) * t) + a3) * t + a2) * t + a1) * t * np.exp(-x * x)
        return 0.5 * (1.0 + sign * y)

    def plot_ic_heatmap(
        self,
        ic_matrix: pd.DataFrame,
        title: str = "因子IC热力图",
        figsize: Tuple[int, int] = (12, 8),
    ) -> Optional[object]:
        """
        绘制IC热力图

        Args:
            ic_matrix: IC矩阵, 行=因子, 列=时间周期/日期
            title: 图表标题
            figsize: 图表尺寸

        Returns:
            matplotlib Figure (若matplotlib可用)
        """
        if not HAS_MPL:
            logger.warning("matplotlib未安装, 无法绘图")
            return None

        fig, ax = plt.subplots(figsize=figsize)
        _apply_dark_theme(ax)

        # 绘制热力图
        data = ic_matrix.values
        n_rows, n_cols = data.shape

        # 使用imshow绘制
        cmap = plt.cm.RdYlGn  # 红-黄-绿配色
        im = ax.imshow(data, cmap=cmap, aspect='auto', vmin=-0.1, vmax=0.1)

        # 设置坐标轴
        ax.set_xticks(range(n_cols))
        ax.set_yticks(range(n_rows))

        # 列标签
        if n_cols <= 20:
            col_labels = [str(c)[:10] for c in ic_matrix.columns]
            ax.set_xticklabels(col_labels, rotation=45, ha='right', fontsize=8)
        else:
            # 太多列时只显示部分
            step = max(n_cols // 10, 1)
            ax.set_xticks(range(0, n_cols, step))
            ax.set_xticklabels(
                [str(ic_matrix.columns[i])[:10] for i in range(0, n_cols, step)],
                rotation=45, ha='right', fontsize=8,
            )

        # 行标签
        row_labels = [str(r)[:20] for r in ic_matrix.index]
        ax.set_yticklabels(row_labels, fontsize=9)

        # 数值标注 (矩阵不太大时)
        if n_rows * n_cols <= 200:
            for i in range(n_rows):
                for j in range(n_cols):
                    val = data[i, j]
                    if not np.isnan(val):
                        color = TEXT_WHITE if abs(val) > 0.05 else TEXT_GRAY
                        ax.text(j, i, f"{val:.3f}", ha="center", va="center",
                                color=color, fontsize=7)

        # 色条
        cbar = fig.colorbar(im, ax=ax, shrink=0.8)
        cbar.ax.tick_params(colors=TEXT_GRAY, labelsize=8)
        cbar.set_label("IC值", color=TEXT_WHITE, fontsize=10)

        ax.set_title(title, fontsize=14, fontweight='bold', pad=15)
        ax.set_xlabel("时间", fontsize=11)
        ax.set_ylabel("因子", fontsize=11)

        fig.tight_layout()
        return fig

    def plot_ic_series(
        self,
        ic_series: pd.Series,
        title: str = "滚动IC序列",
        figsize: Tuple[int, int] = (14, 5),
    ) -> Optional[object]:
        """
        绘制IC时序图

        Args:
            ic_series: IC序列
            title: 图表标题
            figsize: 图表尺寸

        Returns:
            matplotlib Figure
        """
        if not HAS_MPL:
            return None

        fig, ax = plt.subplots(figsize=figsize)
        _apply_dark_theme(ax)

        ic_clean = ic_series.dropna()
        ax.bar(range(len(ic_clean)), ic_clean.values,
               color=[BRAND_GREEN if v > 0 else BRAND_RED for v in ic_clean.values],
               alpha=0.7, width=0.8)
        ax.axhline(y=0, color=TEXT_GRAY, linewidth=0.5, linestyle='-')
        ax.axhline(y=ic_clean.mean(), color=BRAND_CYAN, linewidth=1, linestyle='--',
                   label=f"均值IC={ic_clean.mean():.4f}")

        ax.set_title(title, fontsize=14, fontweight='bold', pad=15)
        ax.set_xlabel("期数", fontsize=11)
        ax.set_ylabel("IC", fontsize=11)
        ax.legend(
            loc="upper right",
            fontsize=9,
            facecolor=DARK_BG2,
            edgecolor=TEXT_GRAY,
            labelcolor=TEXT_WHITE,
        )

        fig.tight_layout()
        return fig


# ============================================================================
# 4. 另类数据信号验证器
# ============================================================================

class SignalVerifier:
    """
    另类数据信号验证器

    核心功能:
    - verify_signal: 验证信号是否具有预测力
    - cross_validate: 时序交叉验证
    - signal_decay_analysis: 信号衰减分析

    使用示例:
        >>> verifier = SignalVerifier()
        >>> result = verifier.verify_signal(signal_data, price_data)
        >>> cv_result = verifier.cross_validate(signal_data, price_data, n_splits=5)
        >>> decay = verifier.signal_decay_analysis(signal_data, price_data)
    """

    def __init__(self, ic_method: str = "spearman"):
        """
        初始化信号验证器

        Args:
            ic_method: IC计算方法 ('spearman' 或 'pearson')
        """
        self.ic_tester = FactorICTester(method=ic_method)

    def verify_signal(
        self,
        signal_data: pd.DataFrame,
        price_data: pd.DataFrame,
        method: str = "ic",
        forward_period: int = 5,
    ) -> Dict[str, Union[float, Dict]]:
        """
        验证另类数据信号是否具有预测力

        Args:
            signal_data: 信号数据, 需含 date 和 signal 列 (或 stock 列做截面)
            price_data: 价格数据, 需含 date 和 close 列
            method: 验证方法 ('ic' 信息系数 / 'hit_rate' 命中率 / 'both' 两者)
            forward_period: 远期收益天数

        Returns:
            Dict: {
                ic: IC值,
                ic_ir: IC信息比率,
                hit_rate: 命中率 (信号方向与收益方向一致的比例),
                p_value: 显著性p值,
                method: 使用的方法,
                n_samples: 有效样本数,
            }
        """
        # 对齐数据
        merged = self._align_signal_price(signal_data, price_data, forward_period)

        if len(merged) < 10:
            logger.warning(f"有效样本不足 ({len(merged)}), 验证结果不可靠")
            return {
                "ic": 0.0, "ic_ir": 0.0, "hit_rate": 0.0,
                "p_value": 1.0, "method": method, "n_samples": len(merged),
            }

        result = {"method": method, "n_samples": len(merged)}

        # IC验证
        if method in ("ic", "both"):
            ic = self.ic_tester.compute_ic(merged["signal"], merged["forward_return"])
            ic_series = self._compute_rolling_ic(merged, window=20)
            ic_summary = self.ic_tester.ic_summary(ic_series)
            result["ic"] = ic
            result["ic_ir"] = ic_summary["ic_ir"]
            result["p_value"] = ic_summary["p_value"]

        # 命中率验证
        if method in ("hit_rate", "both"):
            hit_rate = self._compute_hit_rate(merged["signal"], merged["forward_return"])
            result["hit_rate"] = hit_rate

            # 如果没有IC结果, 用命中率做显著性检验
            if method == "hit_rate":
                n = len(merged)
                k = int(hit_rate * n)
                if HAS_SCIPY:
                    # 二项检验
                    p_val = scipy_stats.binom_test(k, n, 0.5) if hasattr(scipy_stats, 'binom_test') else \
                            2 * (1 - scipy_stats.binom.cdf(k - 1, n, 0.5))
                else:
                    # 正态近似
                    z = (hit_rate - 0.5) / np.sqrt(0.25 / n) if n > 0 else 0
                    p_val = 2 * (1 - FactorICTester._norm_cdf(abs(z)))
                result["p_value"] = p_val

        # 确保所有键都有值
        result.setdefault("ic", 0.0)
        result.setdefault("ic_ir", 0.0)
        result.setdefault("hit_rate", 0.0)
        result.setdefault("p_value", 1.0)

        return result

    def cross_validate(
        self,
        signal_data: pd.DataFrame,
        price_data: pd.DataFrame,
        n_splits: int = 5,
        forward_period: int = 5,
        method: str = "ic",
    ) -> Dict[str, Union[float, List]]:
        """
        时序交叉验证 (避免未来信息泄露)

        Args:
            signal_data: 信号数据
            price_data: 价格数据
            n_splits: 折数
            forward_period: 远期收益天数
            method: 验证方法

        Returns:
            Dict: {
                mean_ic: 平均IC,
                std_ic: IC标准差,
                ic_ir: IC信息比率,
                mean_hit_rate: 平均命中率,
                fold_results: 各折结果,
                n_splits: 折数,
            }
        """
        merged = self._align_signal_price(signal_data, price_data, forward_period)

        if len(merged) < n_splits * 20:
            logger.warning(f"数据不足以做{n_splits}折交叉验证")
            return {
                "mean_ic": 0.0, "std_ic": 0.0, "ic_ir": 0.0,
                "mean_hit_rate": 0.0, "fold_results": [], "n_splits": n_splits,
            }

        # 时序分割 (不能随机打乱)
        fold_size = len(merged) // n_splits
        fold_results = []

        for i in range(n_splits):
            start = i * fold_size
            end = start + fold_size if i < n_splits - 1 else len(merged)
            fold_data = merged.iloc[start:end]

            if len(fold_data) < 10:
                continue

            ic = self.ic_tester.compute_ic(fold_data["signal"], fold_data["forward_return"])
            hit_rate = self._compute_hit_rate(fold_data["signal"], fold_data["forward_return"])

            fold_results.append({
                "fold": i + 1,
                "ic": ic,
                "hit_rate": hit_rate,
                "n_samples": len(fold_data),
            })

        if not fold_results:
            return {
                "mean_ic": 0.0, "std_ic": 0.0, "ic_ir": 0.0,
                "mean_hit_rate": 0.0, "fold_results": [], "n_splits": n_splits,
            }

        ics = [f["ic"] for f in fold_results]
        hit_rates = [f["hit_rate"] for f in fold_results]
        mean_ic = np.mean(ics)
        std_ic = np.std(ics)
        ic_ir = mean_ic / std_ic if std_ic > 0 else 0.0

        return {
            "mean_ic": float(mean_ic),
            "std_ic": float(std_ic),
            "ic_ir": float(ic_ir),
            "mean_hit_rate": float(np.mean(hit_rates)),
            "fold_results": fold_results,
            "n_splits": n_splits,
        }

    def signal_decay_analysis(
        self,
        signal_data: pd.DataFrame,
        price_data: pd.DataFrame,
        max_lag: int = 20,
    ) -> Dict[str, Union[np.ndarray, List, float]]:
        """
        信号衰减分析 (信号预测力随时间衰减)

        Args:
            signal_data: 信号数据
            price_data: 价格数据
            max_lag: 最大滞后期数

        Returns:
            Dict: {
                decay_curve: 各滞后期IC数组,
                lags: 滞后期列表,
                half_life: 半衰期 (IC降至一半的期数),
                optimal_lag: 最优滞后期,
                ic_at_lag_1: 第1期IC,
            }
        """
        # 准备基础数据
        if "date" not in signal_data.columns or "date" not in price_data.columns:
            logger.warning("信号和价格数据均需含 date 列")
            return {
                "decay_curve": np.array([]),
                "lags": [],
                "half_life": np.nan,
                "optimal_lag": 0,
                "ic_at_lag_1": 0.0,
            }

        # 对齐信号与价格
        merged = pd.merge(signal_data, price_data[["date", "close"]], on="date", how="inner")
        merged = merged.sort_values("date").reset_index(drop=True)

        if len(merged) < max_lag + 10:
            logger.warning(f"数据量不足以分析 {max_lag} 期衰减")
            max_lag = max(len(merged) - 10, 1)

        # 计算各滞后期IC
        decay_curve = []
        lags = list(range(1, max_lag + 1))

        for lag in lags:
            forward_ret = merged["close"].pct_change(lag).shift(-lag)
            valid = pd.DataFrame({
                "signal": merged["signal"],
                "return": forward_ret,
            }).dropna()

            if len(valid) < 10:
                decay_curve.append(0.0)
                continue

            ic = self.ic_tester.compute_ic(valid["signal"], valid["return"])
            decay_curve.append(ic)

        decay_curve = np.array(decay_curve)

        # 计算半衰期
        ic_at_1 = decay_curve[0] if len(decay_curve) > 0 else 0.0
        half_life = np.nan
        if abs(ic_at_1) > 0.01:
            target = ic_at_1 / 2
            for i, ic in enumerate(decay_curve):
                if abs(ic) < abs(target):
                    # 线性插值
                    if i > 0:
                        prev_ic = decay_curve[i - 1]
                        frac = (abs(target) - abs(prev_ic)) / (abs(ic) - abs(prev_ic) + 1e-10)
                        half_life = (i - 1) + frac + 1  # +1 因为lag从1开始
                    else:
                        half_life = 1.0
                    break
            if np.isnan(half_life):
                half_life = float(max_lag)

        # 最优滞后期
        optimal_lag = int(np.argmax(np.abs(decay_curve)) + 1) if len(decay_curve) > 0 else 0

        return {
            "decay_curve": decay_curve,
            "lags": lags,
            "half_life": float(half_life),
            "optimal_lag": optimal_lag,
            "ic_at_lag_1": float(ic_at_1),
        }

    def plot_decay_curve(
        self,
        decay_result: Dict,
        title: str = "信号衰减分析",
        figsize: Tuple[int, int] = (12, 5),
    ) -> Optional[object]:
        """
        绘制信号衰减曲线

        Args:
            decay_result: signal_decay_analysis 的返回值
            title: 图表标题
            figsize: 图表尺寸

        Returns:
            matplotlib Figure
        """
        if not HAS_MPL:
            return None

        curve = decay_result.get("decay_curve", [])
        lags = decay_result.get("lags", [])
        half_life = decay_result.get("half_life", np.nan)

        if len(curve) == 0:
            return None

        fig, ax = plt.subplots(figsize=figsize)
        _apply_dark_theme(ax)

        ax.bar(lags, curve, color=BRAND_CYAN, alpha=0.7, width=0.8)
        ax.axhline(y=0, color=TEXT_GRAY, linewidth=0.5)

        # 半衰期标注
        if not np.isnan(half_life):
            ax.axvline(x=half_life, color=BRAND_GOLD, linewidth=1.5, linestyle='--',
                       label=f"半衰期={half_life:.1f}")

        ax.set_title(title, fontsize=14, fontweight='bold', pad=15)
        ax.set_xlabel("滞后期 (天)", fontsize=11)
        ax.set_ylabel("IC", fontsize=11)
        ax.legend(
            loc="upper right",
            fontsize=9,
            facecolor=DARK_BG2,
            edgecolor=TEXT_GRAY,
            labelcolor=TEXT_WHITE,
        )

        fig.tight_layout()
        return fig

    # ------------------------------------------------------------------
    # 内部辅助方法
    # ------------------------------------------------------------------

    @staticmethod
    def _align_signal_price(
        signal_data: pd.DataFrame,
        price_data: pd.DataFrame,
        forward_period: int = 5,
    ) -> pd.DataFrame:
        """
        对齐信号数据与价格数据, 计算远期收益

        Args:
            signal_data: 信号数据, 需含 date 和 signal 列
            price_data: 价格数据, 需含 date 和 close 列
            forward_period: 远期天数

        Returns:
            DataFrame: [date, signal, close, forward_return]
        """
        # 确保列名正确
        sig = signal_data.copy()
        pri = price_data.copy()

        if "date" in sig.columns:
            sig["date"] = pd.to_datetime(sig["date"])
        if "date" in pri.columns:
            pri["date"] = pd.to_datetime(pri["date"])

        # 确保价格数据有close列
        if "close" not in pri.columns:
            logger.warning("价格数据缺少 close 列, 无法计算远期收益")
            return pd.DataFrame()

        # 合并键
        merge_cols = ["date"]
        if "stock" in sig.columns and "stock" in pri.columns:
            merge_cols.append("stock")

        # 信号数据中如果已有close列, 先移除避免冲突
        sig_cols = [c for c in sig.columns if c != "close"]
        merged = pd.merge(
            sig[sig_cols],
            pri[merge_cols + ["close"]],
            on=merge_cols,
            how="inner",
        )
        merged = merged.sort_values(merge_cols).reset_index(drop=True)

        # 计算远期收益
        if "stock" in merged.columns:
            merged["forward_return"] = merged.groupby("stock")["close"].pct_change(forward_period).shift(-forward_period)
        else:
            merged["forward_return"] = merged["close"].pct_change(forward_period).shift(-forward_period)

        return merged.dropna()

    @staticmethod
    def _compute_hit_rate(signal: pd.Series, forward_return: pd.Series) -> float:
        """
        计算命中率 (信号方向与收益方向一致的比例)

        Args:
            signal: 信号值
            forward_return: 远期收益

        Returns:
            float: 命中率 (0-1)
        """
        valid = pd.DataFrame({"signal": signal, "return": forward_return}).dropna()
        if len(valid) == 0:
            return 0.0

        # 信号方向与收益方向一致
        same_direction = ((valid["signal"] > 0) & (valid["return"] > 0)) | \
                         ((valid["signal"] < 0) & (valid["return"] < 0))
        # 零信号不计入
        non_zero = valid["signal"] != 0
        if non_zero.sum() == 0:
            return 0.5

        hit_rate = same_direction[non_zero].sum() / non_zero.sum()
        return float(hit_rate)

    def _compute_rolling_ic(
        self,
        merged: pd.DataFrame,
        window: int = 20,
    ) -> pd.Series:
        """计算滚动IC (内部使用)"""
        ic_list = []
        for i in range(window, len(merged)):
            slice_data = merged.iloc[i - window:i]
            ic = self.ic_tester.compute_ic(slice_data["signal"], slice_data["forward_return"])
            ic_list.append(ic)

        if not ic_list:
            return pd.Series(dtype=float)

        return pd.Series(ic_list, index=merged.index[window:])
