# -*- coding: utf-8 -*-
"""
QuantInsight Pro - QVeris 数据源适配器
======================================

通过 QVeris REST API 获取 A 股实时行情与历史 K 线，写入 SQLite 缓存。
作为东方财富 / Baostock / AKShare 的补充与兜底数据源。

配置:
    streamlit_app/.streamlit/secrets.toml  →  QVERIS_API_KEY = "sk-cn-..."
    或环境变量 QVERIS_API_KEY

用法:
    from features.qveris_source import fetch_realtime_snapshot, sync_historical_to_sqlite
    sync_historical_to_sqlite(["600519", "300750"], days=365)
"""

from __future__ import annotations

import logging
import os
import re
import time
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import requests

logger = logging.getLogger(__name__)

# 经 MCP 验证的实时行情工具 (caidazi, ~1 credit/次)
_REALTIME_TOOL_ID = "caidazi.get_real_time_record.execute.v1.7a43f96e"
# 批量实时行情 (最多 50 只/次)
_BATCH_REALTIME_TOOL_ID = "cn_financial_pro.real_time_quotation.v1"
# A 股历史日线 (cn_financial, ~1 credit/次, 最低计费)
_HISTORY_TOOL_ID = "cn_financial_pro.history_quotation.v1"

# stock_spot 为空时的默认市值龙头 (Demo / 离线兜底)
DEFAULT_TOP30_CODES: List[str] = [
    "600519", "601857", "601988", "600941", "601628", "600036", "601318", "600900",
    "601728", "600276", "601888", "600030", "601166", "601398", "600887", "603259",
    "601668", "300750", "002594", "601288", "600050", "601328", "600000", "000333",
    "002415", "601899", "600809", "300059", "601088", "000858",
]

DEFAULT_TOP100_CODES: List[str] = DEFAULT_TOP30_CODES + [
    "000001", "000002", "000063", "000100", "000568", "000596", "000625", "000651",
    "000725", "000776", "000938", "000963", "002027", "002049", "002142", "002230",
    "002241", "002304", "002352", "002371", "002714", "002736", "300014", "300015",
    "300033", "300124", "300274", "300760", "300896", "600009", "600028", "600031",
    "600048", "600089", "600104", "600111", "600150", "600196", "600346", "600406",
    "600436", "600438", "600489", "600547", "600570", "600585", "600690", "600760",
    "600893", "600905", "601006", "601066", "601138", "601211", "601225", "601319",
    "601390", "601633", "601658", "601688", "601698", "601766", "601816", "601919",
    "601939", "601985", "601995", "603019", "603288", "603501", "603799", "603986",
    "688981", "688111", "688041", "688012", "688036", "688008", "688256", "688599",
    "688303", "688187", "688169", "688396", "688126", "688223", "688777", "688561",
    "688009", "688363", "688235", "688271", "688506", "688472", "688578", "688180",
    "688082", "688349", "688617", "688728", "688187", "688385", "688516", "688520",
]
# 去重并保持顺序
DEFAULT_TOP100_CODES = list(dict.fromkeys(DEFAULT_TOP100_CODES))[:100]


def _load_hs300_codes() -> List[str]:
    """加载沪深300成分股 (优先本地缓存, 否则 akshare)"""
    cache = Path(__file__).resolve().parents[1] / "data" / "hs300_codes.txt"
    if cache.exists():
        return [ln.strip() for ln in cache.read_text(encoding="utf-8").splitlines() if ln.strip()]
    try:
        import akshare as ak
        df = ak.index_stock_cons_csindex(symbol="000300")
        codes = df["成分券代码"].astype(str).str.zfill(6).unique().tolist()
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_text("\n".join(codes), encoding="utf-8")
        return codes
    except Exception as e:
        logger.warning("获取 HS300 成分失败: %s", e)
        return DEFAULT_TOP100_CODES


def _load_zz500_codes() -> List[str]:
    """加载中证500成分股 (优先本地缓存, 否则 akshare)"""
    cache = Path(__file__).resolve().parents[1] / "data" / "zz500_codes.txt"
    if cache.exists():
        return [ln.strip() for ln in cache.read_text(encoding="utf-8").splitlines() if ln.strip()]
    try:
        import akshare as ak
        df = ak.index_stock_cons_csindex(symbol="000905")
        codes = df["成分券代码"].astype(str).str.zfill(6).unique().tolist()
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_text("\n".join(codes), encoding="utf-8")
        return codes
    except Exception as e:
        logger.warning("获取中证500成分失败: %s", e)
        return []

