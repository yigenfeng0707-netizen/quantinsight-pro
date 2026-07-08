#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
QVeris 历史 K 线同步 — 空闲时批量拉入 SQLite

示例:
  cd streamlit_app
  python ../scripts/qveris_sync_historical.py
  python ../scripts/qveris_sync_historical.py --codes 600519,300750,601318
  python ../scripts/qveris_sync_historical.py --top 200 --days 730

需先在 streamlit_app/.streamlit/secrets.toml 配置 QVERIS_API_KEY。
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "streamlit_app"
sys.path.insert(0, str(ROOT))

from features.qveris_source import is_configured, sync_historical_to_sqlite  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="QVeris 历史 K 线 → SQLite")
    parser.add_argument("--codes", type=str, default="", help="逗号分隔股票代码")
    parser.add_argument("--top", type=int, default=100, help="未指定 codes 时取市值 Top N")
    parser.add_argument("--hs300", action="store_true", help="同步沪深300全部300只成分股")
    parser.add_argument("--zz500", action="store_true", help="同步中证500全部500只成分股")
    parser.add_argument("--days", type=int, default=365, help="回溯天数")
    parser.add_argument("--delay", type=float, default=0.35, help="每次 API 间隔(秒)")
    args = parser.parse_args()

    if not is_configured():
        print("❌ 未配置 QVERIS_API_KEY")
        print("   请在 streamlit_app/.streamlit/secrets.toml 添加:")
        print('   QVERIS_API_KEY = "sk-cn-..."')
        return 1

    codes = [c.strip() for c in args.codes.split(",") if c.strip()] or None
    top_n = 500 if args.zz500 else (300 if args.hs300 else args.top)
    result = sync_historical_to_sqlite(
        codes=codes,
        days=args.days,
        delay=args.delay,
        top_n=top_n,
    )
    print(f"\n完成: 成功 {result['success']}, 跳过 {result.get('skipped', 0)}, 失败 {result['fail']}")
    return 0 if (result.get("success", 0) > 0 or result.get("skipped", 0) > 0) else 1


if __name__ == "__main__":
    raise SystemExit(main())
