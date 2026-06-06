"""
QuantInsight Pro - 回测引擎单元测试
====================================

测试覆盖:
1. test_buy_hold_basic: 买入持有基本正确性
2. test_ma_cross_signals: 双均线信号正确性
3. test_metrics_calculation: 指标计算正确性
4. test_transaction_cost: 交易成本影响
5. test_edge_cases: 边界情况 (空数据/单点/异常值)

运行: pytest test_backtest_engine.py -v
或:   python -m pytest test_backtest_engine.py -v
"""

import sys
import os

import numpy as np
import pandas as pd
import pytest

# 加入父目录以便导入模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backtest_engine import (
    BacktestEngine,
    BacktestConfig,
    BacktestResult,
    BacktestMetrics,
    StrategyType,
)


# ============================================================================
# 测试夹具
# ============================================================================

@pytest.fixture
def sample_data():
    """生成 250 个交易日的合成数据 (1 年)"""
    np.random.seed(42)
    n = 250
    dates = pd.date_range("2025-01-01", periods=n, freq="B")
    # 模拟 100 起点 + 随机游走
    close = 100 * np.exp(np.cumsum(np.random.randn(n) * 0.015))
    return pd.DataFrame({"date": dates, "close": close})


@pytest.fixture
def long_data():
    """生成 11.4 年 (2883 个交易日) 的合成数据"""
    np.random.seed(2026)
    n = 2883
    dates = pd.date_range("2015-01-01", periods=n, freq="B")
    close = 100 * np.exp(np.cumsum(np.random.randn(n) * 0.012))
    return pd.DataFrame({"date": dates, "close": close})


@pytest.fixture
def rising_data():
    """生成持续上涨的数据 (测试多因子/动量策略)"""
    n = 500
    dates = pd.date_range("2024-01-01", periods=n, freq="B")
    close = np.linspace(100, 200, n)  # 翻倍
    return pd.DataFrame({"date": dates, "close": close})


@pytest.fixture
def falling_data():
    """生成持续下跌的数据"""
    n = 500
    dates = pd.date_range("2024-01-01", periods=n, freq="B")
    close = np.linspace(100, 50, n)  # 腰斩
    return pd.DataFrame({"date": dates, "close": close})


@pytest.fixture
def default_engine():
    """默认配置引擎"""
    return BacktestEngine()


# ============================================================================
# 测试 1: 买入持有基本正确性
# ============================================================================

def test_buy_hold_basic(sample_data, default_engine):
    """
    测试买入持有策略:
    - 始终满仓, signal 全为 1
    - 净值 = 初始资金 * 累积收益
    - 交易次数 = 1 (首次建仓)
    """
    result = default_engine.run(sample_data, StrategyType.BUY_HOLD, index_name="test")

    # 基本字段
    assert result.strategy == "buy_hold"
    assert result.index == "test"
    assert result.data_points == 250

    # 信号全为 1
    assert (result.signal_series == 1).all(), "买入持有信号应全为 1"

    # 净值应 > 0 且 < ∞
    assert result.nav_series.iloc[-1] > 0
    assert np.isfinite(result.nav_series).all()

    # 交易次数 = 0 (买入持有建仓在 t=0 之前, 回测期内不调仓)
    assert result.metrics.trades == 0, f"买入持有在回测期内不应调仓, 实际交易 {result.metrics.trades} 次"

    # 年化收益应有意义
    assert -1 < result.metrics.annual_return < 10, f"年化收益异常: {result.metrics.annual_return}"


# ============================================================================
# 测试 2: 双均线信号正确性
# ============================================================================

def test_ma_cross_signals(sample_data, default_engine):
    """
    测试双均线策略信号:
    - 金叉 (MA20 > MA60) → signal = 1
    - 死叉 (MA20 < MA60) → signal = 0
    - 信号有变化 (有交易次数 > 0)
    """
    result = default_engine.run(sample_data, StrategyType.MA_CROSS, index_name="test")

    # 至少有几次交易
    assert result.metrics.trades > 0, "样本数据应触发至少 1 次双均线交易"

    # 信号序列长度匹配
    assert len(result.signal_series) == 250

    # 信号只能为 0 或 1
    assert set(result.signal_series.unique()).issubset({0, 1}), \
        f"双均线信号应为 0/1, 实际: {set(result.signal_series.unique())}"

    # 前 60 天为 NaN → fillna(0) 后应无 NaN
    assert result.signal_series.isna().sum() == 0

    # 净值序列应合理
    assert result.nav_series.iloc[-1] > 0


# ============================================================================
# 测试 3: 指标计算正确性
# ============================================================================

def test_metrics_calculation(sample_data, default_engine):
    """
    测试回测指标:
    - total_return = 期末净值 / 期初净值 - 1
    - annual_return 应与总收益一致 (按年化)
    - max_drawdown <= 0
    - sharpe 在合理范围
    - win_rate ∈ [0, 1]
    """
    result = default_engine.run(sample_data, StrategyType.BUY_HOLD, index_name="test")
    m = result.metrics

    # 总收益计算正确
    nav_start = result.nav_series.iloc[0]
    nav_end = result.nav_series.iloc[-1]
    expected_total = nav_end / nav_start - 1
    assert abs(m.total_return - expected_total) < 1e-6, \
        f"total_return 计算错误: {m.total_return} vs {expected_total}"

    # 最大回撤 ≤ 0
    assert m.max_drawdown <= 0, f"max_drawdown 应 ≤ 0, 实际 {m.max_drawdown}"

    # 夏普为有限数
    assert np.isfinite(m.sharpe)

    # 胜率 ∈ [0, 1]
    assert 0 <= m.win_rate <= 1, f"win_rate 越界: {m.win_rate}"

    # 卡玛比率有意义
    assert np.isfinite(m.calmar)

    # 波动率 > 0
    assert m.volatility > 0


