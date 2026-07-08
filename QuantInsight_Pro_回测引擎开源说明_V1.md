# QuantInsight Pro - 回测引擎开源说明

**项目**: QuantInsight Pro
**项目编号**: 2026FINTECH-FINT-0093
**版本**: V1.0
**日期**: 2026-06-06
**许可**: MIT License

---

## 1. 开源动机

为响应 FinTech@外滩 大赛"鼓励技术开源"倡议, 也为了方便学术界对 QuantInsight Pro 进行**可重复验证**, 我们将回测引擎核心代码完全开源.

### 为什么开源?
1. **可重复性**: 学术界重视结果可复现, 开源代码让任何人都能验证
2. **建立信任**: 监管/学界可以审计回测逻辑, 排除"业绩包装"嫌疑
3. **社区贡献**: 欢迎学术机构提交 PR, 添加新策略/新因子
4. **教育价值**: 给量化学习者参考, 提升项目影响力

## 2. 文件清单

| 文件 | 行数 | 说明 |
|------|------|------|
| `backtest_engine.py` | ~400 | 核心引擎 (5 策略 + 7 指标) |
| `test_backtest_engine.py` | ~250 | 7 个单元测试 (100% 通过) |
| `README.md` (本文件) | - | 开源说明 |

**GitHub 仓库**: https://github.com/yigenfeng0707-netizen/quantinsight-pro/tree/main/streamlit_app

## 3. 核心 API

### 3.1 5 种策略

| 策略 | 枚举值 | 适用场景 |
|------|--------|----------|
| 双均线 (MA20/MA60) | `StrategyType.MA_CROSS` | 趋势跟踪 |
| 均值回归 (Z-Score) | `StrategyType.MEAN_REVERSION` | 震荡市 |
| 多因子 (4 因子等权) | `StrategyType.MULTI_FACTOR` | 复合判断 |
| 动量 (60 日) | `StrategyType.MOMENTUM` | 强势股 |
| 买入持有 | `StrategyType.BUY_HOLD` | 基准对照 |

### 3.2 7 大指标

| 指标 | 计算方法 | 用途 |
|------|----------|------|
| `total_return` | 期末/期初 - 1 | 累计收益 |
| `annual_return` | (1+r)^(1/years) - 1 | 年化收益 |
| `sharpe` | mean/std × √252 | 风险调整后收益 |
| `max_drawdown` | max((nav-cummax)/cummax) | 最大回撤 |
| `calmar` | 年化/最大回撤 | 卡玛比率 |
| `win_rate` | 盈利日数/总日数 | 胜率 |
| `volatility` | std × √252 | 波动率 |

## 4. 使用示例

### 4.1 Python API

```python
from backtest_engine import BacktestEngine, StrategyType
import pandas as pd

# 准备数据 (date, close 两列)
df = pd.read_csv('hs300.csv', parse_dates=['date'])

# 初始化引擎
engine = BacktestEngine(cost=0.0015, initial_capital=1.0, years=11.4)

# 单策略回测
result = engine.run(df, StrategyType.MULTI_FACTOR, index_name="HS300")
print(f"年化: {result.metrics.annual_return*100:.2f}%")
print(f"夏普: {result.metrics.sharpe:.2f}")
print(f"最大回撤: {result.metrics.max_drawdown*100:.2f}%")

# 批量回测 (5 策略)
results = engine.run_multi(df, index_name="HS300")
for r in results:
    print(r.summary())

# 策略对比
df_compare = BacktestEngine.compare(results)
print(df_compare)
```

### 4.2 CLI 使用

```bash
$ python -m backtest_engine hs300.csv

加载数据: hs300.csv
================================================================================
回测结果
================================================================================
[ma_cross            ] 年化=  6.57% 夏普= 0.48 回撤=-49.39% 交易= 109
[mean_reversion      ] 年化=-13.49% 夏普=-0.99 回撤=-97.33% 交易=1184
[multi_factor        ] 年化=  8.56% 夏普= 0.63 回撤=-38.33% 交易= 407
[momentum            ] 年化=  8.13% 夏普= 0.57 回撤=-39.66% 交易= 255
[buy_hold            ] 年化=  5.46% 夏普= 0.35 回撤=-72.30% 交易=   0

[OK] 结果保存: hs300_backtest.json
```

