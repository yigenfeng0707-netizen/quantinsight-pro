#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
QuantInsight Pro - 11.4 年回测 (2015-2026)
Phase 1 A1: 5 策略 + 3 指数 全周期回测
"""

import os
import json
import pandas as pd
import numpy as np
from datetime import datetime

OUT_DIR = r"D:\shFintech"
PERIOD = "2015-01-01 ~ 2026-06-05"
YEARS = 11.4

# 策略参数
MA_SHORT = 20
MA_LONG = 60
COST = 0.0015  # 0.15% 双边
INITIAL_CAPITAL = 1.0

# 3 标的 + 5 策略 (回测 11.4 年)
INDICES = ["hs300", "zz500", "cyb"]
STRATEGIES = ["ma_cross", "mean_reversion", "multi_factor", "momentum", "buy_hold"]


def ma_cross_strategy(df, short=MA_SHORT, long=MA_LONG, cost=COST):
    """双均线 MA20/MA60"""
    df = df.copy()
    df['ma_short'] = df['close'].rolling(short).mean()
    df['ma_long'] = df['close'].rolling(long).mean()
    df['signal'] = 0
    df.loc[df['ma_short'] > df['ma_long'], 'signal'] = 1
    df['signal'] = df['signal'].shift(1).fillna(0)
    df['position'] = df['signal']
    df['strategy_ret'] = df['position'] * df['close'].pct_change()
    df['turnover'] = df['position'].diff().abs()
    df['strategy_ret_net'] = df['strategy_ret'] - df['turnover'] * cost
    df['nav'] = (1 + df['strategy_ret_net']).cumprod() * INITIAL_CAPITAL
    return df


def mean_reversion_strategy(df, window=20, threshold=1.5, cost=COST):
    """均值回归: z-score > threshold 卖出, < -threshold 买入"""
    df = df.copy()
    df['ma'] = df['close'].rolling(window).mean()
    df['std'] = df['close'].rolling(window).std()
    df['zscore'] = (df['close'] - df['ma']) / df['std']
    df['signal'] = 0
    df.loc[df['zscore'] < -threshold, 'signal'] = 1
    df.loc[df['zscore'] > threshold, 'signal'] = -1
    df.loc[df['zscore'].abs() < 0.5, 'signal'] = 0
    df['signal'] = df['signal'].shift(1).fillna(0)
    df['position'] = df['signal']
    df['strategy_ret'] = df['position'] * df['close'].pct_change()
    df['turnover'] = df['position'].diff().abs()
    df['strategy_ret_net'] = df['strategy_ret'] - df['turnover'] * cost
    df['nav'] = (1 + df['strategy_ret_net']).cumprod() * INITIAL_CAPITAL
    return df


def multi_factor_strategy(df, cost=COST):
    """多因子: MA20 趋势 + 动量 + 均值"""
    df = df.copy()
    df['ma20'] = df['close'].rolling(20).mean()
    df['ma60'] = df['close'].rolling(60).mean()
    df['momentum'] = df['close'].pct_change(20)
    df['zscore'] = (df['close'] - df['close'].rolling(20).mean()) / df['close'].rolling(20).std()

    df['score'] = 0.0
    df.loc[df['close'] > df['ma20'], 'score'] += 0.3
    df.loc[df['close'] > df['ma60'], 'score'] += 0.3
    df.loc[df['momentum'] > 0, 'score'] += 0.2
    df.loc[df['zscore'] < 0, 'score'] += 0.2
    df['signal'] = (df['score'] > 0.5).astype(int).shift(1).fillna(0)
    df['position'] = df['signal']
    df['strategy_ret'] = df['position'] * df['close'].pct_change()
    df['turnover'] = df['position'].diff().abs()
    df['strategy_ret_net'] = df['strategy_ret'] - df['turnover'] * cost
    df['nav'] = (1 + df['strategy_ret_net']).cumprod() * INITIAL_CAPITAL
    return df


def momentum_strategy(df, window=60, cost=COST):
    """动量策略: 60 日动量 > 0 做多"""
    df = df.copy()
    df['momentum'] = df['close'].pct_change(window)
    df['signal'] = (df['momentum'] > 0).astype(int).shift(1).fillna(0)
    df['position'] = df['signal']
    df['strategy_ret'] = df['position'] * df['close'].pct_change()
    df['turnover'] = df['position'].diff().abs()
    df['strategy_ret_net'] = df['strategy_ret'] - df['turnover'] * cost
    df['nav'] = (1 + df['strategy_ret_net']).cumprod() * INITIAL_CAPITAL
    return df


def buy_hold_strategy(df, cost=COST):
    """买入持有 (基准)"""
    df = df.copy()
    df['position'] = 1
    df['strategy_ret'] = df['close'].pct_change()
    df['turnover'] = 0
    df.loc[df.index[0], 'turnover'] = 1  # 首次建仓
    df['strategy_ret_net'] = df['strategy_ret'] - df['turnover'] * cost
    df['nav'] = (1 + df['strategy_ret_net']).cumprod() * INITIAL_CAPITAL
    return df


def calc_metrics(df):
    """计算回测指标"""
    nav = df['nav']
    total_return = nav.iloc[-1] - 1
    annual_return = (nav.iloc[-1]) ** (1/YEARS) - 1
    daily_ret = df['strategy_ret_net'].dropna()
    sharpe = daily_ret.mean() / daily_ret.std() * np.sqrt(252) if daily_ret.std() > 0 else 0
    cummax = nav.cummax()
    drawdown = (nav - cummax) / cummax
    max_dd = drawdown.min()
    calmar = annual_return / abs(max_dd) if max_dd != 0 else 0
    win_rate = (daily_ret > 0).sum() / len(daily_ret) if len(daily_ret) > 0 else 0
    trades = df['turnover'].sum() / 2
    return {
        "total_return": total_return,
        "annual_return": annual_return,
        "sharpe": sharpe,
        "max_drawdown": max_dd,
        "calmar": calmar,
        "win_rate": win_rate,
        "trades": trades,
    }


def main():
    print("="*60)
    print(f"QuantInsight Pro - 11.4 年回测 ({PERIOD})")
    print("="*60)

    results = {}
    strategy_funcs = {
        "ma_cross": ma_cross_strategy,
        "mean_reversion": mean_reversion_strategy,
        "multi_factor": multi_factor_strategy,
        "momentum": momentum_strategy,
        "buy_hold": buy_hold_strategy,
    }

    for index in INDICES:
        print(f"\n--- {index.upper()} ---")
        csv_file = f"{OUT_DIR}\\_data_{index}_full.csv"
        if not os.path.exists(csv_file):
            print(f"  [SKIP] 文件不存在: {csv_file}")
            continue

        df = pd.read_csv(csv_file)
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date').reset_index(drop=True)
        print(f"  数据: {len(df)} 点 ({df['date'].iloc[0].date()} ~ {df['date'].iloc[-1].date()})")

        results[index] = {}
        for strat_name, strat_func in strategy_funcs.items():
            df_strat = strat_func(df)
            metrics = calc_metrics(df_strat)
            results[index][strat_name] = metrics
            print(f"  {strat_name:20s} 年化={metrics['annual_return']*100:6.2f}% "
                  f"夏普={metrics['sharpe']:5.2f} "
                  f"回撤={metrics['max_drawdown']*100:6.2f}% "
                  f"交易={metrics['trades']:4.0f}")

    # 保存结果
    out_file = f"{OUT_DIR}\\_backtest_results_v2.json"
    with open(out_file, 'w', encoding='utf-8') as f:
        json.dump({
            "period": PERIOD,
            "years": YEARS,
            "strategies": STRATEGIES,
            "indices": INDICES,
            "results": results,
        }, f, indent=2, ensure_ascii=False, default=str)
    print(f"\n[OK] 结果保存: {out_file}")

    # 关键总结
    print("\n" + "="*60)
    print("11.4 年回测关键结论")
    print("="*60)
    for index in INDICES:
        if index in results:
            bh = results[index].get("buy_hold", {})
            mc = results[index].get("ma_cross", {})
            mf = results[index].get("multi_factor", {})
            mr = results[index].get("mean_reversion", {})
            mom = results[index].get("momentum", {})
            print(f"\n{index.upper()}:")
            print(f"  买入持有: 年化={bh.get('annual_return', 0)*100:6.2f}%, 夏普={bh.get('sharpe', 0):5.2f}")
            print(f"  双均线:   年化={mc.get('annual_return', 0)*100:6.2f}%, 夏普={mc.get('sharpe', 0):5.2f}")
            print(f"  多因子:   年化={mf.get('annual_return', 0)*100:6.2f}%, 夏普={mf.get('sharpe', 0):5.2f}")
            print(f"  均值回归: 年化={mr.get('annual_return', 0)*100:6.2f}%, 夏普={mr.get('sharpe', 0):5.2f}")
            print(f"  动量:     年化={mom.get('annual_return', 0)*100:6.2f}%, 夏普={mom.get('sharpe', 0):5.2f}")


if __name__ == "__main__":
    main()