# discover 结果缓存 (进程内)
_tool_cache: Dict[str, Tuple[str, str]] = {}


def _secrets_paths() -> List[Path]:
    app_dir = Path(__file__).resolve().parents[1]
    return [
        app_dir / ".streamlit" / "secrets.toml",
        Path("/opt/quantinsight/.streamlit/secrets.toml"),
        Path(os.environ.get("QVERIS_SECRETS_PATH", "")),
    ]


def _read_toml_key(path: Path, key: str) -> Optional[str]:
    if not path.exists():
        return None
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return None
    m = re.search(rf'^{re.escape(key)}\s*=\s*"([^"]+)"', text, re.MULTILINE)
    return m.group(1).strip() if m else None


def resolve_api_key() -> Optional[str]:
    """从环境变量或 secrets.toml 读取 QVeris API Key"""
    key = os.environ.get("QVERIS_API_KEY", "").strip()
    if key:
        return key
    for path in _secrets_paths():
        if not path:
            continue
        val = _read_toml_key(path, "QVERIS_API_KEY")
        if val:
            return val
    return None


def is_configured() -> bool:
    key = resolve_api_key()
    return bool(key and not key.startswith("your-") and len(key) > 20)


def _base_url(api_key: str) -> str:
    if api_key.startswith("sk-cn-"):
        return "https://qveris.cn/api/v1"
    return "https://qveris.ai/api/v1"


def _to_market_symbol(code: str) -> str:
    code = str(code).strip().upper()
    if "." in code:
        return code
    digits = re.sub(r"\D", "", code)[-6:]
    if digits.startswith(("6", "5", "9")):
        return f"{digits}.SH"
    return f"{digits}.SZ"


def _bare_code(symbol: str) -> str:
    digits = re.sub(r"\D", "", str(symbol))
    if not digits:
        return ""
    return digits.zfill(6)[-6:]


class QVerisClient:
    """QVeris REST API 轻量客户端"""

    def __init__(self, api_key: Optional[str] = None, timeout: int = 30):
        self.api_key = api_key or resolve_api_key()
        if not self.api_key:
            raise RuntimeError(
                "未配置 QVERIS_API_KEY。请在 streamlit_app/.streamlit/secrets.toml "
                "或环境变量中设置。"
            )
        self.base_url = _base_url(self.api_key)
        self.timeout = timeout
        self.session_id = f"quantinsight-{datetime.now():%Y%m%d}-{uuid.uuid4().hex[:8]}"

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def discover(self, query: str, limit: int = 5) -> Dict[str, Any]:
        resp = requests.post(
            f"{self.base_url}/search",
            headers=self._headers(),
            json={"query": query, "limit": limit, "session_id": self.session_id},
            timeout=self.timeout,
        )
        resp.raise_for_status()
        return resp.json()

    def execute(
        self,
        tool_id: str,
        search_id: str,
        parameters: Dict[str, Any],
        max_response_size: int = 204800,
    ) -> Dict[str, Any]:
        resp = requests.post(
            f"{self.base_url}/tools/execute",
            params={"tool_id": tool_id},
            headers=self._headers(),
            json={
                "search_id": search_id,
                "session_id": self.session_id,
                "parameters": parameters,
                "max_response_size": max_response_size,
            },
            timeout=self.timeout,
        )
        resp.raise_for_status()
        data = resp.json()
        if not data.get("success"):
            raise RuntimeError(data.get("error_message") or "QVeris 调用失败")
        return data


def _parse_caidazi_table(text: str) -> Optional[Dict[str, Any]]:
    """解析 caidazi 返回的 Markdown 表格为 dict"""
    if not text or "|" not in text:
        return None
    lines = [ln.strip() for ln in text.splitlines() if ln.strip() and "|" in ln]
    if len(lines) < 2:
        return None
    headers = [h.strip() for h in lines[0].strip("|").split("|")]
    # 跳过分隔行
    data_line = lines[2] if len(lines) > 2 and re.match(r"^[\|\s\-]+$", lines[1]) else lines[1]
    values = [v.strip() for v in data_line.strip("|").split("|")]
    if len(values) != len(headers):
        return None
    return dict(zip(headers, values))