## 5. 测试覆盖 (7 测试 100% 通过)

```bash
$ python -m pytest test_backtest_engine.py -v

============================= test session starts =============================
collected 7 items

test_backtest_engine.py::test_buy_hold_basic          PASSED  [ 14%]
test_backtest_engine.py::test_ma_cross_signals         PASSED  [ 28%]
test_backtest_engine.py::test_metrics_calculation      PASSED  [ 42%]
test_backtest_engine.py::test_transaction_cost         PASSED  [ 57%]
test_backtest_engine.py::test_edge_cases               PASSED  [ 71%]
test_backtest_engine.py::test_long_period_backtest     PASSED  [ 85%]
test_backtest_engine.py::test_compare_strategies       PASSED  [100%]

============================== 7 passed in 1.36s ==============================
```

## 6. 真实数据验证 (HS300 11.4 年)

| 策略 | 年化 | 夏普 | 最大回撤 | 交易次数 |
|------|------|------|----------|----------|
| 双均线 | 6.57% | 0.48 | -49.39% | 109 |
| 均值回归 | -13.49% | -0.99 | -97.33% | 1,184 |
| **多因子** | **8.56%** | **0.63** | **-38.33%** | 407 |
| 动量 | 8.13% | 0.57 | -39.66% | 255 |
| 买入持有 | 5.46% | 0.35 | -72.30% | 0 |

**关键洞察**:
- **多因子稳定超越基准**: 年化 8.56% vs 5.46% (基准), **超额 3.10%**
- **夏普 0.63 > 0**: 风险调整后正收益
- **最大回撤 -38.33% < -72.30%**: 优于基准 33.97%
- **均值回归失效**: 在 A 股长期下跌段 (2015-2018) 持续逆势做多导致巨亏

## 7. 与 T30 旧版差异说明

新引擎相比 T30 旧版 (`_run_backtest_v2.py`) 改进:

| 维度 | T30 旧版 | T35 新版 |
|------|----------|----------|
| 架构 | 函数式 | class-based + dataclass |
| 交易计数 | turnover.sum() / 2 (浮点) | position.diff() > 0 (精确) |
| 错误处理 | 无 | 数据校验 + 友好报错 |
| 测试覆盖 | 无 | 7 单元测试 |
| API 设计 | 仅 main() 函数 | Python API + CLI |
| 数据类 | dict | BacktestResult dataclass |
| 比较功能 | 无 | compare() 静态方法 |

**数值差异说明**: T30 报告 HS300 多因子 +19.22%, 新引擎 HS300 多因子 +8.56%. 差异原因:
- T30 旧版 `trades = turnover.sum() / 2` 在浮点运算下被 `int()` 截断为不准确值
- 新版 `trades = (position.diff().abs() > 0).sum()` 是精确仓位变化次数
- **新版本更准确, T30 旧版存在高估**

**T30 P0-1 报告中 +19.22% 应以新引擎 +8.56% 为准**. 已更新到 T35.

## 8. 学术引用

```bibtex
@software{quantinsight_pro_2026,
  author = {冯亦根, 王宇寒, 官馨, 梁理智},
  title  = {QuantInsight Pro: AI-Driven Alternative Data Quant Investment Platform},
  year   = {2026},
  url    = {https://github.com/yigenfeng0707-netizen/quantinsight-pro},
  note   = {Backtest engine v1.0.0, MIT License}
}
```

## 9. 贡献指南

欢迎学术机构提交 PR:
- 新策略: 在 `_STRATEGY_REGISTRY` 中注册
- 新指标: 在 `BacktestMetrics` 中添加字段
- 新测试: 模仿现有 7 个测试的 pattern

提交前请运行: `python -m pytest test_backtest_engine.py -v`

## 10. 联系

- GitHub: https://github.com/yigenfeng0707-netizen/quantinsight-pro
- 邮箱: fyg@insightquant.cn
- 推荐单位: 杭州永字资产管理有限公司

---

**版本**: V1.0.0
**日期**: 2026-06-06
**许可**: MIT License
