"""
QuantInsight Pro - 东方财富 Choice 数据源
==========================================

基于 akshare 封装的东方财富数据接口, 提供 A 股全量数据:
- 实时行情 (全 A 股 spot)
- 个股历史 OHLCV
- 财务报表 (业绩报表 / 利润表 / 资产负债表 / 现金流量表)
- 资金流向 (主力资金 / 北向持仓 / 板块资金)
- 估值对比
- 宏观经济 (GDP / CPI / PMI / M2)
- 股评/研报评分

版本: 2.0
日期: 2026-06-13
License: MIT
"""

from __future__ import annotations

import logging
import time
from typing import Optional

import numpy as np
import pandas as pd

from data_pipeline import DataSource, DataSourceError, NetworkError, DataValidationError

__version__ = "2.0.0"
logger = logging.getLogger(__name__)

ASHARE_SYSTEM_GUARD = (
    "仅分析中国 A 股市场，禁止引用美股/欧股/日经/费城半导体等海外指标；"
    "宏观数据须用中国 PMI/CPI/社融等，新闻须来自 A 股/国内财经来源。"
)


def _extract_macro_value(df, value_hints, valid_range=None):
    """从 akshare 宏观表提取最新有效数值（避免误取日期/索引列）。"""
    if df is None or len(df) == 0:
        return None
    row = df.iloc[-1]
    skip_cols = ("日期", "月份", "时间", "商品", "date", "month")
    for col in df.columns:
        cs = str(col)
        if any(s in cs for s in skip_cols):
            continue
        if any(h in cs for h in value_hints):
            v = pd.to_numeric(row[col], errors="coerce")
            if pd.notna(v):
                if valid_range and not (valid_range[0] <= float(v) <= valid_range[1]):
                    continue
                return f"{float(v):.2f}".rstrip("0").rstrip(".")
    for col in df.columns:
        cs = str(col)
        if any(s in cs for s in skip_cols):
            continue
        v = pd.to_numeric(row[col], errors="coerce")
        if pd.notna(v):
            fv = float(v)
            if valid_range and not (valid_range[0] <= fv <= valid_range[1]):
                continue
            return f"{fv:.2f}".rstrip("0").rstrip(".")
    return None


