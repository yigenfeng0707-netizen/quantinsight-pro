#!/usr/bin/env python
"""
QuantInsight Pro - financials 表批量构建
=========================================
akshare 财报接口 → qi_data.db(financials 表)，供语义层财务指标接地。

用法（生产服务器上运行）：
  python scripts/build_financials.py                       # 默认：核心具名标的
  python scripts/build_financials.py --all                 # 全部 800 标的（慢，限速）
  python scripts/build_financials.py --codes 600519,000858
  python scripts/build_financials.py --db data/qi_data.db --mock   # 管线自检（不入生产数据）

指标映射（metric_key ← akshare 财报摘要指标名）：
  revenue          ← 营业收入 / 营业总收入
  net_profit_parent← 归属于母公司股东的净利润 / 归母净利润
  net_profit       ← 净利润
  gross_margin     ← 销售毛利率 / 毛利率

报告期：默认只取年报（period 形如 2025-12-31）；--all-periods 取全部期间。
"""

from __future__ import annotations

import argparse
import logging
import re
import shutil
import sqlite3
import sys
import time
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger("build_financials")

# 指标名 → metric_key（与 semantic/metrics.ttl 的 bindingColumn 对应）
METRIC_MAP = {
    "营业收入": "revenue",
    "营业总收入": "revenue",
    "归属于母公司股东的净利润": "net_profit_parent",
    "归母净利润": "net_profit_parent",
    "归属于母公司所有者的净利润": "net_profit_parent",
    "净利润": "net_profit",
    "销售毛利率": "gross_margin",
    "毛利率": "gross_margin",
}

PERIOD_RE = re.compile(r"(20\d{2})[-/年]?(\d{1,2})?[-/月]?(\d{1,2})?")


def normalize_period(raw: str) -> str | None:
    """年报期间归一化为 'YYYY-12-31'；非年报返回 None（除非保留全部期间）。"""
    s = str(raw).strip()
    m = PERIOD_RE.match(s)
    if not m:
        return None
    y, mo, d = m.groups()
    if mo is None:
        return f"{y}-12-31"
    mo_i = int(mo)
    d_i = int(d) if d else None
    if mo_i == 12 and (d_i in (31, None)):
        return f"{y}-12-31"
    return f"{y}-{mo_i:02d}-{d_i or 1:02d}"  # 期间型，保留原值


def is_annual(period: str) -> bool:
    return period.endswith("12-31")


def fetch_one(code: str) -> list[dict]:
    """拉单只标的财报摘要 → financials 行。失败返回 []。"""
    import akshare as ak

    df = ak.stock_financial_abstract(symbol=code)
    if df is None or getattr(df, "empty", True):
        return []

    # 防御性列解析：找 指标 / 报告期 / 数值 三列（中英文均可）
    cols = {str(c).strip(): c for c in df.columns}
    def find_col(*cands):
        for c in cands:
            for real, orig in cols.items():
                if c in real:
                    return orig
        return None
    col_item = find_col("指标")
    col_period = find_col("报告期", "日期")
    col_value = find_col("数值", "金额")

    if col_item is None or col_period is None or col_value is None:
        log.warning("%s: 财报摘要列结构无法识别 %s", code, list(df.columns))
        return []

    rows = []
    seen = set()
    for _, r in df.iterrows():
        metric_key = METRIC_MAP.get(str(r[col_item]).strip())
        if not metric_key:
            continue
        period = normalize_period(r[col_period])
        if not period:
            continue
        try:
            val = float(r[col_value])
        except (TypeError, ValueError):
            continue
        key = (code, period, metric_key)
        if key in seen:
            continue
        seen.add(key)
        rows.append({"code": code, "period": period,
                     "metric_key": metric_key, "value": val})
    return rows


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", type=Path,
                    default=Path(__file__).parent.parent / "streamlit_app" / "data" / "qi_data.db")
    ap.add_argument("--codes", default="", help="逗号分隔代码列表（默认核心标的）")
    ap.add_argument("--all", action="store_true", help="覆盖 stock_history 全部代码")
    ap.add_argument("--all-periods", action="store_true", help="保留季报/半年报（默认只年报）")
    ap.add_argument("--sleep", type=float, default=0.6, help="每只标的间隔秒数")
    ap.add_argument("--mock", action="store_true",
                    help="管线自检：写合成数据行（source 标记 selftest_mock），供本地验证")
    args = ap.parse_args()

    if not args.db.exists():
        sys.exit(f"找不到数据库：{args.db}")

    sys.path.insert(0, str(Path(__file__).parent.parent / "streamlit_app"))
    from features.sqlite_data_layer import QIDataDB  # noqa: E402

    # 选码
    if args.all:
        conn = sqlite3.connect(f"file:{args.db}?mode=ro", uri=True)
        codes = [r[0] for r in conn.execute(
            "SELECT DISTINCT code FROM stock_history ORDER BY code")]
        conn.close()
    elif args.codes:
        codes = [c.strip() for c in args.codes.split(",") if c.strip()]
    else:
        from semantic.build_entities import CORE_STOCKS  # noqa: E402
        codes = sorted(CORE_STOCKS)
    log.info("标的 %d 只：%s%s", len(codes),
             ",".join(codes[:5]), "..." if len(codes) > 5 else "")

    if args.mock:
        # 管线自检：合成行，快速验证 upsert/get 通路（不来自任何接口）
        QIDataDB(str(args.db))  # 触发建表
        mock_rows = [
            {"code": c, "period": "2025-12-31", "metric_key": k, "value": v,
             "source": "selftest_mock"}
            for c in codes[:3]
            for k, v in (("revenue", 1.5e11), ("net_profit_parent", 7.5e10))
        ]
        db = QIDataDB(str(args.db))
        db.upsert_financials(mock_rows)
        df = db.get_financials(codes[0], ["revenue"])
        log.info("mock 写入 %d 行；回读样例：%s", len(mock_rows),
                 df.iloc[0].to_dict() if df is not None and not df.empty else None)
        return 0

    db = QIDataDB(str(args.db))
    total, fail = 0, 0
    for i, code in enumerate(codes, 1):
        try:
            rows = fetch_one(code)
            if not args.all_periods:
                rows = [r for r in rows if is_annual(r["period"])]
            if rows:
                db.upsert_financials(rows)
                total += len(rows)
                log.info("[%d/%d] %s: %d 行", i, len(codes), code, len(rows))
            else:
                log.info("[%d/%d] %s: 无可识别的年报指标", i, len(codes), code)
        except Exception as e:
            fail += 1
            log.warning("[%d/%d] %s 失败: %s", i, len(codes), code,
                        str(e)[:120])
        if i < len(codes) and args.sleep > 0:
            time.sleep(args.sleep)
    log.info("完成：写入 %d 行，失败 %d 只", total, fail)
    return 0 if total else (1 if fail else 0)


if __name__ == "__main__":
    raise SystemExit(main())
