"""
QuantInsight Pro - 多源数据集成与FAISS向量检索 (Multi-Source Data & Vector Search)
==================================================================================

多源金融数据整合 + FAISS 向量语义检索, 为情感分析提供数据底座.

功能:
- 多数据源股票/宏观/另类数据获取 (AKShare / yfinance / OpenBB / Finnhub)
- FAISS 向量语义检索 (或 numpy 余弦相似度降级)
- 另类数据信号生成 (卫星/舆情/供应链/资金流/内部人交易)

License: MIT
"""

import hashlib
import logging
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# ============================================================================
# 可选依赖检测
# ============================================================================

try:
    import akshare as ak
    HAS_AKSHARE = True
except ImportError:
    HAS_AKSHARE = False
    logger.debug("AKShare 未安装, 该数据源不可用")

try:
    import yfinance as yf
    HAS_YFINANCE = True
except ImportError:
    HAS_YFINANCE = False
    logger.debug("yfinance 未安装, 该数据源不可用")

try:
    from openbb import obb
    HAS_OPENBB = True
except ImportError:
    HAS_OPENBB = False
    logger.debug("OpenBB 未安装, 该数据源不可用")

try:
    import finnhub
    HAS_FINNHUB = True
except ImportError:
    HAS_FINNHUB = False
    logger.debug("finnhub-python 未安装, 该数据源不可用")

try:
    import faiss
    HAS_FAISS = True
except ImportError:
    HAS_FAISS = False
    logger.debug("faiss-cpu 未安装, 将使用 numpy 余弦相似度降级方案")

try:
    from sentence_transformers import SentenceTransformer
    HAS_SENTENCE_TRANSFORMERS = True
except ImportError:
    HAS_SENTENCE_TRANSFORMERS = False
    logger.debug("sentence-transformers 未安装, 将使用 TF-IDF + SVD 降级方案")

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.decomposition import TruncatedSVD
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False
    logger.debug("scikit-learn 未安装, 将使用哈希嵌入降级方案")

# V3.13: 尝试加载 DashScope embedding 配置 (阿里云 text-embedding-v2)
# 注意: token-plan API 不支持 embedding, 只有标准 DashScope API key 才能用
try:
    import os as _os
    import tomllib as _tomllib
    _DASHSCOPE_API_KEY = None
    _DASHSCOPE_MODEL = "text-embedding-v2"
    _DASHSCOPE_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1/embeddings"
    # 尝试从 secrets.toml 读取
    _secrets_paths = [
        "/opt/quantinsight/.streamlit/secrets.toml",
        ".streamlit/secrets.toml",
        "streamlit_app/.streamlit/secrets.toml",
    ]
    for _sp in _secrets_paths:
        try:
            if _os.path.exists(_sp):
                with open(_sp, "rb") as _f:
                    _secrets = _tomllib.load(_f)
                    # V3.13: 只用专门的 DASHSCOPE_API_KEY (标准 DashScope API)
                    # QWEN_API_KEY 是 token-plan 类型, 不支持 embedding
                    _DASHSCOPE_API_KEY = _secrets.get("DASHSCOPE_API_KEY")
                    _DASHSCOPE_MODEL = _secrets.get("DASHSCOPE_EMBED_MODEL", "text-embedding-v2")
                    break
        except Exception:
            pass
    if not _DASHSCOPE_API_KEY:
        _DASHSCOPE_API_KEY = _os.environ.get("DASHSCOPE_API_KEY")
    HAS_DASHSCOPE_EMBED = bool(_DASHSCOPE_API_KEY)
except Exception:
    HAS_DASHSCOPE_EMBED = False
    _DASHSCOPE_API_KEY = None
    _DASHSCOPE_MODEL = "text-embedding-v2"
    _DASHSCOPE_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1/embeddings"

# V3.13: LLM 配置 (用于语义关键词提取, 替代 embedding)
try:
    _LLM_API_KEY = None
    _LLM_BASE_URL = None
    _LLM_MODEL = None
    for _sp in _secrets_paths:
        try:
            if _os.path.exists(_sp):
                with open(_sp, "rb") as _f:
                    _secrets = _tomllib.load(_f)
                    _LLM_API_KEY = _secrets.get("QWEN_API_KEY") or _secrets.get("DEEPSEEK_API_KEY")
                    _LLM_BASE_URL = _secrets.get("QWEN_BASE_URL") or _secrets.get("DEEPSEEK_BASE_URL")
                    _LLM_MODEL = _secrets.get("QWEN_MODEL") or _secrets.get("DEEPSEEK_MODEL")
                    break
        except Exception:
            pass
    HAS_LLM_FOR_KEYWORDS = bool(_LLM_API_KEY and _LLM_BASE_URL and _LLM_MODEL)
except Exception:
    HAS_LLM_FOR_KEYWORDS = False
    _LLM_API_KEY = None
    _LLM_BASE_URL = None
    _LLM_MODEL = None


# ============================================================================
# 多源数据中枢
# ============================================================================

@dataclass
class SourceStatus:
    """数据源状态信息"""
    name: str
    available: bool
    latency_ms: Optional[float] = None
    last_error: Optional[str] = None
    supports: List[str] = field(default_factory=list)