class EastMoneyChoiceSource(DataSource):
    """
    东方财富 Choice 数据源 (通过 akshare 封装)

    覆盖:
    - 实时行情: stock_zh_a_spot_em
    - 个股历史: stock_zh_a_hist
    - 财务报表: stock_yjbb_em / stock_lrb_em / stock_zcfz_em / stock_xjll_em
    - 资金流向: stock_individual_fund_flow_rank / stock_hsgt_hold_stock_em
    - 估值: stock_zh_valuation_comparison_em
    - 宏观: macro_china_gdp / macro_china_cpi / macro_china_pmi / macro_china_money_supply
    - 股评: stock_comment_detail_zhpj_lspf_em

    优势: 数据全面, 免费 (akshare 封装), 东方财富原生数据质量高
    局限: akshare 限流 (5 req/s 推荐), 部分接口不稳定
    """

    def __init__(self, rate_limit: int = 5):
        super().__init__(rate_limit=rate_limit, name="eastmoney_choice")
        self._ak = None

    def _import_ak(self):
        """懒加载 akshare"""
        if self._ak is None:
            try:
                import akshare as ak
                self._ak = ak
            except ImportError:
                raise DataSourceError("akshare 未安装, 请运行: pip install akshare")
        return self._ak

    # ========================================================================
    # DataSource ABC 实现 (向后兼容)
    # ========================================================================

    def fetch_index(self, symbol: str, start: str, end: str) -> pd.DataFrame:
        """拉取指数数据 (兼容旧接口)"""
        self._throttle()
        ak = self._import_ak()

        symbol_map = {
            "hs300": "sh000300",
            "zz500": "sh000905",
            "cyb": "sz399006",
            "sz50": "sh000016",
            "zz1000": "sh000852",
        }
        full_symbol = symbol_map.get(symbol.lower(), symbol)

        try:
            df = ak.stock_zh_index_daily(symbol=full_symbol)
        except Exception as e:
            raise NetworkError(f"拉取指数 {full_symbol} 失败: {e}")

        if "date" in df.columns and "close" in df.columns:
            df = df[["date", "close"]].copy()
        elif "日期" in df.columns and "收盘" in df.columns:
            df = df.rename(columns={"日期": "date", "收盘": "close"})[["date", "close"]].copy()
        else:
            raise DataValidationError(f"返回字段不匹配: {df.columns.tolist()}")

        df["date"] = pd.to_datetime(df["date"])
        df = df[(df["date"] >= start) & (df["date"] <= end)].reset_index(drop=True)
        return df

    def fetch_sw_industries(self) -> pd.DataFrame:
        """拉取申万三级行业列表"""
        self._throttle()
        ak = self._import_ak()
        try:
            df = ak.sw_index_third_info()
        except Exception as e:
            raise NetworkError(f"拉取申万行业失败: {e}")
        if df is None or len(df) == 0:
            raise DataValidationError("申万行业数据为空")
        return df

    def fetch_industry_constituents(self, industry_code: str) -> pd.DataFrame:
        """拉取行业成分股"""
        self._throttle()
        ak = self._import_ak()
        try:
            df = ak.stock_board_industry_cons_em(symbol=industry_code)
        except Exception as e:
            raise NetworkError(f"拉取行业 {industry_code} 成分股失败: {e}")
        if df is None or len(df) == 0:
            raise DataValidationError(f"行业 {industry_code} 成分股为空")
        return df

    # ========================================================================
    # 东方财富 Choice 扩展接口
    # ========================================================================

    def fetch_stock_universe(self, top_n: int = 0) -> pd.DataFrame:
        """
        拉取全 A 股实时行情 (东方财富)

        返回字段: 代码, 名称, 最新价, 涨跌幅, 涨跌额, 成交量, 成交额,
                  振幅, 最高, 最低, 今开, 昨收, 量比, 换手率,
                  市盈率-动态, 市净率, 总市值, 流通市值, 60日涨跌幅

        Args:
            top_n: 返回前 N 只 (0=全部)
        """
        self._throttle()
        ak = self._import_ak()
        try:
            df = ak.stock_zh_a_spot_em()
        except Exception as e:
            raise NetworkError(f"拉取全A股行情失败: {e}")

        if df is None or len(df) == 0:
            raise DataValidationError("全A股行情为空")

        # 过滤 ST 和退市股
        if "名称" in df.columns:
            df = df[~df["名称"].str.contains("ST|退市", na=False)]

        if top_n > 0:
            df = df.head(top_n)

        return df.reset_index(drop=True)

    def fetch_stock_history(
        self,
        symbol: str,
        start: str = "20200101",
        end: str = "",
        period: str = "daily",
        adjust: str = "qfq",
    ) -> pd.DataFrame:
        """
        拉取个股历史 OHLCV (东方财富)

        Args:
            symbol: 股票代码 (如 "600519")
            start: 开始日期 "YYYYMMDD"
            end: 结束日期 "YYYYMMDD" (空=今天)
            period: "daily" / "weekly" / "monthly"
            adjust: "qfq" (前复权) / "hfq" (后复权) / "" (不复权)

        Returns:
            DataFrame: date, open, close, high, low, volume, amount, amplitude, pct_change, change, turnover
        """
        self._throttle()
        ak = self._import_ak()
        try:
            df = ak.stock_zh_a_hist(
                symbol=symbol,
                period=period,
                start_date=start,
                end_date=end if end else None,
                adjust=adjust,
            )
        except Exception as e:
            raise NetworkError(f"拉取个股 {symbol} 历史数据失败: {e}")

        if df is None or len(df) == 0:
            raise DataValidationError(f"个股 {symbol} 历史数据为空")

        # 标准化列名 (东方财富返回中文列名)
        col_map = {
            "日期": "date", "开盘": "open", "收盘": "close",
            "最高": "high", "最低": "low", "成交量": "volume",
            "成交额": "amount", "振幅": "amplitude",
            "涨跌幅": "pct_change", "涨跌额": "change", "换手率": "turnover",
        }
        df = df.rename(columns=col_map)

        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"])
            df = df.sort_values("date").reset_index(drop=True)

        return df

    def fetch_stock_profile(self, symbol: str) -> dict:
        """
        拉取个股基本信息 (东方财富)

        Returns:
            dict: 公司基本信息 (行业, 上市日期, 注册资本 等)
        """
        self._throttle()
        ak = self._import_ak()
        try:
            df = ak.stock_individual_info_em(symbol=symbol)
        except Exception as e:
            raise NetworkError(f"拉取个股 {symbol} 信息失败: {e}")

        if df is None or len(df) == 0:
            return {}

        # 转为 dict (item -> value)
        result = {}
        for _, row in df.iterrows():
            key = row.iloc[0] if len(row) > 0 else ""
            val = row.iloc[1] if len(row) > 1 else ""
            result[str(key)] = val
        return result

    # ========================================================================
    # 财务报表接口
    # ========================================================================

    def fetch_earnings_report(self, date: str = "20240930") -> pd.DataFrame:
        """
        拉取业绩报表 (东方财富 stock_yjbb_em)

        Args:
            date: 报告期 "YYYYMMDD" (如 "20240930", "20240630")

        Returns:
            DataFrame: 股票代码, 名称, 每股收益, 营收, 净利润 等
        """
        self._throttle()
        ak = self._import_ak()
        try:
            df = ak.stock_yjbb_em(date=date)
        except Exception as e:
            raise NetworkError(f"拉取业绩报表 {date} 失败: {e}")

        if df is None or len(df) == 0:
            raise DataValidationError(f"业绩报表 {date} 为空")
        return df

    def fetch_income_statement(self, date: str = "20240930") -> pd.DataFrame:
        """拉取利润表 (东方财富 stock_lrb_em)"""
        self._throttle()
        ak = self._import_ak()
        try:
            df = ak.stock_lrb_em(date=date)
        except Exception as e:
            raise NetworkError(f"拉取利润表 {date} 失败: {e}")
        if df is None or len(df) == 0:
            raise DataValidationError(f"利润表 {date} 为空")
        return df

    def fetch_balance_sheet(self, date: str = "20240930") -> pd.DataFrame:
        """拉取资产负债表 (东方财富 stock_zcfz_em)"""
        self._throttle()
        ak = self._import_ak()
        try:
            df = ak.stock_zcfz_em(date=date)
        except Exception as e:
            raise NetworkError(f"拉取资产负债表 {date} 失败: {e}")
        if df is None or len(df) == 0:
            raise DataValidationError(f"资产负债表 {date} 为空")
        return df

    def fetch_cashflow_statement(self, date: str = "20240930") -> pd.DataFrame:
        """拉取现金流量表 (东方财富 stock_xjll_em)"""
        self._throttle()
        ak = self._import_ak()
        try:
            df = ak.stock_xjll_em(date=date)
        except Exception as e:
            raise NetworkError(f"拉取现金流量表 {date} 失败: {e}")
        if df is None or len(df) == 0:
            raise DataValidationError(f"现金流量表 {date} 为空")
        return df

    # ========================================================================
    # 资金流向接口
    # ========================================================================

    def fetch_fund_flow_rank(self, indicator: str = "今日") -> pd.DataFrame:
        """
        拉取个股资金流向排名 (东方财富)

        Args:
            indicator: "今日" / "3日" / "5日" / "10日"

        Returns:
            DataFrame: 代码, 名称, 最新价, 涨跌幅, 主力净流入, 超大单净流入 等
        """
        self._throttle()
        ak = self._import_ak()
        try:
            df = ak.stock_individual_fund_flow_rank(indicator=indicator)
        except Exception as e:
            raise NetworkError(f"拉取资金流向排名 ({indicator}) 失败: {e}")

        if df is None or len(df) == 0:
            raise DataValidationError(f"资金流向排名 ({indicator}) 为空")
        return df

    def fetch_northbound_holdings(
        self, market: str = "北向", indicator: str = "今日排行"
    ) -> pd.DataFrame:
        """
        拉取北向资金持仓 (东方财富)

        Args:
            market: "北向" / "沪股通" / "深股通"
            indicator: "今日排行" / "5日排行" / "10日排行" / "月排行" / "季排行"
        """
        self._throttle()
        ak = self._import_ak()
        try:
            df = ak.stock_hsgt_hold_stock_em(market=market, indicator=indicator)
        except Exception as e:
            raise NetworkError(f"拉取北向持仓 ({market} {indicator}) 失败: {e}")

        if df is None or len(df) == 0:
            raise DataValidationError(f"北向持仓 ({market} {indicator}) 为空")
        return df

    def fetch_sector_flow(self, symbol: str = "即时", indicator: str = "今日排行") -> pd.DataFrame:
        """
        拉取板块资金流向 (东方财富)

        Args:
            symbol: "即时" / "行业" / "概念"
            indicator: "今日排行" / "5日排行" / "10日排行"
        """
        self._throttle()
        ak = self._import_ak()
        try:
            df = ak.stock_hsgt_board_rank_em(symbol=symbol, indicator=indicator)
        except Exception as e:
            raise NetworkError(f"拉取板块资金流向 ({symbol}) 失败: {e}")

        if df is None or len(df) == 0:
            raise DataValidationError(f"板块资金流向 ({symbol}) 为空")
        return df

    # ========================================================================
    # 估值数据
    # ========================================================================

    def fetch_valuation(self, symbol: str) -> pd.DataFrame:
        """
        拉取个股估值对比 (东方财富)

        Returns:
            DataFrame: 同业PE/PB/PS对比
        """
        self._throttle()
        ak = self._import_ak()
        try:
            df = ak.stock_zh_valuation_comparison_em(symbol=symbol)
        except Exception as e:
            raise NetworkError(f"拉取估值对比 {symbol} 失败: {e}")

        if df is None or len(df) == 0:
            raise DataValidationError(f"估值对比 {symbol} 为空")
        return df

    # ========================================================================
    # 宏观经济数据
    # ========================================================================

    def fetch_macro_gdp(self) -> pd.DataFrame:
        """拉取中国GDP数据"""
        self._throttle()
        ak = self._import_ak()
        try:
            df = ak.macro_china_gdp()
            return df
        except Exception as e:
            logger.warning(f"拉取GDP数据失败: {e}")
            return pd.DataFrame()

    def fetch_macro_cpi(self) -> pd.DataFrame:
        """拉取中国CPI数据"""
        self._throttle()
        ak = self._import_ak()
        try:
            df = ak.macro_china_cpi()
            return df
        except Exception as e:
            logger.warning(f"拉取CPI数据失败: {e}")
            return pd.DataFrame()

    def fetch_macro_pmi(self) -> pd.DataFrame:
        """拉取中国PMI数据"""
        self._throttle()
        ak = self._import_ak()
        try:
            df = ak.macro_china_pmi()
            return df
        except Exception as e:
            logger.warning(f"拉取PMI数据失败: {e}")
            return pd.DataFrame()

    def fetch_macro_money_supply(self) -> pd.DataFrame:
        """拉取中国货币供应量 (M0/M1/M2)"""
        self._throttle()
        ak = self._import_ak()
        try:
            df = ak.macro_china_money_supply()
            return df
        except Exception as e:
            logger.warning(f"拉取货币供应量数据失败: {e}")
            return pd.DataFrame()

            return pd.DataFrame()

    def fetch_macro_summary(self) -> dict:
        """
        拉取宏观经济摘要 (GDP/CPI/PMI/M2 最新值)

        Returns:
            dict: {"gdp": str, "cpi": str, "pmi": str, "m2": str, ...}
        """
        result = {}
        try:
            gdp = self.fetch_macro_gdp()
            val = _extract_macro_value(gdp, ("今值", "同比", "GDP"), valid_range=(0, 30))
            if val:
                result["gdp"] = val
        except Exception:
            result["gdp"] = "N/A"

        try:
            cpi = self.fetch_macro_cpi()
            val = _extract_macro_value(cpi, ("今值", "同比", "CPI"), valid_range=(-10, 15))
            if val:
                result["cpi"] = val
        except Exception:
            result["cpi"] = "N/A"

        try:
            pmi = self.fetch_macro_pmi()
            val = _extract_macro_value(pmi, ("制造业", "指数", "PMI", "今值"), valid_range=(30, 70))
            if val:
                result["pmi"] = val
        except Exception:
            result["pmi"] = "N/A"

        return result

    # ========================================================================
    # 股评/研报评分
    # ========================================================================

    def fetch_stock_comment(self, symbol: str) -> pd.DataFrame:
        """
        拉取个股综合评分历史 (东方财富)

        Returns:
            DataFrame: 日期, 综合评分, 主力控盘, 机构参与度 等
        """
        self._throttle()
        ak = self._import_ak()
        try:
            df = ak.stock_comment_detail_zhpj_lspf_em(symbol=symbol)
        except Exception as e:
            logger.warning(f"拉取股评 {symbol} 失败: {e}")
            return pd.DataFrame()
        return df if df is not None else pd.DataFrame()

    # ========================================================================
    # 新闻/舆情
    # ========================================================================

    def fetch_news(self, keyword: str = "财经", count: int = 50) -> pd.DataFrame:
        """
        拉取财经新闻 (东方财富)

        Args:
            keyword: 关键词
            count: 返回条数
        """
        self._throttle()
        ak = self._import_ak()
        try:
            df = ak.stock_news_em(symbol=keyword)
            if df is not None and len(df) > 0:
                return df.head(count)
        except Exception as e:
            logger.warning(f"拉取新闻 ({keyword}) 失败: {e}")
        return pd.DataFrame()

    def fetch_northbound_flow(self) -> pd.DataFrame:
        """拉取北向资金净流入历史"""
        self._throttle()
        ak = self._import_ak()
        try:
            df = ak.stock_hsgt_north_net_flow_in_em(symbol="北向")
            return df if df is not None else pd.DataFrame()
        except Exception as e:
            logger.warning(f"拉取北向资金流失败: {e}")
            return pd.DataFrame()

    # ========================================================================
    # 批量拉取工具
    # ========================================================================

    def fetch_multi_stock_history(
        self,
        symbols: list[str],
        start: str = "20200101",
        end: str = "",
        delay: float = 0.3,
    ) -> dict[str, pd.DataFrame]:
        """
        批量拉取多只个股历史数据 (含限流延迟)

        Args:
            symbols: 股票代码列表
            delay: 每次请求间隔 (秒)

        Returns:
            dict: {symbol: DataFrame}
        """
        results = {}
        for i, sym in enumerate(symbols):
            try:
                if i > 0:
                    time.sleep(delay)
                df = self.fetch_stock_history(sym, start, end)
                results[sym] = df
                logger.info(f"[{i+1}/{len(symbols)}] {sym}: {len(df)} 点")
            except Exception as e:
                logger.error(f"[{i+1}/{len(symbols)}] {sym} 失败: {e}")
        return results


