#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
QuantInsight Pro - 10 年回测数据补充 (2015-2019)
Phase 1 A1: 拉取并合并 5 年历史数据
"""

import os
import sys
import akshare as ak
import pandas as pd
import json
from datetime import datetime

OUT_DIR = r"D:\shFintech"

INDICES = {
    "hs300": ("sh000300", "沪深300"),
    "zz500": ("sh000905", "中证500"),
    "cyb":   ("sz399006", "创业板指"),
}

START_DATE = "2015-01-01"
END_DATE = "2019-12-31"


def fetch_index(code, name):
    """拉取指数日线数据, 截取 2015-2019"""
    print(f"[1/2] 拉取 {name} ({code})...")
    df = ak.stock_zh_index_daily(symbol=code)
    print(f"  总数据: {len(df)} 点 ({df['date'].iloc[0]} ~ {df['date'].iloc[-1]})")

    df['date'] = pd.to_datetime(df['date'])
    mask = (df['date'] >= START_DATE) & (df['date'] <= END_DATE)
    df_period = df[mask].reset_index(drop=True)
    print(f"  {START_DATE}~{END_DATE}: {len(df_period)} 点")
    print(f"  起始价: {df_period['close'].iloc[0]:.2f}")
    print(f"  结束价: {df_period['close'].iloc[-1]:.2f}")
    print(f"  期间收益: {(df_period['close'].iloc[-1]/df_period['close'].iloc[0]-1)*100:.2f}%")
    return df_period


def merge_with_existing():
    """合并 2015-2019 新数据 与 现有 2020-2026 数据"""
    print("\n" + "="*60)
    print("合并 2015-2019 与 2020-2026 数据")
    print("="*60)

    for key, (code, name) in INDICES.items():
        print(f"\n--- {name} ({key}) ---")

        # 拉取 2015-2019
        df_2015_2019 = fetch_index(code, name)

        # 读取现有 2020-2026
        existing_file = f"{OUT_DIR}\\_data_{key}.csv"
        if os.path.exists(existing_file):
            df_existing = pd.read_csv(existing_file)
            df_existing['date'] = pd.to_datetime(df_existing['date'])
            print(f"  现有数据: {len(df_existing)} 点 ({df_existing['date'].iloc[0]} ~ {df_existing['date'].iloc[-1]})")

            # 合并
            df_full = pd.concat([df_2015_2019, df_existing], ignore_index=True)
            df_full = df_full.drop_duplicates(subset=['date'], keep='last')
            df_full = df_full.sort_values('date').reset_index(drop=True)
            print(f"  合并后: {len(df_full)} 点 ({df_full['date'].iloc[0]} ~ {df_full['date'].iloc[-1]})")

            # 保存完整数据
            out_file = f"{OUT_DIR}\\_data_{key}_full.csv"
            df_full.to_csv(out_file, index=False, encoding='utf-8-sig')
            print(f"  [OK] 保存: {out_file}")

            # 保存 2015-2019 单独
            new_file = f"{OUT_DIR}\\_data_{key}_2015_2019.csv"
            df_2015_2019.to_csv(new_file, index=False, encoding='utf-8-sig')
            print(f"  [OK] 保存: {new_file}")
        else:
            print(f"  [WARN] 现有文件不存在: {existing_file}")


def summary():
    """汇总 11.4 年数据"""
    print("\n" + "="*60)
    print("11.4 年数据汇总 (2015-01-01 ~ 2026-06-05)")
    print("="*60)

    for key, (code, name) in INDICES.items():
        full_file = f"{OUT_DIR}\\_data_{key}_full.csv"
        if os.path.exists(full_file):
            df = pd.read_csv(full_file)
            print(f"\n{name} ({key}):")
            print(f"  数据点: {len(df)}")
            print(f"  日期范围: {df['date'].iloc[0]} ~ {df['date'].iloc[-1]}")
            print(f"  起始价: {df['close'].iloc[0]:.2f}")
            print(f"  结束价: {df['close'].iloc[-1]:.2f}")
            print(f"  期间累计收益: {(df['close'].iloc[-1]/df['close'].iloc[0]-1)*100:.2f}%")
            annual = (df['close'].iloc[-1]/df['close'].iloc[0])**(1/11.4) - 1
            print(f"  年化收益: {annual*100:.2f}%")

    print("\n" + "="*60)
    print("[OK] 10 年回测数据准备就绪 (2015-2019 + 2020-2026)")
    print("="*60)


if __name__ == "__main__":
    merge_with_existing()
    summary()
