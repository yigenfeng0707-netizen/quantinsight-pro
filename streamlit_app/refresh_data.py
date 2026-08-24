# -*- coding: utf-8 -*-
"""
QuantInsight Pro - 数据刷新脚本
=================================

从东方财富直连 HTTP API / akshare 拉取数据并写入 SQLite 缓存.
设计为 cron 定时任务运行.

数据源优先级:
1. 东方财富直连 HTTP API (推荐, 服务器可用)
2. akshare (本地开发可用, ECS 可能被封)

用法:
    python refresh_data.py           # 快速模式 (~30s): 行情/资金流/宏观
    python refresh_data.py --full    # 完整模式 (~5min): 含 Top100 个股历史

Cron 示例:
    # 工作日每 30 分钟刷新行情
    */30 9-15 * * 1-5 cd /opt/quantinsight && python streamlit_app/refresh_data.py >> /opt/quantinsight/logs/refresh.log 2>&1
    # 每日收盘后完整刷新
    0 16 * * 1-5 cd /opt/quantinsight && python streamlit_app/refresh_data.py --full >> /opt/quantinsight/logs/refresh.log 2>&1

版本: 2.0
日期: 2026-06-16
License: MIT
"""

from __future__ import annotations

import argparse
import logging
import sys
import time
from datetime import datetime
from pathlib import Path

# 将 streamlit_app 目录加入 sys.path, 以便导入 features 模块
_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

from features.sqlite_data_layer import QIDataDB

# ============================================================================
# 日志配置
# ============================================================================

_ECS_LOG_DIR = Path("/opt/quantinsight/logs")
_LOCAL_LOG_DIR = Path("./logs")


def _setup_logging():
    """配置日志输出到文件和终端"""
    log_dir = _ECS_LOG_DIR if _ECS_LOG_DIR.parent.exists() else _LOCAL_LOG_DIR
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "refresh.log"

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(str(log_file), encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )


logger = logging.getLogger(__name__)


# ============================================================================
# 主刷新逻辑: 优先使用东方财富直连 API
# ============================================================================

def refresh_all(full: bool = False) -> bool:
    """刷新所有数据

    优先使用东方财富直连 HTTP API (服务器可用),
    失败时回退到 akshare (本地可用).

    Args:
        full: 是否执行完整模式 (含 Top100 个股历史)

    Returns:
        True 表示全部成功, False 表示部分失败
    """
    start_time = time.time()
    print(f"\n{'='*60}")
    print(f"QuantInsight Pro - 数据刷新 {'[完整模式]' if full else '[快速模式]'}")
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")

    # 优先使用东方财富直连 API, 失败则回退到 akshare (新浪数据源)
    try:
        from features.eastmoney_direct import refresh_to_sqlite
        print("📡 使用东方财富直连 HTTP API...")
        results = refresh_to_sqlite(full=full)
        # 检查是否全部成功, 如果不是则补充 akshare
        if not all(results.values()):
            failed = [k for k, v in results.items() if not v]
            print(f"⚠️ 东方财富部分失败: {failed}, 使用 akshare 补充...")
            akshare_results = _refresh_via_akshare(full=full, only_steps=failed)
            for k, v in akshare_results.items():
                if v:
                    results[k] = True
        # QVeris 兜底: 行情或历史仍失败时
        _refresh_qveris_fallback(results, full=full)
    except ImportError as e:
        logger.warning("东方财富直连模块不可用: %s, 回退到 akshare", e)
        results = _refresh_via_akshare(full=full)
        _refresh_qveris_fallback(results, full=full)
    except Exception as e:
        logger.warning("东方财富直连刷新失败: %s, 回退到 akshare", e)
        results = _refresh_via_akshare(full=full)
        _refresh_qveris_fallback(results, full=full)

    # 扩展数据源: 概念板块 / 市场宽度 / 宏观快照
    try:
        ext_results = _refresh_extended_sources()
        results.update(ext_results)
    except Exception as e:
        logger.warning("扩展数据源刷新失败: %s", e)

    # stock_spot 仍为空时，用历史 K 线最新价回填 (演示/离线兜底)
    _ensure_stock_spot_from_history(results)

    # 汇总
    elapsed = time.time() - start_time
    success = sum(1 for v in results.values() if v)
    total = len(results)
    all_ok = all(results.values()) if results else False

    print(f"\n{'='*60}")
    print(f"刷新完成: {success}/{total} 步骤成功, 耗时 {elapsed:.1f}s")
    for name, ok in results.items():
        status = "✅" if ok else "❌"
        print(f"  {status} {name}")
    print(f"{'='*60}\n")

    return all_ok