# ============================================================================
# CLI 测试入口
# ============================================================================

def main():
    """CLI 测试: python -m eastmoney_source"""
    import sys

    source = EastMoneyChoiceSource(rate_limit=5)

    print("=" * 60)
    print("东方财富 Choice 数据源 - 接口测试")
    print("=" * 60)

    # 1. 全 A 股行情
    print("\n[1] 全A股实时行情 (top 10)...")
    try:
        df = source.fetch_stock_universe(top_n=10)
        print(f"  ✅ 成功: {len(df)} 只, 字段: {list(df.columns[:8])}")
        print(df[["代码", "名称", "最新价", "涨跌幅"]].head(5).to_string())
    except Exception as e:
        print(f"  ❌ 失败: {e}")

    # 2. 个股历史
    print("\n[2] 贵州茅台(600519) 历史数据...")
    try:
        df = source.fetch_stock_history("600519", "20240101", "20241231")
        print(f"  ✅ 成功: {len(df)} 天")
        print(df[["date", "open", "close", "volume"]].head(3).to_string())
    except Exception as e:
        print(f"  ❌ 失败: {e}")

    # 3. 业绩报表
    print("\n[3] 业绩报表 2024Q3...")
    try:
        df = source.fetch_earnings_report("20240930")
        print(f"  ✅ 成功: {len(df)} 条")
        print(df.head(3).to_string())
    except Exception as e:
        print(f"  ❌ 失败: {e}")

    # 4. 资金流向
    print("\n[4] 资金流向排名 (今日)...")
    try:
        df = source.fetch_fund_flow_rank("今日")
        print(f"  ✅ 成功: {len(df)} 只")
        print(df.head(3).to_string())
    except Exception as e:
        print(f"  ❌ 失败: {e}")

    # 5. 北向资金
    print("\n[5] 北向资金持仓 (今日排行)...")
    try:
        df = source.fetch_northbound_holdings("北向", "今日排行")
        print(f"  ✅ 成功: {len(df)} 只")
    except Exception as e:
        print(f"  ❌ 失败: {e}")

    print("\n" + "=" * 60)
    print("测试完成")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    main()
