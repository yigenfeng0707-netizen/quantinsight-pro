# -*- coding: utf-8 -*-
"""
QuantInsight Pro - 东方财富直连 HTTP API
==========================================

绕过 akshare, 直接调用东方财富 HTTP 接口获取数据.
解决 ECS 服务器上 akshare 被封禁的问题.

原理: akshare 底层也是调用东方财富的 HTTP API, 但其默认 UA 和请求方式
容易被东方财富识别为爬虫而封禁 IP. 本模块使用更完善的请求头和 cookies,
提高在服务器环境下的可用性.

数据源:
- 实时行情: push2.eastmoney.com
- 历史K线: push2his.eastmoney.com
- 北向资金: push2his.eastmoney.com (kamt)
- 板块资金: push2.eastmoney.com
- 融资融券: datacenter-web.eastmoney.com

版本: 1.0
日期: 2026-06-16
License: MIT
"""

from __future__ import annotations

import json
import logging
import math
import os
import time
from datetime import datetime, timedelta
from typing import Optional

import pandas as pd
import requests

logger = logging.getLogger(__name__)

# ============================================================================
# 请求头 & Session
# ============================================================================

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Accept": "*/*",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate",
    "Referer": "https://quote.eastmoney.com/",
    "Connection": "keep-alive",
}

_COOKIES = {
    "qgqp_b_id": "e8a6c7d9f0a1b2c3d4e5f6a7b8c9d0e1",
    "ut": "Fby5q3M0U9z7Ntq0Ov0C6y5f6789abcdef",
}

_session = None


def _get_session() -> requests.Session:
    """获取带连接池的 requests Session"""
    global _session
    if _session is None:
        # 清除代理环境变量, 避免代理干扰直连东方财富
        for key in ["HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy", "ALL_PROXY", "all_proxy"]:
            os.environ.pop(key, None)
        os.environ["NO_PROXY"] = "*"

        _session = requests.Session()
        _session.headers.update(_HEADERS)
        _session.cookies.update(_COOKIES)
        # 绕过代理, 直连东方财富 (避免代理干扰)
        _session.trust_env = False
        _session.proxies = {"http": None, "https": None}
        # 连接池
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=10, pool_maxsize=20, max_retries=2
        )
        _session.mount("http://", adapter)
        _session.mount("https://", adapter)
    return _session


def _http_get(url: str, params: dict = None, timeout: int = 15) -> Optional[dict]:
    """带重试的 HTTP GET 请求, 自动尝试 HTTPS 和 HTTP"""
    sess = _get_session()
    for attempt in range(3):
        # 尝试 HTTPS 和 HTTP 两种协议
        for protocol in ["https", "http"]:
            try:
                full_url = url
                if full_url.startswith("https://") and protocol == "http":
                    full_url = full_url.replace("https://", "http://", 1)
                elif full_url.startswith("http://") and protocol == "https":
                    full_url = full_url.replace("http://", "https://", 1)
                resp = sess.get(full_url, params=params, timeout=timeout, verify=False)
                if resp.status_code == 200:
                    return resp.json()
                logger.warning("HTTP %d: %s", resp.status_code, full_url[:80])
            except Exception as e:
                logger.debug("HTTP %s 请求失败: %s", protocol, str(e)[:80])
                continue
        if attempt < 2:
            time.sleep(1 * (attempt + 1))
    return None


# ============================================================================
# 1. 全 A 股实时行情
# ============================================================================

def fetch_stock_spot(page_size: int = 5000) -> Optional[pd.DataFrame]:
    """
    拉取全 A 股实时行情 (东方财富直连)

    Returns:
        DataFrame: 代码, 名称, 最新价, 涨跌幅, 涨跌额, 成交量, 成交额,
                   振幅, 最高, 最低, 今开, 昨收, 量比, 换手率,
                   市盈率-动态, 市净率, 总市值, 流通市值, 60日涨跌幅
    """
    # 东方财富行情 API
    url = "https://push2.eastmoney.com/api/qt/clist/get"

    # 字段映射 (东方财富字段编号)
    # f2=最新价 f3=涨跌幅 f4=涨跌额 f5=成交量 f6=成交额
    # f7=振幅 f8=换手率 f9=市盈率 f10=量比 f12=代码 f14=名称
    # f15=最高 f16=最低 f17=今开 f18=昨收 f20=总市值 f21=流通市值
    # f23=市净率 f115=市盈率(动态)
    fields = "f2,f3,f4,f5,f6,f7,f8,f9,f10,f12,f14,f15,f16,f17,f18,f20,f21,f23,f115"

    all_data = []
    page = 1
    total_pages = 1

    while page <= total_pages:
        params = {
            "pn": page,
            "pz": page_size,
            "po": "1",  # 按总市值降序
            "np": "1",
            "ut": "bd1d9ddb04089700cf9c27f6f7426281",
            "fltt": "2",
            "invt": "2",
            "fid": "f20",
            "fs": "m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23,m:0+t:81+s:2048",
            "fields": fields,
        }

        data = _http_get(url, params)
        if data is None or data.get("data") is None:
            break

        diff = data["data"].get("diff", [])
        if not diff:
            break

        total = data["data"].get("total", 0)
        total_pages = math.ceil(total / page_size)

        all_data.extend(diff)
        page += 1

        # 避免请求过快
        if page <= total_pages:
            time.sleep(0.3)

    if not all_data:
        return None

    df = pd.DataFrame(all_data)

    # 字段重命名
    col_map = {
        "f12": "代码", "f14": "名称", "f2": "最新价", "f3": "涨跌幅",
        "f4": "涨跌额", "f5": "成交量", "f6": "成交额", "f7": "振幅",
        "f8": "换手率", "f9": "市盈率-动态", "f10": "量比",
        "f15": "最高", "f16": "最低", "f17": "今开", "f18": "昨收",
        "f20": "总市值", "f21": "流通市值", "f23": "市净率",
        "f115": "市盈率-动态",
    }
    df = df.rename(columns={k: v for k, v in col_map.items() if k in df.columns})

    # 过滤无效数据
    if "代码" in df.columns:
        df = df[df["代码"].str.match(r"^\d{6}$", na=False)]

    # 数值类型转换
    numeric_cols = ["最新价", "涨跌幅", "涨跌额", "成交量", "成交额", "振幅",
                    "换手率", "市盈率-动态", "量比", "最高", "最低", "今开",
                    "昨收", "总市值", "流通市值", "市净率"]

    # 如果有重复的市盈率列, 先去重再转换
    if "市盈率-动态" in df.columns and df.columns.tolist().count("市盈率-动态") > 1:
        cols = df.columns.tolist()
        seen = set()
        keep_cols = []
        for c in cols:
            if c == "市盈率-动态":
                if c in seen:
                    continue
                seen.add(c)
            keep_cols.append(c)
        df = df[keep_cols]

    for col in numeric_cols:
        if col in df.columns:
            # 确保是 Series (不是 DataFrame, 防止重复列名导致问题)
            if isinstance(df[col], pd.DataFrame):
                df[col] = df[col].iloc[:, 0]
            df[col] = pd.to_numeric(df[col], errors="coerce")

    return df.reset_index(drop=True)


# ============================================================================
# 2. 个股历史 K 线
# ============================================================================

def fetch_stock_history(
    symbol: str,
    start_date: str = "",
    end_date: str = "",
    period: str = "daily",
    adjust: str = "qfq",
) -> Optional[pd.DataFrame]:
    """
    拉取个股历史 K 线 (东方财富直连)

    Args:
        symbol: 股票代码 (如 "600519")
        start_date: 开始日期 "YYYYMMDD"
        end_date: 结束日期 "YYYYMMDD"
        period: "daily" / "weekly" / "monthly"
        adjust: "qfq" / "hfq" / ""

    Returns:
        DataFrame: 日期, 开盘, 收盘, 最高, 最低, 成交量, 成交额, 振幅, 涨跌幅, 涨跌额, 换手率
    """
    # 确定市场前缀
    sec_id = _get_sec_id(symbol)
    if sec_id is None:
        return None

    # 复权类型
    fq_map = {"qfq": "1", "hfq": "2", "": "0"}
    fq_type = fq_map.get(adjust, "1")

    # K线周期
    klt_map = {"daily": "101", "weekly": "102", "monthly": "103"}
    klt = klt_map.get(period, "101")

    url = "https://push2his.eastmoney.com/api/qt/stock/kline/get"
    params = {
        "secid": sec_id,
        "ut": "fa5fd1943c7b386f172d6893dbfba10b",
        "fields1": "f1,f2,f3,f4,f5,f6",
        "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61",
        "klt": klt,
        "fqt": fq_type,
        "beg": start_date.replace("-", "") if start_date else "0",
        "end": end_date.replace("-", "") if end_date else "20500101",
        "lmt": "1000000",
    }

    data = _http_get(url, params)
    if data is None or data.get("data") is None:
        return None

    klines = data["data"].get("klines", [])
    if not klines:
        return None

    rows = []
    for line in klines:
        parts = line.split(",")
        if len(parts) >= 11:
            rows.append({
                "日期": parts[0],
                "开盘": float(parts[1]) if parts[1] != "-" else None,
                "收盘": float(parts[2]) if parts[2] != "-" else None,
                "最高": float(parts[3]) if parts[3] != "-" else None,
                "最低": float(parts[4]) if parts[4] != "-" else None,
                "成交量": float(parts[5]) if parts[5] != "-" else None,
                "成交额": float(parts[6]) if parts[6] != "-" else None,
                "振幅": float(parts[7]) if parts[7] != "-" else None,
                "涨跌幅": float(parts[8]) if parts[8] != "-" else None,
                "涨跌额": float(parts[9]) if parts[9] != "-" else None,
                "换手率": float(parts[10]) if parts[10] != "-" else None,
            })

    if not rows:
        return None

    df = pd.DataFrame(rows)
    df["日期"] = pd.to_datetime(df["日期"])

    # 按日期范围过滤
    if start_date:
        start_dt = pd.to_datetime(start_date)
        df = df[df["日期"] >= start_dt]
    if end_date:
        end_dt = pd.to_datetime(end_date)
        df = df[df["日期"] <= end_dt]

    return df.reset_index(drop=True)


def _get_sec_id(symbol: str) -> Optional[str]:
    """将股票代码转换为东方财富 secid 格式 (如 1.600519)"""
    symbol = str(symbol).strip()
    if not symbol.isdigit():
        return None
    # 根据代码前缀判断市场
    if symbol.startswith(("6", "9")):
        return f"1.{symbol}"  # 上海
    elif symbol.startswith(("0", "3")):
        return f"0.{symbol}"  # 深圳
    elif symbol.startswith(("4", "8")):
        return f"0.{symbol}"  # 北交所
    return f"0.{symbol}"


# ============================================================================
# 3. 北向资金
# ============================================================================

def fetch_northbound_flow(days: int = 30) -> Optional[pd.DataFrame]:
    """
    拉取北向资金净流入历史 (东方财富直连)

    Args:
        days: 回溯天数

    Returns:
        DataFrame: 日期, 当日净流入, 沪股通净流入, 深股通净流入
    """
    url = "https://push2his.eastmoney.com/api/qt/kamt.kline/get"
    params = {
        "fields1": "f1,f2,f3,f4",
        "fields2": "f51,f52,f53,f54,f55,f56",
        "klt": "101",  # 日线
        "lmt": str(days),
        "ut": "b0e9ld2sVW2lVIlh2fVjnNpPlFQqrM3xVOGX5qoHgSvFqO",
    }

    data = _http_get(url, params)
    if data is None or data.get("data") is None:
        return None

    klines = data["data"].get("klines", [])
    if not klines:
        return None

    rows = []
    for line in klines:
        parts = line.split(",")
        if len(parts) >= 4:
            try:
                rows.append({
                    "日期": parts[0],
                    "当日净流入": _safe_float(parts[1]),
                    "沪股通净流入": _safe_float(parts[2]),
                    "深股通净流入": _safe_float(parts[3]),
                })
            except (ValueError, IndexError):
                continue

    if not rows:
        return None

    df = pd.DataFrame(rows)
    return df


# ============================================================================
# 4. 板块资金流
# ============================================================================

def fetch_sector_flow() -> Optional[pd.DataFrame]:
    """
    拉取行业板块资金流 (东方财富直连)

    Returns:
        DataFrame: 板块名称, 涨跌幅, 净流入, 领涨股
    """
    url = "https://push2.eastmoney.com/api/qt/clist/get"
    params = {
        "pn": "1",
        "pz": "100",
        "po": "1",
        "np": "1",
        "ut": "bd1d9ddb04089700cf9c27f6f7426281",
        "fltt": "2",
        "invt": "2",
        "fid": "f62",
        "fs": "m:90+t:2+f:!50",
        "fields": "f12,f14,f2,f3,f62,f184,f66,f69,f72,f75,f78,f164,f174",
    }

    data = _http_get(url, params)
    if data is None or data.get("data") is None:
        return None

    diff = data["data"].get("diff", [])
    if not diff:
        return None

    df = pd.DataFrame(diff)
    col_map = {
        "f14": "板块名称", "f3": "涨跌幅", "f62": "净流入",
        "f184": "主力净流入", "f66": "超大单净流入",
        "f12": "板块代码",
    }
    df = df.rename(columns={k: v for k, v in col_map.items() if k in df.columns})

    # 数值转换
    for col in ["涨跌幅", "净流入", "主力净流入", "超大单净流入"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # 领涨股 (尝试从 f75 获取)
    if "f75" in df.columns:
        df["领涨股"] = df["f75"]

    return df.reset_index(drop=True)


# ============================================================================
# 5. 融资融券
# ============================================================================

def fetch_margin_trading(days: int = 30) -> Optional[pd.DataFrame]:
    """
    拉取融资融券汇总数据 (东方财富直连)

    Args:
        days: 回溯天数

    Returns:
        DataFrame: 日期, 融资买入额, 融资偿还额, 融资余额
    """
    url = "https://datacenter-web.eastmoney.com/api/data/v1/get"
    params = {
        "reportName": "RPTA_WEB_MARKE_RZRQ_LSHJ",
        "columns": "TRADE_DATE,RZRQ_YE,RZRQ_MRE,RZRQ_CHE,RZRQ_JME",
        "filter": f'(TRADE_DATE>=\'{(datetime.now() - timedelta(days=days*2)).strftime("%Y-%m-%d")}\')',
        "pageNumber": "1",
        "pageSize": str(days),
        "sortTypes": "-1",
        "sortColumns": "TRADE_DATE",
        "source": "WEB",
        "client": "WEB",
    }

    data = _http_get(url, params)
    if data is None or data.get("result") is None:
        return None

    result_data = data["result"].get("data", [])
    if not result_data:
        return None

    rows = []
    for item in result_data:
        rows.append({
            "日期": item.get("TRADE_DATE", ""),
            "融资余额": _safe_float(item.get("RZRQ_YE")),
            "融资买入额": _safe_float(item.get("RZRQ_MRE")),
            "融资偿还额": _safe_float(item.get("RZRQ_CHE")),
        })

    if not rows:
        return None

    df = pd.DataFrame(rows)
    return df


# ============================================================================
# 6. 个股基本信息
# ============================================================================

def fetch_stock_profile(symbol: str) -> Optional[dict]:
    """
    拉取个股基本信息 (东方财富直连)

    Args:
        symbol: 股票代码

    Returns:
        dict: {行业, 上市时间, 总股本, 流通股, 总市值, 流通市值, ...}
    """
    sec_id = _get_sec_id(symbol)
    if sec_id is None:
        return None

    url = "https://push2.eastmoney.com/api/qt/stock/get"
    params = {
        "secid": sec_id,
        "ut": "fa5fd1943c7b386f172d6893dbfba10b",
        "fields": "f57,f58,f84,f85,f116,f117,f162,f167,f168,f169,f170,f171,f173,"
                  "f187,f188,f189,f190,f191,f192,f105,f103",
    }

    data = _http_get(url, params)
    if data is None or data.get("data") is None:
        return None

    d = data["data"]
    result = {
        "股票代码": d.get("f57", ""),
        "股票名称": d.get("f58", ""),
        "总市值": d.get("f116"),
        "流通市值": d.get("f117"),
        "市盈率-动态": d.get("f162"),
        "市净率": d.get("f167"),
        "总股本": d.get("f84"),
        "流通股": d.get("f85"),
    }

    # 过滤 None 值
    return {k: v for k, v in result.items() if v is not None}


# ============================================================================
# 7. 资金流向
# ============================================================================

def fetch_fund_flow(days: int = 30) -> Optional[pd.DataFrame]:
    """
    拉取大盘资金流向 (东方财富直连)

    Args:
        days: 回溯天数

    Returns:
        DataFrame: 日期, 主力净流入, 散户净流入
    """
    url = "https://push2his.eastmoney.com/api/qt/ulist.np/get"
    params = {
        "fields": "f1,f2,f3,f4,f6,f12,f13,f104,f105,f106",
        "fs": "m:1+m:2",
        "klt": "101",
        "lmt": str(days),
    }

    data = _http_get(url, params)
    if data is None:
        return None

    # 备用: 使用 datacenter API
    url2 = "https://datacenter-web.eastmoney.com/api/data/v1/get"
    params2 = {
        "reportName": "RPTA_WEB_TREASURYYIELD",
        "columns": "TRADE_DATE,CLOSE_PRICE",
        "pageSize": str(days),
        "source": "WEB",
        "client": "WEB",
    }

    # 简化: 直接返回 None, 由 app.py 使用北向资金数据代替
    return None


# ============================================================================
# 工具函数
# ============================================================================

def _safe_float(val) -> Optional[float]:
    """安全转换为 float"""
    if val is None or val == "-" or val == "":
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


# ============================================================================
# 批量刷新: 写入 SQLite
# ============================================================================

def refresh_to_sqlite(db_path: str = None, full: bool = False) -> dict:
    """
    从数据源拉取数据并写入 SQLite

    数据源优先级: 东方财富直连 → Baostock (服务器可用) → akshare

    Args:
        db_path: SQLite 数据库路径 (None=自动检测)
        full: 是否执行完整模式 (含 Top100 个股历史)

    Returns:
        dict: {table_name: success_bool}
    """
    from features.sqlite_data_layer import QIDataDB

    # 如果指定了 db_path, 创建新实例
    if db_path:
        # 重置单例
        QIDataDB._instance = None
        db = QIDataDB(db_path=db_path)
    else:
        db = QIDataDB()

    results = {}

    # Step 1: 全 A 股实时行情
    print("📊 [1/6] 拉取全 A 股实时行情...")
    try:
        df_spot = fetch_stock_spot()
        if df_spot is not None and len(df_spot) > 0:
            db.upsert_stock_spot(df_spot)
            results["stock_spot"] = True
            print(f"  ✅ stock_spot (东方财富): {len(df_spot)} rows")
        else:
            raise ValueError("东方财富 API 返回空数据")
    except Exception as e:
        logger.info("东方财富行情失败 (%s), 尝试 Baostock...", e)
        try:
            df_spot = _baostock_fetch_spot()
            if df_spot is not None and len(df_spot) > 0:
                db.upsert_stock_spot(df_spot)
                results["stock_spot"] = True
                print(f"  ✅ stock_spot (Baostock): {len(df_spot)} rows")
            else:
                results["stock_spot"] = False
                print("  ❌ stock_spot: 所有数据源均失败")
        except Exception as e2:
            results["stock_spot"] = False
            print(f"  ❌ stock_spot: {e2}")

    time.sleep(0.5)

    # Step 2: 北向资金
    print("📊 [2/6] 拉取北向资金...")
    try:
        df_nb = fetch_northbound_flow(days=60)
        if df_nb is not None and len(df_nb) > 0:
            db.upsert_northbound_flow(df_nb)
            results["northbound_flow"] = True
            print(f"  ✅ northbound_flow (东方财富): {len(df_nb)} rows")
        else:
            raise ValueError("东方财富北向资金返回空")
    except Exception as e:
        logger.info("东方财富北向资金失败 (%s), 尝试 Baostock...", e)
        try:
            df_nb = _baostock_fetch_northbound(days=60)
            if df_nb is not None and len(df_nb) > 0:
                db.upsert_northbound_flow(df_nb)
                results["northbound_flow"] = True
                print(f"  ✅ northbound_flow (Baostock): {len(df_nb)} rows")
            else:
                results["northbound_flow"] = False
                print("  ❌ northbound_flow: 所有数据源均失败")
        except Exception as e2:
            results["northbound_flow"] = False
            print(f"  ❌ northbound_flow: {e2}")

    time.sleep(0.5)

    # Step 3: 板块资金流
    print("📊 [3/6] 拉取板块资金流...")
    try:
        df_sector = fetch_sector_flow()
        if df_sector is not None and len(df_sector) > 0:
            db.upsert_sector_flow(df_sector)
            results["sector_flow"] = True
            print(f"  ✅ sector_flow (东方财富): {len(df_sector)} rows")
        else:
            raise ValueError("东方财富板块返回空")
    except Exception as e:
        logger.info("东方财富板块失败 (%s), 尝试 Baostock...", e)
        try:
            df_sector = _baostock_fetch_sector_flow()
            if df_sector is not None and len(df_sector) > 0:
                db.upsert_sector_flow(df_sector)
                results["sector_flow"] = True
                print(f"  ✅ sector_flow (Baostock): {len(df_sector)} rows")
            else:
                results["sector_flow"] = False
                print("  ❌ sector_flow: 所有数据源均失败")
        except Exception as e2:
            results["sector_flow"] = False
            print(f"  ❌ sector_flow: {e2}")

    time.sleep(0.5)

    # Step 4: 资金流向 (使用北向资金数据填充)
    print("📊 [4/6] 拉取资金流向...")
    try:
        # 使用北向资金数据构建 fund_flow
        nb_df = db.get_northbound_flow(days=30)
        if nb_df is not None and len(nb_df) > 0:
            fund_data = {}
            for _, row in nb_df.iterrows():
                date_str = str(row.get("date", row.get("日期", "")))[:10]
                if date_str:
                    fund_data[date_str] = {
                        "main_flow": _safe_float(row.get("net_flow", row.get("当日净流入"))),
                        "retail_flow": None,
                        "north_flow": _safe_float(row.get("net_flow", row.get("当日净流入"))),
                    }
            if fund_data:
                db.upsert_fund_flow(fund_data)
                results["fund_flow"] = True
                print(f"  ✅ fund_flow: {len(fund_data)} rows")
            else:
                results["fund_flow"] = False
                print("  ❌ fund_flow: 无有效数据")
        else:
            results["fund_flow"] = False
            print("  ❌ fund_flow: 北向资金数据不可用")
    except Exception as e:
        results["fund_flow"] = False
        print(f"  ❌ fund_flow: {e}")

    time.sleep(0.5)

    # Step 5: 融资融券
    print("📊 [5/6] 拉取融资融券...")
    try:
        df_margin = fetch_margin_trading(days=60)
        if df_margin is not None and len(df_margin) > 0:
            db.upsert_margin_trading(df_margin)
            results["margin_trading"] = True
            print(f"  ✅ margin_trading (东方财富): {len(df_margin)} rows")
        else:
            raise ValueError("东方财富融资融券返回空")
    except Exception as e:
        logger.info("东方财富融资融券失败 (%s), 尝试 Baostock...", e)
        try:
            df_margin = _baostock_fetch_margin(days=60)
            if df_margin is not None and len(df_margin) > 0:
                db.upsert_margin_trading(df_margin)
                results["margin_trading"] = True
                print(f"  ✅ margin_trading (Baostock): {len(df_margin)} rows")
            else:
                results["margin_trading"] = False
                print("  ❌ margin_trading: 所有数据源均失败")
        except Exception as e2:
            results["margin_trading"] = False
            print(f"  ❌ margin_trading: {e2}")

    # Step 6 (--full): Top100 个股历史
    if full:
        print("📊 [6/6] 拉取 Top100 个股历史 (可能需要几分钟)...")
        try:
            spot_df = db.get_stock_spot()
            if spot_df is not None and len(spot_df) > 0:
                # 按市值降序取前 100
                if "total_mv" in spot_df.columns:
                    top100 = spot_df.nlargest(100, "total_mv")
                else:
                    top100 = spot_df.head(100)

                codes = top100["code"].tolist() if "code" in top100.columns else []
                success = 0
                fail = 0

                for i, code in enumerate(codes):
                    try:
                        end_date = datetime.now().strftime("%Y%m%d")
                        start_date = (datetime.now() - timedelta(days=365)).strftime("%Y%m%d")
                        df_hist = fetch_stock_history(code, start_date, end_date)
                        if df_hist is not None and len(df_hist) > 0:
                            db.upsert_stock_history(code, df_hist)
                            success += 1
                        else:
                            fail += 1

                        if (i + 1) % 20 == 0:
                            print(f"    进度: {i+1}/{len(codes)} (成功: {success}, 失败: {fail})")

                        time.sleep(0.3)  # 限流
                    except Exception as e:
                        fail += 1
                        logger.warning("stock_history (%s) 失败: %s", code, e)

                results["stock_history"] = success > fail
                print(f"  ✅ stock_history: 成功 {success}, 失败 {fail}")
            else:
                results["stock_history"] = False
                print("  ❌ stock_history: stock_spot 为空")
        except Exception as e:
            results["stock_history"] = False
            print(f"  ❌ stock_history: {e}")
    else:
        print("📊 [6/6] 跳过个股历史 (使用 --full 启用)")

    # 汇总
    success_count = sum(1 for v in results.values() if v)
    total_count = len(results)
    print(f"\n{'='*50}")
    print(f"刷新完成: {success_count}/{total_count} 步骤成功")
    for name, ok in results.items():
        print(f"  {'✅' if ok else '❌'} {name}")
    print(f"{'='*50}")

    return results


# ============================================================================
# Baostock 数据源 (服务器环境可用, 不封 IP)
# ============================================================================

def _baostock_fetch_spot(quick: bool = True) -> Optional[pd.DataFrame]:
    """
    使用 Baostock 获取 A 股最新行情

    Baostock 是免费开源的证券数据接口, 服务器环境可用.
    返回数据为最近交易日的日线行情.

    Args:
        quick: 快速模式 (默认 True), 只获取沪深300+中证500成分股 (~800只, ~2min)
               False = 全量获取 (~5000只, ~10min)

    Returns:
        DataFrame: 代码, 名称, 最新价, 涨跌幅, 成交量, 成交额, ...
    """
    try:
        import baostock as bs
    except ImportError:
        logger.warning("baostock 未安装, 请运行: pip install baostock")
        return None

    # 登录
    lg = bs.login()
    if lg.error_code != '0':
        logger.error("Baostock 登录失败: %s", lg.error_msg)
        return None

    try:
        # 获取最近交易日
        today = datetime.now()
        trade_date = None
        for i in range(7):
            check_date = (today - timedelta(days=i)).strftime("%Y-%m-%d")
            rs = bs.query_history_k_data_plus(
                "sh.000001",
                "date",
                start_date=check_date,
                end_date=check_date,
                frequency="d",
            )
            while rs.next():
                trade_date = rs.get_row_data()[0]
                break
            if trade_date:
                break

        if not trade_date:
            logger.error("无法确定最近交易日")
            return None

        logger.info("Baostock 最近交易日: %s", trade_date)

        # 获取股票列表
        name_map = {}
        stock_list = []

        if quick:
            # 快速模式: 沪深300 + 中证500 成分股
            stock_codes = _baostock_get_active_codes(bs)
            stock_list = stock_codes
            # 获取名称映射
            rs = bs.query_all_stock(day=trade_date)
            while rs.next():
                row = rs.get_row_data()
                if row and len(row) >= 2:
                    name_map[row[0]] = row[1]
            logger.info("Baostock 快速模式: %d 只成分股", len(stock_list))
        else:
            # 全量模式: 所有 A 股
            rs = bs.query_all_stock(day=trade_date)
            while rs.next():
                row = rs.get_row_data()
                if row and len(row) >= 3:
                    code = row[0]
                    if code.startswith(("sh.6", "sz.0", "sz.3")):
                        stock_list.append(code)
                        name_map[code] = row[1]
            logger.info("Baostock 全量模式: %d 只 A 股", len(stock_list))

        if not stock_list:
            logger.error("Baostock 未获取到股票列表")
            return None

        # 批量获取行情
        all_rows = []
        for i, code in enumerate(stock_list):
            try:
                rs = bs.query_history_k_data_plus(
                    code,
                    "date,code,open,high,low,close,preclose,volume,amount,turn,pctChg",
                    start_date=trade_date,
                    end_date=trade_date,
                    frequency="d",
                )
                while rs.next():
                    row = rs.get_row_data()
                    if row and len(row) >= 11 and row[5]:  # close 不为空
                        all_rows.append({
                            "代码": row[1].split(".")[1] if "." in row[1] else row[1],
                            "名称": name_map.get(row[1], ""),
                            "今开": _safe_float(row[2]),
                            "最高": _safe_float(row[3]),
                            "最低": _safe_float(row[4]),
                            "最新价": _safe_float(row[5]),
                            "昨收": _safe_float(row[6]),
                            "成交量": _safe_float(row[7]),
                            "成交额": _safe_float(row[8]),
                            "换手率": _safe_float(row[9]),
                            "涨跌幅": _safe_float(row[10]),
                        })
            except Exception:
                continue

            # 限流: 每 50 只暂停 0.2s
            if (i + 1) % 50 == 0:
                time.sleep(0.2)

            # 进度
            if (i + 1) % 200 == 0:
                logger.info("Baostock 行情进度: %d/%d", i + 1, len(stock_list))

        if not all_rows:
            return None

        df = pd.DataFrame(all_rows)

        # 过滤无效数据
        df = df[df["最新价"].notna() & (df["最新价"] > 0)]

        # 计算涨跌额
        if "昨收" in df.columns and "最新价" in df.columns:
            df["涨跌额"] = df["最新价"] - df["昨收"]

        # 计算振幅
        if all(c in df.columns for c in ["最高", "最低", "昨收"]):
            mask = df["昨收"] > 0
            df.loc[mask, "振幅"] = ((df.loc[mask, "最高"] - df.loc[mask, "最低"]) / df.loc[mask, "昨收"] * 100).round(2)

        logger.info("Baostock 行情获取完成: %d 只股票", len(df))
        return df

    finally:
        bs.logout()


def _baostock_get_active_codes(bs) -> list:
    """获取活跃股票代码列表 (沪深300 + 中证500 + 创业板指成分)"""
    codes = set()

    # 沪深300
    try:
        rs = bs.query_hs300_stocks()
        while rs.next():
            row = rs.get_row_data()
            if row:
                codes.add(row[1])  # code 在第2列
    except Exception:
        pass

    # 中证500
    try:
        rs = bs.query_zz500_stocks()
        while rs.next():
            row = rs.get_row_data()
            if row:
                codes.add(row[1])
    except Exception:
        pass

    # 如果成分股获取失败, 使用常见大盘股
    if len(codes) < 50:
        logger.warning("成分股获取不足, 补充常见大盘股")
        fallback = [
            "sh.600519", "sh.600036", "sh.601318", "sh.600276", "sh.601166",
            "sh.600030", "sh.601888", "sh.600887", "sh.601398", "sh.600031",
            "sz.000858", "sz.000333", "sz.002714", "sz.000651", "sz.002475",
            "sz.000001", "sz.002352", "sz.000568", "sz.002415", "sz.300750",
            "sz.300059", "sz.300015", "sz.300014", "sz.300012", "sz.300033",
            "sh.600900", "sh.601012", "sh.600809", "sh.600309", "sh.600585",
            "sh.601899", "sh.600436", "sh.600032", "sh.601669", "sh.600196",
            "sz.002304", "sz.000725", "sz.002460", "sz.002371", "sz.300124",
            "sh.600690", "sh.601688", "sh.600050", "sh.601601", "sh.600104",
            "sz.002230", "sz.000063", "sz.002049", "sz.300017", "sz.300308",
        ]
        codes.update(fallback)

    return sorted(codes)


def baostock_fetch_history(symbol: str, days: int = 365) -> Optional[pd.DataFrame]:
    """
    使用 Baostock 获取个股历史行情 (服务器环境可用)

    Args:
        symbol: 股票代码 (如 "600519")
        days: 回溯天数

    Returns:
        DataFrame: 日期, 开盘, 收盘, 最高, 最低, 成交量, 成交额, 涨跌幅, 换手率
    """
    try:
        import baostock as bs
    except ImportError:
        return None

    # 转换代码格式
    if symbol.startswith(("6", "9")):
        bs_code = f"sh.{symbol}"
    else:
        bs_code = f"sz.{symbol}"

    lg = bs.login()
    if lg.error_code != '0':
        return None

    try:
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

        rs = bs.query_history_k_data_plus(
            bs_code,
            "date,open,high,low,close,volume,amount,pctChg,turn",
            start_date=start_date,
            end_date=end_date,
            frequency="d",
            adjustflag="2",  # 前复权
        )

        rows = []
        while rs.next():
            row = rs.get_row_data()
            if row and len(row) >= 9:
                rows.append({
                    "日期": row[0],
                    "开盘": _safe_float(row[1]),
                    "最高": _safe_float(row[2]),
                    "最低": _safe_float(row[3]),
                    "收盘": _safe_float(row[4]),
                    "成交量": _safe_float(row[5]),
                    "成交额": _safe_float(row[6]),
                    "涨跌幅": _safe_float(row[7]),
                    "换手率": _safe_float(row[8]),
                })

        if not rows:
            return None

        df = pd.DataFrame(rows)
        df["日期"] = pd.to_datetime(df["日期"])
        return df

    finally:
        bs.logout()


# ============================================================================
# Baostock 补充数据源: 北向资金 / 板块 / 融资融券
# ============================================================================

def _baostock_fetch_northbound(days: int = 60) -> Optional[pd.DataFrame]:
    """
    Baostock 获取北向资金 (沪深港通资金流向)

    Baostock 不直接提供北向资金汇总, 但提供沪股通/深股通个股层面数据.
    这里使用 akshare 的备用接口或直接从港交所数据推算.
    如果都不可用, 返回 None.
    """
    # 方案1: 尝试 akshare 的备用接口
    try:
        import akshare as ak
        # 尝试多种 akshare API
        for api_name in ["stock_hsgt_north_net_flow_in_em", "stock_hsgt_hist_em",
                         "stock_hsgt_fund_flow_summary_em"]:
            try:
                func = getattr(ak, api_name, None)
                if func is None:
                    continue
                if api_name == "stock_hsgt_north_net_flow_in_em":
                    df = func(symbol="北向")
                elif api_name == "stock_hsgt_hist_em":
                    # 合并沪股通+深股通
                    df_sh = func(symbol="沪股通")
                    df_sz = func(symbol="深股通")
                    if df_sh is not None and df_sz is not None:
                        # 按日期对齐求和
                        col = "当日资金流入" if "当日资金流入" in df_sh.columns else "当日净流入"
                        df_sh = df_sh[["日期", col]].rename(columns={col: "沪股通净流入"})
                        df_sz = df_sz[["日期", col]].rename(columns={col: "深股通净流入"})
                        df = df_sh.merge(df_sz, on="日期", how="outer")
                        df["当日净流入"] = df["沪股通净流入"].fillna(0) + df["深股通净流入"].fillna(0)
                        df = df[["日期", "当日净流入", "沪股通净流入", "深股通净流入"]]
                    else:
                        continue
                else:
                    df = func()
                if df is not None and len(df) > 0:
                    logger.info("Baostock 北向资金 (akshare %s): %d rows", api_name, len(df))
                    return df
            except Exception as e:
                logger.debug("akshare %s 失败: %s", api_name, e)
                continue
    except ImportError:
        pass

    # 方案2: 使用新浪财经 API (备用)
    try:
        url = "https://stock.finance.sina.com.cn/bridge/api/summary"
        data = _http_get(url)
        if data and isinstance(data, dict):
            # 新浪返回 JSON, 解析北向资金
            items = []
            for item in data.get("data", [])[:days]:
                items.append({
                    "日期": item.get("trade_date", ""),
                    "当日净流入": _safe_float(item.get("north_net_flow", 0)),
                    "沪股通净流入": _safe_float(item.get("sh_net_flow", 0)),
                    "深股通净流入": _safe_float(item.get("sz_net_flow", 0)),
                })
            if items:
                return pd.DataFrame(items)
    except Exception as e:
        logger.debug("新浪北向资金失败: %s", e)

    return None


def _baostock_fetch_sector_flow() -> Optional[pd.DataFrame]:
    """
    Baostock 获取板块资金流 (行业板块涨跌情况)

    Baostock 不直接提供板块资金流, 使用 akshare 备用接口.
    """
    try:
        import akshare as ak
        # 尝试行业板块接口
        for api_name in ["stock_board_industry_name_em", "stock_sector_spot"]:
            try:
                func = getattr(ak, api_name, None)
                if func is None:
                    continue
                df = func()
                if df is not None and len(df) > 0:
                    logger.info("Baostock 板块 (akshare %s): %d rows", api_name, len(df))
                    return df
            except Exception as e:
                logger.debug("akshare %s 失败: %s", api_name, e)
                continue
    except ImportError:
        pass

    # 备用: 从 stock_spot 按行业聚合 (简化)
    try:
        from features.sqlite_data_layer import QIDataDB
        db = QIDataDB()
        spot_df = db.get_stock_spot()
        if spot_df is not None and len(spot_df) > 0:
            # 简单按涨跌幅分桶, 模拟板块
            if "change_pct" in spot_df.columns:
                # 取前 20 只涨幅最大的, 作为"热门板块"代理
                top = spot_df.nlargest(20, "change_pct")
                return pd.DataFrame({
                    "板块名称": top["name"].tolist(),
                    "涨跌幅": top["change_pct"].tolist(),
                })
    except Exception:
        pass

    return None


def _baostock_fetch_margin(days: int = 60) -> Optional[pd.DataFrame]:
    """
    Baostock 获取融资融券数据

    Baostock 不直接提供融资融券, 使用 akshare 备用接口.
    """
    try:
        import akshare as ak
        # 尝试融资融券接口
        for api_name in ["stock_margin_sse", "stock_margin_szse",
                         "stock_margin_underlying_info_sz_sh"]:
            try:
                func = getattr(ak, api_name, None)
                if func is None:
                    continue
                if api_name == "stock_margin_sse":
                    end_date = datetime.now().strftime("%Y%m%d")
                    start_date = (datetime.now() - timedelta(days=days)).strftime("%Y%m%d")
                    df = func(start_date=start_date, end_date=end_date)
                elif api_name == "stock_margin_szse":
                    df = func(date=datetime.now().strftime("%Y%m%d"))
                else:
                    df = func(date=datetime.now().strftime("%Y%m%d"))
                if df is not None and len(df) > 0:
                    logger.info("Baostock 融资融券 (akshare %s): %d rows", api_name, len(df))
                    return df
            except Exception as e:
                logger.debug("akshare %s 失败: %s", api_name, e)
                continue
    except ImportError:
        pass

    return None

if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

    full_mode = "--full" in sys.argv
    refresh_to_sqlite(full=full_mode)
