"""
QuantInsight Pro - 真实回测引擎
基于 akshare 公开 A 股数据
回测区间：2020-01-01 ~ 2026-06-05（约 5.4 年）
"""

import pandas as pd
import numpy as np
from datetime import datetime
import json
import os

# ============== 1. 数据加载 ==============
print('=== 加载数据 ===')
hs300 = pd.read_csv('D:/shFintech/_data_hs300.csv', parse_dates=['date'])
zz500 = pd.read_csv('D:/shFintech/_data_zz500.csv', parse_dates=['date'])
cyb = pd.read_csv('D:/shFintech/_data_cyb.csv', parse_dates=['date'])

# 筛选回测区间
START = '2020-01-01'
END = '2026-06-05'

for df, name in [(hs300, 'HS300'), (zz500, 'ZZ500'), (cyb, 'CYB')]:
    df.sort_values('date', inplace=True)
    df.reset_index(drop=True, inplace=True)
    print(f'{name}: {df.shape[0]} days, {df["date"].min().date()} ~ {df["date"].max().date()}')

# ============== 2. 工具函数 ==============

def compute_returns(prices):
    return prices.pct_change().fillna(0)

def compute_metrics(nav, name='Strategy', bench_nav=None):
    """计算回测核心指标"""
    daily_ret = nav.pct_change().fillna(0)
    years = (nav.index[-1] - nav.index[0]).days / 365.25

    # 总收益
    total_ret = (nav.iloc[-1] / nav.iloc[0]) - 1

    # 年化收益
    annual_ret = (1 + total_ret) ** (1/years) - 1

    # 年化波动率
    annual_vol = daily_ret.std() * np.sqrt(252)

    # 夏普比率（无风险利率 2.5%）
    rf = 0.025
    sharpe = (annual_ret - rf) / annual_vol if annual_vol > 0 else 0

    # 最大回撤
    cummax = nav.cummax()
    drawdown = (nav - cummax) / cummax
    max_dd = drawdown.min()

    # Calmar 比率
    calmar = annual_ret / abs(max_dd) if max_dd != 0 else 0

    # 胜率
    win_rate = (daily_ret > 0).sum() / (daily_ret != 0).sum()

    # 信息比率（vs 基准）
    info_ratio = None
    alpha = None
    beta = None
    if bench_nav is not None:
        bench_ret = bench_nav.pct_change().fillna(0)
        excess_ret = daily_ret - bench_ret
        info_ratio = excess_ret.mean() / excess_ret.std() * np.sqrt(252) if excess_ret.std() > 0 else 0
        # Beta
        cov = np.cov(daily_ret, bench_ret)
        beta = cov[0,1] / cov[1,1] if cov[1,1] != 0 else 0
        # Alpha (Jensen)
        alpha = annual_ret - (rf + beta * (annual_ret - rf))  # 简化

    return {
        'name': name,
        'total_return': total_ret,
        'annual_return': annual_ret,
        'annual_vol': annual_vol,
        'sharpe': sharpe,
        'max_drawdown': max_dd,
        'calmar': calmar,
        'win_rate': win_rate,
        'information_ratio': info_ratio,
        'alpha': alpha,
        'beta': beta,
    }

# ============== 3. 策略实现 ==============

def strategy_dual_ma(df, fast=20, slow=60, cost=0.0015):
    """双均线动量策略"""
    df = df.copy()
    df['ma_fast'] = df['close'].rolling(fast).mean()
    df['ma_slow'] = df['close'].rolling(slow).mean()
    df['signal'] = (df['ma_fast'] > df['ma_slow']).astype(int)
    df['signal_shift'] = df['signal'].shift(1).fillna(0)

    # 计算收益
    df['ret'] = df['close'].pct_change().fillna(0)
    df['strat_ret'] = df['signal_shift'] * df['ret']
    # 扣除交易成本（换手）
    df['turnover'] = df['signal'].diff().abs().fillna(0)
    df['strat_ret'] = df['strat_ret'] - df['turnover'] * cost
    df['nav'] = (1 + df['strat_ret']).cumprod()

    return df

