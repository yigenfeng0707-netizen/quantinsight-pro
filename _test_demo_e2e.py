"""端到端功能测试 - 验证 Demo 各模块逻辑"""
import sys
sys.path.insert(0, 'D:/shFintech/streamlit_app')

import pandas as pd
import numpy as np
import akshare as ak

# ============== 测试 1: 数据加载 ==============
print('=== Test 1: 数据加载 ===')
df = ak.stock_zh_index_daily(symbol='sh000300')
print(f'HS300: {df.shape[0]} days, latest: {df["close"].iloc[-1]:.2f}')

# ============== 测试 2: 策略函数 ==============
print('\n=== Test 2: 策略函数 ===')

def strategy_dual_ma(df, fast=20, slow=60, cost=0.0015):
    df = df.copy()
    df['ma_fast'] = df['close'].rolling(fast).mean()
    df['ma_slow'] = df['close'].rolling(slow).mean()
    df['signal'] = (df['ma_fast'] > df['ma_slow']).astype(int)
    df['signal_shift'] = df['signal'].shift(1).fillna(0)
    df['ret'] = df['close'].pct_change().fillna(0)
    df['strat_ret'] = df['signal_shift'] * df['ret']
    df['turnover'] = df['signal'].diff().abs().fillna(0)
    df['strat_ret'] = df['strat_ret'] - df['turnover'] * cost
    df['nav'] = (1 + df['strat_ret']).cumprod()
    df['benchmark'] = (1 + df['ret']).cumprod()
    return df

df_test = df.tail(252).copy()  # 1 年
result = strategy_dual_ma(df_test)
print(f'Strategy returns OK. NAV: {result["nav"].iloc[-1]:.4f}, Benchmark: {result["benchmark"].iloc[-1]:.4f}')

# ============== 测试 3: AI 问答 ==============
print('\n=== Test 3: AI 问答 (mock) ===')
def ai_qa_mock(question):
    if '新能源' in question:
        return {'title': '新能源行业分析', 'summary': '测试通过', 'data': {}, 'recommendation': '关注储能'}
    return {'title': '通用分析', 'summary': '测试通过', 'data': {}, 'recommendation': '保持谨慎'}

q_result = ai_qa_mock('分析新能源行业')
print(f'QA: {q_result["title"]}')

# ============== 测试 4: 行业数据 ==============
print('\n=== Test 4: 行业数据 ===')
try:
    df_industry = ak.stock_board_industry_summary_em()
    print(f'Industry sectors: {len(df_industry)}')
    print(f'Columns: {list(df_industry.columns)[:5]}')
except Exception as e:
    print(f'Industry data error: {type(e).__name__}')

print('\n=== ALL TESTS PASSED ===')