def _ensure_stock_spot_from_history(results: dict) -> None:
    """实时行情 API 失败或清洗后无数据时，用 stock_history 最新 K 线回填 stock_spot"""
    db = QIDataDB()
    try:
        count = db._get_conn().execute("SELECT COUNT(*) FROM stock_spot").fetchone()[0]
    except Exception:
        count = 0
    if count > 0:
        return

    spot = db.get_spot_from_history_latest()
    if spot is None or spot.empty:
        logger.warning("stock_spot 为空且 history 无数据，无法回填")
        results["stock_spot"] = False
        return

    db.upsert_stock_spot_rows(spot, source="history_latest")
    count = db._get_conn().execute("SELECT COUNT(*) FROM stock_spot").fetchone()[0]
    if count > 0:
        results["stock_spot"] = True
        print(f"  ✅ stock_spot (history 回填): {count} rows")
    else:
        results["stock_spot"] = False
        print("  ❌ stock_spot: history 回填失败")


def _refresh_qveris_fallback(results: dict, full: bool = False) -> None:
    """QVeris 兜底: 行情 / 历史仍失败时尝试付费 API"""
    try:
        from features.qveris_source import is_configured, refresh_spot_to_sqlite, sync_historical_to_sqlite
    except ImportError:
        return

    if not is_configured():
        return

    if not results.get("stock_spot"):
        print("📡 QVeris 兜底: 更新 Top50 实时行情...")
        ok = refresh_spot_to_sqlite(top_n=50)
        if ok:
            results["stock_spot"] = True
            print("  ✅ stock_spot (QVeris 部分更新)")

    if full and not results.get("stock_history"):
        print("📡 QVeris 兜底: 同步 Top100 历史 K 线 (消耗积分, 较慢)...")
        hist = sync_historical_to_sqlite(top_n=100)
        if hist.get("success", 0) > 0:
            results["stock_history"] = True
            print(f"  ✅ stock_history (QVeris): {hist['success']} 成功, {hist['fail']} 失败")


# ============================================================================
# 扩展数据源刷新 (概念板块 / 市场宽度 / 宏观快照)
# ============================================================================

def _macro_bundle_to_indices(bundle: dict) -> dict:
    """将 fetch_macro_bundle 结果转为 macro_indices 格式"""
    macro_data: dict = {}
    key_map = {"cpi": "CPI", "pmi": "PMI", "m2": "M2", "gdp": "GDP"}
    for key, indicator in key_map.items():
        records = bundle.get(key)
        if not isinstance(records, list):
            continue
        date_value = {}
        for rec in records:
            if not isinstance(rec, dict):
                continue
            date_str = None
            value = None
            for k, v in rec.items():
                kl = str(k).lower()
                if date_str is None and any(x in kl for x in ["date", "月份", "日期", "time", "year", "月"]):
                    date_str = str(v)
                elif value is None and any(x in kl for x in ["value", "值", "cpi", "ppi", "pmi", "gdp", "m2", "今值", "同比"]):
                    try:
                        value = float(v)
                    except (ValueError, TypeError):
                        pass
            if date_str and value is not None:
                date_value[date_str] = value
        if date_value:
            macro_data[indicator] = date_value
    return macro_data