def _row_to_spot_dict(row: Dict[str, Any]) -> Dict[str, Any]:
    """统一转为 upsert 兼容的中文字段 dict"""
    def _f(key: str) -> Optional[float]:
        v = row.get(key)
        if v is None or v == "":
            return None
        try:
            return float(str(v).replace(",", ""))
        except (ValueError, TypeError):
            return None

    code = _bare_code(row.get("股票代码") or row.get("code") or row.get("symbol", ""))
    name = row.get("股票名称") or row.get("name") or code
    mv_wan = _f("总市值（万元）")
    total_mv = (mv_wan * 10000) if mv_wan is not None else _f("总市值")
    return {
        "代码": code,
        "名称": name,
        "最新价": _f("最新价（元）") or _f("最新价") or _f("latest_price"),
        "涨跌幅": _f("涨跌幅(%)") or _f("涨跌幅") or _f("change_pct"),
        "市盈率-动态": _f("市盈率(TTM)") or _f("pe_ttm"),
        "市净率": _f("市净率") or _f("pb"),
        "总市值": total_mv,
        "换手率": _f("换手率（%）") or _f("换手率") or _f("turnover_rate"),
        "成交额": _f("成交额（元）") or _f("成交额") or _f("amount"),
    }


def fetch_realtime_snapshot(code: str, client: Optional[QVerisClient] = None) -> Optional[Dict[str, Any]]:
    """获取单只股票实时快照"""
    if not is_configured():
        return None
    client = client or QVerisClient()
    symbol = _to_market_symbol(code)
    try:
        disc = client.discover("A股实时行情快照", limit=3)
        search_id = disc.get("search_id", "")
        tool_id = _REALTIME_TOOL_ID
        for r in disc.get("results", []):
            if "real_time" in r.get("tool_id", "") or "实时" in r.get("name", ""):
                tool_id = r["tool_id"]
                break
        data = client.execute(tool_id, search_id, {"symbol": symbol})
        result = data.get("result") or {}
        inner = result.get("data") if isinstance(result, dict) else result
        if isinstance(inner, dict):
            payload = inner.get("result") or inner.get("data") or inner
            if isinstance(payload, str):
                parsed = _parse_caidazi_table(payload)
                if parsed:
                    return _row_to_spot_dict(parsed)
            if isinstance(payload, dict):
                return _row_to_spot_dict(payload)
        return None
    except Exception as e:
        logger.warning("QVeris 实时行情失败 %s: %s", symbol, e)
        return None


def fetch_realtime_batch(codes: List[str], client: Optional[QVerisClient] = None) -> pd.DataFrame:
    """批量获取实时行情 (最多 50 只/批)"""
    if not is_configured() or not codes:
        return pd.DataFrame()
    client = client or QVerisClient()
    symbols = [_to_market_symbol(c) for c in codes[:50]]
    code_str = ",".join(symbols)
    rows: List[Dict[str, Any]] = []
    try:
        disc = client.discover("A股实时行情", limit=3)
        search_id = disc.get("search_id", "")
        data = client.execute(
            _BATCH_REALTIME_TOOL_ID,
            search_id,
            {"codes": code_str, "indicators": "common"},
            max_response_size=512000,
        )
        result = data.get("result") or {}
        payload = result.get("data") if isinstance(result, dict) else result
        items = payload if isinstance(payload, list) else payload.get("results") or payload.get("list") or []
        if isinstance(items, list):
            for item in items:
                if isinstance(item, dict):
                    rows.append(_row_to_spot_dict(item))
        # 批量失败时逐只降级
        if not rows:
            for sym in symbols:
                row = fetch_realtime_snapshot(sym, client=client)
                if row:
                    rows.append(row)
                time.sleep(0.15)
    except Exception as e:
        logger.warning("QVeris 批量实时行情失败, 逐只重试: %s", e)
        for sym in symbols:
            row = fetch_realtime_snapshot(sym, client=client)
            if row:
                rows.append(row)
            time.sleep(0.15)
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows)