def strategy_mean_reversion(df, window=20, std=2.0, cost=0.0015):
    """布林带均值回归策略"""
    df = df.copy()
    df['ma'] = df['close'].rolling(window).mean()
    df['std'] = df['close'].rolling(window).std()
    df['upper'] = df['ma'] + std * df['std']
    df['lower'] = df['ma'] - std * df['std']

    # 价格触及下轨买入，触及上轨卖出
    df['signal'] = 0
    df.loc[df['close'] < df['lower'], 'signal'] = 1  # 超卖买入
    df.loc[df['close'] > df['upper'], 'signal'] = 0  # 超买卖出
    df['signal'] = df['signal'].ffill().fillna(0)

    df['signal_shift'] = df['signal'].shift(1).fillna(0)
    df['ret'] = df['close'].pct_change().fillna(0)
    df['strat_ret'] = df['signal_shift'] * df['ret']
    df['turnover'] = df['signal'].diff().abs().fillna(0)
    df['strat_ret'] = df['strat_ret'] - df['turnover'] * cost
    df['nav'] = (1 + df['strat_ret']).cumprod()

    return df

def strategy_multi_factor(df, cost=0.0015):
    """多因子策略：动量 + 均值回归 + 波动率过滤"""
    df = df.copy()
    # 因子1: 20日动量
    df['mom'] = df['close'].pct_change(20)
    # 因子2: 5日均值回归信号
    df['mr'] = -(df['close'] / df['close'].rolling(5).mean() - 1)
    # 因子3: 20日波动率（反向）
    df['vol'] = df['close'].pct_change().rolling(20).std()

    # 因子合成
    df['mom_rank'] = df['mom'].rolling(60).rank(pct=True)
    df['mr_rank'] = df['mr'].rolling(60).rank(pct=True)
    df['combined'] = (df['mom_rank'] + df['mr_rank']) / 2

    # 持仓：综合得分前 30%
    df['threshold'] = df['combined'].rolling(60).quantile(0.7)
    df['signal'] = (df['combined'] > df['threshold']).astype(int)
    df['signal_shift'] = df['signal'].shift(1).fillna(0)

    df['ret'] = df['close'].pct_change().fillna(0)
    df['strat_ret'] = df['signal_shift'] * df['ret']
    df['turnover'] = df['signal'].diff().abs().fillna(0)
    df['strat_ret'] = df['strat_ret'] - df['turnover'] * cost
    df['nav'] = (1 + df['strat_ret']).cumprod()

    return df

# ============== 4. 回测执行 ==============

print('\n=== 执行回测 ===')
results = {}

# 沪深300
hs300_sub = hs300[(hs300['date'] >= START) & (hs300['date'] <= END)].copy()
hs300_sub.set_index('date', inplace=True)
hs300_sub['nav'] = hs300_sub['close'] / hs300_sub['close'].iloc[0]

# 策略1: 双均线
df_ma = strategy_dual_ma(hs300_sub.reset_index())
df_ma.set_index('date', inplace=True)
results['HS300_DualMA'] = compute_metrics(df_ma['nav'], 'HS300 双均线(20/60)', hs300_sub['nav'])

# 策略2: 均值回归
df_mr = strategy_mean_reversion(hs300_sub.reset_index())
df_mr.set_index('date', inplace=True)
results['HS300_MeanRev'] = compute_metrics(df_mr['nav'], 'HS300 均值回归(20,2σ)', hs300_sub['nav'])

# 策略3: 多因子
df_mf = strategy_multi_factor(hs300_sub.reset_index())
df_mf.set_index('date', inplace=True)
results['HS300_MultiFactor'] = compute_metrics(df_mf['nav'], 'HS300 多因子', hs300_sub['nav'])

# 基准
results['HS300_BuyHold'] = compute_metrics(hs300_sub['nav'], 'HS300 买入持有', None)