def _refresh_extended_sources(db: QIDataDB = None) -> dict:
    """刷新 extended_data_sources 提供的补充数据类型"""
    from features.extended_data_sources import (
        fetch_concept_boards,
        fetch_limit_stats,
        fetch_macro_bundle,
    )

    if db is None:
        db = QIDataDB()

    results = {}

    print("📊 [扩展] 概念板块...")
    try:
        res = fetch_concept_boards(top_n=100)
        if res.ok and res.data is not None and not res.data.empty:
            db.upsert_concept_board(res.data, source=res.source)
            results["concept_board"] = True
            print(f"  ✅ concept_board ({res.source}): {len(res.data)} rows")
        else:
            results["concept_board"] = False
            print(f"  ❌ concept_board: {res.error or '无数据'}")
    except Exception as e:
        results["concept_board"] = False
        print(f"  ❌ concept_board: {e}")

    print("📊 [扩展] 市场宽度 (涨跌停)...")
    try:
        res = fetch_limit_stats()
        if res.ok and isinstance(res.data, dict):
            db.upsert_market_breadth(res.data, source=res.source)
            results["market_breadth"] = True
            print(f"  ✅ market_breadth ({res.source}): {res.data}")
        else:
            results["market_breadth"] = False
            print(f"  ❌ market_breadth: {res.error or '无数据'}")
    except Exception as e:
        results["market_breadth"] = False
        print(f"  ❌ market_breadth: {e}")

    print("📊 [扩展] 宏观指标包...")
    try:
        res = fetch_macro_bundle()
        if res.ok and isinstance(res.data, dict):
            db.upsert_macro_snapshot(res.data, source=res.source)
            macro_indices = _macro_bundle_to_indices(res.data)
            if macro_indices:
                db.upsert_macro_indices(macro_indices)
            results["macro_snapshot"] = True
            print(f"  ✅ macro_snapshot ({res.source}): {len(res.data)} keys")
        else:
            results["macro_snapshot"] = False
            print(f"  ❌ macro_snapshot: {res.error or '无数据'}")
    except Exception as e:
        results["macro_snapshot"] = False
        print(f"  ❌ macro_snapshot: {e}")

    return results


# ============================================================================
# akshare 回退 (本地开发用)
# ============================================================================

import os
import json
import pandas as pd

_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0",
]

_ua_index = 0


def _rotate_ua() -> str:
    """轮换 User-Agent"""
    global _ua_index
    ua = _USER_AGENTS[_ua_index % len(_USER_AGENTS)]
    _ua_index += 1
    return ua


def _akshare_call_with_retry(func, *args, max_retries=3, **kwargs):
    """带 UA 轮换和重试的 akshare 调用"""
    for attempt in range(max_retries):
        ua = _rotate_ua()
        os.environ["AKSHARE_UA"] = ua
        try:
            result = func(*args, **kwargs)
            if result is not None and not (isinstance(result, pd.DataFrame) and result.empty):
                return result
            logger.warning("akshare 返回空数据 (attempt %d/%d, UA: %s)",
                           attempt + 1, max_retries, ua[:50])
        except Exception as e:
            logger.warning("akshare 调用失败 (attempt %d/%d, UA: %s): %s",
                           attempt + 1, max_retries, ua[:50], e)
        if attempt < max_retries - 1:
            time.sleep(2 * (attempt + 1))
    return None