class DataHub:
    """
    多源金融数据中枢

    统一接入 AKShare / yfinance / OpenBB / Finnhub 等数据源,
    自动选择最优可用源, 并提供优雅降级.
    """

    def __init__(self, finnhub_api_key: Optional[str] = None):
        """
        初始化数据中枢

        Args:
            finnhub_api_key: Finnhub API 密钥 (可选)
        """
        self._finnhub_client = None
        if HAS_FINNHUB and finnhub_api_key:
            try:
                self._finnhub_client = finnhub.FinnhubClient(api_key=finnhub_api_key)
            except Exception as e:
                logger.warning(f"Finnhub 客户端初始化失败: {e}")

        # 缓存各数据源延迟
        self._latency_cache: Dict[str, float] = {}

    # ------------------------------------------------------------------
    # 股票数据
    # ------------------------------------------------------------------

    def fetch_stock_data(
        self,
        code: str,
        source: str = "auto",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        从多数据源获取股票行情数据

        Args:
            code: 股票代码 (如 '000001' 或 'AAPL')
            source: 数据源选择 ('auto' / 'akshare' / 'yfinance' / 'openbb' / 'finnhub')
            start_date: 起始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)

        Returns:
            包含 OHLCV 数据的 DataFrame
        """
        if start_date is None:
            start_date = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")
        if end_date is None:
            end_date = datetime.now().strftime("%Y-%m-%d")

        # 自动选择数据源
        if source == "auto":
            source = self._auto_select_source(code)

        # 按源获取
        fetchers = {
            "akshare": self._fetch_stock_akshare,
            "yfinance": self._fetch_stock_yfinance,
            "openbb": self._fetch_stock_openbb,
            "finnhub": self._fetch_stock_finnhub,
        }

        fetcher = fetchers.get(source)
        if fetcher is None:
            logger.warning(f"未知数据源: {source}, 尝试降级")
            return self._fetch_stock_fallback(code, start_date, end_date)

        try:
            t0 = time.time()
            df = fetcher(code, start_date, end_date)
            self._latency_cache[source] = (time.time() - t0) * 1000
            if df is not None and not df.empty:
                return df
        except Exception as e:
            logger.warning(f"数据源 {source} 获取失败: {e}, 尝试降级")

        # 降级: 依次尝试其他源
        for fallback_name, fallback_fn in fetchers.items():
            if fallback_name == source:
                continue
            try:
                t0 = time.time()
                df = fallback_fn(code, start_date, end_date)
                self._latency_cache[fallback_name] = (time.time() - t0) * 1000
                if df is not None and not df.empty:
                    logger.info(f"降级至 {fallback_name} 成功")
                    return df
            except Exception:
                continue

        # 最终降级: 返回模拟数据
        return self._fetch_stock_fallback(code, start_date, end_date)

    def _auto_select_source(self, code: str) -> str:
        """根据股票代码自动选择最优数据源"""
        # 美股代码通常为纯字母
        is_us = code.isalpha() and len(code) <= 5
        # 港股代码通常为数字 + .HK
        is_hk = code.endswith(".HK")

        if is_us or is_hk:
            if HAS_YFINANCE:
                return "yfinance"
            if HAS_FINNHUB and self._finnhub_client:
                return "finnhub"

        # A 股优先 AKShare
        if HAS_AKSHARE:
            return "akshare"
        if HAS_YFINANCE:
            return "yfinance"
        if HAS_OPENBB:
            return "openbb"
        if HAS_FINNHUB and self._finnhub_client:
            return "finnhub"

        return "fallback"

    def _fetch_stock_akshare(self, code: str, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
        """通过 AKShare 获取 A 股数据"""
        if not HAS_AKSHARE:
            return None
        try:
            df = ak.stock_zh_a_hist(
                symbol=code,
                period="daily",
                start_date=start_date.replace("-", ""),
                end_date=end_date.replace("-", ""),
                adjust="qfq",
            )
            if df is not None and not df.empty:
                df = df.rename(columns={
                    "日期": "date", "开盘": "open", "收盘": "close",
                    "最高": "high", "最低": "low", "成交量": "volume",
                    "成交额": "amount", "涨跌幅": "pct_change",
                })
                df["date"] = pd.to_datetime(df["date"])
                df = df.set_index("date").sort_index()
                return df[["open", "high", "low", "close", "volume"]].astype(float)
        except Exception as e:
            logger.debug(f"AKShare 获取 {code} 失败: {e}")
        return None

    def _fetch_stock_yfinance(self, code: str, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
        """通过 yfinance 获取股票数据 (支持 A/US/HK)"""
        if not HAS_YFINANCE:
            return None
        try:
            # A 股添加后缀
            yf_code = code
            if code.isdigit() and len(code) == 6:
                yf_code = f"{code}.SS" if code.startswith("6") else f"{code}.SZ"

            ticker = yf.Ticker(yf_code)
            df = ticker.history(start=start_date, end=end_date)
            if df is not None and not df.empty:
                df = df.rename(columns={
                    "Open": "open", "High": "high", "Low": "low",
                    "Close": "close", "Volume": "volume",
                })
                return df[["open", "high", "low", "close", "volume"]].astype(float)
        except Exception as e:
            logger.debug(f"yfinance 获取 {code} 失败: {e}")
        return None

    def _fetch_stock_openbb(self, code: str, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
        """通过 OpenBB 获取股票数据"""
        if not HAS_OPENBB:
            return None
        try:
            df = obb.equity.price.historical(
                symbol=code, start_date=start_date, end_date=end_date
            ).to_df()
            if df is not None and not df.empty:
                col_map = {c.lower(): c.lower() for c in df.columns}
                rename = {}
                for k, v in [("open", "open"), ("high", "high"), ("low", "low"),
                             ("close", "close"), ("volume", "volume")]:
                    if k in col_map:
                        rename[col_map[k]] = v
                df = df.rename(columns=rename)
                keep = [c for c in ["open", "high", "low", "close", "volume"] if c in df.columns]
                return df[keep].astype(float)
        except Exception as e:
            logger.debug(f"OpenBB 获取 {code} 失败: {e}")
        return None

    def _fetch_stock_finnhub(self, code: str, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
        """通过 Finnhub 获取实时股票数据"""
        if not HAS_FINNHUB or self._finnhub_client is None:
            return None
        try:
            from datetime import datetime as _dt
            start_ts = int(_dt.strptime(start_date, "%Y-%m-%d").timestamp())
            end_ts = int(_dt.strptime(end_date, "%Y-%m-%d").timestamp())
            res = self._finnhub_client.stock_candles(
                code, "D", start_ts, end_ts
            )
            if res and res.get("s") == "ok":
                df = pd.DataFrame({
                    "date": pd.to_datetime(res["t"], unit="s"),
                    "open": res["o"], "high": res["h"], "low": res["l"],
                    "close": res["c"], "volume": res["v"],
                }).set_index("date")
                return df[["open", "high", "low", "close", "volume"]].astype(float)
        except Exception as e:
            logger.debug(f"Finnhub 获取 {code} 失败: {e}")
        return None

    def _fetch_stock_fallback(self, code: str, start_date: str, end_date: str) -> pd.DataFrame:
        """最终降级: 生成模拟行情数据"""
        logger.info(f"所有数据源不可用, 为 {code} 生成模拟数据")
        dates = pd.bdate_range(start=start_date, end=end_date)
        n = len(dates)
        if n == 0:
            dates = pd.bdate_range(start=start_date, periods=60)
            n = 60

        np.random.seed(hash(code) % 2**31)
        base_price = 10 + np.random.rand() * 90
        returns = np.random.randn(n) * 0.02
        close = base_price * np.cumprod(1 + returns)
        high = close * (1 + np.abs(np.random.randn(n) * 0.01))
        low = close * (1 - np.abs(np.random.randn(n) * 0.01))
        open_ = close * (1 + np.random.randn(n) * 0.005)
        volume = (np.random.rand(n) * 1e7 + 1e6).astype(int)

        return pd.DataFrame({
            "open": open_, "high": high, "low": low,
            "close": close, "volume": volume.astype(float),
        }, index=dates)

    # ------------------------------------------------------------------
    # 宏观数据
    # ------------------------------------------------------------------

    def fetch_macro_data(self, source: str = "auto") -> Dict[str, Any]:
        """
        从多数据源获取宏观经济指标

        Args:
            source: 数据源 ('auto' / 'akshare' / 'openbb')

        Returns:
            包含宏观指标的字典
        """
        if source == "auto":
            if HAS_AKSHARE:
                source = "akshare"
            elif HAS_OPENBB:
                source = "openbb"
            else:
                source = "fallback"

        if source == "akshare":
            try:
                return self._fetch_macro_akshare()
            except Exception as e:
                logger.warning(f"AKShare 宏观数据获取失败: {e}")

        if source == "openbb":
            try:
                return self._fetch_macro_openbb()
            except Exception as e:
                logger.warning(f"OpenBB 宏观数据获取失败: {e}")

        return self._fetch_macro_fallback()

    def _fetch_macro_akshare(self) -> Dict[str, Any]:
        """通过 AKShare 获取宏观指标"""
        if not HAS_AKSHARE:
            raise RuntimeError("AKShare 不可用")
        result = {}
        try:
            # CPI
            cpi = ak.macro_china_cpi_yearly()
            if cpi is not None and not cpi.empty:
                latest = cpi.iloc[-1]
                result["cpi_yoy"] = float(latest.iloc[1]) if len(latest) > 1 else None
        except Exception:
            pass
        try:
            # PMI
            pmi = ak.macro_china_pmi_yearly()
            if pmi is not None and not pmi.empty:
                latest = pmi.iloc[-1]
                result["pmi"] = float(latest.iloc[1]) if len(latest) > 1 else None
        except Exception:
            pass
        try:
            # M2
            m2 = ak.macro_china_money_supply_yearly()
            if m2 is not None and not m2.empty:
                latest = m2.iloc[-1]
                result["m2_yoy"] = float(latest.iloc[1]) if len(latest) > 1 else None
        except Exception:
            pass
        result["source"] = "akshare"
        result["timestamp"] = datetime.now().isoformat()
        return result

    def _fetch_macro_openbb(self) -> Dict[str, Any]:
        """通过 OpenBB 获取宏观指标"""
        if not HAS_OPENBB:
            raise RuntimeError("OpenBB 不可用")
        result = {}
        try:
            gdp = obb.economy.gdp(real=True).to_df()
            if gdp is not None and not gdp.empty:
                result["gdp_growth"] = float(gdp.iloc[-1].iloc[0])
        except Exception:
            pass
        result["source"] = "openbb"
        result["timestamp"] = datetime.now().isoformat()
        return result

    def _fetch_macro_fallback(self) -> Dict[str, Any]:
        """宏观指标降级: 返回模拟数据"""
        np.random.seed(int(datetime.now().strftime("%Y%m%d")) % 2**31)
        return {
            "cpi_yoy": round(np.random.uniform(0.5, 3.0), 2),
            "pmi": round(np.random.uniform(48.0, 53.0), 1),
            "m2_yoy": round(np.random.uniform(8.0, 13.0), 1),
            "gdp_growth": round(np.random.uniform(4.0, 6.5), 1),
            "interest_rate": round(np.random.uniform(2.5, 4.5), 2),
            "unemployment": round(np.random.uniform(4.5, 6.0), 1),
            "source": "demo",
            "timestamp": datetime.now().isoformat(),
        }

    # ------------------------------------------------------------------
    # 另类数据
    # ------------------------------------------------------------------

    def fetch_alternative_data(
        self, data_type: str, source: str = "auto", **kwargs
    ) -> Dict[str, Any]:
        """
        获取另类数据

        Args:
            data_type: 数据类型
                - 'satellite': 卫星图像指数
                - 'sentiment': 新闻/社交舆情
                - 'supply_chain': 供应链追踪
                - 'fund_flow': 资金流向
                - 'insider': 内部人交易
            source: 数据源 ('auto' 或指定)
            **kwargs: 额外参数 (如 stock_code, industry)

        Returns:
            另类数据字典
        """
        fetchers = {
            "satellite": self._fetch_alt_satellite,
            "sentiment": self._fetch_alt_sentiment,
            "supply_chain": self._fetch_alt_supply_chain,
            "fund_flow": self._fetch_alt_fund_flow,
            "insider": self._fetch_alt_insider,
        }

        fetcher = fetchers.get(data_type)
        if fetcher is None:
            logger.warning(f"未知另类数据类型: {data_type}")
            return {"error": f"不支持的数据类型: {data_type}", "data_type": data_type}

        try:
            return fetcher(source=source, **kwargs)
        except Exception as e:
            logger.warning(f"获取 {data_type} 数据失败: {e}")
            return {"error": str(e), "data_type": data_type}

    def _fetch_alt_satellite(self, source: str = "auto", industry: str = "general", **kw) -> Dict[str, Any]:
        """卫星图像指数 (演示数据)"""
        np.random.seed(hash(industry) % 2**31)
        return {
            "data_type": "satellite",
            "industry": industry,
            "indices": {
                "industrial_activity": round(np.random.uniform(60, 95), 1),
                "construction_intensity": round(np.random.uniform(40, 85), 1),
                "shipping_port_activity": round(np.random.uniform(50, 90), 1),
                "crop_health_index": round(np.random.uniform(55, 88), 1),
                "nightlight_growth": round(np.random.uniform(-2.0, 5.0), 2),
                "oil_storage_estimate": round(np.random.uniform(60, 95), 1),
            },
            "trend": np.random.choice(["上升", "下降", "持平"]),
            "source": "demo",
            "timestamp": datetime.now().isoformat(),
        }

    def _fetch_alt_sentiment(self, source: str = "auto", stock_code: str = "", **kw) -> Dict[str, Any]:
        """新闻/社交舆情数据"""
        # 尝试 AKShare 新闻
        if source in ("auto", "akshare") and HAS_AKSHARE and stock_code:
            try:
                news = ak.stock_news_em(symbol=stock_code)
                if news is not None and not news.empty:
                    articles = []
                    for _, row in news.head(20).iterrows():
                        articles.append({
                            "title": str(row.get("新闻标题", "")),
                            "content": str(row.get("新闻内容", "")),
                            "date": str(row.get("发布时间", "")),
                            "source": str(row.get("文章来源", "")),
                        })
                    return {
                        "data_type": "sentiment",
                        "stock_code": stock_code,
                        "articles": articles,
                        "total": len(articles),
                        "source": "akshare",
                        "timestamp": datetime.now().isoformat(),
                    }
            except Exception as e:
                logger.debug(f"AKShare 舆情获取失败: {e}")

        # 降级: 模拟舆情数据
        np.random.seed(hash(stock_code) % 2**31 if stock_code else 42)
        demo_titles = [
            "市场情绪回暖, 北向资金持续净流入",
            "行业景气度上行, 龙头企业业绩超预期",
            "政策利好频出, 板块迎来估值修复",
            "外部不确定性增加, 投资者观望情绪浓厚",
            "技术面出现底部信号, 机构建议逢低布局",
            "供应链压力缓解, 企业盈利预期改善",
            "资金面边际收紧, 短期波动或加大",
            "产业升级加速, 新兴赛道关注度提升",
        ]
        articles = []
        for i, title in enumerate(demo_titles):
            articles.append({
                "title": title,
                "content": f"关于{stock_code or '市场'}的最新分析: {title}。详细内容涉及行业基本面、资金面及技术面综合研判。",
                "date": (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d"),
                "source": np.random.choice(["财联社", "证券时报", "上海证券报", "中国证券报"]),
                "sentiment_score": round(np.random.uniform(0.2, 0.9), 2),
            })
        return {
            "data_type": "sentiment",
            "stock_code": stock_code,
            "articles": articles,
            "total": len(articles),
            "source": "demo",
            "timestamp": datetime.now().isoformat(),
        }

    def _fetch_alt_supply_chain(self, source: str = "auto", industry: str = "general", **kw) -> Dict[str, Any]:
        """供应链追踪数据"""
        np.random.seed(hash(industry) % 2**31)
        return {
            "data_type": "supply_chain",
            "industry": industry,
            "metrics": {
                "supplier_delivery_time_days": round(np.random.uniform(5, 30), 1),
                "inventory_turnover_ratio": round(np.random.uniform(3.0, 8.0), 2),
                "order_backlog_index": round(np.random.uniform(40, 80), 1),
                "logistics_cost_pct": round(np.random.uniform(5, 15), 1),
                "supply_chain_risk_score": round(np.random.uniform(20, 70), 1),
            },
            "disruption_alerts": [
                {"region": "东南亚", "severity": "中等", "impact": "电子元器件交付延迟2-3周"},
                {"region": "欧洲", "severity": "低", "impact": "航运成本小幅上升"},
            ] if np.random.rand() > 0.4 else [],
            "source": "demo",
            "timestamp": datetime.now().isoformat(),
        }

    def _fetch_alt_fund_flow(self, source: str = "auto", market: str = "A股", **kw) -> Dict[str, Any]:
        """资金流向数据"""
        # 尝试 AKShare
        if source in ("auto", "akshare") and HAS_AKSHARE:
            try:
                flow = ak.stock_market_fund_flow()
                if flow is not None and not flow.empty:
                    latest = flow.iloc[-1]
                    return {
                        "data_type": "fund_flow",
                        "market": market,
                        "metrics": {
                            "northbound_net_flow": float(latest.iloc[1]) if len(latest) > 1 else 0,
                            "main_force_net_flow": float(latest.iloc[3]) if len(latest) > 3 else 0,
                            "retail_net_flow": float(latest.iloc[5]) if len(latest) > 5 else 0,
                        },
                        "source": "akshare",
                        "timestamp": datetime.now().isoformat(),
                    }
            except Exception as e:
                logger.debug(f"AKShare 资金流向获取失败: {e}")

        # 降级
        np.random.seed(int(datetime.now().strftime("%Y%m%d")) % 2**31)
        return {
            "data_type": "fund_flow",
            "market": market,
            "metrics": {
                "northbound_net_flow": round(np.random.uniform(-80, 120), 2),
                "main_force_net_flow": round(np.random.uniform(-150, 200), 2),
                "retail_net_flow": round(np.random.uniform(-100, 100), 2),
                "margin_balance_change": round(np.random.uniform(-50, 80), 2),
                "etf_net_inflow": round(np.random.uniform(-30, 60), 2),
            },
            "source": "demo",
            "timestamp": datetime.now().isoformat(),
        }

    def _fetch_alt_insider(self, source: str = "auto", stock_code: str = "", **kw) -> Dict[str, Any]:
        """内部人交易数据"""
        np.random.seed(hash(stock_code) % 2**31 if stock_code else 42)
        names = ["张XX", "李XX", "王XX", "赵XX", "陈XX"]
        positions = ["董事", "高管", "监事", "大股东"]
        actions = ["买入", "卖出"]
        trades = []
        for i in range(np.random.randint(3, 8)):
            trades.append({
                "name": np.random.choice(names),
                "position": np.random.choice(positions),
                "action": np.random.choice(actions),
                "shares": int(np.random.uniform(1000, 50000)),
                "amount_wan": round(np.random.uniform(5, 200), 2),
                "date": (datetime.now() - timedelta(days=np.random.randint(0, 30))).strftime("%Y-%m-%d"),
            })
        return {
            "data_type": "insider",
            "stock_code": stock_code,
            "trades": trades,
            "summary": {
                "buy_count": sum(1 for t in trades if t["action"] == "买入"),
                "sell_count": sum(1 for t in trades if t["action"] == "卖出"),
                "net_amount_wan": round(sum(
                    t["amount_wan"] * (1 if t["action"] == "买入" else -1) for t in trades
                ), 2),
            },
            "source": "demo",
            "timestamp": datetime.now().isoformat(),
        }

    # ------------------------------------------------------------------
    # 数据源状态
    # ------------------------------------------------------------------

    def get_source_status(self) -> List[SourceStatus]:
        """
        获取各数据源可用状态与延迟

        Returns:
            SourceStatus 列表
        """
        statuses = []

        # AKShare
        ak_latency = self._latency_cache.get("akshare")
        statuses.append(SourceStatus(
            name="AKShare",
            available=HAS_AKSHARE,
            latency_ms=ak_latency,
            supports=["A股行情", "宏观数据", "新闻舆情", "资金流向"],
        ))

        # yfinance
        yf_latency = self._latency_cache.get("yfinance")
        statuses.append(SourceStatus(
            name="yfinance",
            available=HAS_YFINANCE,
            latency_ms=yf_latency,
            supports=["美股行情", "港股行情", "A股行情"],
        ))

        # OpenBB
        obb_latency = self._latency_cache.get("openbb")
        statuses.append(SourceStatus(
            name="OpenBB",
            available=HAS_OPENBB,
            latency_ms=obb_latency,
            supports=["全球行情", "宏观数据", "另类数据"],
        ))

        # Finnhub
        fh_latency = self._latency_cache.get("finnhub")
        statuses.append(SourceStatus(
            name="Finnhub",
            available=HAS_FINNHUB and self._finnhub_client is not None,
            latency_ms=fh_latency,
            supports=["美股实时", "新闻", "内部人交易"],
        ))

        return statuses


# ============================================================================
# FAISS 向量语义检索
# ============================================================================

class SentimentVectorStore:
    """
    基于 FAISS 的情感向量检索引擎

    支持对新闻/文档进行语义检索, 查找相似历史事件.
    降级方案: FAISS → numpy 余弦相似度; sentence-transformers → TF-IDF+SVD → 哈希嵌入.
    """

    def __init__(self, dimension: int = 384):
        """
        初始化向量存储

        Args:
            dimension: 嵌入向量维度 (sentence-transformers 默认 384)
        """
        # V3.13: DashScope embedding 维度是 1536, 需要调整
        if HAS_DASHSCOPE_EMBED:
            dimension = 1536
        self.dimension = dimension
        self.documents: List[Dict] = []  # 原始文档列表
        self.embeddings: Optional[np.ndarray] = None  # 嵌入矩阵 (N, D)
        self._stock_index: Dict[str, List[int]] = defaultdict(list)  # 股票代码 → 文档索引

        # 初始化嵌入模型
        self._encoder = self._init_encoder()

        # 初始化 FAISS 索引
        self._faiss_index = self._init_faiss()

    def _init_encoder(self):
        """初始化文本编码器 (优先级: DashScope > LLM关键词 > sentence-transformers > TF-IDF+SVD > 哈希)"""
        # V3.13: 优先使用 DashScope embedding (需要标准 DashScope API key)
        if HAS_DASHSCOPE_EMBED:
            logger.info("使用 DashScope embedding 编码器 (text-embedding-v2)")
            return ("dashscope", {"api_key": _DASHSCOPE_API_KEY, "model": _DASHSCOPE_MODEL, "base_url": _DASHSCOPE_BASE_URL})

        # V3.13: 用 LLM 提取关键词做语义匹配 (token-plan API 支持 chat, 不支持 embedding)
        if HAS_LLM_FOR_KEYWORDS:
            logger.info("使用 LLM 关键词语义匹配 (qwen3.6-plus)")
            return ("llm_keywords", {"api_key": _LLM_API_KEY, "base_url": _LLM_BASE_URL, "model": _LLM_MODEL})

        if HAS_SENTENCE_TRANSFORMERS:
            try:
                model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
                logger.info("已加载 sentence-transformers 编码器")
                return ("sentence_transformers", model)
            except Exception as e:
                logger.warning(f"sentence-transformers 加载失败: {e}")

        if HAS_SKLEARN:
            logger.info("使用 TF-IDF + SVD 编码器")
            return ("tfidf_svd", {
                "vectorizer": TfidfVectorizer(max_features=5000),
                "svd": TruncatedSVD(n_components=self.dimension),
                "fitted": False,
                "corpus": [],
            })

        logger.info("使用哈希嵌入编码器 (最终降级)")
        return ("hash", None)

    def _init_faiss(self):
        """初始化 FAISS 索引"""
        if HAS_FAISS:
            try:
                index = faiss.IndexFlatIP(self.dimension)  # 内积相似度
                logger.info("已初始化 FAISS 索引")
                return index
            except Exception as e:
                logger.warning(f"FAISS 索引初始化失败: {e}")
        return None

    def _encode(self, texts: List[str]) -> np.ndarray:
        """
        将文本列表编码为嵌入向量

        Args:
            texts: 文本列表

        Returns:
            嵌入矩阵 (N, dimension)
        """
        if not texts:
            return np.zeros((0, self.dimension), dtype=np.float32)

        encoder_type = self._encoder[0]

        # V3.13: DashScope embedding (阿里云 text-embedding-v2)
        if encoder_type == "dashscope":
            return self._dashscope_encode(texts)

        if encoder_type == "sentence_transformers":
            model = self._encoder[1]
            embeddings = model.encode(texts, show_progress_bar=False)
            return np.array(embeddings, dtype=np.float32)

        if encoder_type == "tfidf_svd":
            config = self._encoder[1]
            vectorizer = config["vectorizer"]
            svd = config["svd"]

            if not config["fitted"]:
                # 首次编码时拟合
                tfidf_matrix = vectorizer.fit_transform(texts)
                n_components = min(self.dimension, tfidf_matrix.shape[1] - 1, len(texts) - 1)
                n_components = max(n_components, 1)
                svd = TruncatedSVD(n_components=n_components)
                reduced = svd.fit_transform(tfidf_matrix)
                config["svd"] = svd
                config["fitted"] = True
            else:
                tfidf_matrix = vectorizer.transform(texts)
                reduced = svd.transform(tfidf_matrix)

            # 填充至目标维度
            result = np.zeros((len(texts), self.dimension), dtype=np.float32)
            result[:, :reduced.shape[1]] = reduced
            return result

        # 哈希嵌入 (最终降级)
        return self._hash_encode(texts)

    def _dashscope_encode(self, texts: List[str]) -> np.ndarray:
        """V3.13: 使用 DashScope text-embedding-v2 编码 (1536维)"""
        import requests

        config = self._encoder[1]
        api_key = config["api_key"]
        model = config["model"]
        url = config["base_url"]

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        all_embeddings = []
        # 批量处理 (DashScope 单次最多25条)
        batch_size = 25
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            payload = {
                "model": model,
                "input": batch,
            }
            try:
                resp = requests.post(url, headers=headers, json=payload, timeout=30)
                resp.raise_for_status()
                result = resp.json()
                batch_embeddings = [item["embedding"] for item in result["data"]]
                all_embeddings.extend(batch_embeddings)
            except Exception as e:
                logger.warning(f"DashScope embedding 失败 (batch {i}): {e}, 降级到哈希编码")
                return self._hash_encode(texts)

        embeddings = np.array(all_embeddings, dtype=np.float32)
        # L2 归一化
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        embeddings = embeddings / norms
        return embeddings

    def _hash_encode(self, texts: List[str]) -> np.ndarray:
        """基于哈希的嵌入生成 (无需任何外部依赖)"""
        embeddings = np.zeros((len(texts), self.dimension), dtype=np.float32)
        for i, text in enumerate(texts):
            # 对每个文本生成确定性哈希向量
            for j in range(self.dimension):
                seed = f"{text}_{j}"
                h = hashlib.md5(seed.encode("utf-8")).hexdigest()
                embeddings[i, j] = (int(h[:8], 16) / 2**32) - 0.5
        # L2 归一化
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        embeddings = embeddings / norms
        return embeddings

    def add_documents(self, documents: List[Dict]) -> int:
        """
        添加文档到向量存储

        Args:
            documents: 文档列表, 每个文档包含:
                - text: 文本内容 (必需)
                - date: 日期 (可选)
                - source: 来源 (可选)
                - sentiment_score: 情感分数 (可选)
                - stock_codes: 关联股票代码列表 (可选)

        Returns:
            成功添加的文档数量
        """
        if not documents:
            return 0

        valid_docs = []
        valid_texts = []
        for doc in documents:
            text = doc.get("text", "").strip()
            if not text:
                continue
            valid_docs.append(doc)
            valid_texts.append(text)

        if not valid_texts:
            return 0

        # 编码
        new_embeddings = self._encode(valid_texts)

        # L2 归一化 (用于内积 = 余弦相似度)
        norms = np.linalg.norm(new_embeddings, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        new_embeddings = new_embeddings / norms

        # 存储文档
        start_idx = len(self.documents)
        for i, doc in enumerate(valid_docs):
            idx = start_idx + i
            self.documents.append({
                "text": doc["text"],
                "date": doc.get("date", ""),
                "source": doc.get("source", "unknown"),
                "sentiment_score": doc.get("sentiment_score", 0.5),
                "stock_codes": doc.get("stock_codes", []),
            })
            # 建立股票代码索引
            for code in doc.get("stock_codes", []):
                self._stock_index[code].append(idx)

        # 更新嵌入矩阵
        if self.embeddings is None:
            self.embeddings = new_embeddings
        else:
            self.embeddings = np.vstack([self.embeddings, new_embeddings])

        # 更新 FAISS 索引
        if self._faiss_index is not None:
            try:
                self._faiss_index.add(new_embeddings)
            except Exception as e:
                logger.warning(f"FAISS 索引更新失败: {e}")

        return len(valid_docs)

    def search(self, query: str, top_k: int = 10) -> List[Dict]:
        """
        语义搜索

        Args:
            query: 查询文本
            top_k: 返回前 K 个结果

        Returns:
            匹配结果列表, 每项包含 {text, date, source, score, distance}
        """
        if not self.documents:
            return []

        # V3.13: LLM 关键词匹配模式 (token-plan API 不支持 embedding)
        if self._encoder[0] == "llm_keywords":
            return self._llm_keyword_search(query, top_k)

        if self.embeddings is None:
            return []

        top_k = min(top_k, len(self.documents))

        # 编码查询
        query_emb = self._encode([query])
        norms = np.linalg.norm(query_emb, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        query_emb = query_emb / norms

        # 搜索
        if self._faiss_index is not None and self._faiss_index.ntotal > 0:
            try:
                scores, indices = self._faiss_index.search(query_emb, top_k)
                results = []
                for score, idx in zip(scores[0], indices[0]):
                    if idx < 0 or idx >= len(self.documents):
                        continue
                    doc = self.documents[idx]
                    results.append({
                        "text": doc["text"],
                        "date": doc["date"],
                        "source": doc["source"],
                        "score": float(score),
                        "distance": float(1 - score),
                    })
                return results
            except Exception as e:
                logger.warning(f"FAISS 搜索失败, 降级至 numpy: {e}")

        # numpy 余弦相似度降级
        return self._numpy_search(query_emb[0], top_k)

    def _llm_keyword_search(self, query: str, top_k: int) -> List[Dict]:
        """V3.13: LLM 关键词语义匹配 (token-plan API 不支持 embedding 的替代方案)

        策略: 用 LLM 提取查询关键词, 然后与文档做关键词重叠 + 同义词匹配
        """
        import requests as _requests

        config = self._encoder[1]
        api_key = config["api_key"]
        base_url = config["base_url"]
        model = config["model"]

        # 1. 用 LLM 提取查询关键词
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": "你是金融文本分析助手。提取用户查询的关键词和同义词, 用逗号分隔, 只输出关键词, 不加解释。"},
                {"role": "user", "content": f"查询: {query}\n请提取5-10个关键词和同义词:"},
            ],
            "temperature": 0.3,
            "max_tokens": 200,
        }
        # V3.13: qwen3.x 推理模型禁用思考
        if "qwen3" in model.lower() or "qwen-3" in model.lower():
            payload["enable_thinking"] = False

        try:
            resp = _requests.post(base_url, headers=headers, json=payload, timeout=30)
            resp.raise_for_status()
            result = resp.json()
            keywords_text = result["choices"][0]["message"]["content"].strip()
            # 解析关键词 (逗号分隔)
            query_keywords = [k.strip() for k in keywords_text.replace("，", ",").replace("、", ",").split(",") if k.strip()]
            logger.info(f"LLM 提取关键词: {query_keywords}")
        except Exception as e:
            logger.warning(f"LLM 关键词提取失败: {e}, 降级到简单分词")
            # 降级: 简单分词
            query_keywords = [w for w in query.replace("，", " ").replace("、", " ").split() if len(w) > 1]

        # 2. 计算每个文档与查询的关键词匹配分数
        scored_docs = []
        for i, doc in enumerate(self.documents):
            doc_text = doc["text"]
            # 计算关键词命中数
            hits = 0
            for kw in query_keywords:
                if kw in doc_text:
                    hits += 1
            # 计算分数: 命中关键词数 / 总关键词数, 加上查询词直接命中
            score = hits / max(len(query_keywords), 1)
            # 额外: 查询中的词直接出现在文档中
            query_words = [w for w in query.replace("，", " ").replace("、", " ").split() if len(w) > 1]
            for qw in query_words:
                if qw in doc_text:
                    score += 0.1
            scored_docs.append((i, min(score, 1.0)))

        # 3. 按分数排序, 取 top_k
        scored_docs.sort(key=lambda x: x[1], reverse=True)
        results = []
        for idx, score in scored_docs[:top_k]:
            doc = self.documents[idx]
            results.append({
                "text": doc["text"],
                "date": doc["date"],
                "source": doc["source"],
                "score": float(score),
                "distance": float(1 - score),
            })
        return results

    def _numpy_search(self, query_vec: np.ndarray, top_k: int) -> List[Dict]:
        """使用 numpy 计算余弦相似度进行搜索"""
        similarities = np.dot(self.embeddings, query_vec)
        top_indices = np.argsort(similarities)[::-1][:top_k]

        results = []
        for idx in top_indices:
            idx = int(idx)
            if idx >= len(self.documents):
                continue
            doc = self.documents[idx]
            score = float(similarities[idx])
            results.append({
                "text": doc["text"],
                "date": doc["date"],
                "source": doc["source"],
                "score": score,
                "distance": float(1 - score),
            })
        return results

    def search_by_stock(self, stock_code: str, top_k: int = 10) -> List[Dict]:
        """
        按股票代码搜索相关文档

        Args:
            stock_code: 股票代码
            top_k: 返回前 K 个结果

        Returns:
            匹配结果列表
        """
        indices = self._stock_index.get(stock_code, [])
        if not indices:
            return []

        # 按情感分数排序
        results = []
        for idx in indices:
            if idx < len(self.documents):
                doc = self.documents[idx]
                results.append({
                    "text": doc["text"],
                    "date": doc["date"],
                    "source": doc["source"],
                    "sentiment_score": doc["sentiment_score"],
                    "stock_codes": doc["stock_codes"],
                })

        results.sort(key=lambda x: abs(x["sentiment_score"] - 0.5), reverse=True)
        return results[:top_k]

    def get_similar_events(self, event_text: str, top_k: int = 5) -> List[Dict]:
        """
        查找相似历史事件

        Args:
            event_text: 事件描述文本
            top_k: 返回前 K 个结果

        Returns:
            相似事件列表, 包含相似度与情感标签
        """
        results = self.search(event_text, top_k=top_k)

        # 附加情感标签
        for r in results:
            score = r.get("score", 0)
            if score > 0.6:
                r["sentiment_label"] = "正面"
            elif score < 0.4:
                r["sentiment_label"] = "负面"
            else:
                r["sentiment_label"] = "中性"

        return results


# ============================================================================
# 另类数据信号生成器
# ============================================================================

class AltDataSignalGenerator:
    """
    另类数据交易信号生成器

    基于卫星、舆情、供应链、资金流等另类数据,
    生成可量化的交易信号.
    """

    # 行业卫星信号基线
    _SATELLITE_BASELINES = {
        "新能源汽车": {"industrial": 78, "construction": 65, "shipping": 72},
        "半导体": {"industrial": 82, "construction": 55, "shipping": 68},
        "光伏": {"industrial": 75, "construction": 70, "shipping": 60},
        "医药": {"industrial": 60, "construction": 45, "shipping": 55},
        "房地产": {"industrial": 50, "construction": 40, "shipping": 35},
        "消费": {"industrial": 65, "construction": 50, "shipping": 70},
    }

    # 行业供应链风险基线
    _SUPPLY_CHAIN_BASELINES = {
        "新能源汽车": {"delivery_days": 18, "risk_score": 45},
        "半导体": {"delivery_days": 25, "risk_score": 55},
        "光伏": {"delivery_days": 15, "risk_score": 38},
        "医药": {"delivery_days": 12, "risk_score": 30},
        "房地产": {"delivery_days": 22, "risk_score": 50},
        "消费": {"delivery_days": 10, "risk_score": 25},
    }

    def __init__(self, data_hub: Optional[DataHub] = None):
        """
        初始化信号生成器

        Args:
            data_hub: DataHub 实例 (可选, 用于获取真实数据)
        """
        self.data_hub = data_hub or DataHub()

    def generate_satellite_signal(self, industry: str) -> Dict[str, Any]:
        """
        生成卫星数据交易信号

        Args:
            industry: 行业名称

        Returns:
            信号字典 {signal_type, signal_value, confidence, data_source, timestamp}
        """
        baseline = self._SATELLITE_BASELINES.get(industry, {"industrial": 65, "construction": 55, "shipping": 60})

        # 模拟当前值 (围绕基线波动)
        np.random.seed(hash(industry + datetime.now().strftime("%Y%m%d")) % 2**31)
        current = {
            k: round(v + np.random.uniform(-10, 10), 1)
            for k, v in baseline.items()
        }

        # 计算综合信号
        avg_change = np.mean([
            (current[k] - baseline[k]) / baseline[k]
            for k in baseline
        ])

        # 信号值: -1 到 +1
        signal_value = np.clip(avg_change * 5, -1, 1)

        # 置信度: 基于数据一致性
        changes = [(current[k] - baseline[k]) / baseline[k] for k in baseline]
        consistency = 1 - np.std(changes) / (np.std(changes) + 0.1)
        confidence = round(float(np.clip(consistency * 0.7 + 0.2, 0.2, 0.9)), 2)

        return {
            "signal_type": "satellite",
            "signal_value": round(float(signal_value), 3),
            "signal_label": "看多" if signal_value > 0.2 else ("看空" if signal_value < -0.2 else "中性"),
            "confidence": confidence,
            "details": {
                "industry": industry,
                "baseline": baseline,
                "current": current,
                "avg_change_pct": round(float(avg_change * 100), 2),
            },
            "data_source": "satellite_demo",
            "timestamp": datetime.now().isoformat(),
        }

    def generate_sentiment_signal(self, stock_code: str) -> Dict[str, Any]:
        """
        生成舆情交易信号

        Args:
            stock_code: 股票代码

        Returns:
            信号字典
        """
        # 获取舆情数据
        alt_data = self.data_hub.fetch_alternative_data("sentiment", stock_code=stock_code)
        articles = alt_data.get("articles", [])

        if articles:
            # 计算加权情感分数
            scores = []
            recency_weights = []
            for i, art in enumerate(articles):
                score = art.get("sentiment_score", 0.5)
                scores.append(score)
                # 越新权重越高
                recency_weights.append(1.0 / (1 + i * 0.2))

            scores = np.array(scores)
            weights = np.array(recency_weights)
            weights = weights / weights.sum()
            weighted_score = float(np.average(scores, weights=weights))

            # 信号值: 将 0-1 映射到 -1 到 +1
            signal_value = (weighted_score - 0.5) * 2

            # 置信度: 基于样本量和一致性
            sample_size_factor = min(len(articles) / 20, 1.0)
            consistency_factor = 1 - np.std(scores)
            confidence = round(float(np.clip(
                sample_size_factor * 0.4 + consistency_factor * 0.5 + 0.1, 0.15, 0.95
            )), 2)
        else:
            # 无数据时返回中性信号
            signal_value = 0.0
            confidence = 0.1
            weighted_score = 0.5

        return {
            "signal_type": "sentiment",
            "signal_value": round(float(signal_value), 3),
            "signal_label": "看多" if signal_value > 0.2 else ("看空" if signal_value < -0.2 else "中性"),
            "confidence": confidence,
            "details": {
                "stock_code": stock_code,
                "weighted_sentiment": round(weighted_score, 3),
                "article_count": len(articles),
                "positive_ratio": round(
                    sum(1 for a in articles if a.get("sentiment_score", 0.5) > 0.6) / max(len(articles), 1), 3
                ),
            },
            "data_source": alt_data.get("source", "demo"),
            "timestamp": datetime.now().isoformat(),
        }

    def generate_supply_chain_signal(self, industry: str) -> Dict[str, Any]:
        """
        生成供应链交易信号

        Args:
            industry: 行业名称

        Returns:
            信号字典
        """
        baseline = self._SUPPLY_CHAIN_BASELINES.get(
            industry, {"delivery_days": 15, "risk_score": 35}
        )

        # 获取供应链数据
        alt_data = self.data_hub.fetch_alternative_data("supply_chain", industry=industry)
        metrics = alt_data.get("metrics", {})

        if metrics:
            current_delivery = metrics.get("supplier_delivery_time_days", baseline["delivery_days"])
            current_risk = metrics.get("supply_chain_risk_score", baseline["risk_score"])
        else:
            np.random.seed(hash(industry + datetime.now().strftime("%Y%m%d")) % 2**31)
            current_delivery = baseline["delivery_days"] + np.random.uniform(-5, 8)
            current_risk = baseline["risk_score"] + np.random.uniform(-10, 15)

        # 交付时间延长 → 负面信号; 风险分升高 → 负面信号
        delivery_signal = -(current_delivery - baseline["delivery_days"]) / baseline["delivery_days"]
        risk_signal = -(current_risk - baseline["risk_score"]) / max(baseline["risk_score"], 1)

        # 综合信号
        signal_value = np.clip((delivery_signal * 0.6 + risk_signal * 0.4) * 3, -1, 1)

        # 置信度
        confidence = round(float(np.clip(0.5 + 0.3 * (1 - abs(signal_value)) + 0.1, 0.2, 0.85)), 2)

        return {
            "signal_type": "supply_chain",
            "signal_value": round(float(signal_value), 3),
            "signal_label": "看多" if signal_value > 0.2 else ("看空" if signal_value < -0.2 else "中性"),
            "confidence": confidence,
            "details": {
                "industry": industry,
                "baseline_delivery_days": baseline["delivery_days"],
                "current_delivery_days": round(current_delivery, 1),
                "baseline_risk_score": baseline["risk_score"],
                "current_risk_score": round(current_risk, 1),
                "disruption_alerts": alt_data.get("disruption_alerts", []),
            },
            "data_source": alt_data.get("source", "demo"),
            "timestamp": datetime.now().isoformat(),
        }

    def generate_fund_flow_signal(self, market: str = "A股") -> Dict[str, Any]:
        """
        生成资金流向交易信号

        Args:
            market: 市场名称

        Returns:
            信号字典
        """
        alt_data = self.data_hub.fetch_alternative_data("fund_flow", market=market)
        metrics = alt_data.get("metrics", {})

        northbound = metrics.get("northbound_net_flow", 0)
        main_force = metrics.get("main_force_net_flow", 0)
        retail = metrics.get("retail_net_flow", 0)

        # 北向资金 + 主力净流入为正面信号, 散户为反向指标
        # 归一化: 假设 ±200 亿为极端值
        north_signal = np.clip(northbound / 150, -1, 1)
        main_signal = np.clip(main_force / 200, -1, 1)
        retail_signal = np.clip(-retail / 150, -1, 1)  # 散户净流入为反向指标

        # 综合信号 (北向权重最高)
        signal_value = np.clip(north_signal * 0.45 + main_signal * 0.35 + retail_signal * 0.2, -1, 1)

        # 置信度: 资金流向一致性
        signals = [north_signal, main_signal, retail_signal]
        if np.all(np.array(signals) > 0) or np.all(np.array(signals) < 0):
            consistency = 0.9
        else:
            consistency = 0.5
        confidence = round(float(np.clip(consistency * 0.7 + 0.2, 0.2, 0.9)), 2)

        return {
            "signal_type": "fund_flow",
            "signal_value": round(float(signal_value), 3),
            "signal_label": "看多" if signal_value > 0.2 else ("看空" if signal_value < -0.2 else "中性"),
            "confidence": confidence,
            "details": {
                "market": market,
                "northbound_net_flow": round(northbound, 2),
                "main_force_net_flow": round(main_force, 2),
                "retail_net_flow": round(retail, 2),
                "margin_balance_change": round(metrics.get("margin_balance_change", 0), 2),
                "etf_net_inflow": round(metrics.get("etf_net_inflow", 0), 2),
            },
            "data_source": alt_data.get("source", "demo"),
            "timestamp": datetime.now().isoformat(),
        }


# ============================================================================
# 便捷函数
# ============================================================================

def create_data_hub(finnhub_api_key: Optional[str] = None) -> DataHub:
    """创建数据中枢实例"""
    return DataHub(finnhub_api_key=finnhub_api_key)


def create_sentiment_store(dimension: int = 384) -> SentimentVectorStore:
    """创建情感向量存储实例"""
    return SentimentVectorStore(dimension=dimension)


def create_signal_generator(data_hub: Optional[DataHub] = None) -> AltDataSignalGenerator:
    """创建另类数据信号生成器实例"""
    return AltDataSignalGenerator(data_hub=data_hub)


def load_demo_documents() -> List[Dict]:
    """
    加载演示文档数据 (用于测试向量检索)

    Returns:
        演示文档列表
    """
    demo_docs = [
        {
            "text": "央行宣布降准0.5个百分点, 释放长期资金约1万亿元, 市场流动性预期改善",
            "date": "2024-03-15",
            "source": "央行公告",
            "sentiment_score": 0.85,
            "stock_codes": ["000001", "601398"],
        },
        {
            "text": "新能源汽车销量连续三个月环比增长, 行业景气度持续上行",
            "date": "2024-03-14",
            "source": "中汽协",
            "sentiment_score": 0.78,
            "stock_codes": ["300750", "002594"],
        },
        {
            "text": "半导体行业面临库存调整压力, 部分企业下调业绩指引",
            "date": "2024-03-13",
            "source": "行业研报",
            "sentiment_score": 0.32,
            "stock_codes": ["688981", "603501"],
        },
        {
            "text": "光伏产业链价格企稳回升, 硅料价格环比上涨3.2%",
            "date": "2024-03-12",
            "source": "PV Infolink",
            "sentiment_score": 0.72,
            "stock_codes": ["601012", "002129"],
        },
        {
            "text": "房地产调控政策继续优化, 多城市取消限购限售",
            "date": "2024-03-11",
            "source": "住建部",
            "sentiment_score": 0.68,
            "stock_codes": ["000002", "600048"],
        },
        {
            "text": "全球供应链紧张局势加剧, 航运指数创年内新高",
            "date": "2024-03-10",
            "source": "波罗的海交易所",
            "sentiment_score": 0.25,
            "stock_codes": ["601919", "601872"],
        },
        {
            "text": "消费复苏势头良好, 社零数据超预期, 餐饮旅游板块活跃",
            "date": "2024-03-09",
            "source": "国家统计局",
            "sentiment_score": 0.75,
            "stock_codes": ["600754", "000524"],
        },
        {
            "text": "美联储维持利率不变, 但释放鹰派信号, 美股承压下跌",
            "date": "2024-03-08",
            "source": "Fed声明",
            "sentiment_score": 0.28,
            "stock_codes": [],
        },
        {
            "text": "人工智能概念持续火热, 算力需求爆发, 相关公司股价大涨",
            "date": "2024-03-07",
            "source": "科技媒体",
            "sentiment_score": 0.82,
            "stock_codes": ["002230", "688787"],
        },
        {
            "text": "银行板块估值修复, 股息率优势凸显, 北向资金持续增持",
            "date": "2024-03-06",
            "source": "券商研报",
            "sentiment_score": 0.71,
            "stock_codes": ["601398", "600036"],
        },
        {
            "text": "医药集采结果出炉, 部分品种降价幅度超预期, 企业利润承压",
            "date": "2024-03-05",
            "source": "医保局",
            "sentiment_score": 0.22,
            "stock_codes": ["600276", "000538"],
        },
        {
            "text": "锂电池原材料价格回落, 中游电池企业成本压力缓解",
            "date": "2024-03-04",
            "source": "百川盈孚",
            "sentiment_score": 0.65,
            "stock_codes": ["300750", "300014"],
        },
    ]
    return demo_docs
