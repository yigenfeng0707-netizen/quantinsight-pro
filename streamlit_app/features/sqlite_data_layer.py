# -*- coding: utf-8 -*-
"""
QuantInsight Pro - SQLite 数据缓存层
======================================

轻量级 SQLite 数据层, 将金融数据本地缓存, 解决 ECS 服务器上 akshare 被封禁的问题.

设计原则:
- 单例模式, 全局共享一个数据库连接
- WAL 模式, 支持并发读写
- 自动建表, 零配置启动
- 数据过期检测, 过期返回 None 由调用方降级

版本: 1.0
日期: 2026-06-16
License: MIT
"""

from __future__ import annotations

import json
import logging
import os
import sqlite3
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import pandas as pd

logger = logging.getLogger(__name__)

# ============================================================================
# 数据库路径
# ============================================================================

_ECS_DATA_DIR = Path("/opt/quantinsight/data")
_LOCAL_DATA_DIR = Path("./data")

def _resolve_db_path() -> Path:
    """根据运行环境决定数据库路径"""
    if _ECS_DATA_DIR.parent.exists():
        db_dir = _ECS_DATA_DIR
    else:
        db_dir = _LOCAL_DATA_DIR
    db_dir.mkdir(parents=True, exist_ok=True)
    return db_dir / "qi_data.db"


# ============================================================================
# 建表 SQL
# ============================================================================

_CREATE_TABLES_SQL = """
-- 全A股实时行情
CREATE TABLE IF NOT EXISTS stock_spot (
    code        TEXT PRIMARY KEY,
    name        TEXT,
    latest_price REAL,
    change_pct  REAL,
    pe_ttm      REAL,
    pb          REAL,
    total_mv    REAL,
    turnover_rate REAL,
    amount      REAL,
    change_pct_60d REAL,
    updated_at  TEXT
);

-- 个股历史行情
CREATE TABLE IF NOT EXISTS stock_history (
    code        TEXT NOT NULL,
    date        TEXT NOT NULL,
    open        REAL,
    close       REAL,
    high        REAL,
    low         REAL,
    volume      REAL,
    amount      REAL,
    pct_change  REAL,
    turnover    REAL,
    PRIMARY KEY (code, date)
);

-- 个股基本信息
CREATE TABLE IF NOT EXISTS stock_profile (
    code        TEXT PRIMARY KEY,
    data_json   TEXT,
    updated_at  TEXT
);

-- 北向资金
CREATE TABLE IF NOT EXISTS northbound_flow (
    date        TEXT PRIMARY KEY,
    net_flow    REAL,
    sh_flow     REAL,
    sz_flow     REAL
);

-- 板块资金流
CREATE TABLE IF NOT EXISTS sector_flow (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    date        TEXT NOT NULL,
    sector_name TEXT NOT NULL,
    change_pct  REAL,
    net_flow    REAL,
    lead_stock  TEXT
);
CREATE INDEX IF NOT EXISTS idx_sector_flow_date ON sector_flow(date);

-- 宏观指数
CREATE TABLE IF NOT EXISTS macro_indices (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    date            TEXT NOT NULL,
    indicator_name  TEXT NOT NULL,
    value           REAL
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_macro_indices_uniq ON macro_indices(date, indicator_name);

-- 资金流向
CREATE TABLE IF NOT EXISTS fund_flow (
    date        TEXT PRIMARY KEY,
    main_flow   REAL,
    retail_flow REAL,
    north_flow  REAL
);

-- 融资融券
CREATE TABLE IF NOT EXISTS margin_trading (
    date        TEXT PRIMARY KEY,
    buy_amount  REAL,
    sell_amount REAL,
    balance     REAL
);

-- 数据元信息
CREATE TABLE IF NOT EXISTS data_meta (
    table_name  TEXT PRIMARY KEY,
    last_updated TEXT,
    row_count   INTEGER,
    source      TEXT
);
"""