def _resolve_history_tool(client: QVerisClient) -> Tuple[str, str]:
    cache_key = "history_daily"
    if cache_key in _tool_cache:
        return _tool_cache[cache_key]

    disc = client.discover("A股历史行情 日线", limit=10)
    search_id = disc.get("search_id", "")
    tool_id = _HISTORY_TOOL_ID

    for r in disc.get("results", []):
        tid = r.get("tool_id", "")
        if tid == _HISTORY_TOOL_ID or "history_quotation" in tid:
            tool_id = tid
            break
        cats = {c.get("slug", "") for c in r.get("categories", [])}
        if "china_market" in cats and "history" in cats:
            tool_id = tid
            break

    _tool_cache[cache_key] = (tool_id, search_id)
    return tool_id, search_id


def _normalize_history_df(raw: Any, code: str) -> pd.DataFrame:
    """将 QVeris 历史数据归一化为标准 OHLCV DataFrame"""
    records: List[Dict[str, Any]] = []

    def _collect(obj):
        if isinstance(obj, list):
            for item in obj:
                _collect(item)
        elif isinstance(obj, dict):
            if any(k in obj for k in ("date", "日期", "trade_date", "time", "open", "开盘", "close", "收盘")):
                records.append(obj)
            else:
                for v in obj.values():
                    _collect(v)

    _collect(raw)

    if not records:
        return pd.DataFrame()

    rows = []
    for rec in records:
        date_val = (
            rec.get("time") or rec.get("date") or rec.get("日期")
            or rec.get("trade_date") or rec.get("tradeDate")
        )
        if not date_val:
            continue
        rows.append({
            "日期": str(date_val)[:10],
            "开盘": rec.get("open") or rec.get("开盘") or rec.get("adjOpen"),
            "收盘": rec.get("close") or rec.get("收盘") or rec.get("adjClose"),
            "最高": rec.get("high") or rec.get("最高") or rec.get("adjHigh"),
            "最低": rec.get("low") or rec.get("最低") or rec.get("adjLow"),
            "成交量": rec.get("volume") or rec.get("成交量"),
            "成交额": rec.get("amount") or rec.get("成交额"),
            "涨跌幅": (
                rec.get("changeRatio") or rec.get("pct_change")
                or rec.get("涨跌幅") or rec.get("change_pct")
            ),
            "换手率": rec.get("turnoverRatio") or rec.get("turnover") or rec.get("换手率"),
        })

    df = pd.DataFrame(rows)
    if df.empty:
        return df
    df["日期"] = pd.to_datetime(df["日期"], errors="coerce")
    df = df.dropna(subset=["日期"]).sort_values("日期")
    df = df.drop_duplicates(subset=["日期"], keep="last")
    return df


def fetch_stock_history(
    code: str,
    start_date: str = "",
    end_date: str = "",
    client: Optional[QVerisClient] = None,
) -> Optional[pd.DataFrame]:
    """通过 QVeris 拉取个股历史日线"""
    if not is_configured():
        return None
    client = client or QVerisClient()
    symbol = _to_market_symbol(code)
    end_date = (end_date or datetime.now().strftime("%Y%m%d")).replace("-", "")
    start_date = (start_date or (datetime.now() - timedelta(days=365)).strftime("%Y%m%d")).replace("-", "")

    tool_id, search_id = _resolve_history_tool(client)
    symbol = _to_market_symbol(code)

    params = {
        "codes": symbol,
        "startdate": start_date,
        "enddate": end_date,
        "interval": "D",
        "cps": "6",
        "indicators": "stock_common",
    }

    try:
        data = client.execute(tool_id, search_id, params, max_response_size=2048000)
        result = data.get("result") or {}
        payload = result.get("data") if isinstance(result, dict) else result
        df = _normalize_history_df(payload, code)
        if df is not None and not df.empty:
            return df
    except Exception as e:
        logger.warning("QVeris 历史 K 线失败 %s: %s", symbol, e)

    logger.warning("QVeris 历史 K 线无数据: %s", symbol)
    return None