def _refresh_via_akshare(full: bool = False, only_steps: list = None) -> dict:
    """使用 akshare 刷新数据 (回退方案)

    Args:
        full: 是否执行完整模式 (含 Top100 个股历史)
        only_steps: 仅刷新指定步骤 (None 表示全部刷新).
                    可选值: stock_spot / northbound_flow / sector_flow /
                    fund_flow / margin_trading / stock_history
    """
    try:
        import akshare as ak
    except ImportError:
        logger.error("akshare 未安装")
        return {}

    db = QIDataDB()
    results = {}

    def _should_run(step_name: str) -> bool:
        """判断是否需要执行该步骤"""
        if only_steps is None:
            return True
        return step_name in only_steps

    # Step 1: 全A股实时行情
    if not _should_run("stock_spot"):
        logger.info("跳过 stock_spot (不在 only_steps 列表)")
    else:
        print("📊 [1/6] akshare: 全A股实时行情...")
        try:
            df = _akshare_call_with_retry(ak.stock_zh_a_spot_em)
            if df is not None:
                db.upsert_stock_spot(df)
                results["stock_spot"] = True
                print(f"  ✅ stock_spot: {len(df)} rows")
            else:
                results["stock_spot"] = False
                print("  ❌ stock_spot: 获取失败")
        except Exception as e:
            results["stock_spot"] = False
            print(f"  ❌ stock_spot: {e}")

    # Step 2: 北向资金
    if not _should_run("northbound_flow"):
        logger.info("跳过 northbound_flow (不在 only_steps 列表)")
    else:
        print("📊 [2/6] akshare: 北向资金...")
        try:
            # 尝试多种 akshare API 名称 (不同版本名称不同)
            df = None
            for api_name in ["stock_hsgt_north_net_flow_in_em", "stock_hsgt_hist_em"]:
                try:
                    func = getattr(ak, api_name, None)
                    if func is not None:
                        if api_name == "stock_hsgt_north_net_flow_in_em":
                            df = _akshare_call_with_retry(func, symbol="北向")
                        else:
                            df = _akshare_call_with_retry(func, symbol="沪股通")
                        if df is not None:
                            break
                except Exception:
                    continue

            if df is not None:
                db.upsert_northbound_flow(df)
                results["northbound_flow"] = True
                print(f"  ✅ northbound_flow: {len(df)} rows")
            else:
                results["northbound_flow"] = False
                print("  ❌ northbound_flow: 获取失败")
        except Exception as e:
            results["northbound_flow"] = False
            print(f"  ❌ northbound_flow: {e}")

    # Step 3: 板块资金流
    if not _should_run("sector_flow"):
        logger.info("跳过 sector_flow (不在 only_steps 列表)")
    else:
        print("📊 [3/6] akshare: 板块资金流...")
        try:
            df = _akshare_call_with_retry(ak.stock_board_industry_name_em)
            if df is not None:
                db.upsert_sector_flow(df)
                results["sector_flow"] = True
                print(f"  ✅ sector_flow: {len(df)} rows")
            else:
                results["sector_flow"] = False
                print("  ❌ sector_flow: 获取失败")
        except Exception as e:
            results["sector_flow"] = False
            print(f"  ❌ sector_flow: {e}")

    # Step 4: 资金流向
    if not _should_run("fund_flow"):
        logger.info("跳过 fund_flow (不在 only_steps 列表)")
    else:
        print("📊 [4/6] akshare: 资金流向...")
        try:
            df = _akshare_call_with_retry(ak.stock_market_fund_flow)
            if df is not None:
                data = {}
                for _, row in df.iterrows():
                    date_str = str(row.iloc[0]) if len(row) > 0 else None
                    if date_str is None:
                        continue
                    data[date_str] = {
                        "main_flow": float(row.iloc[1]) if len(row) > 1 and pd.notna(row.iloc[1]) else None,
                        "retail_flow": float(row.iloc[2]) if len(row) > 2 and pd.notna(row.iloc[2]) else None,
                        "north_flow": float(row.iloc[3]) if len(row) > 3 and pd.notna(row.iloc[3]) else None,
                    }
                db.upsert_fund_flow(data)
                results["fund_flow"] = True
                print(f"  ✅ fund_flow: {len(data)} rows")
            else:
                results["fund_flow"] = False
                print("  ❌ fund_flow: 获取失败")
        except Exception as e:
            results["fund_flow"] = False
            print(f"  ❌ fund_flow: {e}")

    # Step 5: 融资融券
    if not _should_run("margin_trading"):
        logger.info("跳过 margin_trading (不在 only_steps 列表)")
    else:
        print("📊 [5/6] akshare: 融资融券...")
        try:
            df = None
            try:
                from features.eastmoney_direct import fetch_margin_trading
                df = fetch_margin_trading(days=60)
            except Exception as em_err:
                logger.debug("eastmoney margin: %s", em_err)
            if df is None:
                for source_func, source_name in [
                    (lambda: ak.stock_margin_sse(start_date=(datetime.now() - timedelta(days=60)).strftime("%Y%m%d"),
                                               end_date=datetime.now().strftime("%Y%m%d")), "上交所汇总"),
                ]:
                    df = _akshare_call_with_retry(source_func)
                    if df is not None:
                        logger.info("融资融券数据来源: %s", source_name)
                        break

            if df is not None:
                db.upsert_margin_trading(df)
                results["margin_trading"] = True
                print(f"  ✅ margin_trading: {len(df)} rows")
            else:
                results["margin_trading"] = False
                print("  ❌ margin_trading: 获取失败")
        except Exception as e:
            results["margin_trading"] = False
            print(f"  ❌ margin_trading: {e}")

    # Step 6 (--full): 个股历史
    if full and _should_run("stock_history"):
        print("📊 [6/6] akshare: Top100 个股历史...")
        try:
            spot_df = db.get_stock_spot()
            if spot_df is not None and len(spot_df) > 0:
                if "total_mv" in spot_df.columns:
                    top100 = spot_df.nlargest(100, "total_mv")
                else:
                    top100 = spot_df.head(100)

                codes = top100["code"].tolist() if "code" in top100.columns else []
                success_count = 0
                fail_count = 0

                for i, code in enumerate(codes):
                    try:
                        df = _akshare_call_with_retry(
                            ak.stock_zh_a_hist,
                            symbol=code,
                            period="daily",
                            start_date=(datetime.now().replace(year=datetime.now().year - 1)).strftime("%Y%m%d"),
                            end_date=datetime.now().strftime("%Y%m%d"),
                            adjust="qfq",
                        )
                        if df is not None:
                            db.upsert_stock_history(code, df)
                            success_count += 1
                        else:
                            fail_count += 1

                        if (i + 1) % 20 == 0:
                            print(f"    进度: {i+1}/{len(codes)} (成功: {success_count}, 失败: {fail_count})")

                        time.sleep(0.5)
                    except Exception as e:
                        fail_count += 1
                        logger.warning("stock_history (%s) 失败: %s", code, e)

                results["stock_history"] = fail_count < success_count
                print(f"  ✅ stock_history: 成功 {success_count}, 失败 {fail_count}")
            else:
                results["stock_history"] = False
                print("  ❌ stock_history: stock_spot 为空")
        except Exception as e:
            results["stock_history"] = False
            print(f"  ❌ stock_history: {e}")
    elif full and not _should_run("stock_history"):
        logger.info("跳过 stock_history (不在 only_steps 列表)")
    elif not full:
        print("📊 [6/6] 跳过个股历史 (使用 --full 启用)")

    # Step 7: 个股基本面 (V3.11 新增)
    if not _should_run("stock_profile"):
        logger.info("跳过 stock_profile (不在 only_steps 列表)")
    else:
        print("📊 [7/8] akshare: Top50 个股基本面...")
        try:
            spot_df = db.get_stock_spot()
            if spot_df is not None and len(spot_df) > 0:
                if "total_mv" in spot_df.columns:
                    top50 = spot_df.nlargest(50, "total_mv")
                else:
                    top50 = spot_df.head(50)

                codes = top50["code"].tolist() if "code" in top50.columns else []
                success_count = 0
                fail_count = 0

                for i, code in enumerate(codes):
                    try:
                        # akshare 个股信息
                        df_info = _akshare_call_with_retry(
                            ak.stock_individual_info_em, symbol=code
                        )
                        if df_info is not None and not df_info.empty:
                            # 转为 JSON 存储
                            info_dict = {}
                            for _, row in df_info.iterrows():
                                item = row.iloc[0] if len(row) > 0 else ""
                                value = row.iloc[1] if len(row) > 1 else ""
                                info_dict[str(item)] = str(value)
                            db.upsert_stock_profile(code, json.dumps(info_dict, ensure_ascii=False))
                            success_count += 1
                        else:
                            fail_count += 1

                        if (i + 1) % 10 == 0:
                            print(f"    进度: {i+1}/{len(codes)} (成功: {success_count}, 失败: {fail_count})")

                        time.sleep(0.3)
                    except Exception as e:
                        fail_count += 1
                        logger.warning("stock_profile (%s) 失败: %s", code, e)

                results["stock_profile"] = success_count > 0
                print(f"  ✅ stock_profile: 成功 {success_count}, 失败 {fail_count}")
            else:
                results["stock_profile"] = False
                print("  ❌ stock_profile: stock_spot 为空")
        except Exception as e:
            results["stock_profile"] = False
            print(f"  ❌ stock_profile: {e}")

    # Step 8: 宏观指数 (V3.11 新增)
    if not _should_run("macro_indices"):
        logger.info("跳过 macro_indices (不在 only_steps 列表)")
    else:
        print("📊 [8/8] akshare: 宏观经济指数...")
        try:
            macro_data = {}
            today = datetime.now().strftime("%Y-%m-%d")

            # 尝试获取宏观经济数据 (CPI/PPI/PMI 等)
            macro_apis = [
                ("CPI", lambda: _akshare_call_with_retry(ak.macro_china_cpi_monthly)),
                ("PPI", lambda: _akshare_call_with_retry(ak.macro_china_ppi_yearly)),
                ("PMI", lambda: _akshare_call_with_retry(ak.macro_china_pmi)),
                ("GDP", lambda: _akshare_call_with_retry(ak.macro_china_gdp_yearly)),
                ("M2", lambda: _akshare_call_with_retry(ak.macro_china_money_supply)),
            ]

            for indicator_name, api_func in macro_apis:
                try:
                    df = api_func()
                    if df is not None and not df.empty:
                        # 取最近 12 条记录
                        recent = df.tail(12)
                        date_value = {}
                        for _, row in recent.iterrows():
                            # 尝试多种列名
                            date_col = None
                            value_col = None
                            for col in recent.columns:
                                col_lower = str(col).lower()
                                if any(k in col_lower for k in ["date", "月份", "日期", "time", "year"]):
                                    date_col = col
                                elif any(k in col_lower for k in ["value", "值", "cpi", "ppi", "pmi", "gdp", "m2"]):
                                    value_col = col

                            if date_col and value_col:
                                d = str(row[date_col])
                                try:
                                    v = float(row[value_col])
                                    date_value[d] = v
                                except (ValueError, TypeError):
                                    pass

                        if date_value:
                            macro_data[indicator_name] = date_value
                            print(f"    {indicator_name}: {len(date_value)} 条")
                    time.sleep(0.5)
                except Exception as e:
                    logger.warning("宏观指标 %s 获取失败: %s", indicator_name, e)

            if macro_data:
                db.upsert_macro_indices(macro_data)
                results["macro_indices"] = True
                total_indicators = sum(len(v) for v in macro_data.values())
                print(f"  ✅ macro_indices: {len(macro_data)} 个指标, {total_indicators} 条数据")
            else:
                results["macro_indices"] = False
                print("  ❌ macro_indices: 未获取到数据")
        except Exception as e:
            results["macro_indices"] = False
            print(f"  ❌ macro_indices: {e}")

    return results