# 中证500
zz500_sub = zz500[(zz500['date'] >= START) & (zz500['date'] <= END)].copy()
zz500_sub.set_index('date', inplace=True)
zz500_sub['nav'] = zz500_sub['close'] / zz500_sub['close'].iloc[0]

df_ma_zz = strategy_dual_ma(zz500_sub.reset_index())
df_ma_zz.set_index('date', inplace=True)
results['ZZ500_DualMA'] = compute_metrics(df_ma_zz['nav'], 'ZZ500 双均线(20/60)', zz500_sub['nav'])

df_mf_zz = strategy_multi_factor(zz500_sub.reset_index())
df_mf_zz.set_index('date', inplace=True)
results['ZZ500_MultiFactor'] = compute_metrics(df_mf_zz['nav'], 'ZZ500 多因子', zz500_sub['nav'])

# 创业板指
cyb_sub = cyb[(cyb['date'] >= START) & (cyb['date'] <= END)].copy()
cyb_sub.set_index('date', inplace=True)
cyb_sub['nav'] = cyb_sub['close'] / cyb_sub['close'].iloc[0]

df_ma_cyb = strategy_dual_ma(cyb_sub.reset_index())
df_ma_cyb.set_index('date', inplace=True)
results['CYB_DualMA'] = compute_metrics(df_ma_cyb['nav'], 'CYB 双均线(20/60)', cyb_sub['nav'])

df_mf_cyb = strategy_multi_factor(cyb_sub.reset_index())
df_mf_cyb.set_index('date', inplace=True)
results['CYB_MultiFactor'] = compute_metrics(df_mf_cyb['nav'], 'CYB 多因子', cyb_sub['nav'])

# ============== 5. 输出报告 ==============
print('\n=== 回测结果汇总 ===')
print(f'{"策略":<35} {"年化收益":>10} {"夏普":>8} {"最大回撤":>10} {"胜率":>8} {"Calmar":>8}')
print('-' * 90)
for key, m in results.items():
    print(f'{m["name"]:<35} {m["annual_return"]*100:>9.2f}% {m["sharpe"]:>8.2f} {m["max_drawdown"]*100:>9.2f}% {m["win_rate"]*100:>7.1f}% {m["calmar"]:>8.2f}')

# 保存结果
import json
results_clean = {}
for k, v in results.items():
    results_clean[k] = {kk: (float(vv) if isinstance(vv, (np.floating, float)) else vv) for kk, vv in v.items()}

with open('D:/shFintech/_backtest_results.json', 'w', encoding='utf-8') as f:
    json.dump(results_clean, f, indent=2, ensure_ascii=False)
print('\n结果已保存: D:/shFintech/_backtest_results.json')

# 保存 NAV 数据用于画图
nav_data = {
    'HS300_Benchmark': hs300_sub['nav'].to_dict(),
    'HS300_DualMA': df_ma['nav'].to_dict(),
    'HS300_MeanRev': df_mr['nav'].to_dict(),
    'HS300_MultiFactor': df_mf['nav'].to_dict(),
    'ZZ500_Benchmark': zz500_sub['nav'].to_dict(),
    'ZZ500_DualMA': df_ma_zz['nav'].to_dict(),
    'ZZ500_MultiFactor': df_mf_zz['nav'].to_dict(),
    'CYB_Benchmark': cyb_sub['nav'].to_dict(),
    'CYB_DualMA': df_ma_cyb['nav'].to_dict(),
    'CYB_MultiFactor': df_mf_cyb['nav'].to_dict(),
}
# 转换 datetime 为 str
nav_data_clean = {}
for k, v in nav_data.items():
    nav_data_clean[k] = {str(d): float(val) for d, val in v.items()}

with open('D:/shFintech/_backtest_nav.json', 'w', encoding='utf-8') as f:
    json.dump(nav_data_clean, f, indent=2, ensure_ascii=False)
print('NAV 数据已保存: D:/shFintech/_backtest_nav.json')