def sync_historical_to_sqlite(
    codes: Optional[List[str]] = None,
    days: int = 365,
    delay: float = 0.35,
    top_n: int = 100,
) -> Dict[str, Any]:
    """
    将历史 K 线写入 SQLite (适合空闲时批量跑)

    Args:
        codes: 股票代码列表; None 时从 stock_spot 取 Top N 市值
        days: 回溯天数
        delay: 每次 API 调用间隔 (秒), 避免过快消耗积分
        top_n: codes 为空时取前 N 只

    Returns:
        {"success": int, "fail": int, "skipped": bool, "errors": [...]}
    """
    from features.sqlite_data_layer import QIDataDB

    if not is_configured():
        logger.warning("QVeris 未配置, 跳过历史同步")
        return {"success": 0, "fail": 0, "skipped": True, "errors": ["QVERIS_API_KEY 未配置"]}

    db = QIDataDB()
    if not codes:
        spot = db.get_stock_spot()
        if spot is not None and not spot.empty:
            sort_col = "total_mv" if "total_mv" in spot.columns else spot.columns[0]
            codes = spot.nlargest(top_n, sort_col)["code"].astype(str).tolist()
        else:
            if top_n >= 500:
                pool = _load_zz500_codes()
                print(f"stock_spot 为空, 使用中证500成分 ({len(pool)} 只)")
            elif top_n >= 300:
                pool = _load_hs300_codes()
                print(f"stock_spot 为空, 使用沪深300成分 ({len(pool)} 只)")
            elif top_n > len(DEFAULT_TOP30_CODES):
                pool = DEFAULT_TOP100_CODES
                print(f"stock_spot 为空, 使用内置 Top100 列表")
            else:
                pool = DEFAULT_TOP30_CODES
                print(f"stock_spot 为空, 使用内置 Top30 列表")
            codes = pool[:top_n]

    end_date = datetime.now().strftime("%Y%m%d")
    start_date = (datetime.now() - timedelta(days=days)).strftime("%Y%m%d")
    client = QVerisClient()

    success = fail = skipped = 0
    errors: List[str] = []
    min_bars = max(int(days * 0.55), 180)

    print(f"QVeris 历史同步: {len(codes)} 只股票, {days} 天")
    for i, code in enumerate(codes):
        bare = _bare_code(code)
        try:
            existing = db.get_stock_history(bare, days=days + 30)
            if existing is not None and len(existing) >= min_bars:
                skipped += 1
                print(f"  [SKIP] [{i+1}/{len(codes)}] {bare}: already {len(existing)} bars")
                continue

            df = fetch_stock_history(bare, start_date, end_date, client=client)
            if df is not None and not df.empty:
                db.upsert_stock_history(bare, df)
                db._update_meta("stock_history", len(df), source="qveris")
                success += 1
                print(f"  [OK] [{i+1}/{len(codes)}] {bare}: {len(df)} bars")
            else:
                fail += 1
                errors.append(f"{bare}: no data")
                print(f"  [FAIL] [{i+1}/{len(codes)}] {bare}: no data")
        except Exception as e:
            fail += 1
            errors.append(f"{bare}: {e}")
            print(f"  [FAIL] [{i+1}/{len(codes)}] {bare}: {e}")
        if i + 1 < len(codes):
            time.sleep(delay)

    return {"success": success, "fail": fail, "skipped": skipped, "errors": errors[:20]}


def refresh_spot_to_sqlite(codes: Optional[List[str]] = None, top_n: int = 50) -> bool:
    """
    用 QVeris 更新部分实时行情 (按行 upsert, 不清空全表)

    适合东方财富全量拉取失败后的兜底, 或更新重点自选池。
    """
    from features.sqlite_data_layer import QIDataDB

    if not is_configured():
        return False

    db = QIDataDB()
    if not codes:
        spot = db.get_stock_spot()
        if spot is None or spot.empty:
            # 默认自选: 大赛 Demo 常用标的
            codes = ["600519", "300750", "601318", "000001", "600036"]
        else:
            sort_col = "total_mv" if "total_mv" in spot.columns else "code"
            codes = spot.nlargest(top_n, sort_col)["code"].astype(str).tolist()

    df = fetch_realtime_batch(codes)
    if df.empty:
        return False

    db.upsert_stock_spot_rows(df, source="qveris")
    logger.info("QVeris spot 更新 %d 行", len(df))
    return True


def refresh_to_sqlite(full: bool = False, historical_codes: Optional[List[str]] = None) -> Dict[str, bool]:
    """
    QVeris 刷新入口 (供 refresh_data.py 调用)

    full=True 时同步历史 K 线到 SQLite。
    """
    results: Dict[str, bool] = {}
    results["stock_spot_qveris"] = refresh_spot_to_sqlite()
    if full:
        hist = sync_historical_to_sqlite(codes=historical_codes)
        results["stock_history_qveris"] = hist["success"] > 0 and not hist.get("skipped")
    return results