# ============================================================================
# 数据新鲜度阈值 (分钟)
# ============================================================================

_STALE_MINUTES = {
    "stock_spot": 60,
    "stock_history": 1440,       # 24h
    "stock_profile": 1440,
    "northbound_flow": 120,
    "sector_flow": 120,
    "macro_indices": 1440,
    "fund_flow": 120,
    "margin_trading": 1440,
}


# ============================================================================
# QIDataDB - 单例 SQLite 数据库管理器
# ============================================================================

class QIDataDB:
    """
    QuantInsight SQLite 数据层 (单例)

    用法:
        db = QIDataDB()
        df = db.get_stock_spot()        # 读取缓存
        db.upsert_stock_spot(df)        # 写入缓存
        freshness = db.get_freshness("stock_spot")
    """

    _instance: Optional["QIDataDB"] = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self, db_path: Optional[str] = None):
        if self._initialized:
            return
        self._initialized = True

        if db_path:
            self._db_path = Path(db_path)
        else:
            self._db_path = _resolve_db_path()

        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._local = threading.local()
        self._init_db()

    # ------------------------------------------------------------------
    # 连接管理
    # ------------------------------------------------------------------

    def _get_conn(self) -> sqlite3.Connection:
        """获取当前线程的数据库连接 (每线程一个)"""
        conn = getattr(self._local, "conn", None)
        if conn is None:
            conn = sqlite3.connect(
                str(self._db_path),
                timeout=30,
                check_same_thread=False,
            )
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=NORMAL")
            conn.execute("PRAGMA busy_timeout=30000")
            conn.row_factory = sqlite3.Row
            self._local.conn = conn
        return conn

    def _init_db(self):
        """初始化数据库, 创建所有表"""
        conn = self._get_conn()
        conn.executescript(_CREATE_TABLES_SQL)
        conn.commit()
        logger.info(f"QIDataDB 初始化完成: {self._db_path}")

    def close(self):
        """关闭当前线程的连接"""
        conn = getattr(self._local, "conn", None)
        if conn is not None:
            conn.close()
            self._local.conn = None

    # ------------------------------------------------------------------
    # 通用工具
    # ------------------------------------------------------------------

    def _now_iso(self) -> str:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def _update_meta(self, table_name: str, row_count: int, source: str = "akshare"):
        """更新 data_meta 表"""
        conn = self._get_conn()
        conn.execute(
            """INSERT INTO data_meta (table_name, last_updated, row_count, source)
               VALUES (?, ?, ?, ?)
               ON CONFLICT(table_name) DO UPDATE SET
                   last_updated=excluded.last_updated,
                   row_count=excluded.row_count,
                   source=excluded.source
            """,
            (table_name, self._now_iso(), row_count, source),
        )
        conn.commit()

    # ==================================================================
    # Read 方法 (供 app.py 调用)
    # ==================================================================

    def get_stock_spot(self) -> Optional[pd.DataFrame]:
        """读取全A股实时行情缓存

        Returns:
            DataFrame 或 None (数据为空时返回 None)

        V3.13: 移除表级新鲜度检查, 避免数据过期后所有功能都不可用
        """
        conn = self._get_conn()
        try:
            df = pd.read_sql("SELECT * FROM stock_spot ORDER BY total_mv DESC", conn)
        except Exception as e:
            logger.warning("读取 stock_spot 失败: %s", e)
            return None

        if df.empty:
            return None
        return df

    def get_stock_history(self, code: str, days: int = 365) -> Optional[pd.DataFrame]:
        """读取个股历史行情

        Args:
            code: 股票代码 (如 600519)
            days: 回溯天数

        Returns:
            DataFrame 或 None
        """
        # V3.11: 移除表级新鲜度检查, 改为按 code 检查数据是否存在
        # 如果表中有该股票的数据就直接返回, 不再因整表过期而返回 None
        start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        conn = self._get_conn()
        try:
            df = pd.read_sql(
                "SELECT * FROM stock_history WHERE code = ? AND date >= ? ORDER BY date",
                conn,
                params=(code, start_date),
            )
        except Exception as e:
            logger.warning("读取 stock_history 失败 (%s): %s", code, e)
            return None

        if df.empty:
            return None
        return df

    def get_stock_profile(self, code: str) -> Optional[dict]:
        """读取个股基本信息

        Args:
            code: 股票代码

        Returns:
            dict 或 None
        """
        conn = self._get_conn()
        try:
            row = conn.execute(
                "SELECT data_json FROM stock_profile WHERE code = ?",
                (code,),
            ).fetchone()
        except Exception as e:
            logger.warning("读取 stock_profile 失败 (%s): %s", code, e)
            return None

        if row is None:
            return None
        try:
            return json.loads(row["data_json"])
        except (json.JSONDecodeError, KeyError):
            return None

    def get_northbound_flow(self, days: int = 30) -> Optional[pd.DataFrame]:
        """读取北向资金数据

        Args:
            days: 回溯天数

        Returns:
            DataFrame 或 None
        """
        start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        conn = self._get_conn()
        try:
            df = pd.read_sql(
                "SELECT * FROM northbound_flow WHERE date >= ? ORDER BY date",
                conn,
                params=(start_date,),
            )
        except Exception as e:
            logger.warning("读取 northbound_flow 失败: %s", e)
            return None

        if df.empty:
            return None
        return df

    def get_sector_flow(self) -> Optional[pd.DataFrame]:
        """读取板块资金流数据

        Returns:
            DataFrame 或 None
        """
        conn = self._get_conn()
        try:
            df = pd.read_sql(
                "SELECT * FROM sector_flow ORDER BY date DESC, net_flow ASC",
                conn,
            )
        except Exception as e:
            logger.warning("读取 sector_flow 失败: %s", e)
            return None

        if df.empty:
            return None
        return df

    def get_macro_indices(self) -> Optional[dict]:
        """读取宏观指数数据

        Returns:
            {indicator_name: {date: value, ...}, ...} 或 None
        """
        conn = self._get_conn()
        try:
            rows = conn.execute(
                "SELECT date, indicator_name, value FROM macro_indices ORDER BY date"
            ).fetchall()
        except Exception as e:
            logger.warning("读取 macro_indices 失败: %s", e)
            return None

        if not rows:
            return None

        result: dict = {}
        for row in rows:
            name = row["indicator_name"]
            if name not in result:
                result[name] = {}
            result[name][row["date"]] = row["value"]
        return result

    def get_fund_flow(self) -> Optional[dict]:
        """读取资金流向数据

        Returns:
            {date: {main_flow, retail_flow, north_flow}, ...} 或 None
        """
        conn = self._get_conn()
        try:
            rows = conn.execute(
                "SELECT date, main_flow, retail_flow, north_flow FROM fund_flow ORDER BY date"
            ).fetchall()
        except Exception as e:
            logger.warning("读取 fund_flow 失败: %s", e)
            return None

        if not rows:
            return None

        result: dict = {}
        for row in rows:
            result[row["date"]] = {
                "main_flow": row["main_flow"],
                "retail_flow": row["retail_flow"],
                "north_flow": row["north_flow"],
            }
        return result

    def get_margin_trading(self) -> Optional[pd.DataFrame]:
        """读取融资融券数据

        Returns:
            DataFrame 或 None
        """
        conn = self._get_conn()
        try:
            df = pd.read_sql(
                "SELECT * FROM margin_trading ORDER BY date",
                conn,
            )
        except Exception as e:
            logger.warning("读取 margin_trading 失败: %s", e)
            return None

        if df.empty:
            return None
        return df

    def get_freshness(self, table_name: str) -> dict:
        """查询数据新鲜度

        Args:
            table_name: 表名

        Returns:
            {"last_updated": str|None, "row_count": int|None, "age_minutes": float|None}
        """
        conn = self._get_conn()
        try:
            row = conn.execute(
                "SELECT last_updated, row_count FROM data_meta WHERE table_name = ?",
                (table_name,),
            ).fetchone()
        except Exception as e:
            logger.warning("读取 data_meta 失败 (%s): %s", table_name, e)
            return {"last_updated": None, "row_count": None, "age_minutes": None}

        if row is None:
            return {"last_updated": None, "row_count": None, "age_minutes": None}

        last_updated_str = row["last_updated"]
        row_count = row["row_count"]

        age_minutes = None
        if last_updated_str:
            try:
                last_updated = datetime.strptime(last_updated_str, "%Y-%m-%d %H:%M:%S")
                age_minutes = (datetime.now() - last_updated).total_seconds() / 60.0
            except ValueError:
                pass

        return {
            "last_updated": last_updated_str,
            "row_count": row_count,
            "age_minutes": age_minutes,
        }

    # ==================================================================
    # Write 方法 (供 refresh_data.py 调用)
    # ==================================================================

    def upsert_stock_spot(self, df: pd.DataFrame):
        """批量写入全A股实时行情 (全量替换)

        Args:
            df: 包含 akshare stock_zh_a_spot_em 原始列的 DataFrame
        """
        if df is None or df.empty:
            logger.warning("upsert_stock_spot: 空数据, 跳过")
            return

        now = self._now_iso()
        conn = self._get_conn()

        # 列映射: akshare 列名 → 数据库列名
        col_map = {
            "代码": "code",
            "名称": "name",
            "最新价": "latest_price",
            "涨跌幅": "change_pct",
            "市盈率-动态": "pe_ttm",
            "市净率": "pb",
            "总市值": "total_mv",
            "换手率": "turnover_rate",
            "成交额": "amount",
            "60日涨跌幅": "change_pct_60d",
        }

        # 构建写入 DataFrame
        write_df = pd.DataFrame()
        for src_col, dst_col in col_map.items():
            if src_col in df.columns:
                write_df[dst_col] = df[src_col].values
            else:
                write_df[dst_col] = None
        write_df["updated_at"] = now

        # 数据清洗: 过滤无效数据
        # 1. 代码必须为 6 位数字
        if "code" in write_df.columns:
            write_df = write_df[write_df["code"].astype(str).str.match(r"^\d{6}$", na=False)]
        # 2. 最新价必须 > 0
        if "latest_price" in write_df.columns:
            write_df = write_df[
                write_df["latest_price"].notna() &
                (write_df["latest_price"] > 0)
            ]
        # 3. 名称不能为空或单字符 (脏数据)
        if "name" in write_df.columns:
            write_df = write_df[
                write_df["name"].notna() &
                (write_df["name"].astype(str).str.len() >= 2)
            ]

        if write_df.empty:
            logger.warning("upsert_stock_spot: 清洗后无有效数据, 跳过")
            return

        # 全量替换: 先清空再写入
        try:
            conn.execute("DELETE FROM stock_spot")
            write_df.to_sql("stock_spot", conn, if_exists="append", index=False)
            conn.commit()
            self._update_meta("stock_spot", len(write_df))
            logger.info("upsert_stock_spot: 写入 %d 行", len(write_df))
        except Exception as e:
            conn.rollback()
            logger.error("upsert_stock_spot 失败: %s", e)
            raise

    def upsert_stock_history(self, code: str, df: pd.DataFrame):
        """追加写入个股历史行情 (跳过重复日期)

        Args:
            code: 股票代码
            df: 包含 OHLCV 数据的 DataFrame
        """
        if df is None or df.empty:
            return

        conn = self._get_conn()

        # V3.11: 同时支持中文和英文列名映射
        col_map = {
            # 中文列名 (akshare 东方财富源)
            "日期": "date",
            "开盘": "open",
            "收盘": "close",
            "最高": "high",
            "最低": "low",
            "成交量": "volume",
            "成交额": "amount",
            "涨跌幅": "pct_change",
            "换手率": "turnover",
            # 英文列名 (Baostock / akshare 新浪源)
            "date": "date",
            "open": "open",
            "close": "close",
            "high": "high",
            "low": "low",
            "volume": "volume",
            "amount": "amount",
            "pct_change": "pct_change",
            "turnover": "turnover",
        }

        write_df = pd.DataFrame()
        for src_col, dst_col in col_map.items():
            if src_col in df.columns and dst_col not in write_df.columns:
                write_df[dst_col] = df[src_col].values
        # 确保所有必要列都存在
        for col in ["date", "open", "close", "high", "low", "volume", "amount", "pct_change", "turnover"]:
            if col not in write_df.columns:
                write_df[col] = None
        write_df["code"] = code

        # 确保日期为字符串
        if "date" in write_df.columns:
            write_df["date"] = write_df["date"].astype(str)

        try:
            # 获取已有日期
            existing = conn.execute(
                "SELECT date FROM stock_history WHERE code = ?", (code,)
            ).fetchall()
            existing_dates = {row["date"] for row in existing}

            # 过滤掉已存在的日期
            new_rows = write_df[~write_df["date"].isin(existing_dates)]
            if new_rows.empty:
                logger.debug("upsert_stock_history (%s): 无新数据", code)
                return

            new_rows.to_sql("stock_history", conn, if_exists="append", index=False)
            conn.commit()

            total = conn.execute(
                "SELECT COUNT(*) as cnt FROM stock_history WHERE code = ?", (code,)
            ).fetchone()["cnt"]
            self._update_meta("stock_history", total)
            logger.info("upsert_stock_history (%s): 追加 %d 行", code, len(new_rows))
        except Exception as e:
            conn.rollback()
            logger.error("upsert_stock_history 失败 (%s): %s", code, e)
            raise

    def upsert_stock_profile(self, code: str, data_json: str):
        """写入/更新个股基本信息

        Args:
            code: 股票代码
            data_json: JSON 字符串
        """
        now = self._now_iso()
        conn = self._get_conn()
        try:
            conn.execute(
                """INSERT INTO stock_profile (code, data_json, updated_at)
                   VALUES (?, ?, ?)
                   ON CONFLICT(code) DO UPDATE SET
                       data_json=excluded.data_json,
                       updated_at=excluded.updated_at
                """,
                (code, data_json, now),
            )
            conn.commit()
            logger.debug("upsert_stock_profile (%s): 完成", code)
        except Exception as e:
            conn.rollback()
            logger.error("upsert_stock_profile 失败 (%s): %s", code, e)
            raise

    def upsert_northbound_flow(self, df: pd.DataFrame):
        """追加写入北向资金数据 (跳过重复日期)

        Args:
            df: 包含北向资金数据的 DataFrame
        """
        if df is None or df.empty:
            return

        conn = self._get_conn()

        col_map = {
            "日期": "date",
            "当日净流入": "net_flow",
            "沪股通净流入": "sh_flow",
            "深股通净流入": "sz_flow",
        }

        # 也尝试英文名映射
        alt_col_map = {
            "date": "date",
            "north_net": "net_flow",
            "sh_net": "sh_flow",
            "sz_net": "sz_flow",
        }

        write_df = pd.DataFrame()
        mapped = False
        for src_col, dst_col in col_map.items():
            if src_col in df.columns:
                write_df[dst_col] = df[src_col].values
                mapped = True

        if not mapped:
            for src_col, dst_col in alt_col_map.items():
                if src_col in df.columns:
                    write_df[dst_col] = df[src_col].values

        # 确保必要的列存在
        for col in ["date", "net_flow", "sh_flow", "sz_flow"]:
            if col not in write_df.columns:
                write_df[col] = None

        if "date" in write_df.columns:
            write_df["date"] = write_df["date"].astype(str)

        try:
            existing = conn.execute("SELECT date FROM northbound_flow").fetchall()
            existing_dates = {row["date"] for row in existing}

            new_rows = write_df[~write_df["date"].isin(existing_dates)]
            if new_rows.empty:
                logger.debug("upsert_northbound_flow: 无新数据")
                return

            new_rows[["date", "net_flow", "sh_flow", "sz_flow"]].to_sql(
                "northbound_flow", conn, if_exists="append", index=False
            )
            conn.commit()

            total = conn.execute("SELECT COUNT(*) as cnt FROM northbound_flow").fetchone()["cnt"]
            self._update_meta("northbound_flow", total)
            logger.info("upsert_northbound_flow: 追加 %d 行", len(new_rows))
        except Exception as e:
            conn.rollback()
            logger.error("upsert_northbound_flow 失败: %s", e)
            raise

    def upsert_sector_flow(self, df: pd.DataFrame):
        """替换今日板块资金流数据

        Args:
            df: 包含板块资金流数据的 DataFrame
        """
        if df is None or df.empty:
            return

        today = datetime.now().strftime("%Y-%m-%d")
        conn = self._get_conn()

        col_map = {
            "板块名称": "sector_name",
            "涨跌幅": "change_pct",
            "净流入": "net_flow",
            "领涨股": "lead_stock",
        }

        alt_col_map = {
            "sector_name": "sector_name",
            "change_pct": "change_pct",
            "net_amount": "net_flow",
            "lead_stock": "lead_stock",
        }

        write_df = pd.DataFrame()
        mapped = False
        for src_col, dst_col in col_map.items():
            if src_col in df.columns:
                write_df[dst_col] = df[src_col].values
                mapped = True

        if not mapped:
            for src_col, dst_col in alt_col_map.items():
                if src_col in df.columns:
                    write_df[dst_col] = df[src_col].values

        for col in ["sector_name", "change_pct", "net_flow", "lead_stock"]:
            if col not in write_df.columns:
                write_df[col] = None

        write_df["date"] = today

        try:
            conn.execute("DELETE FROM sector_flow WHERE date = ?", (today,))
            write_df[["date", "sector_name", "change_pct", "net_flow", "lead_stock"]].to_sql(
                "sector_flow", conn, if_exists="append", index=False
            )
            conn.commit()

            total = conn.execute("SELECT COUNT(*) as cnt FROM sector_flow").fetchone()["cnt"]
            self._update_meta("sector_flow", total)
            logger.info("upsert_sector_flow: 写入 %d 行 (日期: %s)", len(write_df), today)
        except Exception as e:
            conn.rollback()
            logger.error("upsert_sector_flow 失败: %s", e)
            raise

    def upsert_fund_flow(self, data: dict):
        """写入/更新资金流向数据

        Args:
            data: {date: {main_flow, retail_flow, north_flow}, ...}
        """
        if not data:
            return

        conn = self._get_conn()
        now = self._now_iso()

        try:
            for date_str, values in data.items():
                conn.execute(
                    """INSERT INTO fund_flow (date, main_flow, retail_flow, north_flow)
                       VALUES (?, ?, ?, ?)
                       ON CONFLICT(date) DO UPDATE SET
                           main_flow=excluded.main_flow,
                           retail_flow=excluded.retail_flow,
                           north_flow=excluded.north_flow
                    """,
                    (
                        str(date_str),
                        values.get("main_flow"),
                        values.get("retail_flow"),
                        values.get("north_flow"),
                    ),
                )
            conn.commit()

            total = conn.execute("SELECT COUNT(*) as cnt FROM fund_flow").fetchone()["cnt"]
            self._update_meta("fund_flow", total)
            logger.info("upsert_fund_flow: 写入 %d 条", len(data))
        except Exception as e:
            conn.rollback()
            logger.error("upsert_fund_flow 失败: %s", e)
            raise

    def upsert_margin_trading(self, df: pd.DataFrame):
        """追加写入融资融券数据 (跳过重复日期)

        Args:
            df: 包含融资融券数据的 DataFrame
        """
        if df is None or df.empty:
            return

        conn = self._get_conn()

        col_map = {
            "日期": "date",
            "融资买入额": "buy_amount",
            "融资偿还额": "sell_amount",
            "融资余额": "balance",
        }

        alt_col_map = {
            "date": "date",
            "buy_amount": "buy_amount",
            "sell_amount": "sell_amount",
            "balance": "balance",
        }

        write_df = pd.DataFrame()
        mapped = False
        for src_col, dst_col in col_map.items():
            if src_col in df.columns:
                write_df[dst_col] = df[src_col].values
                mapped = True

        if not mapped:
            for src_col, dst_col in alt_col_map.items():
                if src_col in df.columns:
                    write_df[dst_col] = df[src_col].values

        for col in ["date", "buy_amount", "sell_amount", "balance"]:
            if col not in write_df.columns:
                write_df[col] = None

        if "date" in write_df.columns:
            write_df["date"] = write_df["date"].astype(str)

        try:
            existing = conn.execute("SELECT date FROM margin_trading").fetchall()
            existing_dates = {row["date"] for row in existing}

            new_rows = write_df[~write_df["date"].isin(existing_dates)]
            if new_rows.empty:
                logger.debug("upsert_margin_trading: 无新数据")
                return

            new_rows[["date", "buy_amount", "sell_amount", "balance"]].to_sql(
                "margin_trading", conn, if_exists="append", index=False
            )
            conn.commit()

            total = conn.execute("SELECT COUNT(*) as cnt FROM margin_trading").fetchone()["cnt"]
            self._update_meta("margin_trading", total)
            logger.info("upsert_margin_trading: 追加 %d 行", len(new_rows))
        except Exception as e:
            conn.rollback()
            logger.error("upsert_margin_trading 失败: %s", e)
            raise

    def upsert_macro_indices(self, data: dict):
        """写入/更新宏观指数数据

        V3.11 新增: 补充 macro_indices 表数据

        Args:
            data: {indicator_name: {date: value, ...}, ...}
                  或 {date: {indicator_name: value, ...}, ...}
        """
        if not data:
            return

        conn = self._get_conn()
        now = self._now_iso()
        rows_to_upsert = []

        # 兼容两种格式
        for key, val in data.items():
            if isinstance(val, dict):
                # 格式1: {indicator_name: {date: value}}
                indicator_name = key
                for date_str, value in val.items():
                    if value is not None:
                        try:
                            rows_to_upsert.append((str(date_str), indicator_name, float(value)))
                        except (ValueError, TypeError):
                            pass
            elif isinstance(val, (int, float)):
                # 格式2: {indicator_name: value} (当日数据)
                today = datetime.now().strftime("%Y-%m-%d")
                try:
                    rows_to_upsert.append((today, key, float(val)))
                except (ValueError, TypeError):
                    pass

        if not rows_to_upsert:
            logger.warning("upsert_macro_indices: 无有效数据")
            return

        try:
            for date_str, indicator_name, value in rows_to_upsert:
                conn.execute(
                    """INSERT INTO macro_indices (date, indicator_name, value)
                       VALUES (?, ?, ?)
                       ON CONFLICT(date, indicator_name) DO UPDATE SET
                           value=excluded.value
                    """,
                    (date_str, indicator_name, value),
                )
            conn.commit()

            total = conn.execute("SELECT COUNT(*) as cnt FROM macro_indices").fetchone()["cnt"]
            self._update_meta("macro_indices", total)
            logger.info("upsert_macro_indices: 写入 %d 条指标", len(rows_to_upsert))
        except Exception as e:
            conn.rollback()
            logger.error("upsert_macro_indices 失败: %s", e)
            raise