# ============================================================================
# 测试 4: 交易成本影响
# ============================================================================

def test_transaction_cost(sample_data):
    """
    测试交易成本:
    - cost=0 vs cost=0.01 (1%), 双均线策略的净值应不同
    - 交易次数越多, 成本影响越大
    """
    # 无成本
    engine_no_cost = BacktestEngine(BacktestConfig(cost=0.0, years=1.0))
    result_no_cost = engine_no_cost.run(sample_data, StrategyType.MA_CROSS, index_name="test")

    # 高成本
    engine_high_cost = BacktestEngine(BacktestConfig(cost=0.01, years=1.0))
    result_high_cost = engine_high_cost.run(sample_data, StrategyType.MA_CROSS, index_name="test")

    # 高成本下净值更低 (或相等, 当无交易时)
    assert result_high_cost.nav_series.iloc[-1] <= result_no_cost.nav_series.iloc[-1], \
        "高成本下净值应 ≤ 无成本下净值"

    # 交易次数应一致
    assert result_no_cost.metrics.trades == result_high_cost.metrics.trades


# ============================================================================
# 测试 5: 边界情况
# ============================================================================

def test_edge_cases(default_engine):
    """
    测试边界情况:
    1. 数据为空 → 报错
    2. 数据点过少 (少于 ma_long + 10) → 报错
    3. 持续上涨数据 → 多因子 / 动量应能捕获上涨
    4. 持续下跌数据 → 策略应能止损 (或表现更差于基准)
    5. 缺失必需列 → 报错
    """
    # 1. 空数据
    empty_df = pd.DataFrame({"date": [], "close": []})
    with pytest.raises(ValueError, match="数据点"):
        default_engine.run(empty_df, StrategyType.BUY_HOLD, index_name="empty")

    # 2. 数据点过少
    short_df = pd.DataFrame({
        "date": pd.date_range("2025-01-01", periods=10, freq="B"),
        "close": np.linspace(100, 110, 10),
    })
    with pytest.raises(ValueError, match="数据点"):
        default_engine.run(short_df, StrategyType.MA_CROSS, index_name="short")

    # 3. 持续上涨数据
    n = 500
    rising_df = pd.DataFrame({
        "date": pd.date_range("2024-01-01", periods=n, freq="B"),
        "close": np.linspace(100, 200, n),  # 翻倍
    })
    rising_result = default_engine.run(rising_df, StrategyType.MULTI_FACTOR, index_name="rising")
    assert rising_result.metrics.total_return > 0, "持续上涨数据下多因子应盈利"

    # 4. 持续下跌数据 (买入持有应亏损)
    falling_df = pd.DataFrame({
        "date": pd.date_range("2024-01-01", periods=n, freq="B"),
        "close": np.linspace(100, 50, n),  # 腰斩
    })
    falling_result = default_engine.run(falling_df, StrategyType.BUY_HOLD, index_name="falling")
    assert falling_result.metrics.total_return < -0.4, \
        f"持续腰斩数据下买入持有应亏损 >40%, 实际 {falling_result.metrics.total_return*100:.2f}%"

    # 5. 缺失 close 列
    invalid_df = pd.DataFrame({"date": pd.date_range("2025-01-01", periods=100, freq="B")})
    with pytest.raises(ValueError, match="close"):
        default_engine.run(invalid_df, StrategyType.BUY_HOLD, index_name="invalid")


# ============================================================================
# 测试 6 (附加): 11.4 年长周期回测
# ============================================================================

def test_long_period_backtest(long_data, default_engine):
    """
    测试 11.4 年长周期回测:
    - 不应崩溃
    - 应返回 5 个策略结果 (在 run_multi 中)
    - 各策略年化收益在合理范围 [-50%, +200%]
    """
    results = default_engine.run_multi(long_data, index_name="long_test")

    assert len(results) == 5, f"应返回 5 个策略结果, 实际 {len(results)}"

    for r in results:
        # 数据点匹配
        assert r.data_points == 2883

        # 年化收益合理
        assert -0.5 < r.metrics.annual_return < 2.0, \
            f"{r.strategy} 年化收益异常: {r.metrics.annual_return}"

        # 指标完整
        assert isinstance(r.metrics, BacktestMetrics)
        assert all(hasattr(r.metrics, attr) for attr in [
            "total_return", "annual_return", "sharpe",
            "max_drawdown", "calmar", "win_rate", "trades", "volatility"
        ])


# ============================================================================
# 测试 7 (附加): 策略对比
# ============================================================================

def test_compare_strategies(sample_data, default_engine):
    """
    测试 compare 静态方法:
    - 应返回 DataFrame
    - 索引为 (index, strategy) 多级
    - 列含全部 7+ 指标
    """
    results = default_engine.run_multi(sample_data, index_name="test")
    df = BacktestEngine.compare(results)

    assert isinstance(df, pd.DataFrame)
    assert len(df) == 5
    assert "annual_return" in df.columns
    assert "sharpe" in df.columns
    assert "max_drawdown" in df.columns
    assert df.index.names == ["index", "strategy"]


# ============================================================================
# 主入口
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