# ============================================================================
# CLI 入口
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="QuantInsight Pro - 数据刷新脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python refresh_data.py           # 快速模式 (~30s)
  python refresh_data.py --full    # 完整模式 (~5min)
  python refresh_data.py --qveris-history              # QVeris 同步 Top100 历史
  python refresh_data.py --qveris-history --codes 600519,300750 --days 730
        """,
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="完整模式: 同时刷新 Top100 个股历史行情 (~5min)",
    )
    parser.add_argument(
        "--qveris-history",
        action="store_true",
        help="仅用 QVeris 同步历史 K 线到 SQLite (空闲时跑, 消耗积分)",
    )
    parser.add_argument(
        "--codes",
        type=str,
        default="",
        help="配合 --qveris-history: 指定股票代码, 逗号分隔, 如 600519,300750",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=365,
        help="配合 --qveris-history: 回溯天数 (默认 365)",
    )
    args = parser.parse_args()

    _setup_logging()

    try:
        if args.qveris_history:
            from features.qveris_source import is_configured, sync_historical_to_sqlite

            if not is_configured():
                print("❌ 未配置 QVERIS_API_KEY, 请在 secrets.toml 或环境变量中设置")
                sys.exit(1)
            codes = [c.strip() for c in args.codes.split(",") if c.strip()] or None
            hist = sync_historical_to_sqlite(codes=codes, days=args.days)
            sys.exit(0 if hist.get("success", 0) > 0 else 1)

        all_ok = refresh_all(full=args.full)
        sys.exit(0 if all_ok else 1)
    except Exception as e:
        logger.critical("刷新脚本异常退出: %s", e, exc_info=True)
        print(f"\n💥 刷新脚本异常: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
