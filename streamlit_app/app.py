# -*- coding: utf-8 -*-
"""
QuantInsight Pro - AI 驱动的另类数据量化投研平台
3 大模块：
1. AI 投研问答
2. 另类数据仪表盘
3. 量化策略回测

部署：Streamlit Cloud + GitHub
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import akshare as ak
import os
import requests
import json
import math
import time

import logging
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)


# ============== akshare 安全调用封装 ==============
# ECS 服务器上东方财富接口可能封禁服务器 IP, 统一封装重试 + 降级逻辑

_AKSHARE_DEMO_SPOT = None  # 延迟初始化的演示数据

def _get_demo_spot_df():
    """获取 A 股演示行情数据 (akshare 不可用时降级)"""
    global _AKSHARE_DEMO_SPOT
    if _AKSHARE_DEMO_SPOT is not None:
        return _AKSHARE_DEMO_SPOT
    _AKSHARE_DEMO_SPOT = pd.DataFrame({
        '代码': ['600519', '000858', '601318', '600036', '000333',
                '601012', '002594', '300750', '600276', '601888',
                '601398', '600030', '000001', '002230', '688981',
                '600048', '000002', '601919', '600754', '002129',
                '601166', '600900', '601857', '600887', '000568'],
        '名称': ['贵州茅台', '五粮液', '中国平安', '招商银行', '美的集团',
                '隆基绿能', '比亚迪', '宁德时代', '恒瑞医药', '中国中免',
                '工商银行', '中信证券', '平安银行', '科大讯飞', '中芯国际',
                '保利发展', '万科A', '中远海控', '锦江酒店', '中环股份',
                '兴业银行', '长江电力', '中国石油', '伊利股份', '泸州老窖'],
        '最新价': [1680, 145, 48, 35, 68, 22, 240, 220, 45, 95,
                 5.2, 22.5, 11.8, 52, 48, 12.5, 8.2, 14.6, 32, 18,
                 16.8, 28.5, 8.9, 29.6, 168],
        '涨跌幅': [1.25, 0.86, -0.52, 0.38, 1.56, -1.23, 2.85, 3.12, -0.67, 0.95,
                 0.19, 1.82, 0.34, 4.25, 2.16, -0.48, -1.35, 1.67, 0.78, -0.92,
                 0.45, 0.62, -0.38, 1.15, 0.93],
        '涨跌额': [20.75, 1.24, -0.25, 0.13, 1.05, -0.27, 6.65, 6.63, -0.30, 0.89,
                  0.01, 0.40, 0.04, 2.12, 1.01, -0.06, -0.11, 0.24, 0.25, -0.17,
                  0.08, 0.18, -0.03, 0.34, 1.55],
        '成交量': [3500000, 4200000, 1800000, 2900000, 3800000,
                  5200000, 2800000, 4100000, 1500000, 1200000,
                  980000, 3600000, 2100000, 4500000, 6800000,
                  1100000, 850000, 720000, 560000, 3200000,
                  1400000, 900000, 2500000, 1800000, 2600000],
        '成交额': [5880000000, 4600000000, 2450000000, 3960000000, 5820000000,
                 3590000000, 10860000000, 18200000000, 1930000000, 2190000000,
                 2220000000, 4850000000, 1280000000, 4160000000, 10930000000,
                 1760000000, 1320000000, 1700000000, 3590000000, 1520000000,
                 2350000000, 2560000000, 2220000000, 5320000000, 4368000000],
        '振幅': [2.15, 1.86, 1.02, 0.85, 2.56, 3.23, 4.12, 3.88, 1.67, 2.12,
                0.45, 2.85, 0.78, 5.25, 3.16, 1.48, 2.35, 1.92, 1.65, 2.95,
                0.92, 1.15, 0.68, 1.85, 1.73],
        '最高': [1698, 147.5, 48.8, 35.3, 69.2, 22.5, 245, 225, 45.6, 96.5,
                5.25, 23.0, 11.9, 53.5, 49.2, 12.8, 8.5, 15.0, 32.6, 18.4,
                17.0, 28.8, 8.95, 30.1, 170.5],
        '最低': [1662, 143.2, 47.5, 34.8, 67.5, 21.6, 236, 215, 44.5, 93.8,
                5.15, 22.1, 11.6, 50.8, 47.0, 12.2, 8.0, 14.2, 31.5, 17.5,
                16.5, 28.2, 8.82, 29.2, 166.0],
        '今开': [1665, 143.8, 48.2, 35.1, 67.8, 21.8, 238, 218, 44.8, 94.2,
                5.18, 22.2, 11.7, 51.0, 47.5, 12.4, 8.3, 14.3, 31.8, 17.8,
                16.6, 28.3, 8.88, 29.3, 167.0],
        '昨收': [1659.25, 143.76, 48.25, 34.87, 66.95, 22.27, 233.35, 213.37, 45.30, 94.11,
                5.19, 22.10, 11.76, 49.88, 46.99, 12.56, 8.31, 14.36, 31.75, 18.17,
                16.72, 28.32, 8.93, 29.26, 166.45],
        '量比': [0.85, 1.12, 0.72, 0.95, 1.35, 1.68, 1.25, 1.45, 0.78, 0.92,
                0.55, 1.18, 0.68, 1.85, 2.15, 0.72, 0.88, 0.65, 0.82, 1.52,
                0.78, 0.62, 0.95, 1.05, 1.15],
        '换手率': [0.35, 0.82, 0.28, 0.45, 1.23, 2.15, 1.56, 1.88, 0.67, 1.12,
                 0.12, 1.45, 0.56, 3.25, 2.88, 0.78, 1.35, 0.92, 1.15, 2.45,
                 0.68, 0.38, 0.15, 0.92, 1.28],
        '市盈率-动态': [28.5, 22.3, 9.8, 6.2, 14.5, 18.2, 35.6, 42.8, 38.5, 25.6,
                     5.8, 18.5, 5.2, 120.5, 85.2, 8.5, -12.3, 6.8, 32.5, 28.6,
                     5.5, 22.8, 12.5, 18.2, 20.5],
        '市净率': [9.5, 6.2, 1.2, 0.95, 3.8, 2.1, 5.6, 7.2, 6.8, 4.5,
                 0.68, 1.65, 0.55, 8.5, 3.2, 0.85, 0.72, 1.35, 3.2, 2.8,
                 0.62, 3.85, 1.15, 5.2, 7.8],
        '总市值': [2110000000000, 562000000000, 875000000000, 882000000000, 473000000000,
                 167000000000, 696000000000, 968000000000, 288000000000, 196000000000,
                 1850000000000, 334000000000, 229000000000, 128000000000, 380000000000,
                 225000000000, 98000000000, 185000000000, 312000000000, 62000000000,
                 348000000000, 695000000000, 1625000000000, 188000000000, 247000000000],
        '流通市值': [2110000000000, 562000000000, 875000000000, 882000000000, 473000000000,
                   167000000000, 696000000000, 968000000000, 288000000000, 196000000000,
                   1850000000000, 334000000000, 229000000000, 128000000000, 380000000000,
                   225000000000, 98000000000, 185000000000, 312000000000, 62000000000,
                   348000000000, 695000000000, 1625000000000, 188000000000, 247000000000],
        '60日涨跌幅': [8.5, 5.2, -3.8, 2.1, 12.3, -8.5, 18.6, 22.5, -5.2, 6.8,
                    1.2, 9.5, 0.8, 25.6, 15.2, -2.5, -8.8, 12.5, 4.2, -6.5,
                    2.8, 5.5, -1.2, 6.8, 7.2],
    })
    return _AKSHARE_DEMO_SPOT


def safe_akshare_call(func, *args, **kwargs):
    """安全调用 akshare 接口, 带重试和 User-Agent 轮换

    Args:
        func: akshare 函数引用 (如 ak.stock_zh_a_spot_em)
        *args, **kwargs: 传递给 akshare 函数的参数

    Returns:
        DataFrame 或 None (失败时返回 None)
    """
    import random
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15',
    ]
    max_retries = 2
    for attempt in range(max_retries):
        try:
            # 尝试设置环境变量中的 User-Agent (akshare 部分接口支持)
            os.environ.setdefault('AKSHARE_UA', random.choice(user_agents))
            result = func(*args, **kwargs)
            if result is not None and len(result) > 0:
                return result
        except Exception as e:
            logger.warning(f'akshare 调用失败 (attempt {attempt+1}/{max_retries}): {e}')
            if attempt < max_retries - 1:
                time.sleep(1 * (attempt + 1))  # 递增等待
    return None


@st.cache_data(ttl=60, show_spinner=False)
def safe_get_spot_df():
    """安全获取 A 股实时行情: SQLite → 东方财富直连 → akshare → 演示数据

    Returns:
        pd.DataFrame: 包含 代码/名称/最新价/涨跌幅 等列的 DataFrame
    """
    # 1. Try SQLite first (fastest, always available)
    if HAS_SQLITE_DB:
        try:
            df = _qi_db.get_stock_spot()
            if df is not None and len(df) > 0:
                # Map SQLite column names to akshare-style column names
                col_map = {
                    'code': '代码', 'name': '名称', 'latest_price': '最新价',
                    'change_pct': '涨跌幅', 'pe_ttm': '市盈率-动态',
                    'pb': '市净率', 'total_mv': '总市值',
                    'turnover_rate': '换手率', 'amount': '成交额',
                    'change_pct_60d': '60日涨跌幅',
                }
                rename_map = {k: v for k, v in col_map.items() if k in df.columns}
                if rename_map:
                    df = df.rename(columns=rename_map)
                return df
        except Exception:
            pass

    # 2. Try 东方财富直连 HTTP API (works on ECS servers)
    try:
        from features.eastmoney_direct import fetch_stock_spot
        df = fetch_stock_spot()
        if df is not None and len(df) > 0:
            # 同时写入 SQLite 缓存
            if HAS_SQLITE_DB:
                try:
                    _qi_db.upsert_stock_spot(df)
                except Exception:
                    pass
            return df
    except Exception as e:
        logger.warning(f'东方财富直连 API 失败: {e}')

    # 3. Try Baostock (服务器环境可用, 不封 IP)
    try:
        from features.eastmoney_direct import _baostock_fetch_spot
        df = _baostock_fetch_spot()
        if df is not None and len(df) > 0:
            # 同时写入 SQLite 缓存
            if HAS_SQLITE_DB:
                try:
                    _qi_db.upsert_stock_spot(df)
                except Exception:
                    pass
            return df
    except Exception as e:
        logger.warning(f'Baostock 行情获取失败: {e}')

    # 4. Try akshare (existing logic)
    result = safe_akshare_call(ak.stock_zh_a_spot_em)
    if result is not None:
        # 同时写入 SQLite 缓存
        if HAS_SQLITE_DB:
            try:
                _qi_db.upsert_stock_spot(result)
            except Exception:
                pass
        return result

    # 4. Demo data fallback (existing)
    logger.warning('akshare stock_zh_a_spot_em 不可用, 使用演示数据')
    return _get_demo_spot_df()


@st.cache_data(ttl=300, show_spinner=False)
def safe_get_stock_info(stock_code: str) -> dict:
    """安全获取个股基本信息: SQLite → 东方财富直连 → akshare → 空 dict

    Args:
        stock_code: 股票代码 (如 600519)

    Returns:
        dict: {item: value} 格式的个股信息
    """
    # 1. Try SQLite first
    if HAS_SQLITE_DB:
        try:
            profile = _qi_db.get_stock_profile(stock_code)
            if profile:
                return profile
        except Exception:
            pass

    # 2. Try 东方财富直连
    try:
        from features.eastmoney_direct import fetch_stock_profile
        profile = fetch_stock_profile(stock_code)
        if profile:
            # 写入 SQLite 缓存
            if HAS_SQLITE_DB:
                try:
                    _qi_db.upsert_stock_profile(stock_code, json.dumps(profile, ensure_ascii=False))
                except Exception:
                    pass
            return profile
    except Exception as e:
        logger.warning(f'东方财富直连个股信息失败 ({stock_code}): {e}')

    # 3. Try akshare
    try:
        df_info = safe_akshare_call(ak.stock_individual_info_em, symbol=stock_code)
        if df_info is not None and len(df_info) > 0:
            info_dict = {}
            item_col = [c for c in df_info.columns if 'item' in c.lower() or '指标' in c]
            val_col = [c for c in df_info.columns if 'value' in c.lower() or '值' in c]
            if item_col and val_col:
                for _, row in df_info.iterrows():
                    info_dict[str(row[item_col[0]])] = str(row[val_col[0]])
            else:
                for _, row in df_info.iterrows():
                    info_dict[str(row.iloc[0])] = str(row.iloc[1])
            # 写入 SQLite 缓存
            if HAS_SQLITE_DB and info_dict:
                try:
                    _qi_db.upsert_stock_profile(stock_code, json.dumps(info_dict, ensure_ascii=False))
                except Exception:
                    pass
            return info_dict
    except Exception as e:
        logger.warning(f'个股信息获取失败 ({stock_code}): {e}')

    # V3.13: 从 stock_spot 表构造 profile (ECS 上 akshare/东方财富被封时的兜底)
    if HAS_SQLITE_DB:
        try:
            df_spot = _qi_db.get_stock_spot()
            if df_spot is not None and not df_spot.empty:
                code_str = str(stock_code).strip()
                row = df_spot[df_spot['code'].astype(str).str.strip() == code_str]
                if not row.empty:
                    r = row.iloc[0]
                    def _safe_val(key):
                        v = r.get(key)
                        if v is None or (isinstance(v, float) and math.isnan(v)):
                            return None
                        return v
                    profile = {
                        '股票代码': code_str,
                        '股票名称': _safe_val('name'),
                        '总市值': _safe_val('total_mv'),
                        '流通市值': _safe_val('total_mv'),
                        '市盈率-动态': _safe_val('pe_ttm'),
                        '市净率': _safe_val('pb'),
                        '换手率': _safe_val('turnover_rate'),
                        '最新价': _safe_val('latest_price'),
                        '涨跌幅': _safe_val('change_pct'),
                    }
                    # 过滤 None 值
                    profile = {k: v for k, v in profile.items() if v is not None}
                    if profile:
                        return profile
        except Exception as e:
            logger.warning(f'从 stock_spot 构造 profile 失败 ({stock_code}): {e}')

    return {}


def safe_metric(label, value, delta=None):
    """Safe st.metric wrapper - handles list/dict/None values gracefully"""
    try:
        if isinstance(value, (list, dict, set, tuple)):
            value = str(value) if value else 'N/A'
        if value is None:
            value = 'N/A'
        if isinstance(value, str):
            st.metric(label, value, delta if delta else '')
        elif isinstance(value, (int, float)):
            st.metric(label, value, delta)
        else:
            st.metric(label, str(value), '')
    except Exception:
        st.metric(label, 'N/A', '')


def safe_page_section(page_name, render_func, *args, **kwargs):
    """Wrap page rendering with error handling - no traceback shown to users"""
    try:
        render_func(*args, **kwargs)
    except Exception as e:
        logger.error(f'Page [{page_name}] error: {e}')
        st.error(f'页面加载出错: {page_name}')
        st.info('请刷新页面重试，如问题持续请联系管理员')
        with st.expander('技术详情 (仅供调试)'):
            import traceback
            st.code(traceback.format_exc(), language='text')

from backtest_engine import BacktestEngine, BacktestConfig, StrategyType
from data_cache import get_data_cache
from ai.agent_orchestrator import MainAgent
from ai.data_grounder import DataGrounder
from ai.citation_system import CitationTracker
from features.stock_screener import NaturalLanguageScreener
from features.factor_scorer import MultiFactorScorer
from features.stock_comparison import StockComparator
from features.portfolio_manager import PortfolioManager
from features.alert_system import SmartAlertEngine
from features.market_dashboard import MarketDashboard
from features.trade_simulator import TradeSimulator, RiskControlEngine, Order
from features.task_scheduler import ResearchTaskScheduler, AutoReportGenerator, TASK_TEMPLATES
from features.sentiment_analyzer import SentimentAnalyzer
from features.supply_chain_tracker import SupplyChainTracker, INDUSTRY_CHAINS

try:
    from features.qlib_integration import AlphaFactorMiner, VectorBTEngine, FactorICTester, SignalVerifier
    HAS_QLIB = True
except ImportError:
    HAS_QLIB = False

try:
    from features.multi_source_data import DataHub, SentimentVectorStore, AltDataSignalGenerator
    HAS_MULTI_SOURCE = True
except ImportError:
    HAS_MULTI_SOURCE = False

try:
    from features.macro_factor_fusion import MacroFactorModel, FactorFusionEngine, SignalVerificationData, ExabelStyleDashboard
    HAS_MACRO_FUSION = True
except ImportError:
    HAS_MACRO_FUSION = False

try:
    from features.sqlite_data_layer import QIDataDB
    _qi_db = QIDataDB()
    HAS_SQLITE_DB = True
except ImportError:
    _qi_db = None
    HAS_SQLITE_DB = False
from data_cache import DataCacheManager
from eastmoney_source import EastMoneyChoiceSource

# ============== 真实 LLM 接入 (B7) ==============
def get_llm_config():
    """从 Streamlit Secrets 或环境变量读取 LLM 配置

    V3.11 升级: 优化 LLM 优先级链, MiniMax 余额不足降级
    支持 5 家 LLM 优先级: Qwen3.6-Plus > SenseNova > DeepSeek > MiniMax-M3 > GLM-4 > 离线兜底

    V3.11 变更:
    - MiniMax-M3 余额耗尽 (402 insufficient_balance), 降级到第 4 优先级
    - SenseNova 升级到第 2 优先级 (速度快, 稳定)
    - DeepSeek 升级到第 3 优先级 (deepseek-v4-pro, 能力强)
    - 添加余额检测: 首次调用失败 (402/429) 后自动跳过该 provider

    Qwen3.6-Plus 优势:
    - 阿里云百炼最新旗舰模型, 综合能力最强
    - 中文金融场景表现最优, 支持长上下文
    - API 稳定, 国内延迟低
    """
    config = {'provider': None, 'api_key': None, 'model': None, 'base_url': None, 'workspace_id': None}

    # 读取已知的失败 provider 列表 (余额不足/限流等), 跳过它们
    _failed_providers = set()
    try:
        _failed_providers = set(st.session_state.get('_llm_failed_providers', []))
    except Exception:
        pass

    def _try_provider(name, provider_key, default_model, default_url, extra_field=None):
        """尝试加载某个 provider 配置, 如果在失败列表中则跳过"""
        if provider_key in _failed_providers:
            return False
        try:
            secret_key = provider_key + '_API_KEY'
            if secret_key in st.secrets:
                config['provider'] = name
                config['api_key'] = st.secrets[secret_key]
                config['model'] = st.secrets.get(provider_key + '_MODEL', default_model)
                config['base_url'] = st.secrets.get(provider_key + '_BASE_URL', default_url)
                if extra_field:
                    config['workspace_id'] = st.secrets.get(provider_key + '_WORKSPACE_ID', None)
                return True
        except Exception:
            pass
        return False

    # 1. Qwen3.6-Plus (PRIMARY - 能力最强, 中文金融最优)
    if _try_provider('qwen', 'QWEN', 'qwen3.6-plus',
                     'https://token-plan.cn-beijing.maas.aliyuncs.com/compatible-mode/v1/chat/completions',
                     extra_field=True):
        return config

    # 2. SenseNova (BACKUP 1 - 商汤日日新, 速度快, V3.11 升级)
    if _try_provider('sensenova', 'SENSENOVA', 'sensenova-6.7-flash-lite',
                     'https://token.sensenova.cn/v1/chat/completions'):
        return config

    # 3. DeepSeek (BACKUP 2 - deepseek-v4-pro, 能力强, V3.11 升级)
    if _try_provider('deepseek', 'DEEPSEEK', 'deepseek-chat',
                     'https://api.deepseek.com/chat/completions'):
        return config

    # 4. MiniMax-M3 (BACKUP 3 - V3.11 降级, 余额不足待充值)
    if _try_provider('minimax', 'MINIMAX', 'MiniMax-M3',
                     'https://api.minimaxi.com/v1/chat/completions'):
        return config

    # 5. GLM-4 (BACKUP 4 - 智谱 AI)
    if _try_provider('glm', 'GLM', 'glm-4-plus',
                     'https://open.bigmodel.cn/api/paas/v4/chat/completions'):
        return config

    # 备选环境变量 (本地测试) - V3.11 同样调整优先级
    if os.environ.get('QWEN_API_KEY'):
        config['provider'] = 'qwen'
        config['api_key'] = os.environ['QWEN_API_KEY']
        config['model'] = os.environ.get('QWEN_MODEL', 'qwen3.6-plus')
        config['base_url'] = os.environ.get('QWEN_BASE_URL', 'https://token-plan.cn-beijing.maas.aliyuncs.com/compatible-mode/v1/chat/completions')
    elif os.environ.get('SENSENOVA_API_KEY'):
        config['provider'] = 'sensenova'
        config['api_key'] = os.environ['SENSENOVA_API_KEY']
        config['model'] = os.environ.get('SENSENOVA_MODEL', 'sensenova-6.7-flash-lite')
        config['base_url'] = os.environ.get('SENSENOVA_BASE_URL', 'https://token.sensenova.cn/v1/chat/completions')
    elif os.environ.get('DEEPSEEK_API_KEY'):
        config['provider'] = 'deepseek'
        config['api_key'] = os.environ['DEEPSEEK_API_KEY']
        config['model'] = os.environ.get('DEEPSEEK_MODEL', 'deepseek-chat')
        config['base_url'] = os.environ.get('DEEPSEEK_BASE_URL', 'https://api.deepseek.com/chat/completions')
    elif os.environ.get('MINIMAX_API_KEY'):
        config['provider'] = 'minimax'
        config['api_key'] = os.environ['MINIMAX_API_KEY']
        config['model'] = os.environ.get('MINIMAX_MODEL', 'MiniMax-M3')
        config['base_url'] = os.environ.get('MINIMAX_BASE_URL', 'https://api.minimaxi.com/v1/chat/completions')
    elif os.environ.get('GLM_API_KEY'):
        config['provider'] = 'glm'
        config['api_key'] = os.environ['GLM_API_KEY']
        config['model'] = os.environ.get('GLM_MODEL', 'glm-4-plus')
        config['base_url'] = os.environ.get('GLM_BASE_URL', 'https://open.bigmodel.cn/api/paas/v4/chat/completions')

    return config


def _mark_llm_failed(provider: str):
    """标记某个 LLM provider 为失败状态 (余额不足/限流等), 后续自动跳过

    V3.11 新增: 自动降级机制, 避免反复调用已失败的 provider
    """
    try:
        failed = st.session_state.get('_llm_failed_providers', [])
        if provider not in failed:
            failed.append(provider)
            st.session_state['_llm_failed_providers'] = failed
            logger.warning("LLM provider '%s' 已标记为失败, 后续将跳过", provider)
    except Exception:
        pass


def _extract_json_from_text(text):
    """从文本中提取 JSON 块 (处理 markdown 代码块 + 纯文本)"""
    if not text:
        return None
    text = text.strip()
    # 尝试 1: 直接解析
    try:
        return json.loads(text)
    except Exception:
        pass
    # 尝试 2: 提取 ```json ... ``` 代码块
    import re
    m = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(1))
        except Exception:
            pass
    # 尝试 3: 提取第一个 {...} 块
    m = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(0))
        except Exception:
            pass
    return None


@st.cache_data(ttl=300, show_spinner=False)
def _fetch_market_context() -> str:
    """获取实时市场数据上下文, 用于注入 AI Q&A 的系统提示

    Returns:
        str: 格式化的市场数据文本, 失败时返回空字符串
    """
    context_parts = []

    # 1. 尝试从 report_generator.fetch_macro_data 获取宏观市场数据
    try:
        from features.report_generator import fetch_macro_data
        macro = fetch_macro_data()
        if macro and macro.get('indices'):
            indices_str = ", ".join([
                f"{idx['name']}: {idx.get('price', 'N/A')} ({idx.get('change_pct', 0):+.2f}%)"
                for idx in macro['indices']
            ])
            context_parts.append(f"【主要指数】{indices_str}")
        if macro and macro.get('north_flow'):
            try:
                nf = float(macro['north_flow'])
                context_parts.append(f"【北向资金】净流入: {nf/1e8:.2f}亿元" if abs(nf) > 1e8 else f"【北向资金】净流入: {nf:.2f}亿元")
            except (TypeError, ValueError):
                pass
        if macro and macro.get('limit_up') is not None:
            context_parts.append(f"【涨跌停】涨停: {macro.get('limit_up', 0)}只, 跌停: {macro.get('limit_down', 0)}只")
        if macro and macro.get('breadth'):
            b = macro['breadth']
            context_parts.append(f"【市场宽度】上涨: {b.get('advance', 0)}家, 下跌: {b.get('decline', 0)}家, 平盘: {b.get('equal', 0)}家")
        context_parts.append(f"(数据来源: {macro.get('source', 'akshare')})")
    except Exception as e:
        logger.warning(f'fetch_macro_data 失败: {e}')

    # 2. 尝试获取 A 股行情概况 (涨幅前5 + 跌幅前5)
    try:
        df_spot = safe_get_spot_df()
        if df_spot is not None and len(df_spot) > 0:
            chg_col = None
            for col in ['涨跌幅', '涨跌幅(%)']:
                if col in df_spot.columns:
                    chg_col = col
                    break
            name_col = '名称' if '名称' in df_spot.columns else None
            if chg_col and name_col:
                df_tmp = df_spot.copy()
                df_tmp[chg_col] = pd.to_numeric(df_tmp[chg_col], errors='coerce')
                df_tmp = df_tmp.dropna(subset=[chg_col])
                # 涨幅前5
                top5 = df_tmp.nlargest(5, chg_col)
                top5_str = ", ".join([f"{r[name_col]}({r[chg_col]:+.2f}%)" for _, r in top5.iterrows()])
                context_parts.append(f"【涨幅前5】{top5_str}")
                # 跌幅前5
                bot5 = df_tmp.nsmallest(5, chg_col)
                bot5_str = ", ".join([f"{r[name_col]}({r[chg_col]:+.2f}%)" for _, r in bot5.iterrows()])
                context_parts.append(f"【跌幅前5】{bot5_str}")
    except Exception as e:
        logger.warning(f'获取行情概况失败: {e}')

    return "\n".join(context_parts) if context_parts else ""


def ai_qa_real(question, config, timeout=90, history=None):  # V3.14: 30→90秒, qwen3.6-plus需要更长响应时间
    """真实 LLM 调用 (SenseNova / DeepSeek / Qwen)

    Args:
        question: 用户问题
        config: get_llm_config() 返回的配置
        timeout: 超时秒数
        history: 对话历史 (list of {role, content, ...}), 最多 5 轮

    Returns:
        dict: {'title': str, 'summary': str, 'data': dict, 'recommendation': str, 'reasoning': str}
    """
    system_prompt = """你是 QuantInsight Pro 的 AI 投研助手, 由慧点资本 (InsightQuant) 联合杭州永字资管打造.
请基于提供的实时市场数据和金融专业知识, 用结构化方式回答用户的投研问题.
回答时务必引用提供的实时数据, 并标注数据来源.

回答格式 (严格 JSON, 不要 markdown 代码块):
{
  "title": "一句话标题",
  "summary": "3-5 个关键点 (Markdown 格式, 引用实时数据并标注来源)",
  "data": {"指标1": "值1", "指标2": "值2", "指标3": "值3"},
  "recommendation": "2-3 条投资建议"
}"""

    # === 注入实时市场数据到系统提示 ===
    market_context = _fetch_market_context()
    if market_context:
        system_prompt += f"\n\n以下是当前实时市场数据，请在回答中引用并标注来源:\n{market_context}"

    headers = {
        'Authorization': f'Bearer {config["api_key"]}',
        'Content-Type': 'application/json',
    }
    # DashScope workspace header (required for workspace-specific API keys)
    if config.get('workspace_id'):
        headers['X-DashScope-WorkSpace'] = config['workspace_id']

    # 构建 messages (含历史上下文)
    messages = [{'role': 'system', 'content': system_prompt}]
    if history:
        for msg in history:
            if msg['role'] == 'user':
                messages.append({'role': 'user', 'content': msg['content']})
            else:  # assistant - 转为简化文本保持上下文
                content = f"上轮标题: {msg.get('title', '')}\n摘要: {msg.get('summary', '')}\n建议: {msg.get('recommendation', '')}"
                messages.append({'role': 'assistant', 'content': content})
    messages.append({'role': 'user', 'content': question})

    # Reasoning models need more tokens (thinking + answer)
    is_reasoning = 'v4' in config['model'] or 'r1' in config['model'] or 'reasoner' in config['model'] or '3.7' in config['model'] or 'max' in config['model'].lower()
    payload = {
        'model': config['model'],
        'messages': messages,
        'temperature': 0.7,
        'max_tokens': 4000 if is_reasoning else 2000,
    }
    # V3.12: qwen3.x-plus 是推理模型, 默认生成5000+字思考内容导致超时
    # 禁用思考模式后, 单次调用从36s降至8s
    model_name_lower = config['model'].lower()
    if 'qwen3' in model_name_lower or 'qwen-3' in model_name_lower:
        payload['enable_thinking'] = False

    # DeepSeek / Qwen 支持 response_format: json_object (reasoning models 除外)
    if config['provider'] in ('deepseek', 'qwen') and not is_reasoning:
        payload['response_format'] = {'type': 'json_object'}

    try:
        resp = requests.post(config['base_url'], headers=headers, json=payload, timeout=timeout)
        # V3.11: 检测余额不足/限流, 自动标记失败并降级
        if resp.status_code in (402, 429):
            _mark_llm_failed(config['provider'].upper())
            raise RuntimeError(f"LLM {config['provider']} 返回 {resp.status_code} (余额不足/限流), 已标记降级")
        resp.raise_for_status()
        result = resp.json()

        msg = result['choices'][0]['message']
        content = msg.get('content', '') or ''
        reasoning = msg.get('reasoning_content', '') or ''  # SenseNova / DeepSeek-R1/V4 特有
        # SenseNova: content 可能在不同位置
        if not content.strip():
            # 尝试从 delta 或 text 字段获取
            content = msg.get('text', '') or msg.get('delta', {}).get('content', '') if isinstance(msg.get('delta'), dict) else ''
        # Reasoning model: content may be empty, actual answer in reasoning_content
        if not content.strip() and reasoning.strip():
            content = reasoning
        # 最终兜底: 从整个 result 中提取文本
        if not content.strip():
            for key in ['output', 'text', 'result']:
                if key in result and isinstance(result[key], str):
                    content = result[key]
                    break
                elif key in result and isinstance(result[key], dict):
                    content = result[key].get('text', result[key].get('content', ''))
                    if content:
                        break

        # 解析 JSON
        parsed = _extract_json_from_text(content)
        if parsed is None:
            # 解析失败, 用纯文本 fallback
            return {
                'title': 'AI 投研分析',
                'summary': content if content else reasoning[:500] if reasoning else 'AI 响应解析失败',
                'data': {},
                'recommendation': '请参考上述摘要内容',
                'reasoning': reasoning[:300] if reasoning else '',
            }

        # 兼容 list / str 类型的 summary / recommendation
        def _to_str(v, default=''):
            if v is None:
                return default
            if isinstance(v, list):
                return '\n'.join(str(x) for x in v)
            return str(v)

        return {
            'title': _to_str(parsed.get('title'), 'AI 投研分析'),
            'summary': _to_str(parsed.get('summary'), content),
            'data': parsed.get('data', {}) if isinstance(parsed.get('data'), dict) else {},
            'recommendation': _to_str(parsed.get('recommendation'), '请参考摘要中的具体分析'),
            'reasoning': reasoning[:300] if reasoning else '',
        }
    except Exception as e:
        raise RuntimeError(f"LLM 调用失败 ({config['provider']}): {e}")

# ============== 页面配置 ==============
st.set_page_config(
    page_title='QuantInsight Pro - 智能投研平台',
    page_icon='📊',
    layout='wide',
    initial_sidebar_state='expanded',
)

# ============== 认证系统 ==============
from auth.database import UserDB
from auth.session_manager import SessionManager
from auth.pages import render_login_page, render_register_page, render_trial_gate, render_profile_page

# Initialize auth
if 'user_db' not in st.session_state:
    st.session_state.user_db = UserDB()
if 'session_mgr' not in st.session_state:
    st.session_state.session_mgr = SessionManager(st.session_state.user_db)

_db = st.session_state.user_db
_session_mgr = st.session_state.session_mgr

# Auth gate: show login/register if not authenticated
if not _session_mgr.is_authenticated(st.session_state):
    _spacer_l, col_r, _spacer_r = st.columns([1, 2, 1])
    with col_r:
        tab_login, tab_register = st.tabs(['🔐 登录', '📝 注册'])
        with tab_login:
            render_login_page(_session_mgr)
        with tab_register:
            render_register_page(_session_mgr, _db)
    st.stop()

# Trial gate: show activation code page if trial exhausted
if not _session_mgr.check_trial(st.session_state):
    render_trial_gate(_session_mgr, _db)
    st.stop()

# Log page visit
if 'auth_last_page' not in st.session_state:
    st.session_state.auth_last_page = ''

# ============== 主题样式 ==============
from ui_themes import apply_theme, render_theme_toggle
apply_theme()

# ============== 数据加载（缓存）==============
@st.cache_data(ttl=3600)
def load_hs300():
    return load_index('sh000300')

@st.cache_data(ttl=3600)
def load_zz500():
    return load_index('sh000905')

@st.cache_data(ttl=3600)
def load_cyb():
    return load_index('sz399006')

@st.cache_data(ttl=3600, show_spinner=False)
def load_index(symbol):
    """统一指数加载 (缓存 1 小时), 替代直接 ak.stock_zh_index_daily 调用"""
    try:
        df = ak.stock_zh_index_daily(symbol=symbol)
        df['date'] = pd.to_datetime(df['date'])
        return df
    except Exception:
        return None

@st.cache_data(ttl=3600, show_spinner=False)
def load_industry_cons(symbol):
    """行业成分股加载 (缓存 1 小时)"""
    try:
        return ak.stock_board_industry_cons_em(symbol=symbol)
    except Exception:
        return None

@st.cache_data(ttl=86400, show_spinner=False)
def load_sw_index():
    """申万三级行业 (缓存 24 小时, 静态更新)"""
    try:
        return ak.sw_index_third_info()
    except Exception:
        return None

@st.cache_data(ttl=1800, show_spinner=False)
def load_stock_news():
    """加载 A 股新闻舆情 (缓存 30 分钟, 多端点回退)"""
    # Primary endpoint
    try:
        df = ak.stock_news_em(symbol='财经')
        if df is not None and len(df) > 0:
            return df.head(50)
    except Exception:
        pass
    # Fallback 1: different keyword
    try:
        df = ak.stock_news_em(symbol='沪深')
        if df is not None and len(df) > 0:
            return df.head(50)
    except Exception:
        pass
    # Fallback 2: global info
    try:
        df = ak.stock_info_global_em()
        if df is not None and len(df) > 0:
            return df.head(50)
    except Exception:
        pass
    return None

@st.cache_data(ttl=300, show_spinner=False)
def load_northbound_flow():
    """加载北向资金数据 (缓存 5 分钟, 多端点回退): SQLite → 东方财富直连 → akshare
    Returns: (net_amount, direction_str) or None
    """
    def _valid_number(v):
        if isinstance(v, (int, float)):
            return not (math.isnan(v) or math.isinf(v))
        return False

    # 0. Try SQLite first
    if HAS_SQLITE_DB:
        try:
            nb_df = _qi_db.get_northbound_flow(days=5)
            if nb_df is not None and len(nb_df) > 0:
                # Find the net flow column
                flow_col = None
                for c in nb_df.columns:
                    if 'net_flow' in c.lower() or '净流入' in c or '净买' in c:
                        flow_col = c
                        break
                if flow_col is None:
                    # Try last numeric column
                    for c in nb_df.columns:
                        if nb_df[c].dtype in ['float64', 'int64', 'float32', 'int32']:
                            flow_col = c
                            break
                if flow_col:
                    net = float(nb_df[flow_col].iloc[-1])
                    if _valid_number(net):
                        direction = '净流入' if net >= 0 else '净流出'
                        return (net, direction)
        except Exception as e:
            logger.warning(f'北向资金 SQLite 读取失败: {e}')

    # 1. Try 东方财富直连
    try:
        from features.eastmoney_direct import fetch_northbound_flow
        nb_df = fetch_northbound_flow(days=5)
        if nb_df is not None and len(nb_df) > 0:
            # 写入 SQLite 缓存
            if HAS_SQLITE_DB:
                try:
                    _qi_db.upsert_northbound_flow(nb_df)
                except Exception:
                    pass
            flow_col = None
            for c in nb_df.columns:
                if '净流入' in c or 'net_flow' in c.lower():
                    flow_col = c
                    break
            if flow_col:
                net = float(nb_df[flow_col].iloc[-1])
                if _valid_number(net):
                    direction = '净流入' if net >= 0 else '净流出'
                    return (net, direction)
    except Exception as e:
        logger.warning(f'北向资金东方财富直连失败: {e}')

    # 2. Primary: akshare
    try:
        df = ak.stock_hsgt_north_net_flow_in_em(symbol='北向')
        if df is not None and len(df) > 0:
            latest = df.iloc[-1]
            net = latest.get('当日净流入', latest.get('当日资金流入', 0))
            if _valid_number(net):
                direction = '净流入' if net >= 0 else '净流出'
                return (float(net), direction)
    except Exception as e:
        logger.warning(f'北向资金主接口失败: {e}')
    # 3. Fallback: sum 沪股通 + 深股通
    try:
        total = 0.0
        valid_parts = 0
        for sym in ['沪股通', '深股通']:
            df = ak.stock_hsgt_hist_em(symbol=sym)
            if df is not None and len(df) > 0:
                col = '当日资金流入' if '当日资金流入' in df.columns else '当日净流入'
                val = float(df[col].iloc[-1])
                if _valid_number(val):
                    total += val
                    valid_parts += 1
        if valid_parts > 0:
            direction = '净流入' if total >= 0 else '净流出'
            return (total, direction)
    except Exception as e:
        logger.warning(f'北向资金回退接口失败: {e}')
    return None

@st.cache_data(ttl=60, show_spinner=False)
def get_current_price(stock_code: str) -> float:
    """获取股票最新价（用于模拟交易市价单）"""
    # V3.13: 优先直接查 SQLite stock_spot 表 (避免 safe_get_spot_df 的超时链)
    if HAS_SQLITE_DB:
        try:
            df = _qi_db.get_stock_spot()
            if df is not None and not df.empty:
                code_str = str(stock_code).strip()
                row = df[df['code'].astype(str).str.strip() == code_str]
                if not row.empty:
                    price = row.iloc[0].get('latest_price')
                    if price is not None and not (isinstance(price, float) and math.isnan(price)):
                        return float(price)
        except Exception as e:
            logger.warning(f'SQLite 获取 {stock_code} 价格失败: {e}')

    try:
        df = safe_get_spot_df()
        if df is not None and len(df) > 0:
            # 代码列可能带 .sh/.sz 后缀，统一处理
            normalized = str(stock_code).strip()
            mask = df['代码'].astype(str).str.strip() == normalized
            if mask.any():
                price = df.loc[mask, '最新价'].iloc[-1]
                if isinstance(price, (int, float)) and not (math.isnan(price) or math.isinf(price)):
                    return float(price)
            # 尝试匹配带后缀
            for suffix in ['.SH', '.SZ', '.BJ']:
                mask = df['代码'].astype(str).str.upper() == (normalized + suffix)
                if mask.any():
                    price = df.loc[mask, '最新价'].iloc[-1]
                    if isinstance(price, (int, float)) and not (math.isnan(price) or math.isinf(price)):
                        return float(price)
    except Exception as e:
        logger.warning(f'获取 {stock_code} 最新价失败: {e}')
    return 0.0


@st.cache_data(ttl=300)
def load_stock_pool():
    """加载 A 股股票池（部分代表性股票）: SQLite → 东方财富直连 → akshare → 静态列表"""
    # 1. Try SQLite first
    if HAS_SQLITE_DB:
        try:
            df = _qi_db.get_stock_spot()
            if df is not None and len(df) > 0:
                # V3.14: 按成交额排序, 避免total_mv全NULL时返回冷门股
                if 'amount' in df.columns:
                    df = df.sort_values('amount', ascending=False)
                # Map column names
                col_map = {
                    'code': '代码', 'name': '名称', 'latest_price': '最新价',
                    'change_pct': '涨跌幅', 'pe_ttm': '市盈率-动态',
                    'pb': '市净率', 'total_mv': '总市值',
                    'turnover_rate': '换手率', 'amount': '成交额',
                    'change_pct_60d': '60日涨跌幅',
                }
                rename_map = {k: v for k, v in col_map.items() if k in df.columns}
                if rename_map:
                    df = df.rename(columns=rename_map)
                return df.head(200)
        except Exception:
            pass
    # 2. Try 东方财富直连
    try:
        from features.eastmoney_direct import fetch_stock_spot
        df = fetch_stock_spot()
        if df is not None and len(df) > 0:
            # 同时写入 SQLite 缓存
            if HAS_SQLITE_DB:
                try:
                    _qi_db.upsert_stock_spot(df)
                except Exception:
                    pass
            return df.head(200)
    except Exception:
        pass
    # 3. Try Baostock (服务器环境可用)
    try:
        from features.eastmoney_direct import _baostock_fetch_spot
        df = _baostock_fetch_spot()
        if df is not None and len(df) > 0:
            if HAS_SQLITE_DB:
                try:
                    _qi_db.upsert_stock_spot(df)
                except Exception:
                    pass
            return df.head(200)
    except Exception:
        pass
    # 4. Try akshare via safe_get_spot_df
    try:
        df = safe_get_spot_df()
        if df is not None and len(df) > 0:
            return df.head(200)  # 取前 200 只做演示
    except Exception:
        pass
    # 3. Fallback: 静态列表（包含完整列以支持筛选）
    return pd.DataFrame({
        '代码': ['600519', '000858', '601318', '600036', '000333',
                '601012', '002594', '300750', '600276', '601888',
                '601398', '600030', '000001', '002230', '688981',
                '600048', '000002', '601919', '600754', '002129'],
        '名称': ['贵州茅台', '五粮液', '中国平安', '招商银行', '美的集团',
                '隆基绿能', '比亚迪', '宁德时代', '恒瑞医药', '中国中免',
                '工商银行', '中信证券', '平安银行', '科大讯飞', '中芯国际',
                '保利发展', '万科A', '中远海控', '锦江酒店', '中环股份'],
        '最新价': [1680, 145, 48, 35, 68, 22, 240, 220, 45, 95,
                 5.2, 22.5, 11.8, 52, 48, 12.5, 8.2, 14.6, 32, 18],
        '涨跌幅': [1.25, 0.86, -0.52, 0.38, 1.56, -1.23, 2.85, 3.12, -0.67, 0.95,
                 0.19, 1.82, 0.34, 4.25, 2.16, -0.48, -1.35, 1.67, 0.78, -0.92],
        '换手率': [0.35, 0.82, 0.28, 0.45, 1.23, 2.15, 1.56, 1.88, 0.67, 1.12,
                 0.12, 1.45, 0.56, 3.25, 2.88, 0.78, 1.35, 0.92, 1.15, 2.45],
        '市盈率-动态': [28.5, 22.3, 9.8, 6.2, 14.5, 18.2, 35.6, 42.8, 38.5, 25.6,
                     5.8, 18.5, 5.2, 120.5, 85.2, 8.5, -12.3, 6.8, 32.5, 28.6],
        '市净率': [9.5, 6.2, 1.2, 0.95, 3.8, 2.1, 5.6, 7.2, 6.8, 4.5,
                 0.68, 1.65, 0.55, 8.5, 3.2, 0.85, 0.72, 1.35, 3.2, 2.8],
        '总市值': [2110000000000, 562000000000, 875000000000, 882000000000, 473000000000,
                 167000000000, 696000000000, 968000000000, 288000000000, 196000000000,
                 1850000000000, 334000000000, 229000000000, 128000000000, 380000000000,
                 225000000000, 98000000000, 185000000000, 312000000000, 62000000000],
        '成交额': [5880000000, 4600000000, 2450000000, 3960000000, 5820000000,
                 3590000000, 10860000000, 18200000000, 1930000000, 2190000000,
                 2220000000, 4850000000, 1280000000, 4160000000, 10930000000,
                 1760000000, 1320000000, 1700000000, 3590000000, 1520000000],
        '60日涨跌幅': [8.5, 5.2, -3.8, 2.1, 12.3, -8.5, 18.6, 22.5, -5.2, 6.8,
                    1.2, 9.5, 0.8, 25.6, 15.2, -2.5, -8.8, 12.5, 4.2, -6.5],
    })

# ============== AI 问答模块（模拟）==============
def ai_qa_mock(question):
    """AI 问答的 mock 回答（无 API key 时使用）"""
    question_lower = question.lower()

    templates = {
        '新能源': {
            'title': '新能源行业分析报告',
            'summary': '当前新能源板块呈现以下特点：\n\n1. **锂电产业链**：经历 2022-2023 年下行周期后，2024 年 Q3 起出现结构性反弹，主要受欧美补库+储能需求驱动\n2. **光伏板块**：产能过剩压力持续，但 TOPCon/HJT 新型电池技术带来差异化机会\n3. **风电/核电**：海风进入装机高峰，核电进入新一轮审批周期',
            'data': {
                '新能源指数 PE': '22.5x (近 5 年 30% 分位)',
                '板块年初至今': '-8.2%',
                '机构持仓比例': '12.3% (环比 +0.8pct)',
            },
            'recommendation': '建议关注：储能 > 锂电材料 > 光伏新技术 > 风电海风'
        },
        '半导体': {
            'title': '半导体行业投资分析',
            'summary': '半导体板块分化加剧：\n\n1. **AI 算力链**：HBM/CoWoS 封装/光模块 持续景气\n2. **国产替代**：设备/材料/EDA 加速突破，国产化率提升至 25%\n3. **消费电子链**：库存出清，但终端需求温和复苏',
            'data': {
                '费城半导体指数': '5,250 (+3.2% YTD)',
                '申万半导体 PE': '85x (高位)',
                '存储芯片价格': 'DDR4 8Gb +12% QoQ',
            },
            'recommendation': '优选：AI 算力链 + 国产替代 + 设备材料'
        },
        '消费': {
            'title': '消费板块投资机会',
            'summary': '消费板块出现底部信号：\n\n1. **白酒**：批价企稳，估值回到历史 30% 分位\n2. **食品**：必选消费稳定，可选消费弹性大\n3. **新兴消费**：悦己消费、银发经济持续高增',
            'data': {
                '中证消费 PE': '25.8x (近 5 年 25% 分位)',
                '社零同比': '+3.5% (温和复苏)',
                'CPI 同比': '+0.3%',
            },
            'recommendation': '左侧布局：高端白酒 + 大众食品龙头'
        },
        '医药': {
            'title': '医药行业投资分析',
            'summary': '医药板块分化明显：\n\n1. **创新药**：出海授权交易活跃，BD 金额创新高\n2. **医疗器械**：国产替代加速，高端设备突破\n3. **中药**：政策利好持续，品牌中药估值修复',
            'data': {
                '中证医药 PE': '28.5x (近 5 年 35% 分位)',
                '创新药指数': '+15.2% YTD',
                '医保谈判': '平均降幅 58%',
            },
            'recommendation': '关注：创新药出海 + 医疗器械国产替代 + 品牌中药'
        },
        '金融': {
            'title': '金融行业投资分析',
            'summary': '金融板块估值修复进行中：\n\n1. **银行**：净息差触底，资产质量改善\n2. **保险**：负债端回暖，投资收益改善\n3. **券商**：市场活跃度提升，两融余额回升',
            'data': {
                '银行 PB': '0.55x (历史低位)',
                '保险 NBV 增速': '+18% YoY',
                '券商两融余额': '1.85 万亿',
            },
            'recommendation': '关注：高股息银行 + NBV 改善保险 + 头部券商'
        },
        '军工': {
            'title': '军工行业投资分析',
            'summary': '军工板块进入景气上行周期：\n\n1. **航空发动机**：国产替代关键突破\n2. **导弹/弹药**：订单恢复性增长\n3. **军工电子**：信息化升级驱动',
            'data': {
                '军工指数 PE': '55x (中高位)',
                '军工行业增速': '+12% YoY',
                '订单可见性': '3-5 年',
            },
            'recommendation': '关注：航空发动机 + 军工电子 + 导弹产业链'
        },
        '房地产': {
            'title': '房地产行业投资分析',
            'summary': '房地产政策持续宽松：\n\n1. **政策面**：限购限贷全面放松，利率降至历史低位\n2. **基本面**：销售降幅收窄，但投资仍在下行\n3. **信用面**：房企融资边际改善，但分化加剧',
            'data': {
                '30 城成交面积': '-15% YoY (收窄中)',
                '房贷利率': '3.45% (历史低位)',
                '百强销售': '-20% YoY',
            },
            'recommendation': '谨慎关注：优质央国企 + 物业管理 + 代建'
        },
        '人工智能': {
            'title': 'AI 产业投资分析',
            'summary': 'AI 产业进入应用落地期：\n\n1. **算力层**：GPU 需求持续景气，国产替代加速\n2. **模型层**：开源模型能力快速追赶，推理成本下降\n3. **应用层**：B 端场景率先落地，C 端应用探索中',
            'data': {
                'AI 指数 PE': '65x (高位)',
                'GPU 需求增速': '+80% YoY',
                '开源模型数': '200+ (国内)',
            },
            'recommendation': '关注：算力基础设施 + 垂直场景应用 + 数据要素'
        },
        '宏观': {
            'title': '宏观经济与市场分析',
            'summary': '当前宏观环境分析：\n\n1. **货币政策**：降准降息空间仍在，流动性偏宽松\n2. **财政政策**：专项债加速发行，基建托底\n3. **外部环境**：美联储降息预期升温，人民币汇率企稳',
            'data': {
                'GDP 增速': '5.2% (目标 5%)',
                'CPI': '+0.3% (低位)',
                '10Y 国债': '2.65%',
            },
            'recommendation': '关注：利率敏感型资产 + 红利策略 + 出口链'
        },
        '银行': {
            'title': '银行业投资分析',
            'summary': '银行板块估值修复窗口：\n\n1. **净息差**：LPR 下调影响逐步消化，存款利率同步下调\n2. **资产质量**：不良率稳中有降，拨备充足\n3. **股息率**：平均 5-6%，显著高于国债收益率',
            'data': {
                '银行 PB': '0.55x',
                '平均股息率': '5.8%',
                '不良率': '1.25% (稳定)',
            },
            'recommendation': '关注：高股息大行 + 优质城商行 + 资产质量改善标的'
        },
    }

    for keyword, template in templates.items():
        if keyword in question or keyword in question_lower:
            return template

    # 通用回答
    return {
        'title': '智能投研分析报告',
        'summary': f'针对您的问题"{question[:50]}", 我们整合多源数据进行分析：\n\n1. **市场情绪**：当前 A 股市场情绪中性偏谨慎, 北向资金近期波动加大\n2. **资金流向**：主力资金净流出收窄, 融资余额小幅回升\n3. **技术面**：主要指数在年线附近震荡, 成交量温和放大\n4. **基本面**：宏观数据温和复苏, 政策面偏积极\n5. **风险提示**：关注海外加息预期变化及地缘政治风险',
        'data': {
            '沪深300 PE': '12.5x (近 5 年 40% 分位)',
            '10Y 国债': '2.65%',
            '人民币汇率': '7.18',
            '融资余额': '1.52 万亿',
        },
        'recommendation': '建议关注：低估值高分红 + 政策受益板块 + AI 产业链'
    }

# ============== 侧边栏 ==============
st.sidebar.title('📊 QuantInsight Pro')
st.sidebar.markdown('**AI 驱动的另类数据量化投研平台**')

# User info
st.sidebar.markdown('---')
_username = st.session_state.get('auth_username', 'Guest')
_is_admin = st.session_state.get('auth_is_admin', False)
_badge = ' 👑 管理员' if _is_admin else ''
st.sidebar.markdown(f'👤 **{_username}**{_badge}')

# Page navigation
page_options = [
    '🏠 首页',
    '🤖 AI 投研问答',
    '🎯 智能选股',
    '🔍 个股分析',
    '📊 实时数据看板',
    '📡 智能盯盘',
    '💼 我的组合',
    '📈 模拟交易',
    '⚡ 智能指令',
    '📡 另类数据仪表盘',
    '📈 量化策略回测',
    '🔬 因子挖掘与IC测试',
    '🔄 宏观因子融合',
    '📡 信号验证中心',
    '🔍 语义检索',
    '📊 行业分析',
    '👤 个人中心',
]
if _is_admin:
    page_options.append('⚙️ 管理后台')

st.sidebar.markdown('---')
page = st.sidebar.radio('选择功能模块', page_options)

# Log page visit
if page != st.session_state.get('auth_last_page', ''):
    _session_mgr.log_page_visit(st.session_state, page)
    st.session_state.auth_last_page = page

# Sidebar: project info (collapsible)
st.sidebar.markdown('---')
with st.sidebar.expander('📋 项目信息'):
    st.markdown(
        '**项目编号**：2026FINTECH-FINT-0093\n\n'
        '**参赛单位**：慧点资本 (InsightQuant)\n\n'
        '**推荐单位**：杭州永字资产管理有限公司\n\n'
        '**大赛**：Fintech@外滩 第一届金融科技国际创新创业大赛'
    )

# LLM status (compact)
llm_config_status = get_llm_config()
if llm_config_status['api_key']:
    st.sidebar.markdown(f'🤖 AI: 🟢 {llm_config_status["provider"].upper()}')
else:
    st.sidebar.markdown('🤖 AI: 🟡 Mock')

# Logout button
st.sidebar.markdown('---')
render_theme_toggle()
if st.sidebar.button('🚪 退出登录', width='stretch'):
    _session_mgr.logout(st.session_state)
    st.rerun()

# ============== 页面：首页 ==============
if page == '🏠 首页':
    # ========== 英雄区 Hero Section ==========
    st.markdown("""
    <div style="background: linear-gradient(135deg, #0A1628 0%, #1E3A5F 50%, #0F2236 100%);
                padding: 40px 32px; border-radius: 16px; margin-bottom: 24px;
                border: 1px solid rgba(0, 212, 255, 0.3);
                box-shadow: 0 8px 32px rgba(0, 212, 255, 0.15);
                position: relative; overflow: hidden;">
        <div style="position: absolute; top: -50%; right: -10%; width: 400px; height: 400px;
                    background: radial-gradient(circle, rgba(0, 212, 255, 0.15) 0%, transparent 70%);
                    border-radius: 50%;"></div>
        <div style="position: relative; z-index: 1;">
            <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 8px;">
                <span style="font-size: 2.5rem;">⚡</span>
                <h1 style="color: #FFFFFF; margin: 0; font-size: 2.5rem; font-weight: 800;
                           background: linear-gradient(90deg, #00D4FF, #D4AF37);
                           -webkit-background-clip: text; -webkit-text-fill-color: transparent;
                           background-clip: text;">QuantInsight Pro</h1>
            </div>
            <p style="color: #B8C5D6; font-size: 1.15rem; margin: 0 0 16px 0; font-weight: 300;">
                AI 驱动的另类数据量化投研平台 | 慧点资本 × 永字资管 联合打造
            </p>
            <div style="display: flex; gap: 24px; flex-wrap: wrap; margin-top: 16px;">
                <div style="color: #00D4FF; font-size: 0.9rem;">
                    <span style="color: #8B95A5;">📊 数据点</span> <b>500万+</b>
                </div>
                <div style="color: #D4AF37; font-size: 0.9rem;">
                    <span style="color: #8B95A5;">🤖 因子库</span> <b>200+</b>
                </div>
                <div style="color: #00FF88; font-size: 0.9rem;">
                    <span style="color: #8B95A5;">📈 回测期</span> <b>11.4年</b>
                </div>
                <div style="color: #FF9F43; font-size: 0.9rem;">
                    <span style="color: #8B95A5;">🏆 排名</span> <b>种子组 TOP 1%</b>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 实时数据条
    st.markdown("""
    <div style="background: linear-gradient(90deg, rgba(0, 212, 255, 0.1), rgba(212, 175, 55, 0.1));
                padding: 8px 16px; border-radius: 8px; margin-bottom: 16px;
                border-left: 3px solid #00D4FF; display: flex; align-items: center; gap: 12px;">
        <span style="color: #00FF88; font-size: 0.7rem;">●</span>
        <span style="color: #B8C5D6; font-size: 0.85rem;"><b style="color: #FFFFFF;">实时数据</b> · 数据源: akshare公开接口 · 延迟 &lt; 1s</span>
    </div>
    """, unsafe_allow_html=True)

    # 核心指标卡片
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        try:
            df_hs300 = load_hs300()
            st.metric('沪深300', f'{df_hs300["close"].iloc[-1]:.2f}', f'{df_hs300["close"].pct_change().iloc[-1]*100:+.2f}%')
        except Exception:
            st.metric('沪深300', '加载中', '')
    with col2:
        try:
            df_zz500 = load_zz500()
            st.metric('中证500', f'{df_zz500["close"].iloc[-1]:.2f}', f'{df_zz500["close"].pct_change().iloc[-1]*100:+.2f}%')
        except Exception:
            st.metric('中证500', '加载中', '')
    with col3:
        try:
            df_cyb = load_cyb()
            st.metric('创业板指', f'{df_cyb["close"].iloc[-1]:.2f}', f'{df_cyb["close"].pct_change().iloc[-1]*100:+.2f}%')
        except Exception:
            st.metric('创业板指', '加载中', '')
    with col4:
        try:
            north_data = load_northbound_flow()
            if north_data is not None:
                net_amount, direction = north_data
                st.metric('今日北向资金', f'{net_amount/1e8:.1f}亿', f'{direction} {abs(net_amount)/1e8:.1f}亿')
            else:
                st.metric('今日北向资金', '暂无数据', '')
        except Exception:
            st.metric('今日北向资金', '暂无数据', '')

    st.markdown('---')

    # 核心功能介绍 - 升级版卡片
    st.markdown("""
    <h2 style="color: #0A1628; margin-bottom: 8px;">
        🎯 平台核心功能 <span style="color: #D4AF37; font-size: 0.6em; font-weight: 400;">— 业内领先的智能投研平台</span>
    </h2>
    <p style="color: #6C757D; margin-bottom: 24px;">基于开源大模型微调 + RAG + SHAP 可解释性 + 真实akshare数据</p>
    """, unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown("""
        <div class="feature-card" style="background: linear-gradient(135deg, #FFFFFF 0%, #F5F7FA 100%); padding: 20px; border-radius: 12px; border: 1px solid #E8ECF1; border-top: 3px solid #00D4FF; box-shadow: 0 2px 8px rgba(0,0,0,0.04); height: 220px;">
            <h4 style="color: #1F4E78; margin: 0 0 8px 0; font-size: 1.05rem;">🎯 AI 智能选股</h4>
            <p style="color: #4A5568; font-size: 0.85rem; margin: 4px 0;">✅ 自然语言选股<br/>✅ 多因子评分体系<br/>✅ 个股深度对比</p>
            <div style="background: linear-gradient(90deg, #00D4FF22, #00D4FF11); padding: 6px 10px; border-radius: 6px; margin-top: 12px;">
                <small style="color: #1F4E78; font-weight: 600;">💡 试试：</small>
                <code style="color: #D4AF37; font-size: 0.78rem;">"低估值高成长消费股"</code>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="feature-card" style="background: linear-gradient(135deg, #FFFFFF 0%, #F5F7FA 100%); padding: 20px; border-radius: 12px; border: 1px solid #E8ECF1; border-top: 3px solid #D4AF37; box-shadow: 0 2px 8px rgba(0,0,0,0.04); height: 220px;">
            <h4 style="color: #1F4E78; margin: 0 0 8px 0; font-size: 1.05rem;">📡 另类数据中心</h4>
            <p style="color: #4A5568; font-size: 0.85rem; margin: 4px 0;">✅ 宏观景气/PMI/CPI<br/>✅ 资金流向/北向追踪<br/>✅ 期货/机构调研/质押</p>
            <div style="background: linear-gradient(90deg, #D4AF3722, #D4AF3711); padding: 6px 10px; border-radius: 6px; margin-top: 12px;">
                <small style="color: #1F4E78; font-weight: 600;">🎯 差异化：</small>
                <code style="color: #D4AF37; font-size: 0.78rem;">Wind没有的维度</code>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <div class="feature-card" style="background: linear-gradient(135deg, #FFFFFF 0%, #F5F7FA 100%); padding: 20px; border-radius: 12px; border: 1px solid #E8ECF1; border-top: 3px solid #1F4E78; box-shadow: 0 2px 8px rgba(0,0,0,0.04); height: 220px;">
            <h4 style="color: #1F4E78; margin: 0 0 8px 0; font-size: 1.05rem;">📈 量化策略平台</h4>
            <p style="color: #4A5568; font-size: 0.85rem; margin: 4px 0;">✅ 11.4年真实回测<br/>✅ SHAP可解释性<br/>✅ 双均线/布林/多因子</p>
            <div style="background: linear-gradient(90deg, #1F4E7822, #1F4E7811); padding: 6px 10px; border-radius: 6px; margin-top: 12px;">
                <small style="color: #1F4E78; font-weight: 600;">🏆 比赛亮点：</small>
                <code style="color: #D4AF37; font-size: 0.78rem;">不只告诉买什么</code>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown("""
        <div class="feature-card" style="background: linear-gradient(135deg, #FFFFFF 0%, #F5F7FA 100%); padding: 20px; border-radius: 12px; border: 1px solid #E8ECF1; border-top: 3px solid #00FF88; box-shadow: 0 2px 8px rgba(0,0,0,0.04); height: 220px;">
            <h4 style="color: #1F4E78; margin: 0 0 8px 0; font-size: 1.05rem;">🤖 AI 投研问答</h4>
            <p style="color: #4A5568; font-size: 0.85rem; margin: 4px 0;">✅ Qwen3.7-Max推理<br/>✅ 5轮上下文记忆<br/>✅ 引用真实数据</p>
            <div style="background: linear-gradient(90deg, #00FF8822, #00FF8811); padding: 6px 10px; border-radius: 6px; margin-top: 12px;">
                <small style="color: #1F4E78; font-weight: 600;">⚡ 升级：</small>
                <code style="color: #D4AF37; font-size: 0.78rem;">深度思考推理</code>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br/>", unsafe_allow_html=True)

    # 客户Logo墙 + 实时动态
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #FFFFFF 0%, #F8F9FB 100%);
                    padding: 24px; border-radius: 12px; border: 1px solid #E8ECF1;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.04);">
            <h3 style="color: #0A1628; margin: 0 0 16px 0; font-size: 1.15rem;">
                🏆 合作客户 & 战略伙伴
            </h3>
            <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px;">
                <div style="background: linear-gradient(135deg, #1F4E78 0%, #2E86AB 100%);
                            color: white; padding: 16px; border-radius: 8px; text-align: center;
                            border: 1px solid #D4AF37;">
                    <div style="font-size: 1.3rem; font-weight: 700;">永字资产</div>
                    <div style="font-size: 0.7rem; opacity: 0.8; margin-top: 4px;">首年LOI已签</div>
                </div>
                <div style="background: linear-gradient(135deg, #0A1628 0%, #1E3A5F 100%);
                            color: #00D4FF; padding: 16px; border-radius: 8px; text-align: center;
                            border: 1px solid #00D4FF;">
                    <div style="font-size: 1.3rem; font-weight: 700;">慧点资本</div>
                    <div style="font-size: 0.7rem; opacity: 0.8; margin-top: 4px;">联合出品方</div>
                </div>
                <div style="background: linear-gradient(135deg, #D4AF37 0%, #FFD700 100%);
                            color: #0A1628; padding: 16px; border-radius: 8px; text-align: center;
                            border: 1px solid #0A1628;">
                    <div style="font-size: 1.3rem; font-weight: 700;">创·在上海</div>
                    <div style="font-size: 0.7rem; opacity: 0.8; margin-top: 4px;">官方参赛项目</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #FFFFFF 0%, #F8F9FB 100%);
                    padding: 24px; border-radius: 12px; border: 1px solid #E8ECF1;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.04);">
            <h3 style="color: #0A1628; margin: 0 0 16px 0; font-size: 1.15rem;">📰 平台动态</h3>
            <div style="border-left: 3px solid #00FF88; padding-left: 12px; margin: 8px 0;">
                <div style="color: #6C757D; font-size: 0.75rem;">2026-06-15</div>
                <div style="color: #0A1628; font-size: 0.9rem; font-weight: 500;">✅ 完成 SHAP 可解释性模块</div>
            </div>
            <div style="border-left: 3px solid #D4AF37; padding-left: 12px; margin: 8px 0;">
                <div style="color: #6C757D; font-size: 0.75rem;">2026-06-14</div>
                <div style="color: #0A1628; font-size: 0.9rem; font-weight: 500;">🏆 完成全模块回归测试</div>
            </div>
            <div style="border-left: 3px solid #00D4FF; padding-left: 12px; margin: 8px 0;">
                <div style="color: #6C757D; font-size: 0.75rem;">2026-06-12</div>
                <div style="color: #0A1628; font-size: 0.9rem; font-weight: 500;">✅ 永字资管 LOI 签订</div>
            </div>
            <div style="border-left: 3px solid #8B95A5; padding-left: 12px; margin: 8px 0;">
                <div style="color: #6C757D; font-size: 0.75rem;">2026-06-05</div>
                <div style="color: #0A1628; font-size: 0.9rem; font-weight: 500;">📊 多因子回测白皮书 V1.0</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

# ============== 页面：实时数据看板 ==============
elif page == '📊 实时数据看板':
    try:
        from features.dashboard_v2 import render_dashboard
        render_dashboard()
    except ImportError as e:
        st.error(f"❌ 数据看板模块加载失败: {e}")
    except Exception as e:
        st.error(f"❌ 数据看板运行错误: {type(e).__name__}: {str(e)[:300]}")

# ============== 页面：AI 投研问答 ==============
elif page == '🤖 AI 投研问答':
    st.markdown('# 🤖 AI 投研问答')
    st.markdown('**基于开源大模型微调+RAG，支持自然语言投研分析 + 多轮对话**')

    st.markdown('---')

    # 初始化 session state
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []  # list of {role, content, title, summary, data, recommendation, reasoning}
    if 'question_input' not in st.session_state:
        st.session_state.question_input = ''

    # 顶部工具栏: 消息数 + 清空按钮
    col_info, col_clear = st.columns([5, 1])
    with col_info:
        st.caption(f'💬 对话轮数: {len(st.session_state.chat_history) // 2} / 5 (最近 5 轮保留为上下文)')
    with col_clear:
        if st.button('🗑️ 清空对话', width='stretch'):
            st.session_state.chat_history = []
            st.session_state.question_input = ''
            st.rerun()

    # 显示历史对话
    if st.session_state.chat_history:
        st.markdown('### 📜 对话历史')
        for i, msg in enumerate(st.session_state.chat_history):
            if msg['role'] == 'user':
                with st.chat_message('user', avatar='👤'):
                    st.markdown(msg['content'])
            else:  # assistant
                with st.chat_message('assistant', avatar='🤖'):
                    st.markdown(f'## 📄 {msg["title"]}')
                    st.markdown('### 📋 分析摘要')
                    st.markdown(msg['summary'])
                    if msg.get('data'):
                        st.markdown('### 📊 关键数据')
                        cols = st.columns(len(msg['data']))
                        for (k, v), col in zip(msg['data'].items(), cols):
                            with col:
                                safe_metric(k, v)
                    st.markdown('### 💡 投资建议')
                    st.success(msg['recommendation'])
                    if msg.get('reasoning'):
                        with st.expander('🧠 AI 思考过程', expanded=False):
                            st.caption(msg['reasoning'])
        st.markdown('---')

    # 快捷问题
    st.markdown('### 💡 试试这些问题 (单轮模式, 清空对话后使用)')
    col1, col2, col3 = st.columns(3)
    quick_questions = [
        '分析近期新能源行业投资机会',
        '半导体行业当前估值与投资逻辑',
        '消费板块是否到了底部布局时机',
    ]
    cols = [col1, col2, col3]

    for i, (q, col) in enumerate(zip(quick_questions, cols)):
        with col:
            if st.button(f'📌 {q}', key=f'quick_{i}', width='stretch'):
                st.session_state.question_input = q
                st.rerun()

    st.markdown('---')

    # 输入框
    question = st.text_area(
        '💬 请输入您的投研问题 (支持多轮, 上文会作为上下文)',
        value=st.session_state.question_input,
        height=100,
        placeholder='例如：基于上面分析, 哪些标的值得关注?'
    )

    col1, col2 = st.columns([1, 5])
    with col1:
        analyze_btn = st.button('🚀 智能分析', type='primary', width='stretch')

    if analyze_btn and question:
        # 检测 LLM 配置 (B7)
        llm_config = get_llm_config()
        use_real_llm = llm_config['api_key'] is not None

        # 尝试使用 MainAgent (多智能体协作)
        use_multi_agent = use_real_llm and st.checkbox('🧠 启用 Multi-Agent 协作模式', value=True, key='use_ma')

        if use_multi_agent:
            spinner_text = f'🤖 Multi-Agent 协作分析中 (含数据接地 + RAG)...'
        elif use_real_llm:
            spinner_text = f'🤖 {llm_config["provider"].upper()} AI 正在生成分析报告 (含上下文)...'
        else:
            spinner_text = '🤖 AI 正在生成分析报告 (Mock 模式, 配置 API key 可启用真实 LLM)...'

        with st.spinner(spinner_text):
            import time
            t0 = time.time()

            if use_multi_agent:
                try:
                    # 初始化 MainAgent (传入 cache_manager 和 llm_config)
                    if 'data_cache_mgr' not in st.session_state:
                        try:
                            st.session_state.data_cache_mgr = DataCacheManager(EastMoneyChoiceSource())
                        except Exception:
                            st.session_state.data_cache_mgr = None
                    if 'main_agent' not in st.session_state or st.session_state.get('_ma_llm_key') != llm_config.get('api_key'):
                        st.session_state.main_agent = MainAgent(
                            cache_manager=st.session_state.data_cache_mgr,
                            llm_config=llm_config,
                            qi_db=_qi_db if HAS_SQLITE_DB else None,  # V3.11: 传入 SQLite 实例
                        )
                        st.session_state['_ma_llm_key'] = llm_config.get('api_key')
                    agent = st.session_state.main_agent
                    # 构建历史格式
                    agent_history = []
                    for msg in st.session_state.chat_history[-10:]:
                        agent_history.append({'role': msg['role'], 'content': msg.get('content', msg.get('summary', ''))})
                    orch_result = agent.process_query(question, agent_history)
                    orch_d = orch_result.to_dict()
                    result = {
                        'title': orch_d.get('title', 'Multi-Agent 分析'),
                        'summary': orch_d.get('summary', ''),
                        'data': orch_d.get('data', {}),
                        'recommendation': orch_d.get('recommendation', ''),
                        'reasoning': orch_d.get('reasoning', ''),
                    }
                    # V3.11: 检查结果是否真的有内容
                    result_summary = result.get('summary', '')
                    if not result_summary or result_summary.startswith('分析:'):
                        st.warning('⚠️ Multi-Agent 未能生成有效内容, 可能 LLM 调用失败')
                        with st.expander('🔧 调试信息'):
                            st.write(f'LLM Provider: {llm_config.get("provider", "unknown")}')
                            st.write(f'LLM Model: {llm_config.get("model", "unknown")}')
                            if orch_d.get('agent_results'):
                                for item in orch_d['agent_results']:
                                    if isinstance(item, dict):
                                        st.write(f"**{item.get('name', 'agent')}**: success={item.get('success')}, error={item.get('error', 'none')}")
                    else:
                        st.success(f'✅ Multi-Agent 协作完成, 耗时 {time.time()-t0:.1f}s')
                    # 显示 Agent 执行过程
                    if orch_d.get('agent_results'):
                        with st.expander('🧩 Agent 执行详情'):
                            for item in orch_d['agent_results']:
                                if isinstance(item, dict):
                                    st.markdown(f'**{item.get("name", "agent")}**: {str(item.get("output", ""))[:200]}')
                                else:
                                    st.markdown(f'- {str(item)[:200]}')
                except Exception as e:
                    st.warning(f'⚠️ Multi-Agent 失败: {e}, 回退单 Agent')
                    try:
                        result = ai_qa_real(question, llm_config, history=st.session_state.chat_history[-10:])
                    except Exception:
                        result = ai_qa_mock(question)
            else:
                if use_real_llm:
                    try:
                        result = ai_qa_real(question, llm_config, history=st.session_state.chat_history[-10:])
                    except Exception as e:
                        st.warning(f'⚠️ LLM调用失败: {e}, 使用Mock数据')
                        result = ai_qa_mock(question)
                else:
                    time.sleep(1.0)  # 模拟推理时间
                    result = ai_qa_mock(question)

            # 保存到对话历史
            st.session_state.chat_history.append({'role': 'user', 'content': question})
            st.session_state.chat_history.append({
                'role': 'assistant',
                'title': result['title'],
                'summary': result['summary'],
                'data': result.get('data', {}),
                'recommendation': result['recommendation'],
                'reasoning': result.get('reasoning', ''),
            })

            # 限制历史长度: 最近 5 轮 (10 条消息)
            if len(st.session_state.chat_history) > 10:
                st.session_state.chat_history = st.session_state.chat_history[-10:]

            st.session_state.question_input = ''
            st.rerun()

    st.caption('⚠️ 本回答基于公开数据 + AI 模型生成，仅供参考，不构成投资建议')

# ============== 页面：另类数据仪表盘 ==============
elif page == '📡 另类数据仪表盘':
    st.markdown('# 📡 另类数据仪表盘')
    st.markdown('**宏观景气 · 市场情绪 · 产业链传导 — 全量真实数据驱动**')

    # 品牌色
    _BRAND = {'deep_blue': '#0A0E27', 'neon_cyan': '#00D4FF', 'gold': '#FFB800', 'violet': '#7B61FF'}
    _DARK_LAYOUT = go.Layout(template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                             font=dict(color='#E0E0E0'), margin=dict(l=50, r=20, t=50, b=40))

    st.markdown('---')

    tab1, tab2, tab3 = st.tabs(['📊 宏观景气', '💬 市场情绪', '🔗 产业链传导'])

    # ========== Tab1: 宏观景气指标 ==========
    with tab1:
        st.markdown('### 📊 宏观景气领先指标')
        st.caption('数据源：金十数据 / 国家统计局 (akshare 免费接口)')

        col1, col2 = st.columns(2)

        with col1:
            # PMI
            try:
                df_pmi = ak.macro_china_pmi()
                if df_pmi is not None and len(df_pmi) > 0:
                    df_pmi_recent = df_pmi.tail(24).copy()
                    date_col = [c for c in df_pmi_recent.columns if '月份' in c or '日期' in c or '月' in c]
                    mfg_col = [c for c in df_pmi_recent.columns if '制造业' in c and '指数' in c]
                    if not mfg_col:
                        mfg_col = [c for c in df_pmi_recent.columns if '制造业' in c]
                    if not mfg_col:
                        mfg_col = [df_pmi_recent.columns[1]] if len(df_pmi_recent.columns) > 1 else []

                    if date_col and mfg_col:
                        fig = go.Figure(layout=_DARK_LAYOUT)
                        x_vals = df_pmi_recent[date_col[0]].astype(str)
                        y_vals = pd.to_numeric(df_pmi_recent[mfg_col[0]], errors='coerce')
                        fig.add_trace(go.Scatter(x=x_vals, y=y_vals,
                                                 mode='lines+markers', name='制造业PMI',
                                                 line=dict(color=_BRAND['neon_cyan'], width=2.5),
                                                 marker=dict(size=6, color=_BRAND['neon_cyan'])))
                        fig.add_hline(y=50, line_dash='dash', line_color=_BRAND['gold'],
                                      annotation_text='荣枯线 50', annotation_font_color=_BRAND['gold'])
                        # 填充荣枯线上下区域
                        fig.add_trace(go.Scatter(x=x_vals, y=y_vals.clip(lower=50), fill='tozeroy',
                                                 fillcolor='rgba(0,212,255,0.08)', line=dict(width=0), showlegend=False))
                        fig.update_layout(title='中国制造业 PMI (近24月)', yaxis_title='PMI',
                                          height=380, hovermode='x unified')
                        fig.update_xaxes(tickangle=45)
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.caption('PMI 数据格式变化, 暂无法绘图')
                        st.dataframe(df_pmi_recent.tail(10), use_container_width=True)
            except Exception:
                st.warning('PMI 数据加载失败，使用演示数据')
                # 演示数据
                _demo_months = [f'2024-{i:02d}' for i in range(1, 13)] + [f'2025-{i:02d}' for i in range(1, 13)]
                _demo_pmi = [49.2, 49.1, 50.8, 51.4, 51.7, 51.8, 49.4, 49.1, 50.2, 50.1, 50.3, 50.1,
                             49.0, 50.2, 50.5, 51.1, 50.4, 50.5, 49.8, 49.5, 50.4, 50.3, 50.6, 50.2]
                fig = go.Figure(layout=_DARK_LAYOUT)
                fig.add_trace(go.Scatter(x=_demo_months, y=_demo_pmi, mode='lines+markers',
                                         name='制造业PMI(演示)', line=dict(color=_BRAND['neon_cyan'], width=2.5)))
                fig.add_hline(y=50, line_dash='dash', line_color=_BRAND['gold'], annotation_text='荣枯线 50')
                fig.update_layout(title='中国制造业 PMI (演示数据)', yaxis_title='PMI', height=380, hovermode='x unified')
                st.plotly_chart(fig, use_container_width=True)

        with col2:
            # CPI + PPI
            try:
                df_cpi = ak.macro_china_cpi_yearly()
                if df_cpi is not None and len(df_cpi) > 0:
                    df_cpi_recent = df_cpi.tail(24).copy()
                    date_col = [c for c in df_cpi_recent.columns if '日期' in c or '月份' in c or '商品' in c]
                    val_col = [c for c in df_cpi_recent.columns if '今值' in c or '同比' in c]
                    if date_col and val_col:
                        fig = go.Figure(layout=_DARK_LAYOUT)
                        fig.add_trace(go.Bar(x=df_cpi_recent[date_col[0]].astype(str),
                                             y=pd.to_numeric(df_cpi_recent[val_col[0]], errors='coerce'),
                                             name='CPI 同比',
                                             marker_color=_BRAND['violet'],
                                             marker_line=dict(color=_BRAND['violet'], width=1)))
                        fig.update_layout(title='CPI 同比 (近24期)', yaxis_title='%',
                                          height=380, hovermode='x unified')
                        fig.update_xaxes(tickangle=45)
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.dataframe(df_cpi_recent.tail(10), use_container_width=True)
            except Exception:
                st.warning('CPI 数据加载失败，使用演示数据')
                _demo_cpi_months = [f'2024-{i:02d}' for i in range(1, 13)] + [f'2025-{i:02d}' for i in range(1, 7)]
                _demo_cpi = [0.8, 0.7, 0.1, 0.3, 0.3, 0.2, 0.5, 0.6, 0.4, 0.3, 0.2, -0.3,
                             -0.8, -0.7, -0.1, 0.3, 0.2, 0.1]
                fig = go.Figure(layout=_DARK_LAYOUT)
                fig.add_trace(go.Bar(x=_demo_cpi_months, y=_demo_cpi, name='CPI同比(演示)',
                                     marker_color=_BRAND['violet']))
                fig.update_layout(title='CPI 同比 (演示数据)', yaxis_title='%', height=380, hovermode='x unified')
                st.plotly_chart(fig, use_container_width=True)

        # 第二行: 工业增加值 + 社融规模
        col3, col4 = st.columns(2)

        with col3:
            try:
                df_gyzjz = ak.macro_china_gyzjz()
                if df_gyzjz is not None and len(df_gyzjz) > 0:
                    df_gyzjz_recent = df_gyzjz.tail(12).copy()
                    date_col = [c for c in df_gyzjz_recent.columns if '月份' in c or '日期' in c]
                    val_col = [c for c in df_gyzjz_recent.columns if '同比' in c or '增长' in c]
                    if date_col and val_col:
                        fig = go.Figure(layout=_DARK_LAYOUT)
                        fig.add_trace(go.Bar(x=df_gyzjz_recent[date_col[0]].astype(str),
                                             y=pd.to_numeric(df_gyzjz_recent[val_col[0]], errors='coerce'),
                                             name='工业增加值同比',
                                             marker_color=_BRAND['gold'],
                                             marker_line=dict(color=_BRAND['gold'], width=1)))
                        fig.update_layout(title='工业增加值同比 (近12月)', yaxis_title='%',
                                          height=350, hovermode='x unified')
                        fig.update_xaxes(tickangle=45)
                        st.plotly_chart(fig, use_container_width=True)
            except Exception:
                st.warning('工业增加值数据加载失败，使用演示数据')
                _demo_gy_months = [f'2025-{i:02d}' for i in range(1, 13)]
                _demo_gy = [7.0, 7.0, 4.5, 6.7, 5.6, 5.3, 5.1, 4.5, 5.4, 5.3, 5.0, 5.2]
                fig = go.Figure(layout=_DARK_LAYOUT)
                fig.add_trace(go.Bar(x=_demo_gy_months, y=_demo_gy, name='工业增加值(演示)',
                                     marker_color=_BRAND['gold']))
                fig.update_layout(title='工业增加值同比 (演示数据)', yaxis_title='%', height=350, hovermode='x unified')
                st.plotly_chart(fig, use_container_width=True)

        with col4:
            # 社融数据替代用电量（更有宏观意义）
            try:
                df_shrzgm = ak.macro_china_shrzgm()
                if df_shrzgm is not None and len(df_shrzgm) > 0:
                    df_shrzgm_recent = df_shrzgm.tail(12).copy()
                    date_col = [c for c in df_shrzgm_recent.columns if '月份' in c or '日期' in c or '时间' in c]
                    val_col = [c for c in df_shrzgm_recent.columns if '社会融资规模增量' in c or '新增' in c]
                    if not val_col:
                        val_col = [df_shrzgm_recent.columns[-1]] if len(df_shrzgm_recent.columns) > 1 else []
                    if date_col and val_col:
                        fig = go.Figure(layout=_DARK_LAYOUT)
                        fig.add_trace(go.Bar(x=df_shrzgm_recent[date_col[0]].astype(str),
                                             y=pd.to_numeric(df_shrzgm_recent[val_col[0]], errors='coerce') / 1e4,
                                             name='社融增量(万亿)',
                                             marker_color=_BRAND['neon_cyan'],
                                             marker_line=dict(color=_BRAND['neon_cyan'], width=1)))
                        fig.update_layout(title='社会融资规模增量 (近12月)', yaxis_title='万亿',
                                          height=350, hovermode='x unified')
                        fig.update_xaxes(tickangle=45)
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.dataframe(df_shrzgm_recent.tail(6), use_container_width=True, hide_index=True)
            except Exception:
                st.warning('社融数据加载失败，使用演示数据')
                _demo_sr_months = [f'2025-{i:02d}' for i in range(1, 13)]
                _demo_sr = [6.5, 1.5, 4.9, -0.2, 2.1, 3.3, 0.8, 3.0, 3.8, 1.4, 2.3, 1.9]
                fig = go.Figure(layout=_DARK_LAYOUT)
                fig.add_trace(go.Bar(x=_demo_sr_months, y=_demo_sr, name='社融增量(演示/万亿)',
                                     marker_color=_BRAND['neon_cyan']))
                fig.update_layout(title='社会融资规模增量 (演示数据)', yaxis_title='万亿', height=350, hovermode='x unified')
                st.plotly_chart(fig, use_container_width=True)

        st.info('💡 宏观景气指标是另类数据的重要维度: PMI/CPI/工业增加值/社融等领先指标可提前预判经济周期拐点')

    # ========== Tab2: 市场情绪与资金流向 ==========
    with tab2:
        st.markdown('### 💬 市场情绪与资金流向')
        st.caption('数据源：东方财富 / 雪球 (akshare 免费接口)')

        col1, col2 = st.columns(2)

        with col1:
            # 概念板块资金流向
            try:
                df_concept = ak.stock_fund_flow_concept(symbol='即时')
                if df_concept is not None and len(df_concept) > 0:
                    st.markdown('#### 💰 概念板块资金流向 TOP15')
                    df_top = df_concept.head(15)
                    name_col = [c for c in df_top.columns if '行业' in c or '名称' in c or '概念' in c]
                    flow_col = [c for c in df_top.columns if '流入' in c or '净买' in c or '主力' in c]
                    change_col = [c for c in df_top.columns if '涨跌' in c]

                    if name_col and change_col:
                        fig = go.Figure(layout=_DARK_LAYOUT)
                        colors = [_BRAND['neon_cyan'] if v >= 0 else '#FF4D6A' for v in pd.to_numeric(df_top[change_col[0]], errors='coerce').fillna(0)]
                        fig.add_trace(go.Bar(x=pd.to_numeric(df_top[change_col[0]], errors='coerce').fillna(0),
                                             y=df_top[name_col[0]],
                                             orientation='h',
                                             marker_color=colors,
                                             name='涨跌幅%'))
                        fig.update_layout(title='概念板块涨跌幅 TOP15', yaxis_title='',
                                          height=480, yaxis={'categoryorder': 'total ascending'},
                                          xaxis_title='涨跌幅(%)')
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.dataframe(df_top, use_container_width=True, hide_index=True)
            except Exception:
                st.warning('概念板块资金数据加载失败，使用演示数据')
                _demo_concepts = ['AI算力', 'CPO', '机器人', '半导体', '新能源车', '白酒', '医药', '军工', '光伏', '锂电池', '房地产', '银行', '券商', '煤炭', '钢铁']
                _demo_chg = [5.2, 4.1, 3.8, 2.5, 1.9, -0.5, -1.2, 0.8, -2.1, -1.5, -3.2, 0.3, 1.1, -0.8, -1.0]
                fig = go.Figure(layout=_DARK_LAYOUT)
                colors = [_BRAND['neon_cyan'] if v >= 0 else '#FF4D6A' for v in _demo_chg]
                fig.add_trace(go.Bar(x=_demo_chg, y=_demo_concepts, orientation='h',
                                     marker_color=colors, name='涨跌幅%'))
                fig.update_layout(title='概念板块涨跌幅 TOP15 (演示)', yaxis_title='',
                                  height=480, yaxis={'categoryorder': 'total ascending'}, xaxis_title='涨跌幅(%)')
                st.plotly_chart(fig, use_container_width=True)

        with col2:
            # 北向资金历史趋势
            try:
                df_north = ak.stock_hsgt_hist_em(symbol='沪股通')
                if df_north is not None and len(df_north) > 0:
                    st.markdown('#### 🌊 北向资金 (沪股通) 近30日')
                    df_north_recent = df_north.tail(30)
                    date_col = [c for c in df_north_recent.columns if '日期' in c or 'date' in c.lower()]
                    flow_col = [c for c in df_north_recent.columns if '净买' in c or '流入' in c or '成交' in c]

                    if date_col and flow_col:
                        fig = go.Figure(layout=_DARK_LAYOUT)
                        y_data = pd.to_numeric(df_north_recent[flow_col[0]], errors='coerce')
                        colors = [_BRAND['neon_cyan'] if v >= 0 else '#FF4D6A' for v in y_data.fillna(0)]
                        fig.add_trace(go.Bar(x=df_north_recent[date_col[0]], y=y_data,
                                             name='当日净买入', marker_color=colors))
                        # 5日均线
                        if len(y_data) >= 5:
                            ma5 = y_data.rolling(5).mean()
                            fig.add_trace(go.Scatter(x=df_north_recent[date_col[0]], y=ma5,
                                                     mode='lines', name='5日均线',
                                                     line=dict(color=_BRAND['gold'], width=2)))
                        fig.update_layout(title='沪股通净买入 (近30日)', yaxis_title='金额',
                                          height=480, hovermode='x unified')
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.dataframe(df_north_recent.tail(10), use_container_width=True, hide_index=True)
            except Exception:
                st.warning('北向资金数据加载失败，使用演示数据')
                _demo_north_dates = pd.date_range(end=pd.Timestamp.today(), periods=30)
                _demo_north_flow = np.random.uniform(-30, 50, 30).round(2)
                fig = go.Figure(layout=_DARK_LAYOUT)
                colors = [_BRAND['neon_cyan'] if v >= 0 else '#FF4D6A' for v in _demo_north_flow]
                fig.add_trace(go.Bar(x=_demo_north_dates, y=_demo_north_flow, name='净买入(演示)',
                                     marker_color=colors))
                ma5 = pd.Series(_demo_north_flow).rolling(5).mean()
                fig.add_trace(go.Scatter(x=_demo_north_dates, y=ma5, mode='lines', name='5日均线',
                                         line=dict(color=_BRAND['gold'], width=2)))
                fig.update_layout(title='沪股通净买入 (演示数据)', yaxis_title='亿元', height=480, hovermode='x unified')
                st.plotly_chart(fig, use_container_width=True)

        # 市场情绪指标: 涨跌家数 + 融资融券
        col3, col4 = st.columns(2)

        with col3:
            # 涨跌家数统计
            try:
                df_spot = safe_get_spot_df()
                if df_spot is not None and len(df_spot) > 0:
                    chg_col = [c for c in df_spot.columns if '涨跌幅' in c]
                    if chg_col:
                        chg = pd.to_numeric(df_spot[chg_col[0]], errors='coerce').dropna()
                        up_count = (chg > 0).sum()
                        down_count = (chg < 0).sum()
                        flat_count = (chg == 0).sum()
                        limit_up = (chg >= 9.9).sum()
                        limit_down = (chg <= -9.9).sum()
                        fig = go.Figure(layout=_DARK_LAYOUT)
                        fig.add_trace(go.Bar(x=['涨停', '上涨', '平盘', '下跌', '跌停'],
                                             y=[limit_up, up_count - limit_up, flat_count, down_count - limit_down, limit_down],
                                             marker_color=[_BRAND['gold'], _BRAND['neon_cyan'], '#888888', '#FF4D6A', '#8B0000'],
                                             text=[limit_up, up_count - limit_up, flat_count, down_count - limit_down, limit_down],
                                             textposition='auto'))
                        fig.update_layout(title='A股涨跌家数分布', yaxis_title='家数', height=350)
                        st.plotly_chart(fig, use_container_width=True)
            except Exception:
                st.warning('涨跌家数加载失败，使用演示数据')
                fig = go.Figure(layout=_DARK_LAYOUT)
                fig.add_trace(go.Bar(x=['涨停', '上涨', '平盘', '下跌', '跌停'],
                                     y=[42, 2850, 180, 2150, 35],
                                     marker_color=[_BRAND['gold'], _BRAND['neon_cyan'], '#888888', '#FF4D6A', '#8B0000'],
                                     text=[42, 2850, 180, 2150, 35], textposition='auto'))
                fig.update_layout(title='A股涨跌家数分布 (演示)', yaxis_title='家数', height=350)
                st.plotly_chart(fig, use_container_width=True)

        with col4:
            # 融资融券余额趋势
            try:
                df_margin = None
                # Try SQLite first
                if HAS_SQLITE_DB:
                    try:
                        df_margin = _qi_db.get_margin_trading()
                    except Exception:
                        pass
                # Try 东方财富直连
                if df_margin is None or len(df_margin) == 0:
                    try:
                        from features.eastmoney_direct import fetch_margin_trading
                        df_margin = fetch_margin_trading(days=30)
                        if df_margin is not None and len(df_margin) > 0 and HAS_SQLITE_DB:
                            try:
                                _qi_db.upsert_margin_trading(df_margin)
                            except Exception:
                                pass
                    except Exception:
                        pass
                # Fallback to akshare
                if df_margin is None or len(df_margin) == 0:
                    try:
                        df_margin = ak.stock_margin_underlying_info_sz_sh(date=pd.Timestamp.today().strftime('%Y%m%d'))
                    except Exception:
                        pass
                if df_margin is not None and len(df_margin) > 0:
                    st.markdown('#### 📈 融资融券标的')
                    st.dataframe(df_margin.head(15), use_container_width=True, hide_index=True)
            except Exception:
                st.warning('融资融券数据加载失败，使用演示数据')
                _demo_margin_dates = pd.date_range(end=pd.Timestamp.today(), periods=20)
                _demo_margin_val = np.cumsum(np.random.uniform(-50, 80, 20)) + 15000
                fig = go.Figure(layout=_DARK_LAYOUT)
                fig.add_trace(go.Scatter(x=_demo_margin_dates, y=_demo_margin_val, mode='lines+markers',
                                         name='融资余额(亿)', line=dict(color=_BRAND['violet'], width=2.5)))
                fig.update_layout(title='融资余额趋势 (演示数据)', yaxis_title='亿元', height=350, hovermode='x unified')
                st.plotly_chart(fig, use_container_width=True)

        # 大单交易
        try:
            df_big = ak.stock_fund_flow_big_deal()
            if df_big is not None and len(df_big) > 0:
                st.markdown('#### 📋 最新大单交易')
                display_cols = [c for c in ['成交时间', '股票代码', '股票简称', '成交价格', '成交量', '成交金额'] if c in df_big.columns]
                st.dataframe(df_big[display_cols].head(20) if display_cols else df_big.head(20),
                             use_container_width=True, hide_index=True)
        except Exception:
            pass

        st.info('💡 资金流向是另类数据的核心维度: 北向资金/概念板块资金/大单交易可捕捉主力动向')

    # ========== Tab3: 产业链传导与机构行为 ==========
    with tab3:
        st.markdown('### 🔗 产业链传导与机构行为')
        st.caption('数据源：东方财富 / 上海深圳交易所 (akshare 免费接口)')

        col1, col2 = st.columns(2)

        with col1:
            # 期货期现价差 (产业链价格传导)
            try:
                df_futures = ak.futures_spot_price()
                if df_futures is not None and len(df_futures) > 0:
                    st.markdown('#### 🏭 期货期现价差 (产业链价格传导)')
                    # 尝试绘制价格柱状图
                    name_col = [c for c in df_futures.columns if '品种' in c or '名称' in c or '合约' in c]
                    price_col = [c for c in df_futures.columns if '现价' in c or '最新' in c or '价格' in c or '收盘' in c]
                    if name_col and price_col:
                        df_top_futures = df_futures.head(15)
                        fig = go.Figure(layout=_DARK_LAYOUT)
                        fig.add_trace(go.Bar(x=df_top_futures[name_col[0]].astype(str),
                                             y=pd.to_numeric(df_top_futures[price_col[0]], errors='coerce'),
                                             name='最新价', marker_color=_BRAND['neon_cyan']))
                        fig.update_layout(title='主要期货品种价格', yaxis_title='价格', height=400,
                                          xaxis_tickangle=45)
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.dataframe(df_futures.head(20), use_container_width=True, hide_index=True)
            except Exception:
                # fallback: 全球商品价格
                try:
                    df_global = ak.futures_global_spot_em()
                    if df_global is not None and len(df_global) > 0:
                        st.markdown('#### 🌍 全球大宗商品价格')
                        name_col = [c for c in df_global.columns if '品种' in c or '名称' in c or '商品' in c]
                        price_col = [c for c in df_global.columns if '价格' in c or '现价' in c or '最新' in c]
                        if name_col and price_col:
                            df_top_g = df_global.head(15)
                            fig = go.Figure(layout=_DARK_LAYOUT)
                            fig.add_trace(go.Bar(x=df_top_g[name_col[0]].astype(str),
                                                 y=pd.to_numeric(df_top_g[price_col[0]], errors='coerce'),
                                                 name='价格', marker_color=_BRAND['gold']))
                            fig.update_layout(title='全球大宗商品价格', yaxis_title='价格', height=400,
                                              xaxis_tickangle=45)
                            st.plotly_chart(fig, use_container_width=True)
                        else:
                            st.dataframe(df_global.head(20), use_container_width=True, hide_index=True)
                except Exception:
                    st.warning('期货数据加载失败，使用演示数据')
                    _demo_futures = ['螺纹钢', '铁矿石', '焦炭', '原油', '铜', '铝', '锌', '镍', '黄金', '白银', '豆粕', '玉米', '棕榈油', 'PTA', '甲醇']
                    _demo_fut_prices = [3650, 780, 2350, 580, 72000, 19800, 21500, 125000, 580, 7800, 3200, 2650, 8200, 5800, 2500]
                    fig = go.Figure(layout=_DARK_LAYOUT)
                    fig.add_trace(go.Bar(x=_demo_futures, y=_demo_fut_prices, name='价格(演示)',
                                         marker_color=_BRAND['neon_cyan']))
                    fig.update_layout(title='主要期货品种价格 (演示数据)', yaxis_title='价格', height=400, xaxis_tickangle=45)
                    st.plotly_chart(fig, use_container_width=True)

        with col2:
            # 机构调研统计
            try:
                df_jgdy = ak.stock_jgdy_tj_em()
                if df_jgdy is not None and len(df_jgdy) > 0:
                    st.markdown('#### 🔍 机构调研热度 TOP15')
                    display_cols = [c for c in ['股票代码', '股票简称', '最新价', '涨跌幅', '调研机构数'] if c in df_jgdy.columns]
                    if not display_cols:
                        display_cols = df_jgdy.columns[:5].tolist()
                    # 尝试绘制调研热度图
                    name_col_jg = [c for c in df_jgdy.columns if '简称' in c or '名称' in c]
                    count_col = [c for c in df_jgdy.columns if '调研' in c or '机构' in c or '家数' in c]
                    if name_col_jg and count_col:
                        df_jg_top = df_jgdy.head(15)
                        fig = go.Figure(layout=_DARK_LAYOUT)
                        fig.add_trace(go.Bar(x=pd.to_numeric(df_jg_top[count_col[0]], errors='coerce'),
                                             y=df_jg_top[name_col_jg[0]],
                                             orientation='h', name='调研机构数',
                                             marker_color=_BRAND['violet']))
                        fig.update_layout(title='机构调研热度 TOP15', yaxis_title='',
                                          height=400, yaxis={'categoryorder': 'total ascending'},
                                          xaxis_title='调研机构数')
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.dataframe(df_jgdy[display_cols].head(15), use_container_width=True, hide_index=True)
            except Exception:
                st.warning('机构调研数据加载失败，使用演示数据')
                _demo_jg_names = ['迈瑞医疗', '海康威视', '宁德时代', '汇川技术', '三一重工', '美的集团', '比亚迪', '药明康德', '中微公司', '北方华创', '韦尔股份', '紫光国微', '中芯国际', '金山办公', '科大讯飞']
                _demo_jg_counts = [85, 72, 68, 55, 48, 45, 42, 38, 35, 32, 28, 25, 22, 20, 18]
                fig = go.Figure(layout=_DARK_LAYOUT)
                fig.add_trace(go.Bar(x=_demo_jg_counts, y=_demo_jg_names, orientation='h',
                                     name='调研机构数(演示)', marker_color=_BRAND['violet']))
                fig.update_layout(title='机构调研热度 TOP15 (演示数据)', yaxis_title='',
                                  height=400, yaxis={'categoryorder': 'total ascending'}, xaxis_title='调研机构数')
                st.plotly_chart(fig, use_container_width=True)

        # 第二行: 行业资金流向 + 股权质押
        col3, col4 = st.columns(2)

        with col3:
            # 行业板块资金流向
            try:
                df_industry = ak.stock_fund_flow_industry(symbol='即时')
                if df_industry is not None and len(df_industry) > 0:
                    st.markdown('#### 🏢 行业板块资金流向 TOP10')
                    name_col = [c for c in df_industry.columns if '行业' in c or '名称' in c or '板块' in c]
                    flow_col = [c for c in df_industry.columns if '流入' in c or '净买' in c or '主力' in c]
                    if name_col and flow_col:
                        df_ind_top = df_industry.head(10)
                        fig = go.Figure(layout=_DARK_LAYOUT)
                        y_data = pd.to_numeric(df_ind_top[flow_col[0]], errors='coerce').fillna(0)
                        colors = [_BRAND['neon_cyan'] if v >= 0 else '#FF4D6A' for v in y_data]
                        fig.add_trace(go.Bar(x=y_data, y=df_ind_top[name_col[0]], orientation='h',
                                             marker_color=colors, name='主力净流入'))
                        fig.update_layout(title='行业主力资金流向 TOP10', yaxis_title='',
                                          height=380, yaxis={'categoryorder': 'total ascending'},
                                          xaxis_title='净流入金额')
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.dataframe(df_industry.head(10), use_container_width=True, hide_index=True)
            except Exception:
                st.warning('行业资金数据加载失败，使用演示数据')
                _demo_ind_names = ['电子', '计算机', '医药生物', '电力设备', '食品饮料', '银行', '非银金融', '房地产', '钢铁', '煤炭']
                _demo_ind_flow = [25.3, 18.7, 12.1, 8.5, -3.2, -5.8, -8.1, -12.5, -6.3, -4.1]
                fig = go.Figure(layout=_DARK_LAYOUT)
                colors = [_BRAND['neon_cyan'] if v >= 0 else '#FF4D6A' for v in _demo_ind_flow]
                fig.add_trace(go.Bar(x=_demo_ind_flow, y=_demo_ind_names, orientation='h',
                                     marker_color=colors, name='主力净流入(演示)'))
                fig.update_layout(title='行业主力资金流向 TOP10 (演示)', yaxis_title='',
                                  height=380, yaxis={'categoryorder': 'total ascending'}, xaxis_title='净流入(亿)')
                st.plotly_chart(fig, use_container_width=True)

        with col4:
            # 股权质押风险
            try:
                df_zy = ak.stock_gpzy_industry_data_em()
                if df_zy is not None and len(df_zy) > 0:
                    st.markdown('#### ⚠️ 行业股权质押风险')
                    name_col = [c for c in df_zy.columns if '行业' in c or '名称' in c]
                    ratio_col = [c for c in df_zy.columns if '质押' in c or '比例' in c or '占比' in c]
                    if name_col and ratio_col:
                        df_zy_top = df_zy.head(12)
                        fig = go.Figure(layout=_DARK_LAYOUT)
                        fig.add_trace(go.Bar(x=df_zy_top[name_col[0]].astype(str),
                                             y=pd.to_numeric(df_zy_top[ratio_col[0]], errors='coerce'),
                                             name='质押比例',
                                             marker_color=_BRAND['gold']))
                        fig.update_layout(title='行业股权质押比例', yaxis_title='比例(%)',
                                          height=380, xaxis_tickangle=45)
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.dataframe(df_zy.head(15), use_container_width=True, hide_index=True)
            except Exception:
                st.warning('质押数据加载失败，使用演示数据')
                _demo_zy_names = ['房地产', '传媒', '纺织服装', '商贸', '综合', '化工', '建筑', '农林牧渔', '计算机', '电子']
                _demo_zy_ratio = [18.5, 15.2, 13.8, 12.1, 11.5, 10.2, 9.8, 9.1, 8.5, 7.2]
                fig = go.Figure(layout=_DARK_LAYOUT)
                fig.add_trace(go.Bar(x=_demo_zy_names, y=_demo_zy_ratio, name='质押比例(演示%)',
                                     marker_color=_BRAND['gold']))
                fig.update_layout(title='行业股权质押比例 (演示数据)', yaxis_title='比例(%)', height=380, xaxis_tickangle=45)
                st.plotly_chart(fig, use_container_width=True)

        st.info('💡 产业链传导是另类数据的差异化维度: 期货价差反映供需预期, 机构调研揭示关注方向, 质押风险预警系统性风险')

# ============== 页面：量化策略回测 ==============
elif page == '📈 量化策略回测':
    st.markdown('# 📈 量化策略回测')
    st.markdown('**基于公开 A 股数据的真实回测, 11.4 年回测期, 可调参数**')

    st.markdown('---')

    # 第 1 行: 标的选择 + 策略类型
    col1, col2, col3 = st.columns(3)
    with col1:
        index_choice = st.selectbox('📊 标的指数', ['沪深300', '中证500', '创业板指'], key='bt_index')
    with col2:
        strategy_choice = st.selectbox('🧠 策略类型', ['双均线动量', '布林带均值回归', '多因子合成'], key='bt_strategy')
    with col3:
        start_date = st.date_input('📅 起始日期', value=pd.to_datetime('2020-01-01'), key='bt_start')

    # 策略参数默认值 (防止分支外引用未定义变量)
    fast_ma, slow_ma = 20, 60
    window, std_dev = 20, 2.0
    cost = 0.0015

    # 第 2 行: 策略参数 (根据策略类型动态显示)
    if strategy_choice == '双均线动量':
        col1, col2, col3 = st.columns(3)
        with col1:
            fast_ma = st.slider('⚡ 短均线周期', min_value=5, max_value=60, value=20, step=5, help='默认 20, 越小越敏感')
        with col2:
            slow_ma = st.slider('🐢 长均线周期', min_value=20, max_value=250, value=60, step=10, help='默认 60, 必须大于短均线')
        with col3:
            cost = st.slider('💰 手续费率', min_value=0.0, max_value=0.003, value=0.0015, step=0.0001, format='%.4f', help='默认 0.15%')
        # 校验
        if fast_ma >= slow_ma:
            st.error('❌ 短均线必须小于长均线')
            st.stop()
    elif strategy_choice == '布林带均值回归':
        col1, col2, col3 = st.columns(3)
        with col1:
            window = st.slider('📏 布林带窗口', min_value=10, max_value=60, value=20, step=5, help='默认 20 日')
        with col2:
            std_dev = st.slider('📊 标准差倍数', min_value=1.0, max_value=3.0, value=2.0, step=0.1, help='默认 2.0 σ')
        with col3:
            cost = st.slider('💰 手续费率', min_value=0.0, max_value=0.003, value=0.0015, step=0.0001, format='%.4f')
    else:  # 多因子
        col1, col2 = st.columns(2)
        with col1:
            cost = st.slider('💰 手续费率', min_value=0.0, max_value=0.003, value=0.0015, step=0.0001, format='%.4f')
        with col2:
            st.info('💡 多因子策略内部参数固定 (20日动量 + 5日反转 + 60日排名)')

    st.markdown('---')

    col_run, col_reset = st.columns([1, 5])
    with col_run:
        run_btn = st.button('🚀 运行回测', type='primary', width='stretch')

    if run_btn:
        try:
          with st.spinner(f'正在加载 {index_choice} 数据 + 计算 {strategy_choice} 回测...'):
            symbol_map = {'沪深300': 'sh000300', '中证500': 'sh000905', '创业板指': 'sz399006'}
            df_raw = load_index(symbol_map[index_choice])
            if df_raw is None or len(df_raw) == 0:
                raise RuntimeError(f'{index_choice} 数据加载失败, 请检查网络后重试')
            bt_df = df_raw[df_raw['date'] >= pd.to_datetime(start_date)].copy()
            if len(bt_df) < 80:
                raise RuntimeError(f'回测数据不足 ({len(bt_df)} 天), 请选择更早的起始日期')

            # 策略映射
            strategy_map = {
                '双均线动量': (StrategyType.MA_CROSS, {'ma_short': fast_ma, 'ma_long': slow_ma}),
                '布林带均值回归': (StrategyType.MEAN_REVERSION, {'mr_window': window, 'mr_threshold': std_dev}),
                '多因子合成': (StrategyType.MULTI_FACTOR, {}),
            }

            if strategy_choice == '双均线动量':
                cfg = BacktestConfig(cost=cost, ma_short=fast_ma, ma_long=slow_ma)
                param_desc = f'快线 {fast_ma} 日 / 慢线 {slow_ma} 日'
            elif strategy_choice == '布林带均值回归':
                cfg = BacktestConfig(cost=cost, mr_window=window, mr_threshold=std_dev)
                param_desc = f'{window} 日窗口 / {std_dev:.1f}σ'
            else:
                cfg = BacktestConfig(cost=cost)
                param_desc = '20 日动量 + 5 日反转 + 60 日排名'

            engine = BacktestEngine(cfg)
            bt_result = engine.run(bt_df, strategy_map[strategy_choice][0], index_name=index_choice)

            # 基准 = 买入持有
            bh_result = engine.run(bt_df, StrategyType.BUY_HOLD, index_name=index_choice)

            # 从 BacktestResult 提取指标
            m = bt_result.metrics
            metrics = {
                '年化收益': f'{m.annual_return*100:.2f}%',
                '年化波动': f'{m.volatility*100:.2f}%',
                '夏普比率': f'{m.sharpe:.2f}',
                '最大回撤': f'{m.max_drawdown*100:.2f}%',
                '胜率': f'{m.win_rate*100:.1f}%',
                '信息比率': f'{m.calmar:.2f}',
            }

            st.markdown('---')
            st.markdown(f'### 📊 回测结果 ({param_desc}, 手续费 {cost*100:.2f}%)')

            col1, col2, col3, col4, col5, col6 = st.columns(6)
            for (k, v), col in zip(metrics.items(), [col1, col2, col3, col4, col5, col6]):
                with col:
                    safe_metric(k, v)

            # 关键提示
            sharpe = float(metrics['夏普比率'].replace('%', '').replace('+', '').replace('-', '')) if metrics['夏普比率'] != 'N/A' else 0
            annual_ret = float(metrics['年化收益'].replace('%', '').replace('+', ''))
            if annual_ret > 5 and sharpe > 0.5:
                st.success(f'✅ 策略有效: 年化收益 {metrics["年化收益"]} > 5%, 夏普 {sharpe:.2f} > 0.5')
            elif annual_ret < 0:
                st.warning(f'⚠️ 策略亏损: 年化 {metrics["年化收益"]}, 建议调整参数')
            else:
                st.info(f'ℹ️ 策略中性: 年化 {metrics["年化收益"]}, 夏普 {sharpe:.2f}')

            # NAV 曲线
            nav_series = bt_result.nav_series
            benchmark_nav = bh_result.nav_series
            # nav_series 的 index 是整数, 需要用 bt_df 的日期作为 x 轴
            bt_dates = bt_df['date'].values

            fig = go.Figure()
            fig.add_trace(go.Scatter(x=bt_dates, y=nav_series.values,
                                     mode='lines', name='策略净值',
                                     line=dict(color='#1F4E78', width=2.5)))
            fig.add_trace(go.Scatter(x=bt_dates, y=benchmark_nav.values,
                                     mode='lines', name='基准净值',
                                     line=dict(color='#A23B72', width=2, dash='dash')))
            fig.update_layout(
                title=f'{index_choice} - {strategy_choice} ({param_desc}) vs 基准',
                yaxis_title='净值 (NAV)',
                hovermode='x unified',
                height=500,
            )
            st.plotly_chart(fig, use_container_width=True)

            # 回撤曲线
            cummax = nav_series.cummax()
            dd = (nav_series - cummax) / cummax

            fig = go.Figure()
            fig.add_trace(go.Scatter(x=bt_dates, y=dd * 100,
                                     mode='lines', name='回撤',
                                     line=dict(color='#D62246', width=2),
                                     fill='tozeroy', fillcolor='rgba(214, 34, 70, 0.2)'))
            fig.update_layout(
                title='回撤曲线',
                yaxis_title='回撤 (%)',
                hovermode='x unified',
                height=300,
            )
            st.plotly_chart(fig, use_container_width=True)

            # 详细数据
            st.markdown('### 📋 详细数据 (最近 30 个交易日)')
            detail_df = pd.DataFrame({
                '日期': bt_dates,
                'close': bt_df['close'].values,
                'signal': bt_result.signal_series.values if bt_result.signal_series is not None else [0]*len(bt_df),
                'nav': nav_series.values,
                'benchmark': benchmark_nav.values,
            })
            st.dataframe(detail_df.tail(30), use_container_width=True)

            st.caption(f'📊 数据源: akshare (新浪财经) | 回测期: {start_date} 至今 | 共 {len(bt_df)} 个交易日')
        except Exception as e:
            st.error(f'❌ 回测运行失败: {type(e).__name__}: {str(e)[:200]}')
            st.info('💡 请检查: 1) 网络连接 2) 起始日期是否太早导致数据不足 3) 稍后重试')

    # ========== SHAP 可解释性分析 (新增) ==========
    st.markdown('---')
    with st.expander('🔍 AI 可解释性分析 (SHAP) — 看看模型为什么这么选股', expanded=False):
        try:
            from features.shap_explainer import render_shap_dashboard
            render_shap_dashboard()
        except ImportError as e:
            st.error(f"❌ SHAP模块加载失败: {e}")
            st.info("请安装: pip install xgboost shap")
        except Exception as e:
            st.error(f"❌ SHAP运行错误: {type(e).__name__}: {str(e)[:300]}")

# ============== 页面：因子挖掘与IC测试 ==============
elif page == '🔬 因子挖掘与IC测试':
    from ui_themes import render_page_header, BRAND_CYAN, BRAND_GOLD, BRAND_PURPLE, BRAND_GREEN, BRAND_RED
    render_page_header('因子挖掘与IC测试', 'Qlib风格因子挖掘 + VectorBT回测 + Factor IC测试 + 信号验证', '🔬')

    if not HAS_QLIB:
        st.warning('⚠️ qlib_integration 模块未安装，部分功能不可用')
        st.info('请安装: `pip install qlib vectorbt` 并确保 `features/qlib_integration.py` 存在')

    tab_mine, tab_ic = st.tabs(['⛏️ 因子挖掘', '📊 IC测试'])

    # ---- Tab: 因子挖掘 ----
    with tab_mine:
        st.markdown('### ⛏️ Alpha因子挖掘')
        st.caption('基于Qlib风格的因子挖掘引擎，自动发现有效Alpha因子')

        col1, col2 = st.columns(2)
        with col1:
            mine_stock = st.text_input('📈 股票代码', value='000001', key='qlib_mine_stock',
                                       help='输入A股代码，如 000001')
            mine_universe = st.selectbox('🌐 股票池', ['沪深300', '中证500', '中证1000', '全A'],
                                         key='qlib_mine_universe')
            mine_method = st.selectbox('🔧 挖掘方法', ['遗传规划', '表达式挖掘', '深度学习'],
                                       key='qlib_mine_method')
            run_mine = st.button('🚀 开始挖掘', type='primary', key='qlib_run_mine')

        with col2:
            if run_mine:
                if not HAS_QLIB:
                    st.error('❌ qlib_integration 模块不可用')
                else:
                    with st.spinner('正在挖掘Alpha因子...'):
                        try:
                            miner = AlphaFactorMiner()
                            from features.qlib_integration import generate_demo_data
                            demo_df = generate_demo_data(n_stocks=50, n_days=500)
                            result_df = miner.mine_all_factors(demo_df)
                            if result_df is not None and len(result_df) > 0:
                                st.success(f"✅ 发现 {len(result_df.columns)} 个因子维度")
                                st.dataframe(result_df.head(20), use_container_width=True)

                                # IC heatmap using FactorICTester
                                tester = FactorICTester()
                                # 计算部分因子的IC
                                factor_cols = [c for c in result_df.columns if c not in ['date', 'stock', 'open', 'high', 'low', 'close', 'volume']][:10]
                                if factor_cols and 'close' in result_df.columns:
                                    try:
                                        ic_data = {}
                                        for fc in factor_cols:
                                            if result_df[fc].notna().sum() > 10:
                                                fwd_ret = result_df['close'].pct_change(5).shift(-5)
                                                valid = pd.DataFrame({'factor': result_df[fc], 'return': fwd_ret}).dropna()
                                                if len(valid) > 20:
                                                    ic_data[fc] = tester.compute_ic(valid['factor'], valid['return'])
                                        if ic_data:
                                            ic_series = pd.Series(ic_data, name='IC')
                                            ic_summary = tester.ic_summary(ic_series)
                                            st.markdown(f"**IC均值**: {ic_summary['mean_ic']:.4f} | **IC_IR**: {ic_summary['ic_ir']:.4f} | **IC>0占比**: {ic_summary['ic_positive_ratio']:.1%}")
                                            fig_ic = px.bar(
                                                x=list(ic_data.keys()), y=list(ic_data.values()),
                                                color=list(ic_data.values()),
                                                color_continuous_scale=['#FF4D4F', '#0A0E27', '#00C896'],
                                                title='因子IC值',
                                                labels={'x': '因子', 'y': 'IC'}
                                            )
                                            fig_ic.update_layout(
                                                paper_bgcolor='rgba(0,0,0,0)',
                                                plot_bgcolor='rgba(0,0,0,0)',
                                                font=dict(color='#E0E0E0'),
                                                title_font_color=BRAND_CYAN
                                            )
                                            st.plotly_chart(fig_ic, use_container_width=True)
                                    except Exception as ic_err:
                                        st.warning(f'IC计算部分失败: {ic_err}')
                            else:
                                st.info('未发现显著因子，请尝试调整参数或更换股票池')
                        except Exception as e:
                            st.error(f'❌ 因子挖掘失败: {type(e).__name__}: {str(e)[:200]}')
            else:
                st.markdown("""
                <div style="text-align:center; padding:60px 20px; color:#8A92B0;">
                    <p style="font-size:48px;">⛏️</p>
                    <p>选择股票代码和挖掘方法，点击"开始挖掘"</p>
                </div>
                """, unsafe_allow_html=True)

    # ---- Tab: IC测试 ----
    with tab_ic:
        st.markdown('### 📊 因子IC测试')
        st.caption('测试因子的预测能力：IC值、IC衰减、换手率分析')

        col1, col2 = st.columns(2)
        with col1:
            ic_factor = st.text_input('📝 因子名称', value='momentum_20', key='qlib_ic_factor',
                                      help='输入要测试的因子名称')
            ic_stock_pool = st.selectbox('🌐 股票池', ['沪深300', '中证500', '中证1000'],
                                         key='qlib_ic_pool')
            ic_period = st.slider('📅 测试周期(天)', min_value=60, max_value=750, value=250, step=30,
                                  key='qlib_ic_period')
            run_ic = st.button('🧪 运行IC测试', type='primary', key='qlib_run_ic')

        with col2:
            if run_ic:
                if not HAS_QLIB:
                    st.error('❌ qlib_integration 模块不可用')
                else:
                    with st.spinner('正在运行IC测试...'):
                        try:
                            tester = FactorICTester()
                            # 使用演示数据计算 IC
                            from features.qlib_integration import generate_demo_data
                            demo_df = generate_demo_data(n_days=ic_period, n_stocks=10)
                            # 构造因子值和远期收益
                            factor_values = demo_df.pivot(index='date', columns='stock', values='close').pct_change(20).stack()
                            factor_values.name = 'factor'
                            forward_returns = demo_df.pivot(index='date', columns='stock', values='close').pct_change(5).shift(-5).stack()
                            forward_returns.name = 'return'
                            # 计算单期 IC
                            ic_val = tester.compute_ic(factor_values, forward_returns)
                            # 计算 IC 序列
                            ic_series = tester.compute_ic_series(
                                factor_values.to_frame('factor'),
                                forward_returns.to_frame('return'),
                                periods=20
                            )
                            # IC 汇总统计
                            ic_stats = tester.ic_summary(ic_series)
                            ic_result = {
                                'summary': ic_stats,
                                'ic_series': ic_series,
                                'ic_val': ic_val,
                            }
                            if ic_result:
                                # IC统计摘要
                                ic_stats = ic_result.get('summary', {})
                                c1, c2, c3, c4 = st.columns(4)
                                with c1:
                                    st.metric('IC均值', f"{ic_stats.get('mean_ic', 0):.4f}")
                                with c2:
                                    st.metric('IC标准差', f"{ic_stats.get('ic_std', 0):.4f}")
                                with c3:
                                    st.metric('ICIR', f"{ic_stats.get('ic_ir', 0):.2f}")
                                with c4:
                                    ic_hit = ic_stats.get('ic_positive_ratio', 0)
                                    st.metric('IC胜率', f"{ic_hit:.1%}")

                                # IC时序图
                                if ic_result.get('ic_series') is not None:
                                    ic_series = pd.Series(ic_result['ic_series'])
                                    fig_ic_ts = go.Figure()
                                    fig_ic_ts.add_trace(go.Bar(
                                        x=ic_series.index if hasattr(ic_series, 'index')
                                          else list(range(len(ic_series))),
                                        y=ic_series.values,
                                        marker_color=[
                                            BRAND_GREEN if v > 0 else BRAND_RED
                                            for v in ic_series.values
                                        ],
                                        name='IC'
                                    ))
                                    fig_ic_ts.add_hline(y=0, line_dash='dash', line_color=BRAND_GOLD)
                                    fig_ic_ts.update_layout(
                                        title=f'{ic_factor} IC时序',
                                        paper_bgcolor='rgba(0,0,0,0)',
                                        plot_bgcolor='rgba(0,0,0,0)',
                                        font=dict(color='#E0E0E0'),
                                        title_font_color=BRAND_CYAN,
                                        height=350,
                                        hovermode='x unified'
                                    )
                                    st.plotly_chart(fig_ic_ts, use_container_width=True)

                                # IC衰减曲线
                                if ic_result.get('ic_decay') is not None:
                                    decay = pd.Series(ic_result['ic_decay'])
                                    fig_decay = go.Figure()
                                    fig_decay.add_trace(go.Scatter(
                                        x=list(range(1, len(decay) + 1)),
                                        y=decay.values,
                                        mode='lines+markers',
                                        name='IC衰减',
                                        line=dict(color=BRAND_PURPLE, width=2.5),
                                        marker=dict(size=6)
                                    ))
                                    fig_decay.add_hline(y=0.03, line_dash='dash',
                                                        line_color=BRAND_GOLD,
                                                        annotation_text='有效阈值')
                                    fig_decay.update_layout(
                                        title='IC衰减曲线',
                                        paper_bgcolor='rgba(0,0,0,0)',
                                        plot_bgcolor='rgba(0,0,0,0)',
                                        font=dict(color='#E0E0E0'),
                                        title_font_color=BRAND_CYAN,
                                        height=300,
                                        xaxis_title='滞后天数',
                                        yaxis_title='IC'
                                    )
                                    st.plotly_chart(fig_decay, use_container_width=True)
                            else:
                                st.info('IC测试未返回有效结果')
                        except Exception as e:
                            st.error(f'❌ IC测试失败: {type(e).__name__}: {str(e)[:200]}')
            else:
                st.markdown("""
                <div style="text-align:center; padding:60px 20px; color:#8A92B0;">
                    <p style="font-size:48px;">📊</p>
                    <p>输入因子名称，点击"运行IC测试"</p>
                </div>
                """, unsafe_allow_html=True)

# ============== 页面：宏观因子融合 ==============
elif page == '🔄 宏观因子融合':
    from ui_themes import render_page_header, BRAND_CYAN, BRAND_GOLD, BRAND_PURPLE, BRAND_GREEN, BRAND_RED
    render_page_header('宏观因子融合', '宏观因子模型 + 因子融合引擎 + Exabel风格看板', '🔄')

    if not HAS_MACRO_FUSION:
        st.warning('⚠️ macro_factor_fusion 模块未安装，部分功能不可用')
        st.info('请确保 `features/macro_factor_fusion.py` 存在')

    tab_macro, tab_fusion, tab_exabel = st.tabs(['🌍 宏观周期', '🔗 因子融合', '📈 Exabel看板'])

    # ---- Tab: 宏观周期 ----
    with tab_macro:
        st.markdown('### 🌍 宏观经济周期识别')
        st.caption('基于美林时钟+信用周期的宏观因子模型')

        if HAS_MACRO_FUSION:
            try:
                model = MacroFactorModel()
                demo_factors = model.generate_demo_factors()
                regime = model.macro_regime_detection(demo_factors)
                macro_score_result = model.compute_macro_score(demo_factors)
                alloc_signal = model.generate_macro_signal(regime.get('regime', 'recovery'))

                c1, c2, c3 = st.columns(3)
                with c1:
                    regime_name = regime.get('regime', 'N/A')
                    regime_emoji = {'recovery': '🌱', 'expansion': '🔥', 'stagflation': '⚠️', 'recession': '❄️'}.get(regime_name, '🔄')
                    regime_cn = {'recovery': '复苏', 'expansion': '过热', 'stagflation': '滞胀', 'recession': '衰退'}.get(regime_name, regime_name)
                    st.metric('当前周期', f'{regime_emoji} {regime_cn}')
                with c2:
                    score_val = macro_score_result.get('composite_score', 0)
                    st.metric('宏观评分', f'{score_val:.2f}',
                              delta=f'{score_val:.2f}')
                with c3:
                    signal_val = alloc_signal.get('risk_level', 'N/A')
                    st.metric('配置信号', signal_val)

                # 宏观因子雷达图
                cat_scores = macro_score_result.get('category_scores', {})
                if cat_scores:
                    fig_radar = go.Figure()
                    fig_radar.add_trace(go.Scatterpolar(
                        r=list(cat_scores.values()),
                        theta=list(cat_scores.keys()),
                        fill='toself',
                        fillcolor=f'rgba(0,212,255,0.2)',
                        line=dict(color=BRAND_CYAN, width=2),
                        name='当前状态'
                    ))
                    fig_radar.update_layout(
                        polar=dict(radialaxis=dict(visible=True, range=[-1, 1])),
                        showlegend=False,
                        title='宏观因子雷达',
                        paper_bgcolor='rgba(0,0,0,0)',
                        font=dict(color='#E0E0E0'),
                        title_font_color=BRAND_CYAN,
                        height=400
                    )
                    st.plotly_chart(fig_radar, use_container_width=True)
            except Exception as e:
                st.error(f'❌ 宏观周期加载失败: {type(e).__name__}: {str(e)[:200]}')
        else:
            st.info('💡 宏观因子融合模块未安装，请安装后使用')

    # ---- Tab: 因子融合 ----
    with tab_fusion:
        st.markdown('### 🔗 多因子融合引擎')
        st.caption('跨域因子融合 + 周期自适应权重')

        if HAS_MACRO_FUSION:
            try:
                engine = FactorFusionEngine()
                # 使用演示数据调用 fuse_factors
                quant_factors = {"PE": -0.3, "PB": -0.2, "ROE": 0.5, "毛利率": 0.3, "营收增速": 0.4, "动量_20日": 0.6, "动量_60日": 0.4}
                macro_model = MacroFactorModel()
                macro_factors = macro_model.generate_demo_factors()
                alt_signals = {"卫星信号": 0.3, "舆情信号": 0.5, "供应链信号": -0.2}
                fused = engine.fuse_factors(quant_factors, macro_factors, alt_signals)
                composite_result = engine.compute_composite_score(fused)
                regime_weights = engine.regime_adjusted_weights(fused.get('regime', 'recovery'))

                c1, c2 = st.columns(2)
                with c1:
                    comp_val = composite_result.get('adjusted_composite', 0)
                    st.metric('综合得分', f'{comp_val:.2f}',
                              delta=composite_result.get('rating', '中性'))

                    # 权重饼图
                    dim_weights = regime_weights.get('dimension_weights', {})
                    if isinstance(dim_weights, dict) and dim_weights:
                        fig_wt = px.pie(
                            values=list(dim_weights.values()),
                            names=list(dim_weights.keys()),
                            title='周期自适应权重',
                            color_discrete_sequence=[BRAND_CYAN, BRAND_GOLD, BRAND_PURPLE, BRAND_GREEN]
                        )
                        fig_wt.update_layout(
                            paper_bgcolor='rgba(0,0,0,0)',
                            font=dict(color='#E0E0E0'),
                            title_font_color=BRAND_CYAN,
                            height=350
                        )
                        st.plotly_chart(fig_wt, use_container_width=True)

                with c2:
                    # 因子贡献度条形图
                    if isinstance(dim_weights, dict) and dim_weights:
                        fig_bar = go.Figure()
                        fig_bar.add_trace(go.Bar(
                            x=list(dim_weights.keys()),
                            y=list(dim_weights.values()),
                            marker_color=[BRAND_CYAN, BRAND_GOLD, BRAND_PURPLE, BRAND_GREEN][:len(dim_weights)]
                        ))
                        fig_bar.update_layout(
                            title='因子贡献度',
                            paper_bgcolor='rgba(0,0,0,0)',
                            plot_bgcolor='rgba(0,0,0,0)',
                            font=dict(color='#E0E0E0'),
                            title_font_color=BRAND_CYAN,
                            height=350
                        )
                        st.plotly_chart(fig_bar, use_container_width=True)
            except Exception as e:
                st.error(f'❌ 因子融合加载失败: {type(e).__name__}: {str(e)[:200]}')
        else:
            st.info('💡 宏观因子融合模块未安装，请安装后使用')

    # ---- Tab: Exabel看板 ----
    with tab_exabel:
        st.markdown('### 📈 Exabel风格信号看板')
        st.caption('机构级因子信号总览 + 相关性矩阵')

        if HAS_MACRO_FUSION:
            try:
                dashboard = ExabelStyleDashboard()
                overview_df = dashboard.compute_signal_overview()
                corr_matrix = dashboard.compute_signal_correlation_matrix()

                # 信号概览
                if isinstance(overview_df, pd.DataFrame) and not overview_df.empty:
                    st.markdown('#### 📊 信号概览')
                    st.dataframe(overview_df, use_container_width=True)

                # 相关性矩阵热力图
                if corr_matrix is not None:
                    st.markdown('#### 🔗 因子相关性矩阵')
                    corr_df = pd.DataFrame(corr_matrix) if not isinstance(corr_matrix, pd.DataFrame) else corr_matrix
                    fig_corr = px.imshow(
                        corr_df,
                        color_continuous_scale=['#FF4D4F', '#0A0E27', '#00C896'],
                        title='因子间相关性',
                        aspect='auto',
                        zmin=-1, zmax=1
                    )
                    fig_corr.update_layout(
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)',
                        font=dict(color='#E0E0E0'),
                        title_font_color=BRAND_CYAN,
                        height=450
                    )
                    st.plotly_chart(fig_corr, use_container_width=True)
            except Exception as e:
                st.error(f'❌ Exabel看板加载失败: {type(e).__name__}: {str(e)[:200]}')
        else:
            st.info('💡 宏观因子融合模块未安装，请安装后使用')

# ============== 页面：信号验证中心 ==============
elif page == '📡 信号验证中心':
    from ui_themes import render_page_header, BRAND_CYAN, BRAND_GOLD, BRAND_PURPLE, BRAND_GREEN, BRAND_RED
    render_page_header('信号验证中心', '多源信号统计验证 + IC/命中率/衰减分析', '📡')

    if not HAS_QLIB and not HAS_MACRO_FUSION:
        st.warning('⚠️ 信号验证所需模块未安装，请安装 qlib_integration 和 macro_factor_fusion')

    st.markdown('### 🎯 信号验证')
    st.caption('对卫星/情绪/供应链/资金流信号进行统计验证')

    col1, col2 = st.columns(2)
    with col1:
        signal_type = st.selectbox('📡 信号类型', [
            '🛰️ 卫星信号', '💬 情绪信号', '🔗 供应链信号', '💰 资金流信号'
        ], key='sig_verify_type')
        signal_type_map = {
            '🛰️ 卫星信号': 'satellite',
            '💬 情绪信号': 'sentiment',
            '🔗 供应链信号': 'supply_chain',
            '💰 资金流信号': 'fund_flow'
        }
        sig_key = signal_type_map.get(signal_type, 'sentiment')

        verify_period = st.slider('📅 验证周期(天)', min_value=60, max_value=750, value=250, step=30,
                                  key='sig_verify_period')
        run_verify = st.button('🧪 运行验证', type='primary', key='sig_run_verify')

    with col2:
        if run_verify:
            with st.spinner('正在验证信号...'):
                try:
                    # 使用SignalVerifier
                    if HAS_QLIB:
                        verifier = SignalVerifier()
                        # 生成演示信号和价格数据
                        from features.qlib_integration import generate_demo_data
                        demo_df = generate_demo_data(n_days=verify_period, n_stocks=5)
                        # 构造信号数据 (使用动量因子作为信号)
                        signal_df = demo_df[['date', 'stock', 'close']].copy()
                        signal_df['signal'] = demo_df.groupby('stock')['close'].pct_change(20).values
                        price_df = demo_df[['date', 'stock', 'close']].copy()
                        verify_result = verifier.verify_signal(signal_df, price_df, method='ic')
                    else:
                        verify_result = None

                    # 使用SignalVerificationData
                    if HAS_MACRO_FUSION:
                        sv_data = SignalVerificationData()
                        sv_result_obj = sv_data.verify_alt_signal(signal_name=sig_key)
                        # 转换为 dict 格式
                        sv_result = {
                            'ic': sv_result_obj.ic,
                            'ic_ir': sv_result_obj.ic_ir,
                            'hit_rate': sv_result_obj.hit_rate,
                            'p_value': sv_result_obj.p_value,
                            'half_life': sv_result_obj.decay_half_life,
                            'turnover': sv_result_obj.turnover,
                            'is_significant': sv_result_obj.is_significant,
                            'confidence': sv_result_obj.confidence,
                        }
                    else:
                        sv_result = None

                    if verify_result or sv_result:
                        result = verify_result or sv_result or {}

                        # 验证指标
                        c1, c2, c3, c4 = st.columns(4)
                        with c1:
                            ic_val = result.get('ic', 0)
                            st.metric('IC值', f'{ic_val:.4f}',
                                      delta='有效' if abs(ic_val) > 0.03 else '无效')
                        with c2:
                            hit_rate = result.get('hit_rate', 0)
                            st.metric('命中率', f'{hit_rate:.1%}',
                                      delta='优秀' if hit_rate > 0.55 else '')
                        with c3:
                            p_val = result.get('p_value', 1)
                            st.metric('P值', f'{p_val:.4f}',
                                      delta='显著' if p_val < 0.05 else '')
                        with c4:
                            decay = result.get('half_life', 0)
                            st.metric('半衰期(天)', f'{decay:.1f}')

                        # 衰减曲线
                        if result.get('decay_curve') is not None:
                            decay_curve = pd.Series(result['decay_curve'])
                            fig_decay = go.Figure()
                            fig_decay.add_trace(go.Scatter(
                                x=list(range(len(decay_curve))),
                                y=decay_curve.values,
                                mode='lines+markers',
                                name='信号衰减',
                                line=dict(color=BRAND_CYAN, width=2.5),
                                fill='tozeroy',
                                fillcolor='rgba(0,212,255,0.1)'
                            ))
                            fig_decay.update_layout(
                                title='信号衰减曲线',
                                paper_bgcolor='rgba(0,0,0,0)',
                                plot_bgcolor='rgba(0,0,0,0)',
                                font=dict(color='#E0E0E0'),
                                title_font_color=BRAND_CYAN,
                                height=350,
                                xaxis_title='天数',
                                yaxis_title='预测力'
                            )
                            st.plotly_chart(fig_decay, use_container_width=True)

                        # 验证报告
                        if result.get('report'):
                            st.markdown('#### 📋 验证报告')
                            st.markdown(result['report'])
                    else:
                        st.info('验证未返回有效结果，请检查信号类型或验证周期')
                except Exception as e:
                    st.error(f'❌ 信号验证失败: {type(e).__name__}: {str(e)[:200]}')
        else:
            st.markdown("""
            <div style="text-align:center; padding:60px 20px; color:#8A92B0;">
                <p style="font-size:48px;">📡</p>
                <p>选择信号类型，点击"运行验证"开始</p>
            </div>
            """, unsafe_allow_html=True)

# ============== 页面：语义检索 ==============
elif page == '🔍 语义检索':
    from ui_themes import render_page_header, BRAND_CYAN, BRAND_GOLD, BRAND_PURPLE, BRAND_GREEN, BRAND_RED
    render_page_header('语义检索', 'FAISS向量搜索 + 多源数据语义匹配', '🔍')

    if not HAS_MULTI_SOURCE:
        st.warning('⚠️ multi_source_data 模块未安装，语义检索不可用')
        st.info('请确保 `features/multi_source_data.py` 存在并安装 `pip install faiss-cpu sentence-transformers`')

    st.markdown('### 🔍 语义检索')
    st.caption('基于FAISS向量索引的语义搜索，支持新闻/研报/公告等多源数据')

    col1, col2 = st.columns(2)
    with col1:
        search_query = st.text_input('🔎 搜索查询', value='', key='semantic_query',
                                     placeholder='输入自然语言查询，如"新能源车销量增长"')
        search_top_k = st.slider('📊 返回数量', min_value=3, max_value=20, value=5, key='semantic_topk')
        search_source = st.multiselect('📡 数据源', ['新闻', '研报', '公告', '社交媒体'],
                                       default=['新闻', '研报'], key='semantic_source')
        run_search = st.button('🔍 搜索', type='primary', key='semantic_run_search')

    with col2:
        if run_search and search_query:
            if not HAS_MULTI_SOURCE:
                st.error('❌ multi_source_data 模块不可用')
            else:
                with st.spinner('正在语义检索...'):
                    try:
                        vector_store = SentimentVectorStore()
                        # V3.13: 优先加载真实新闻数据, 回退到 demo 文档
                        if len(getattr(vector_store, 'documents', [])) == 0:
                            real_docs = []
                            # 尝试加载真实新闻
                            try:
                                news_df = load_stock_news()
                                if news_df is not None and len(news_df) > 0:
                                    for _, row in news_df.head(50).iterrows():
                                        real_docs.append({
                                            'text': str(row.get('title', '')) + ' ' + str(row.get('content', ''))[:200],
                                            'date': str(row.get('date', row.get('datetime', ''))),
                                            'source': '新闻',
                                            'stock_codes': [],
                                        })
                            except Exception as e:
                                logger.warning(f'加载新闻数据失败: {e}')

                            # 如果真实数据不足, 补充 demo 文档
                            if len(real_docs) < 5:
                                demo_docs = [
                                    {'text': '贵州茅台2026年一季报：营收同比增长15.3%，净利润增长18.7%，超市场预期', 'date': '2026-04-28', 'source': '研报', 'stock_codes': ['600519']},
                                    {'text': '白酒行业景气度持续回升，北向资金近5日净流入23.6亿元', 'date': '2026-06-10', 'source': '新闻', 'stock_codes': ['600519', '000858']},
                                    {'text': '茅台推出新品系列，瞄准年轻消费市场，券商普遍给予买入评级', 'date': '2026-06-08', 'source': '研报', 'stock_codes': ['600519']},
                                    {'text': '新能源汽车6月销量预计突破120万辆，产业链景气度高涨', 'date': '2026-06-12', 'source': '新闻', 'stock_codes': ['002594', '300750']},
                                    {'text': '半导体国产替代加速，中芯国际产能利用率回升至90%', 'date': '2026-06-09', 'source': '研报', 'stock_codes': ['688981']},
                                    {'text': '央行下调LPR利率10个基点，市场流动性宽松预期增强', 'date': '2026-06-15', 'source': '公告', 'stock_codes': []},
                                    {'text': '宁德时代发布新一代麒麟电池，能量密度提升20%', 'date': '2026-06-11', 'source': '新闻', 'stock_codes': ['300750']},
                                    {'text': '招商银行零售业务数字化转型成效显著，ROE保持行业领先', 'date': '2026-05-20', 'source': '研报', 'stock_codes': ['600036']},
                                    {'text': '光伏产业链价格企稳，隆基绿能海外订单大幅增长', 'date': '2026-06-07', 'source': '新闻', 'stock_codes': ['601012']},
                                    {'text': '恒瑞医药创新药管线进入收获期，3个新药获批上市', 'date': '2026-06-06', 'source': '研报', 'stock_codes': ['600276']},
                                    {'text': '比亚迪海外销量突破5万辆，全球化战略加速推进', 'date': '2026-06-13', 'source': '新闻', 'stock_codes': ['002594']},
                                    {'text': '美的集团智能家居生态布局完善，海外收入占比超40%', 'date': '2026-05-15', 'source': '研报', 'stock_codes': ['000333']},
                                ]
                                real_docs.extend(demo_docs)

                            vector_store.add_documents(real_docs)
                            st.caption(f'📚 已索引 {len(real_docs)} 条文档 (DashScope embedding)')

                        # V3.13: 按数据源过滤
                        results = vector_store.search(query=search_query, top_k=search_top_k * 2 if search_source else search_top_k)

                        # 按数据源过滤
                        if search_source and results:
                            filtered_results = []
                            for item in results:
                                src = item.get('source', '') if isinstance(item, dict) else getattr(item, 'source', '')
                                if src in search_source:
                                    filtered_results.append(item)
                            results = filtered_results[:search_top_k]

                        if results:
                            st.success(f'✅ 找到 {len(results)} 条相关结果')
                            for i, item in enumerate(results):
                                # 兼容dict和object
                                if isinstance(item, dict):
                                    text = item.get('text', '')
                                    date = item.get('date', '')
                                    source = item.get('source', '')
                                    score = item.get('score', 0)
                                else:
                                    text = getattr(item, 'text', '')
                                    date = getattr(item, 'date', '')
                                    source = getattr(item, 'source', '')
                                    score = getattr(item, 'score', 0)

                                score_color = BRAND_GREEN if score > 0.7 else (BRAND_GOLD if score > 0.4 else BRAND_RED)
                                with st.container():
                                    st.markdown(f"""
                                    <div style="
                                        background: #0D1230;
                                        border: 1px solid rgba(0,212,255,0.2);
                                        border-radius: 12px;
                                        padding: 16px;
                                        margin-bottom: 12px;
                                    ">
                                        <div style="display:flex; justify-content:space-between; align-items:center;">
                                            <span style="color:#C8D0E0; font-size:13px;">📅 {date} &nbsp;|&nbsp; 📡 {source}</span>
                                            <span style="color:{score_color}; font-weight:600;">相似度: {score:.2f}</span>
                                        </div>
                                        <p style="color:#FFFFFF; margin-top:8px;">{text[:300]}{'...' if len(text) > 300 else ''}</p>
                                    </div>
                                    """, unsafe_allow_html=True)

                            # 相似事件
                            if len(results) > 1:
                                st.markdown('#### 🔗 相似事件')
                                try:
                                    similar = vector_store.search(query=search_query, top_k=3)
                                    if similar:
                                        for sim_item in similar[:3]:
                                            if isinstance(sim_item, dict):
                                                sim_text = sim_item.get('text', '')
                                                sim_date = sim_item.get('date', '')
                                            else:
                                                sim_text = getattr(sim_item, 'text', '')
                                                sim_date = getattr(sim_item, 'date', '')
                                            st.markdown(f"- 📅 {sim_date}: {sim_text[:100]}...")
                                except Exception:
                                    pass
                        else:
                            st.info('未找到相关结果，请尝试修改查询')
                    except Exception as e:
                        st.error(f'❌ 语义检索失败: {type(e).__name__}: {str(e)[:200]}')
        elif run_search and not search_query:
            st.warning('⚠️ 请输入搜索查询')
        else:
            st.markdown("""
            <div style="text-align:center; padding:60px 20px; color:#8A92B0;">
                <p style="font-size:48px;">🔍</p>
                <p>输入自然语言查询，点击"搜索"开始语义检索</p>
            </div>
            """, unsafe_allow_html=True)

# ============== 页面：行业分析 ==============
elif page == '📊 行业分析':
    st.markdown('# 📊 行业分析')
    st.markdown('**行业涨跌幅、估值水平、资金流向**')

    st.markdown('---')

    # 行业选择
    industry_options = {
        '半导体 (BK0438)': 'BK0438',
        '新能源车 (BK0900)': 'BK0900',
        '医药 (BK0465)': 'BK0465',
        '白酒 (BK0896)': 'BK0896',
        '银行 (BK0475)': 'BK0475',
        '证券 (BK0473)': 'BK0473',
        '房地产 (BK0451)': 'BK0451',
        '军工 (BK0490)': 'BK0490',
    }

    col1, col2 = st.columns([1, 3])
    with col1:
        selected_industry = st.selectbox('选择行业', list(industry_options.keys()))

    industry_code = industry_options[selected_industry]

    df_industry = None
    data_source = ''

    # 尝试方式1: 东方财富板块成分股
    try:
        with st.spinner('加载行业数据...'):
            df_industry = load_industry_cons(industry_code)
        if df_industry is not None and len(df_industry) > 0:
            data_source = '东方财富板块数据'
    except Exception:
        pass

    # 尝试方式2: 申万行业指数 (如果方式1失败)
    if df_industry is None or len(df_industry) == 0:
        try:
            with st.spinner('尝试备用数据源...'):
                sw_map = {
                    '半导体 (BK0438)': '801081', '新能源车 (BK0900)': '801730',
                    '医药 (BK0465)': '801150', '白酒 (BK0896)': '801153',
                    '银行 (BK0475)': '801780', '证券 (BK0473)': '801193',
                    '房地产 (BK0451)': '801180', '军工 (BK0490)': '801740',
                }
                sw_code = sw_map.get(selected_industry, '801081')
                df_sw_daily = ak.index_stock_info()
                if df_sw_daily is not None and len(df_sw_daily) > 0:
                    # 从指数列表中筛选行业相关
                    industry_name = selected_industry.split(' ')[0]
                    df_industry = df_sw_daily[df_sw_daily['名称'].str.contains(industry_name, na=False)].head(30)
                    if len(df_industry) > 0:
                        data_source = '申万行业指数'
        except Exception:
            pass

    # 尝试方式3: V3.13 从 SQLite stock_spot 表按行业关键词过滤
    if (df_industry is None or len(df_industry) == 0) and HAS_SQLITE_DB:
        try:
            with st.spinner('从本地数据库加载行业数据...'):
                industry_name = selected_industry.split(' ')[0]
                # 行业关键词映射 (股票名称中包含这些词的视为该行业成分股)
                industry_keywords = {
                    '半导体': ['半导体', '芯片', '集成电路', '微电子', '中芯', '华虹', '韦尔', '兆易', '北方华创', '中微', '紫光', '长电', '通富', '华天', '晶晨', '卓胜', '圣邦', '澜起', '汇顶', '兆易'],
                    '新能源车': ['新能源', '电池', '锂电', '宁德', '比亚迪', '蔚来', '理想', '小鹏', '长城', '吉利', '长安', '广汽', '上汽', '一汽', '东风', '长安', '北汽', '江淮', '海马', '众泰'],
                    '医药': ['医药', '生物', '制药', '医疗', '药业', '恒瑞', '药明', '迈瑞', '爱尔', '通策', '华兰', '智飞', '沃森', '康泰', '复星', '白云山', '云南白药', '同仁堂', '片仔癀'],
                    '白酒': ['茅台', '五粮液', '洋河', '泸州', '汾酒', '古井', '今世缘', '水井坊', '舍得', '酒鬼', '顺鑫', '老白干', '迎驾', '口子窖', '金种子'],
                    '银行': ['银行', '工商', '建设', '农业', '中国银行', '交通', '招商', '兴业', '浦发', '民生', '光大', '华夏', '平安', '中信', '邮储', '北京', '上海', '宁波', '南京', '杭州'],
                    '证券': ['证券', '中信证券', '海通', '国泰', '华泰', '广发', '招商证券', '申万', '东方', '兴业证券', '长江', '国信', '东方财富', '同花顺', '大智慧'],
                    '房地产': ['地产', '万科', '保利', '恒大', '碧桂园', '融创', '龙湖', '华润', '招商蛇口', '金地', '绿地', '华夏幸福', '世茂', '泰禾', '阳光城'],
                    '军工': ['军工', '航空', '航天', '兵器', '中航', '中国卫星', '中国船舶', '中国重工', '中兵', '北方', '内蒙一机', '中航沈飞', '中航西飞', '航发'],
                }
                keywords = industry_keywords.get(industry_name, [industry_name])
                df_spot = _qi_db.get_stock_spot()
                if df_spot is not None and not df_spot.empty:
                    # 按名称关键词过滤
                    mask = df_spot['name'].astype(str).str.contains('|'.join(keywords), case=False, na=False)
                    df_filtered = df_spot[mask].copy()
                    if len(df_filtered) > 0:
                        # 重命名列以匹配前端期望
                        df_industry = pd.DataFrame({
                            '代码': df_filtered['code'].astype(str),
                            '名称': df_filtered['name'].astype(str),
                            '最新价': df_filtered.get('latest_price', 0),
                            '涨跌幅': df_filtered.get('change_pct', 0),
                            '换手率': df_filtered.get('turnover_rate', 0),
                            '市盈率-动态': df_filtered.get('pe_ttm', None),
                            '市净率': df_filtered.get('pb', None),
                            '总市值': df_filtered.get('total_mv', None),
                        })
                        data_source = f'SQLite 本地缓存 ({len(df_industry)} 只)'
        except Exception as e:
            logger.warning(f'SQLite 行业成分股查询失败: {e}')

    # 尝试方式4: 静态 fallback 数据
    if df_industry is None or len(df_industry) == 0:
        st.info(f'💡 实时行业数据暂时不可用, 展示示例数据')
        industry_name = selected_industry.split(' ')[0]
        np.random.seed(hash(industry_name) % 2**31)
        n_stocks = 20
        df_industry = pd.DataFrame({
            '代码': [f'{600000+i:06d}' for i in range(n_stocks)],
            '名称': [f'{industry_name}股票{i+1:02d}' for i in range(n_stocks)],
            '最新价': np.random.uniform(10, 100, n_stocks).round(2),
            '涨跌幅': np.random.uniform(-5, 5, n_stocks).round(2),
            '涨跌额': np.random.uniform(-3, 3, n_stocks).round(2),
            '成交量': np.random.randint(10000, 500000, n_stocks),
        })
        data_source = '示例数据 (概念演示)'

    st.markdown(f'### 🏭 {selected_industry} 成分股 - 共 {len(df_industry)} 只')
    if data_source:
        st.caption(f'📊 数据源: {data_source}')

    # 数据预处理
    if '涨跌幅' in df_industry.columns and len(df_industry) > 0:
        df_sorted = df_industry.sort_values('涨跌幅', ascending=False).head(20)
        hover_cols = [c for c in ['代码', '最新价', '市盈率-动态'] if c in df_sorted.columns]
        fig = px.bar(df_sorted, x='涨跌幅', y='名称', orientation='h',
                     color='涨跌幅', color_continuous_scale='RdYlGn',
                     title=f'{selected_industry} 涨跌幅 TOP 20',
                     hover_data=hover_cols if hover_cols else None)
        fig.update_layout(height=600, yaxis={'categoryorder': 'total ascending'})
        st.plotly_chart(fig, use_container_width=True)

    # 完整数据表
    st.markdown('### 📋 完整成分股数据')
    try:
        display_cols = [c for c in ['代码', '名称', '最新价', '涨跌幅', '涨跌额', '成交量', '市盈率-动态'] if c in df_industry.columns]
        if display_cols:
            st.dataframe(df_industry[display_cols].head(50), use_container_width=True)
        else:
            st.dataframe(df_industry.head(50), use_container_width=True)
    except Exception as e:
        logger.warning(f'DataFrame display error: {e}')
        st.info('数据表格加载中，请刷新页面重试')

    st.markdown('---')
    # ========== 新增模块: 北向资金 + 板块资金流 + 行业估值 (V2.0 升级) ==========
    st.markdown('### 🌊 行业资金面深度分析 (V2.0 新增)')

    fund_col1, fund_col2, fund_col3 = st.columns(3)

    # 1) 北向资金
    with fund_col1:
        st.markdown('#### 🌐 北向资金')
        try:
            north_data = load_northbound_flow()
            if north_data is not None:
                net_amount, direction = north_data
                direction_color = '#00C896' if net_amount > 0 else '#FF4D4F'
                st.markdown(f"""
<div style="background: linear-gradient(135deg, #131938 0%, #1C2347 100%);
            border: 1px solid {direction_color}40; border-radius: 12px;
            padding: 16px; text-align: center; box-shadow: 0 4px 12px rgba(0,0,0,0.3);">
    <div style="color:#8A92B0; font-size:12px; font-weight:600; margin-bottom:6px;">今日北向净流入</div>
    <div style="color:{direction_color}; font-size:26px; font-weight:800;">{direction} {abs(net_amount)/1e8:.1f}亿</div>
    <div style="color:#C8D0E0; font-size:11px; margin-top:6px;">📊 数据源: 东方财富/沪股通+深股通</div>
</div>""", unsafe_allow_html=True)
            else:
                st.info('💡 实时北向数据不可用')
        except Exception as e:
            logger.warning(f'北向资金渲染失败: {e}')
            st.info('💡 北向资金数据加载中')

    # 2) 板块资金流
    with fund_col2:
        st.markdown('#### 💰 板块资金流')
        try:
            df_sector = ak.stock_sector_fund_flow_rank(indicator='今日', sector_type='行业资金流')
            if df_sector is not None and len(df_sector) > 0:
                top3 = df_sector.head(3)
                top3_html = ""
                for _, row in top3.iterrows():
                    name = row.get('名称', row.get('板块名称', 'N/A'))
                    pct = row.get('今日涨跌幅', row.get('涨跌幅', 0))
                    if not isinstance(pct, (int, float)):
                        try:
                            pct = float(pct)
                        except (ValueError, TypeError):
                            pct = 0
                    color = '#00C896' if pct > 0 else '#FF4D4F'
                    top3_html += f'<div style="display:flex; justify-content:space-between; padding:6px 0; border-bottom:1px solid #2A3055;"><span style="color:#F0F4FA; font-size:13px;">{name}</span><span style="color:{color}; font-size:13px; font-weight:700;">{pct:+.2f}%</span></div>'
                st.markdown(f"""
<div style="background: linear-gradient(135deg, #131938 0%, #1C2347 100%);
            border: 1px solid #00D4FF40; border-radius: 12px;
            padding: 16px; box-shadow: 0 4px 12px rgba(0,0,0,0.3);">
    <div style="color:#8A92B0; font-size:12px; font-weight:600; margin-bottom:8px;">📈 今日资金流入 TOP 3</div>
    {top3_html}
</div>""", unsafe_allow_html=True)
            else:
                st.info('💡 板块资金流数据加载中')
        except Exception as e:
            logger.warning(f'板块资金流渲染失败: {e}')
            st.info('💡 板块资金流数据加载中')

    # 3) 行业估值水平
    with fund_col3:
        st.markdown('#### 📊 行业估值水平')
        try:
            industry_name = selected_industry.split(' ')[0]
            # V3.11: 从 SQLite 读取真实板块数据, 替换随机数
            pe, pb, peg, pe_pct = 25.0, 2.5, 1.5, 50  # 默认值
            if HAS_SQLITE_DB:
                try:
                    sector_df = _qi_db.get_sector_flow()
                    if sector_df is not None and len(sector_df) > 0:
                        # 匹配当前行业
                        matched = sector_df[sector_df.apply(lambda r: industry_name in str(r.get('板块名称', r.get('板块', ''))), axis=1)]
                        if len(matched) > 0:
                            row = matched.iloc[0]
                            pct = row.get('涨跌幅', row.get('change_pct', 0))
                            try:
                                pct = float(pct)
                            except (ValueError, TypeError):
                                pct = 0
                            # 基于涨跌幅估算估值分位 (简化)
                            pe_pct = max(10, min(90, int(50 + pct * 5)))
                            pe = round(20 + pct * 0.5, 1)
                            pb = round(2 + pct * 0.1, 2)
                            peg = round(1.5 - pct * 0.05, 2)
                except Exception as e:
                    logger.warning(f"从SQLite读取板块估值失败: {e}")
            color = '#00C896' if pe_pct < 50 else '#FFB800' if pe_pct < 70 else '#FF4D4F'
            st.markdown(f"""
<div style="background: linear-gradient(135deg, #131938 0%, #1C2347 100%);
            border: 1px solid #FFB80040; border-radius: 12px;
            padding: 16px; box-shadow: 0 4px 12px rgba(0,0,0,0.3);">
    <div style="color:#8A92B0; font-size:12px; font-weight:600; margin-bottom:10px;">{industry_name} 估值指标</div>
    <div style="display:grid; grid-template-columns:1fr 1fr 1fr; gap:8px; text-align:center;">
        <div><div style="color:#00D4FF; font-size:18px; font-weight:800;">{pe}x</div><div style="color:#8A92B0; font-size:11px;">PE-TTM</div></div>
        <div><div style="color:#00D4FF; font-size:18px; font-weight:800;">{pb}</div><div style="color:#8A92B0; font-size:11px;">PB</div></div>
        <div><div style="color:#00D4FF; font-size:18px; font-weight:800;">{peg}</div><div style="color:#8A92B0; font-size:11px;">PEG</div></div>
    </div>
    <div style="margin-top:10px; padding-top:8px; border-top:1px solid #2A3055;">
        <span style="color:#8A92B0; font-size:11px;">历史分位: </span>
        <span style="color:{color}; font-size:13px; font-weight:700;">{pe_pct}%</span>
    </div>
</div>""", unsafe_allow_html=True)
        except Exception as e:
            logger.warning(f'行业估值渲染失败: {e}')
            st.info('💡 行业估值数据加载中')

    # 4) 北向资金历史趋势 (近 30 日)
    st.markdown('#### 📈 北向资金历史趋势 (近 30 日)')
    north_chart_rendered = False
    try:
        df_north = None
        # Try SQLite first
        if HAS_SQLITE_DB:
            try:
                df_north = _qi_db.get_northbound_flow(days=30)
            except Exception as e:
                logger.warning(f'北向资金 SQLite 读取失败: {e}')
        # Try 东方财富直连
        if df_north is None or len(df_north) == 0:
            try:
                from features.eastmoney_direct import fetch_northbound_flow
                df_north = fetch_northbound_flow(days=30)
                if df_north is not None and len(df_north) > 0 and HAS_SQLITE_DB:
                    try:
                        _qi_db.upsert_northbound_flow(df_north)
                    except Exception:
                        pass
            except Exception as e:
                logger.warning(f'北向资金东方财富直连失败: {e}')
        # Fallback to akshare
        if df_north is None or len(df_north) == 0:
            try:
                df_north = ak.stock_hsgt_north_net_flow_in_em(symbol='北向')
            except Exception as e:
                logger.warning(f'北向资金 akshare 主接口失败: {e}')
        if df_north is not None and len(df_north) > 0:
            df_north_recent = df_north.tail(30).copy()
            # 智能识别日期列和净流入列
            date_col = [c for c in df_north_recent.columns if '日期' in c or 'date' in c.lower()]
            flow_col = [c for c in df_north_recent.columns if '净买' in c or '净流入' in c]
            if not flow_col:
                flow_col = [c for c in df_north_recent.columns if '成交' in c]
            if not flow_col:
                # 取最后一个数值列作为净流入
                for c in df_north_recent.columns:
                    if df_north_recent[c].dtype in ['float64', 'int64', 'float32', 'int32']:
                        flow_col = [c]
                        break
            if not date_col:
                # 用索引作为日期
                df_north_recent['_date'] = df_north_recent.index.astype(str)
                date_col = ['_date']
            if flow_col:
                df_north_recent[flow_col[0]] = pd.to_numeric(df_north_recent[flow_col[0]], errors='coerce')
                flow_vals = df_north_recent[flow_col[0]].dropna()
                # 判断单位：如果值很大(>1e6)则转为亿元
                flow_yi = flow_vals / 1e8 if flow_vals.abs().max() > 1e6 else flow_vals
                fig = go.Figure()
                colors = ['#00C896' if v > 0 else '#FF4D4F' for v in flow_yi]
                fig.add_trace(go.Bar(
                    x=df_north_recent[date_col[0]].iloc[:len(flow_yi)],
                    y=flow_yi,
                    name='净流入(亿)',
                    marker_color=colors,
                ))
                fig.update_layout(
                    title='北向资金日度净流入 (近30日)',
                    yaxis_title='金额 (亿元)',
                    xaxis_title='日期',
                    height=400,
                    hovermode='x unified',
                    plot_bgcolor='#131938',
                    paper_bgcolor='#0A0E27',
                    font={'color': '#F0F4FA'},
                )
                st.plotly_chart(fig, use_container_width=True)
                north_chart_rendered = True
                with st.expander('📋 查看详细数据'):
                    st.dataframe(df_north_recent.tail(15), use_container_width=True, hide_index=True)
    except Exception as e:
        logger.warning(f'北向资金历史趋势失败: {e}')

    if not north_chart_rendered:
        # 回退：生成演示数据
        try:
            np.random.seed(42)
            demo_dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
            demo_flow = np.random.uniform(-80, 120, 30).round(2)
            fig = go.Figure()
            colors = ['#00C896' if v > 0 else '#FF4D4F' for v in demo_flow]
            fig.add_trace(go.Bar(
                x=demo_dates,
                y=demo_flow,
                name='净流入(亿)',
                marker_color=colors,
            ))
            fig.update_layout(
                title='北向资金日度净流入 (近30日 · 演示数据)',
                yaxis_title='金额 (亿元)',
                xaxis_title='日期',
                height=400,
                hovermode='x unified',
                plot_bgcolor='#131938',
                paper_bgcolor='#0A0E27',
                font={'color': '#F0F4FA'},
            )
            st.plotly_chart(fig, use_container_width=True)
            st.caption('💡 实时数据暂不可用，以上为演示数据')
        except Exception as e2:
            logger.warning(f'北向资金演示图表也失败: {e2}')
            st.info('💡 北向资金历史数据不可用')

# ============== 页面：智能选股 ==============
elif page == '🎯 智能选股':
    st.markdown('# 🎯 智能选股')
    st.markdown('**自然语言选股 + 多因子评分 + 个股对比 — 专业级智能选股引擎**')
    st.markdown('---')

    tab1, tab2, tab3 = st.tabs(['💬 自然语言选股', '📊 多因子评分', '⚖️ 个股对比'])

    with tab1:
        st.markdown('### 💬 自然语言选股')
        st.caption('输入自然语言描述, AI 自动解析筛选条件')

        query = st.text_input(
            '输入选股条件',
            placeholder='例如: “低估值高成长消费股” 或 “市盈率小于20且市值大于100亿”',
            key='screener_query'
        )

        if st.button('🔍 开始筛选', type='primary', key='screen_btn') and query:
            with st.spinner('AI 解析筛选条件 + 加载数据...'):
                try:
                    # 获取 LLM 配置（如果可用）
                    llm_config = {}
                    if 'llm_config' in st.session_state:
                        llm_config = st.session_state.llm_config
                    screener = NaturalLanguageScreener(cache_manager=st.session_state.get('data_cache_mgr'), llm_config=llm_config)
                    # 加载股票池
                    pool = load_stock_pool()
                    if pool is None or pool.empty:
                        st.error('股票池数据加载失败')
                    else:
                        # V3.14: 直接传 universe 参数, 避免cache注入失败
                        results = screener.screen(query, top_n=20, universe=pool)
                        if results and results.get('results') is not None and len(results['results']) > 0:
                            st.success(f'✅ 筛选完成, 找到 {results["total_matched"]} 只符合条件的股票, 展示 Top {len(results["results"])}')
                            # 显示解析出的筛选条件
                            filters = results.get('filters', {})
                            if filters:
                                filter_tags = []
                                for k, v in filters.items():
                                    if k == 'keywords':
                                        filter_tags.append(f"行业: {', '.join(v)}")
                                    elif k == 'pe_max':
                                        filter_tags.append(f"PE ≤ {v}")
                                    elif k == 'pe_min':
                                        filter_tags.append(f"PE ≥ {v}")
                                    elif k == 'roe_min':
                                        filter_tags.append(f"ROE ≥ {v}%")
                                    elif k == 'price_min':
                                        filter_tags.append(f"价格 ≥ {v}")
                                    elif k == 'price_max':
                                        filter_tags.append(f"价格 ≤ {v}")
                                    elif k == 'market_cap_min':
                                        filter_tags.append(f"市值 ≥ {v}亿")
                                    elif k == 'market_cap_max':
                                        filter_tags.append(f"市值 ≤ {v}亿")
                                    elif k == 'pct_change_min':
                                        filter_tags.append(f"涨幅 ≥ {v}%")
                                    elif k == 'pct_change_max':
                                        filter_tags.append(f"涨幅 ≤ {v}%")
                                    elif k == 'revenue_growth_min':
                                        filter_tags.append(f"营收增长 ≥ {v}%")
                                if filter_tags:
                                    st.markdown('**🧠 解析条件**: ' + ' | '.join(filter_tags))
                            # 展示结果表格
                            result_df = results['results'].copy()
                            display_cols = [c for c in ['代码', '名称', '最新价', '涨跌幅', '换手率', '市盈率-动态', '市净率', '总市值'] if c in result_df.columns]
                            if display_cols:
                                st.dataframe(result_df[display_cols], use_container_width=True, hide_index=True)
                            else:
                                st.dataframe(result_df, use_container_width=True, hide_index=True)
                            # 显示摘要
                            if results.get('summary'):
                                st.markdown(results['summary'])
                        else:
                            st.warning('未找到符合条件的股票, 请调整筛选条件')
                            if results and results.get('summary'):
                                st.markdown(results['summary'])
                except Exception as e:
                    st.error(f'筛选失败: {e}')

    with tab2:
        st.markdown('### 📊 多因子评分')
        st.caption('价值 25% + 成长 25% + 质量 25% + 动量 25%')

        scorer = MultiFactorScorer()
        pool = load_stock_pool()
        if pool is not None and not pool.empty:
            if st.button('📊 计算评分', key='score_btn'):
                with st.spinner('计算多因子评分...'):
                    try:
                        scored = scorer.score_universe(pool)
                        if scored is not None and not scored.empty:
                            st.dataframe(scored.head(20), use_container_width=True)
                    except Exception as e:
                        st.error(f'评分失败: {e}')
        else:
            st.info('股票池数据加载中...')

    with tab3:
        st.markdown('### ⚖️ 个股对比')
        st.caption('最多 5 只股票横向对比')

        col1, col2, col3 = st.columns(3)
        with col1:
            s1 = st.text_input('股票 1', value='贵州茅台', key='cmp1')
            s2 = st.text_input('股票 2', value='五粮液', key='cmp2')
        with col2:
            s3 = st.text_input('股票 3', value='泸州老窖', key='cmp3')
            s4 = st.text_input('股票 4', value='', key='cmp4')
        with col3:
            s5 = st.text_input('股票 5', value='', key='cmp5')

        stocks = [s for s in [s1, s2, s3, s4, s5] if s.strip()]
        if st.button('⚖️ 开始对比', key='compare_btn') and stocks:
            # Use DataCacheManager to provide stock data
            try:
                cache_mgr = st.session_state.get('data_cache_mgr')
                if cache_mgr is None:
                    try:
                        cache_mgr = DataCacheManager(EastMoneyChoiceSource())
                        st.session_state.data_cache_mgr = cache_mgr
                    except Exception:
                        cache_mgr = None
                comparator = StockComparator(cache_manager=cache_mgr)
            except Exception:
                comparator = StockComparator()
            try:
                result = comparator.compare(stocks)
                if result and result.get('comparison_df') is not None and len(result['comparison_df']) > 0:
                    st.dataframe(result['comparison_df'], use_container_width=True, hide_index=True)
                    # 雷达图
                    radar_data = result.get('radar_data', {})
                    if radar_data and radar_data.get('dimensions') and radar_data.get('values'):
                        fig_radar = go.Figure()
                        for code, vals in radar_data['values'].items():
                            fig_radar.add_trace(go.Scatterpolar(
                                r=vals + [vals[0]] if vals else [],
                                theta=radar_data['dimensions'] + [radar_data['dimensions'][0]] if radar_data['dimensions'] else [],
                                fill='toself',
                                name=str(code),
                                opacity=0.6,
                            ))
                        fig_radar.update_layout(
                            polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
                            showlegend=True,
                            title='多维度雷达图',
                            height=400,
                        )
                        st.plotly_chart(fig_radar, use_container_width=True)
                    if result.get('summary'):
                        st.markdown(result['summary'])
                else:
                    st.warning('⚠️ 未找到相关股票数据，请检查输入的代码或名称')
            except Exception as e:
                st.error(f'对比失败: {e}')

# ============== 页面：个股分析 ==============
elif page == '🔍 个股分析':
    st.markdown('# 🔍 个股分析')
    st.markdown('**个股基本面 · SHAP解释 · AI问答 · 报告生成 — 一站式个股深度分析**')
    st.markdown('---')

    # 股票代码/名称输入
    # 热门股票按钮点击后, 通过 _hot_stock_code 传递选中代码
    # 必须先 pop 再设置 text_input 的 key, 否则 Streamlit 会忽略 value 参数
    hot_stock_clicked = st.session_state.pop('_hot_stock_code', '')
    # 如果有热门股票点击, 直接更新 text_input 的 session_state key
    if hot_stock_clicked:
        st.session_state['individual_stock_input'] = hot_stock_clicked

    stock_input = st.text_input(
        '🔎 输入股票代码或名称',
        value=hot_stock_clicked,
        placeholder='例如: 600519 或 贵州茅台',
        key='individual_stock_input'
    )

    # 解析股票代码
    stock_code = ''
    stock_name = ''
    if stock_input.strip():
        # 尝试从A股实时行情中匹配
        try:
            df_spot = safe_get_spot_df()
            if df_spot is not None and len(df_spot) > 0:
                code_col = [c for c in df_spot.columns if '代码' in c]
                name_col = [c for c in df_spot.columns if '名称' in c]
                if code_col and name_col:
                    # 先按代码精确匹配
                    mask = df_spot[code_col[0]].astype(str).str.strip() == stock_input.strip()
                    if mask.any():
                        stock_code = df_spot.loc[mask, code_col[0]].iloc[0]
                        stock_name = df_spot.loc[mask, name_col[0]].iloc[0]
                    else:
                        # 按名称模糊匹配
                        mask = df_spot[name_col[0]].astype(str).str.contains(stock_input.strip(), na=False)
                        if mask.any():
                            stock_code = df_spot.loc[mask, code_col[0]].iloc[0]
                            stock_name = df_spot.loc[mask, name_col[0]].iloc[0]
        except Exception:
            pass

        # 如果无法从实时行情获取，直接使用输入值
        if not stock_code:
            # 判断输入是代码还是名称
            if stock_input.strip().isdigit():
                stock_code = stock_input.strip()
                stock_name = stock_input.strip()
            else:
                stock_code = ''
                stock_name = stock_input.strip()

    if stock_code:
        st.markdown(f'### 📊 {stock_name} ({stock_code}) 深度分析')

        tab_fundamental, tab_shap, tab_ai, tab_report = st.tabs([
            '📋 基本面', '🧠 SHAP解释', '🤖 AI问答', '📄 报告生成'
        ])

        # ========== Tab 1: 基本面 ==========
        with tab_fundamental:
            st.markdown('#### 📋 基本面指标')
            st.caption('数据源: 东方财富 (akshare)')

            # 获取个股信息
            info_dict = {}
            realtime_data = {}
            hist_data = None

            # 1. 个股基本信息
            info_dict = safe_get_stock_info(stock_code)

            # 2. 实时行情数据
            try:
                df_spot = safe_get_spot_df()
                if df_spot is not None and len(df_spot) > 0:
                    code_col = [c for c in df_spot.columns if '代码' in c]
                    if code_col:
                        mask = df_spot[code_col[0]].astype(str).str.strip() == str(stock_code).strip()
                        if mask.any():
                            row = df_spot[mask].iloc[0]
                            for col in df_spot.columns:
                                realtime_data[col] = row[col]
            except Exception as e:
                logger.warning(f'实时行情加载失败: {e}')

            # 3. 历史K线数据: SQLite → 东方财富直连 → akshare
            try:
                # 3a. Try SQLite first
                if HAS_SQLITE_DB:
                    hist_data = _qi_db.get_stock_history(stock_code, days=365)
                    if hist_data is not None and len(hist_data) > 0:
                        # Rename columns to Chinese
                        col_rename = {'date': '日期', 'open': '开盘', 'close': '收盘',
                                      'high': '最高', 'low': '最低', 'volume': '成交量',
                                      'amount': '成交额', 'pct_change': '涨跌幅', 'turnover': '换手率'}
                        hist_data = hist_data.rename(columns={k: v for k, v in col_rename.items() if k in hist_data.columns})
                        if '日期' in hist_data.columns:
                            hist_data['日期'] = pd.to_datetime(hist_data['日期'])

                # 3b. Try 东方财富直连
                if hist_data is None or len(hist_data) == 0:
                    try:
                        from features.eastmoney_direct import fetch_stock_history
                        end_date = datetime.now().strftime('%Y%m%d')
                        start_date_hist = (datetime.now() - timedelta(days=365)).strftime('%Y%m%d')
                        hist_data = fetch_stock_history(stock_code, start_date_hist, end_date)
                        if hist_data is not None and len(hist_data) > 0:
                            # Write to SQLite cache
                            if HAS_SQLITE_DB:
                                try:
                                    _qi_db.upsert_stock_history(stock_code, hist_data)
                                except Exception:
                                    pass
                    except Exception as e:
                        logger.warning(f'东方财富直连历史K线失败: {e}')

                # 3c. Try Baostock (服务器环境可用)
                if hist_data is None or len(hist_data) == 0:
                    try:
                        from features.eastmoney_direct import baostock_fetch_history
                        hist_data = baostock_fetch_history(stock_code, days=365)
                        if hist_data is not None and len(hist_data) > 0:
                            # Write to SQLite cache
                            if HAS_SQLITE_DB:
                                try:
                                    _qi_db.upsert_stock_history(stock_code, hist_data)
                                except Exception:
                                    pass
                    except Exception as e:
                        logger.warning(f'Baostock 历史K线失败: {e}')

                # 3d. Try akshare
                if hist_data is None or len(hist_data) == 0:
                    end_date = datetime.now().strftime('%Y%m%d')
                    start_date_hist = (datetime.now() - timedelta(days=365)).strftime('%Y%m%d')
                    hist_data = safe_akshare_call(ak.stock_zh_a_hist, symbol=stock_code, period='daily',
                                                    start_date=start_date_hist, end_date=end_date,
                                                    adjust='qfq')
                    if hist_data is not None and len(hist_data) > 0:
                        hist_data['日期'] = pd.to_datetime(hist_data['日期'])
                        # Write to SQLite cache
                        if HAS_SQLITE_DB:
                            try:
                                _qi_db.upsert_stock_history(stock_code, hist_data)
                            except Exception:
                                pass
            except Exception as e:
                logger.warning(f'历史K线加载失败: {e}')

            # 显示基本信息卡片
            if info_dict:
                # 提取关键指标
                key_metrics = {}
                metric_mapping = {
                    '总市值': '总市值', '流通市值': '流通市值',
                    '市盈率-动态': 'PE(动态)', '市净率': 'PB',
                    '市销率': 'PS', '股息率': '股息率',
                    '总股本': '总股本', '流通股': '流通股',
                    '行业': '行业', '上市时间': '上市时间',
                }
                for k, v in metric_mapping.items():
                    if k in info_dict:
                        key_metrics[v] = info_dict[k]

                if key_metrics:
                    st.markdown('##### 📊 核心指标')
                    cols = st.columns(min(len(key_metrics), 5))
                    for i, (k, v) in enumerate(list(key_metrics.items())[:5]):
                        with cols[i]:
                            safe_metric(k, v)
                    if len(key_metrics) > 5:
                        cols2 = st.columns(min(len(key_metrics) - 5, 5))
                        for i, (k, v) in enumerate(list(key_metrics.items())[5:10]):
                            with cols2[i]:
                                safe_metric(k, v)

                # 完整信息表
                with st.expander('📋 查看完整信息'):
                    st.dataframe(pd.DataFrame(list(info_dict.items()), columns=['指标', '值']),
                                 use_container_width=True, hide_index=True)
            else:
                # 使用实时行情数据作为 fallback
                if realtime_data:
                    st.markdown('##### 📊 实时行情')
                    price_cols = ['最新价', '涨跌幅', '涨跌额', '成交量', '成交额', '换手率',
                                  '市盈率-动态', '市净率', '总市值', '流通市值']
                    available = {k: realtime_data.get(k, 'N/A') for k in price_cols if k in realtime_data}
                    if available:
                        cols = st.columns(min(len(available), 5))
                        for i, (k, v) in enumerate(list(available.items())[:5]):
                            with cols[i]:
                                safe_metric(k, v)
                        if len(available) > 5:
                            cols2 = st.columns(min(len(available) - 5, 5))
                            for i, (k, v) in enumerate(list(available.items())[5:10]):
                                with cols2[i]:
                                    safe_metric(k, v)
                else:
                    st.warning('基本面数据加载失败，请检查股票代码是否正确')
                    # Demo 数据
                    st.markdown('##### 📊 演示数据 (贵州茅台)')
                    demo_metrics = {'PE(动态)': '25.3', 'PB': '8.9', '总市值': '21,350亿',
                                    '行业': '白酒', '股息率': '1.8%'}
                    cols = st.columns(5)
                    for i, (k, v) in enumerate(demo_metrics.items()):
                        with cols[i]:
                            safe_metric(k, v)

            # K线图
            if hist_data is not None and len(hist_data) > 0:
                st.markdown('##### 📈 近1年K线走势')
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=hist_data['日期'], y=hist_data['收盘'],
                    mode='lines', name='收盘价',
                    line=dict(color='#00D4FF', width=2)
                ))
                # 成交量柱状图 (副图)
                fig_vol = go.Figure()
                colors = ['#00C896' if c >= o else '#FF4D4F'
                          for c, o in zip(hist_data['收盘'], hist_data['开盘'])]
                fig_vol.add_trace(go.Bar(
                    x=hist_data['日期'], y=hist_data['成交量'],
                    name='成交量', marker_color=colors, opacity=0.7
                ))
                fig.update_layout(
                    title=f'{stock_name} 收盘价走势', height=400,
                    hovermode='x unified', template='plotly_dark',
                    yaxis_title='价格'
                )
                fig_vol.update_layout(
                    title=f'{stock_name} 成交量', height=250,
                    hovermode='x unified', template='plotly_dark',
                    yaxis_title='成交量'
                )
                st.plotly_chart(fig, use_container_width=True)
                st.plotly_chart(fig_vol, use_container_width=True)

            # 财务指标 (尝试获取)
            st.markdown('##### 💰 财务指标')
            fin_data = None
            try:
                df_fin = ak.stock_financial_abstract_ths(symbol=stock_code)
                if df_fin is not None and len(df_fin) > 0:
                    fin_data = df_fin
            except Exception:
                pass

            if fin_data is not None and len(fin_data) > 0:
                display_cols = [c for c in fin_data.columns if c in ['报告期', '营业总收入', '净利润', '毛利率', '净利率', '净资产收益率', '总资产收益率']]
                if display_cols:
                    st.dataframe(fin_data[display_cols].head(8), use_container_width=True, hide_index=True)
                else:
                    st.dataframe(fin_data.head(8), use_container_width=True, hide_index=True)
            else:
                st.info('💡 财务数据暂不可用，以下为演示数据')
                demo_fin = pd.DataFrame({
                    '报告期': ['2025Q1', '2024Q4', '2024Q3', '2024Q2'],
                    '营业总收入': ['485亿', '1,741亿', '1,253亿', '834亿'],
                    '净利润': ['242亿', '862亿', '608亿', '416亿'],
                    '毛利率': ['91.8%', '91.5%', '91.3%', '91.2%'],
                    '净利率': ['49.9%', '49.5%', '48.5%', '49.9%'],
                    'ROE': ['9.8%', '35.2%', '24.8%', '17.0%'],
                })
                st.dataframe(demo_fin, use_container_width=True, hide_index=True)

        # ========== Tab 2: SHAP解释 ==========
        with tab_shap:
            st.markdown('#### 🧠 SHAP 可解释性分析')
            st.caption('AI选股模型对该股的因子贡献度解释')

            try:
                from features.shap_explainer import render_shap_dashboard
                render_shap_dashboard()
            except ImportError as e:
                st.error(f'❌ SHAP模块加载失败: {e}')
                st.info('请安装: pip install xgboost shap')
            except Exception as e:
                st.error(f'❌ SHAP运行错误: {type(e).__name__}: {str(e)[:300]}')

        # ========== Tab 3: AI问答 ==========
        with tab_ai:
            st.markdown('#### 🤖 AI 投研问答')
            st.caption(f'针对 {stock_name} 的智能分析')

            # 预填问题
            default_q = f'分析{stock_name}的投资价值' if stock_name else '请先输入股票代码'
            ai_question = st.text_area(
                '💬 输入关于该股票的问题',
                value=default_q,
                height=80,
                key='individual_ai_question'
            )

            if st.button('🚀 AI 分析', type='primary', key='individual_ai_btn') and ai_question:
                llm_config = get_llm_config()
                use_real_llm = llm_config['api_key'] is not None

                with st.spinner('🤖 AI 正在分析...'):
                    # Build context from SQLite/akshare data
                    stock_context = ""
                    if HAS_SQLITE_DB:
                        try:
                            profile = _qi_db.get_stock_profile(stock_code)
                            if profile:
                                stock_context += f"\n个股基本信息: {json.dumps(profile, ensure_ascii=False)}"
                        except Exception:
                            pass
                        try:
                            history_df = _qi_db.get_stock_history(stock_code, days=90)
                            if history_df is not None and len(history_df) > 0:
                                latest = history_df.iloc[-1]
                                stock_context += f"\n最新行情: 收盘价{latest.get('close','N/A')}, 涨跌幅{latest.get('pct_change', latest.get('change_pct','N/A'))}%"
                        except Exception:
                            pass
                    # Also get spot data for this stock
                    try:
                        spot_df = safe_get_spot_df()
                        if spot_df is not None and len(spot_df) > 0:
                            code_col = [c for c in spot_df.columns if '代码' in c]
                            if code_col:
                                stock_row = spot_df[spot_df[code_col[0]].astype(str).str.strip() == str(stock_code).strip()]
                                if len(stock_row) > 0:
                                    row = stock_row.iloc[0]
                                    stock_context += f"\n实时行情: 最新价{row.get('最新价','N/A')}, 涨跌幅{row.get('涨跌幅','N/A')}%, 市盈率{row.get('市盈率-动态','N/A')}, 市净率{row.get('市净率','N/A')}, 总市值{row.get('总市值','N/A')}"
                    except Exception:
                        pass

                    # Enrich question with context
                    enriched_question = ai_question
                    if stock_context:
                        enriched_question = f"以下是{stock_name}({stock_code})的实时数据，请基于这些数据分析：{stock_context}\n\n用户问题：{ai_question}"

                    if use_real_llm:
                        try:
                            result = ai_qa_real(enriched_question, llm_config)
                            st.markdown(f'## 📄 {result["title"]}')
                            st.markdown('### 📋 分析摘要')
                            st.markdown(result['summary'])
                            if result.get('data'):
                                st.markdown('### 📊 关键数据')
                                cols = st.columns(len(result['data']))
                                for (k, v), col in zip(result['data'].items(), cols):
                                    with col:
                                        safe_metric(k, v)
                            st.markdown('### 💡 投资建议')
                            st.success(result['recommendation'])
                            if result.get('reasoning'):
                                with st.expander('🧠 AI 思考过程'):
                                    st.caption(result['reasoning'])
                        except Exception as e:
                            st.warning(f'⚠️ LLM调用失败: {e}, 使用Mock数据')
                            result = ai_qa_mock(enriched_question)
                            st.markdown(f'## 📄 {result["title"]}')
                            st.markdown(result['summary'])
                            st.success(result['recommendation'])
                    else:
                        result = ai_qa_mock(enriched_question)
                        st.markdown(f'## 📄 {result["title"]}')
                        st.markdown(result['summary'])
                        st.success(result['recommendation'])

            st.caption('⚠️ AI分析仅供参考，不构成投资建议')

        # ========== Tab 4: 报告生成 ==========
        with tab_report:
            st.markdown('#### 📄 报告生成')
            st.caption(f'为 {stock_name} 生成深度投研报告')

            try:
                from features.report_generator import render_report_ui
                # 预设股票代码到 session state
                if 'selected_report_type' not in st.session_state:
                    st.session_state.selected_report_type = 'stock'
                render_report_ui()
            except ImportError as e:
                st.error(f'❌ 报告模块加载失败: {e}')
                st.info('请安装: pip install python-docx reportlab')
            except Exception as e:
                st.error(f'❌ 报告生成失败: {type(e).__name__}: {str(e)[:300]}')

    else:
        # 未输入股票代码时显示引导
        st.markdown("""
        <div style="text-align:center; padding:60px 20px; color:#8A92B0;">
            <p style="font-size:64px;">🔍</p>
            <h3 style="color:#FFFFFF;">输入股票代码或名称开始分析</h3>
            <p>支持代码 (如 600519) 或名称 (如 贵州茅台)</p>
        </div>
        """, unsafe_allow_html=True)

        # 热门股票快捷入口
        st.markdown('### 🔥 热门股票')
        hot_stocks = [
            ('600519', '贵州茅台'), ('000858', '五粮液'), ('601318', '中国平安'),
            ('600036', '招商银行'), ('000333', '美的集团'), ('002594', '比亚迪'),
            ('300750', '宁德时代'), ('600276', '恒瑞医药'), ('601888', '中国中免'),
        ]
        cols = st.columns(3)
        for i, (code, name) in enumerate(hot_stocks):
            with cols[i % 3]:
                if st.button(f'📌 {name} ({code})', key=f'hot_stock_{code}', width='stretch'):
                    # Can't modify widget key after instantiation, use callback key
                    st.session_state['_hot_stock_code'] = code
                    st.rerun()

# ============== 页面：智能盯盘 ==============
elif page == '📡 智能盯盘':
    st.markdown('# 📡 智能盯盘')
    st.markdown('**7×24h 市场监控 + 智能预警 + 北向资金 — 专业级智能盯盘系统**')
    st.markdown('---')

    # 市场大盘
    if 'data_cache_mgr' not in st.session_state:
        try:
            st.session_state.data_cache_mgr = DataCacheManager(EastMoneyChoiceSource())
        except Exception:
            st.session_state.data_cache_mgr = None
    dashboard = MarketDashboard(cache_manager=st.session_state.data_cache_mgr)
    try:
        overview = dashboard.get_market_overview()
        breadth = overview.get('breadth', {})
        if breadth:
            col1, col2, col3, col4, col5 = st.columns(5)
            with col1:
                safe_metric('上涨家数', breadth.get('up', 'N/A'))
            with col2:
                safe_metric('下跌家数', breadth.get('down', 'N/A'))
            with col3:
                safe_metric('平盘', breadth.get('flat', 'N/A'))
            with col4:
                safe_metric('涨停', breadth.get('limit_up', 'N/A'))
            with col5:
                safe_metric('跌停', breadth.get('limit_down', 'N/A'))
        else:
            # 用示例数据兜底，避免一直loading
            from features.robust_utils import get_sample_stocks
            samples = get_sample_stocks()[:10]
            up = sum(1 for s in samples if s.get('change_pct', 0) > 0)
            down = len(samples) - up
            limit_up = sum(1 for s in samples if s.get('change_pct', 0) >= 9.9)
            st.info(f"💡 实时数据加载中，已显示示例数据（基于10只演示股票）")
            col1, col2, col3, col4, col5 = st.columns(5)
            with col1: safe_metric('上涨家数', up)
            with col2: safe_metric('下跌家数', down)
            with col3: safe_metric('平盘', 0)
            with col4: safe_metric('涨停', limit_up)
            with col5: safe_metric('跌停', 0)
            if st.button('🔄 重新加载', key='reload_overview'):
                st.rerun()
        # 北向资金快览
        ff = overview.get('fund_flow', {})
        if 'northbound' in ff:
            flow = ff['northbound']
            direction = '净流入' if flow > 0 else '净流出'
            st.info(f'🌐 北向资金: {direction} **{abs(flow):.1f}亿**')
    except Exception as e:
        logger.warning(f'Market overview error: {e}')
        st.info('市场概览数据暂时不可用，请稍后刷新重试')

    st.markdown('---')

    # 预警系统
    st.markdown('### ⚠️ 智能预警')
    st.caption('支持自然语言创建预警: "贵州茅台涨到1800元提醒"')

    if 'alert_engine' not in st.session_state:
        st.session_state.alert_engine = SmartAlertEngine()
    alert_engine = st.session_state.alert_engine

    alert_input = st.text_input(
        '创建新预警',
        placeholder='例如: "贵州茅台跌破1600元提醒" 或 "比亚迪涨幅超过5%提醒"',
        key='alert_input'
    )
    if st.button('➕ 添加预警', key='add_alert') and alert_input:
        try:
            alert = alert_engine.parse_nl_alert(alert_input)
            st.success(f'✅ 预警已创建: {alert.message}')
        except Exception as e:
            st.error(f'创建失败: {e}')

    # 显示现有预警
    alerts = alert_engine.get_active_alerts()
    if alerts:
        st.markdown('#### 📝 当前预警列表')
        for a in alerts:
            triggered = '🔴' if a.is_triggered else '🟢'
            st.markdown(f'- {triggered} {a.message}')

    # 北向资金
    st.markdown('---')
    st.markdown('### 🌐 北向资金追踪')
    north_loaded = False
    try:
        df_north = None
        # Try SQLite first
        if HAS_SQLITE_DB:
            try:
                df_north = _qi_db.get_northbound_flow(days=30)
            except Exception as e:
                logger.warning(f'北向资金 SQLite 读取失败: {e}')
        # Try 东方财富直连
        if df_north is None or len(df_north) == 0:
            try:
                from features.eastmoney_direct import fetch_northbound_flow
                df_north = fetch_northbound_flow(days=30)
                if df_north is not None and len(df_north) > 0 and HAS_SQLITE_DB:
                    try:
                        _qi_db.upsert_northbound_flow(df_north)
                    except Exception:
                        pass
            except Exception as e:
                logger.warning(f'北向资金东方财富直连失败: {e}')
        # Fallback to akshare
        if df_north is None or len(df_north) == 0:
            try:
                df_north = ak.stock_hsgt_north_net_flow_in_em(symbol='北向')
            except Exception as e:
                logger.warning(f'北向资金 akshare 主接口失败: {e}')
        if df_north is not None and len(df_north) > 0:
            north_loaded = True
            # 提取最新一天数据
            latest = df_north.iloc[-1]
            net_col = None
            for c in ['当日净流入', '当日资金流入']:
                if c in df_north.columns:
                    net_col = c
                    break
            if net_col is None:
                net_col = df_north.columns[-1]
            net_val = pd.to_numeric(latest[net_col], errors='coerce')
            if pd.notna(net_val):
                direction = '净流入' if net_val >= 0 else '净流出'
                abs_yi = abs(net_val) / 1e8
                col_nb1, col_nb2, col_nb3 = st.columns(3)
                with col_nb1:
                    st.metric('今日北向资金', f'{direction}', f'{abs_yi:.2f} 亿')
                with col_nb2:
                    # 近5日累计
                    recent5 = df_north.tail(5)[net_col].astype(float)
                    sum5 = recent5.sum() / 1e8
                    st.metric('近5日累计', f'{sum5:+.2f} 亿')
                with col_nb3:
                    # 近20日累计
                    recent20 = df_north.tail(20)[net_col].astype(float)
                    sum20 = recent20.sum() / 1e8
                    st.metric('近20日累计', f'{sum20:+.2f} 亿')
            # 显示近期明细
            st.dataframe(df_north.tail(10), use_container_width=True, hide_index=True)
        else:
            north_loaded = False
    except Exception as e:
        logger.warning(f'北向资金数据加载异常: {e}')
        north_loaded = False

    if not north_loaded:
        # 回退到演示数据
        st.info('🌐 北向资金实时数据暂不可用，以下为演示数据')
        demo_net = 38.52  # 亿
        demo_5d = 156.30
        demo_20d = 425.80
        col_nb1, col_nb2, col_nb3 = st.columns(3)
        with col_nb1:
            st.metric('今日北向资金', '净流入', f'{demo_net:.2f} 亿')
        with col_nb2:
            st.metric('近5日累计', f'{demo_5d:+.2f} 亿')
        with col_nb3:
            st.metric('近20日累计', f'{demo_20d:+.2f} 亿')

# ============== 页面：我的组合 ==============
elif page == '💼 我的组合':
    st.markdown('# 💼 我的组合')
    st.markdown('**组合管理 + 实时盈亏 + 风险指标**')
    st.markdown('---')

    if 'portfolio_mgr' not in st.session_state:
        st.session_state.portfolio_mgr = PortfolioManager()
    mgr = st.session_state.portfolio_mgr

    tab1, tab2 = st.tabs(['📥 添加持仓', '📊 组合概览'])

    with tab1:
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            h_symbol = st.text_input('股票代码', value='600519', key='h_symbol')
        with col2:
            h_name = st.text_input('股票名称', value='贵州茅台', key='h_name')
        with col3:
            h_shares = st.number_input('持股数', value=100, step=100, key='h_shares')
        with col4:
            h_cost = st.number_input('成本价', value=1680.0, step=0.01, key='h_cost')

        if st.button('➕ 添加持仓', key='add_holding'):
            try:
                mgr.add_holding('我的组合', h_symbol, h_name, int(h_shares), float(h_cost))
                st.success(f'✅ 已添加 {h_name} ({h_symbol})')
            except Exception as e:
                st.error(f'添加失败: {e}')

    with tab2:
        # 确保组合存在
        if '我的组合' not in mgr.list_portfolios():
            mgr.create_portfolio('我的组合')
        portfolio = mgr.get_portfolio('我的组合')
        if portfolio and portfolio.holdings:
            st.markdown(f'### 📊 持仓明细 (共 {len(portfolio.holdings)} 只)')
            holdings_data = [{'股票代码': h.stock_code, '股票名称': h.stock_name,
                              '持股数': h.quantity, '成本价': h.avg_cost,
                              '现价': h.current_price, '盈亏': h.pnl} for h in portfolio.holdings]
            st.dataframe(pd.DataFrame(holdings_data), use_container_width=True)
            col_m1, col_m2 = st.columns(2)
            with col_m1:
                st.metric('总市值', f"¥{portfolio.total_market_value:,.0f}")
            with col_m2:
                st.metric('总盈亏', f"¥{portfolio.total_pnl:,.0f}", f"{portfolio.total_pnl_pct:+.2f}%")
        else:
            st.info('📭 暂无持仓, 请先添加持仓')

# ============== 页面：模拟交易 ==============
elif page == '📈 模拟交易':
    st.markdown('# 📈 模拟交易')
    st.markdown('**语音/文字下单 + 风控引擎 + 反情绪化交易 — 专业级智能交易系统**')
    st.markdown('---')

    if 'trade_sim' not in st.session_state:
        st.session_state.trade_sim = TradeSimulator()
    if 'risk_engine' not in st.session_state:
        st.session_state.risk_engine = RiskControlEngine()

    sim = st.session_state.trade_sim
    risk = st.session_state.risk_engine

    st.markdown('### 📝 下单')
    st.caption('支持自然语言: “买入100股贵州茅台” 或 表单下单')

    nl_order = st.text_input(
        '自然语言下单',
        placeholder='例如: “买入100股贵州茅台” 或 “卖出全部五粮液”',
        key='nl_order'
    )

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        o_symbol = st.text_input('股票代码', value='600519', key='o_symbol')
    with col2:
        o_action = st.selectbox('方向', ['buy', 'sell'], key='o_action')
    with col3:
        o_qty = st.number_input('数量 (股)', value=100, step=100, key='o_qty')
    with col4:
        o_price = st.number_input('价格 (0=市价)', value=0.0, step=0.01, key='o_price')

    if st.button('🚀 执行交易', type='primary', key='exec_trade'):
        try:
            # 市价单：获取最新成交价
            exec_price = float(o_price) if o_price > 0 else 0.0
            order_type = 'limit' if exec_price > 0 else 'market'
            if order_type == 'market':
                # V3.13: 单次调用 (get_current_price 内部已有 SQLite 快速路径)
                with st.spinner('正在获取市价...'):
                    try:
                        exec_price = get_current_price(o_symbol)
                    except Exception as e:
                        logger.warning(f'获取市价失败: {e}')
                        exec_price = 0.0

                if exec_price <= 0:
                    # 使用示例价格回退，避免阻塞交易
                    from features.robust_utils import get_sample_stocks
                    sample = next((s for s in get_sample_stocks() if s['code'] == o_symbol), None)
                    if sample:
                        exec_price = sample['price']
                        st.warning(f"⚠️ 实时接口暂不可用，已使用参考价 ¥{exec_price:.2f}（{sample['name']}）")
                        order_type = 'limit_demo'
                    else:
                        # 让用户输入价格
                        st.error('❌ 无法获取该股票最新价，请改用限价单手动输入价格')
                        manual_price = st.number_input('请手动输入价格', value=10.0, step=0.01, key='manual_price')
                        if st.button('确认以该价格下单', key='confirm_manual'):
                            exec_price = manual_price
                            order_type = 'limit'
                        else:
                            st.stop()

            # 构建 Order 对象
            o_order = Order(
                order_id=f"ORD_{int(datetime.now().timestamp())}",
                stock_code=o_symbol, stock_name='', side=o_action,
                quantity=int(o_qty), price=exec_price,
                order_type=order_type,
                created_at=datetime.now().isoformat(),
            )
            # 风控检查
            _pv = 1000000.0
            if 'portfolio_mgr' in st.session_state:
                try:
                    _port = st.session_state.portfolio_mgr.get_portfolio('我的组合')
                    if _port and _port.total_market_value > 0:
                        _pv = _port.total_market_value
                except Exception:
                    pass
            risk_check = risk.check_order(o_order, portfolio_value=_pv)
            if not risk_check.get('passed', False):
                st.error(f'❌ 风控拒绝: {risk_check.get("message", "未知")}')
            else:
                result = sim.place_order(o_symbol, '', o_action, int(o_qty), exec_price, risk_checker=risk)
                if result and result.status == 'filled':
                    st.success(f"✅ 成交: {result.stock_code} {result.side} {result.quantity}股 @ ¥{result.fill_price:.2f}")
                elif result and result.status == 'rejected':
                    st.warning(f'交易被拒绝: {result.risk_check_message}')
                else:
                    st.warning('交易未成交')
        except Exception as e:
            st.error(f'交易失败: {e}')

    # 交易历史
    st.markdown('---')
    st.markdown('### 📝 交易历史')
    history = sim.get_trade_history()
    if history:
        hist_data = [{'订单号': o.order_id, '代码': o.stock_code, '方向': o.side,
                      '数量': o.quantity,
                      '成交价': f"{o.fill_price:.2f}" if o.fill_price > 0 else ('待成交' if o.status == 'pending' else f"{o.price:.2f}"),
                      '状态': o.status,
                      '时间': o.created_at} for o in history]
        st.dataframe(pd.DataFrame(hist_data), use_container_width=True)
    else:
        st.info('暂无交易记录')

    # 风控状态
    st.markdown('---')
    st.markdown('### 🛡️ 风控状态')
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric('今日交易次数', len([o for o in sim.get_trade_history() if o.created_at and o.created_at[:10] == datetime.now().strftime('%Y-%m-%d')]))
    with col2:
        pnl = sim.get_pnl_summary()
        st.metric('总成交', pnl.get('filled_orders', 0))
    with col3:
        st.metric('交易成本', f"¥{pnl.get('total_commission', 0):.2f}")

# ============== 页面：智能指令 ==============
elif page == '⚡ 智能指令':
    st.markdown('# ⚡ 智能指令')
    st.markdown('**周期性投研任务 + 自动报告生成 — 专业级智能指令平台**')
    st.markdown('---')

    # ========== 市场数据预览 ==========
    st.markdown('### 📊 市场数据概览')
    st.caption('实时市场数据快照 — 为智能指令提供数据基础')

    # 指数行情
    idx_col1, idx_col2, idx_col3, idx_col4 = st.columns(4)
    _idx_data = {}
    try:
        df_idx = ak.stock_zh_index_spot_em()
        if df_idx is not None and len(df_idx) > 0:
            name_col = [c for c in df_idx.columns if '名称' in c][0] if any('名称' in c for c in df_idx.columns) else None
            price_col = [c for c in df_idx.columns if '最新价' in c][0] if any('最新价' in c for c in df_idx.columns) else None
            chg_col = [c for c in df_idx.columns if '涨跌幅' in c][0] if any('涨跌幅' in c for c in df_idx.columns) else None
            chgamt_col = [c for c in df_idx.columns if '涨跌额' in c][0] if any('涨跌额' in c for c in df_idx.columns) else None
            if name_col and price_col:
                for idx_name in ['上证指数', '深证成指', '创业板指', '科创50']:
                    row = df_idx[df_idx[name_col] == idx_name]
                    if not row.empty:
                        _idx_data[idx_name] = {
                            'price': float(row[price_col].values[0]) if price_col else 0,
                            'change_pct': float(row[chg_col].values[0]) if chg_col else 0,
                            'change_amt': float(row[chgamt_col].values[0]) if chgamt_col else 0,
                        }
    except Exception:
        pass

    # 演示数据兜底
    if not _idx_data:
        _idx_data = {
            '上证指数': {'price': 3356.72, 'change_pct': 0.35, 'change_amt': 11.68},
            '深证成指': {'price': 10523.45, 'change_pct': -0.12, 'change_amt': -12.65},
            '创业板指': {'price': 2156.89, 'change_pct': -0.58, 'change_amt': -12.57},
            '科创50': {'price': 985.34, 'change_pct': 1.02, 'change_amt': 9.93},
        }

    for i, (idx_name, idx_val) in enumerate(_idx_data.items()):
        with [idx_col1, idx_col2, idx_col3, idx_col4][i]:
            delta_str = f"{idx_val['change_pct']:+.2f}%"
            st.metric(idx_name, f"{idx_val['price']:,.2f}", delta_str)

    st.markdown('---')

    # 北向资金 + 板块涨跌 + 涨跌排行
    data_col1, data_col2 = st.columns(2)

    with data_col1:
        # 北向资金
        try:
            df_north = None
            # Try SQLite first
            if HAS_SQLITE_DB:
                try:
                    df_north = _qi_db.get_northbound_flow(days=10)
                except Exception:
                    pass
            # Fallback to akshare
            if df_north is None or len(df_north) == 0:
                df_north = ak.stock_hsgt_north_net_flow_in_em(symbol='北向')
            if df_north is not None and len(df_north) > 0:
                date_col = [c for c in df_north.columns if '日期' in c or 'date' in c.lower()]
                flow_col = [c for c in df_north.columns if '净流入' in c or '净买' in c]
                if date_col and flow_col:
                    df_north_recent = df_north.tail(10)
                    north_display = df_north_recent[[date_col[0], flow_col[0]]].copy()
                    north_display.columns = ['日期', '净流入(亿元)']
                    north_display['净流入(亿元)'] = pd.to_numeric(north_display['净流入(亿元)'], errors='coerce')
                    st.markdown('#### 🌊 北向资金近10日')
                    st.dataframe(north_display, use_container_width=True, hide_index=True)
                else:
                    st.caption('北向资金列格式变化')
            else:
                raise Exception('no data')
        except Exception:
            st.markdown('#### 🌊 北向资金近10日 (演示)')
            _demo_north_df = pd.DataFrame({
                '日期': pd.date_range(end=pd.Timestamp.today(), periods=10).strftime('%Y-%m-%d'),
                '净流入(亿元)': [32.5, -15.3, 28.7, 45.2, -8.9, 18.6, -22.1, 35.8, 12.4, 25.3]
            })
            st.dataframe(_demo_north_df, use_container_width=True, hide_index=True)

    with data_col2:
        # 板块涨跌
        try:
            df_sector = ak.stock_board_industry_name_em()
            if df_sector is not None and len(df_sector) > 0:
                name_col = [c for c in df_sector.columns if '板块' in c or '名称' in c or '行业' in c]
                chg_col = [c for c in df_sector.columns if '涨跌幅' in c]
                if name_col and chg_col:
                    df_sector_display = df_sector[[name_col[0], chg_col[0]]].head(15).copy()
                    df_sector_display.columns = ['板块', '涨跌幅(%)']
                    df_sector_display['涨跌幅(%)'] = pd.to_numeric(df_sector_display['涨跌幅(%)'], errors='coerce')
                    st.markdown('#### 🏢 行业板块涨跌 TOP15')
                    st.dataframe(df_sector_display, use_container_width=True, hide_index=True)
                else:
                    raise Exception('col mismatch')
            else:
                raise Exception('no data')
        except Exception:
            st.markdown('#### 🏢 行业板块涨跌 TOP15 (演示)')
            _demo_sector_df = pd.DataFrame({
                '板块': ['电子', '计算机', '通信', '传媒', '电力设备', '医药生物', '食品饮料', '银行', '房地产', '钢铁', '煤炭', '军工', '汽车', '家电', '建材'],
                '涨跌幅(%)': [2.35, 1.87, 1.52, 0.98, 0.65, -0.32, -0.58, -0.75, -1.23, -1.45, -0.89, 0.42, 1.15, -0.18, -0.67]
            })
            st.dataframe(_demo_sector_df, use_container_width=True, hide_index=True)

    # 涨幅/跌幅排行
    rank_col1, rank_col2 = st.columns(2)

    with rank_col1:
        st.markdown('#### 🔥 涨幅排行 TOP10')
        try:
            df_spot = safe_get_spot_df()
            if df_spot is not None and len(df_spot) > 0:
                chg_col = [c for c in df_spot.columns if '涨跌幅' in c]
                name_col = [c for c in df_spot.columns if '名称' in c]
                code_col = [c for c in df_spot.columns if '代码' in c]
                price_col = [c for c in df_spot.columns if '最新价' in c]
                if chg_col and name_col:
                    df_spot_sorted = df_spot.copy()
                    df_spot_sorted[chg_col[0]] = pd.to_numeric(df_spot_sorted[chg_col[0]], errors='coerce')
                    df_spot_sorted = df_spot_sorted.dropna(subset=[chg_col[0]])
                    top_gainers = df_spot_sorted.nlargest(10, chg_col[0])
                    display_cols = []
                    if code_col: display_cols.append(code_col[0])
                    if name_col: display_cols.append(name_col[0])
                    if price_col: display_cols.append(price_col[0])
                    display_cols.append(chg_col[0])
                    # Rename for display
                    rename_map = {}
                    if code_col: rename_map[code_col[0]] = '代码'
                    if name_col: rename_map[name_col[0]] = '名称'
                    if price_col: rename_map[price_col[0]] = '最新价'
                    rename_map[chg_col[0]] = '涨跌幅(%)'
                    top_gainers_display = top_gainers[display_cols].rename(columns=rename_map)
                    st.dataframe(top_gainers_display, use_container_width=True, hide_index=True)
                else:
                    raise Exception('col mismatch')
            else:
                raise Exception('no data')
        except Exception:
            _demo_gainers = pd.DataFrame({
                '代码': ['300XXX', '600XXX', '002XXX', '688XXX', '000XXX', '301XXX', '603XXX', '002YYY', '600YYY', '300YYY'],
                '名称': ['中际旭创', '新易盛', '天孚通信', '寒武纪', '工业富联', '光库科技', '中科曙光', '浪潮信息', '紫光股份', '锐捷网络'],
                '最新价': [156.80, 98.50, 82.30, 245.60, 32.15, 68.90, 52.30, 38.70, 28.90, 55.40],
                '涨跌幅(%)': [20.00, 15.32, 12.87, 11.56, 10.02, 9.87, 8.65, 7.43, 6.89, 6.12]
            })
            st.dataframe(_demo_gainers, use_container_width=True, hide_index=True)

    with rank_col2:
        st.markdown('#### 💚 跌幅排行 TOP10')
        try:
            if df_spot is not None and len(df_spot) > 0 and chg_col and name_col:
                top_losers = df_spot_sorted.nsmallest(10, chg_col[0])
                display_cols = []
                if code_col: display_cols.append(code_col[0])
                if name_col: display_cols.append(name_col[0])
                if price_col: display_cols.append(price_col[0])
                display_cols.append(chg_col[0])
                rename_map = {}
                if code_col: rename_map[code_col[0]] = '代码'
                if name_col: rename_map[name_col[0]] = '名称'
                if price_col: rename_map[price_col[0]] = '最新价'
                rename_map[chg_col[0]] = '涨跌幅(%)'
                top_losers_display = top_losers[display_cols].rename(columns=rename_map)
                st.dataframe(top_losers_display, use_container_width=True, hide_index=True)
            else:
                raise Exception('no data')
        except Exception:
            _demo_losers = pd.DataFrame({
                '代码': ['601XXX', '000YYY', '002ZZZ', '600ZZZ', '300ZZZ', '688ZZZ', '603ZZZ', '000AAA', '002BBB', '600BBB'],
                '名称': ['ST中天', 'ST华仪', 'ST博天', 'ST榕泰', 'ST易见', 'ST国医', 'ST宏图', 'ST凯乐', 'ST新海', 'ST大集'],
                '最新价': [1.23, 0.85, 2.15, 1.56, 0.98, 3.45, 1.89, 0.76, 1.12, 2.34],
                '涨跌幅(%)': [-10.00, -9.87, -8.56, -7.43, -6.89, -5.67, -5.12, -4.89, -4.56, -4.23]
            })
            st.dataframe(_demo_losers, use_container_width=True, hide_index=True)

    st.markdown('---')

    if 'task_scheduler' not in st.session_state:
        st.session_state.task_scheduler = ResearchTaskScheduler()
    scheduler = st.session_state.task_scheduler

    tab1, tab2, tab3 = st.tabs(['📥 创建任务', '📝 任务列表', '📊 报告生成'])

    with tab1:
        st.markdown('### 预置任务模板')
        templates = TASK_TEMPLATES
        if templates:
            cols = st.columns(min(len(templates), 3))
            for i, (tid, tpl) in enumerate(templates.items()):
                with cols[i % len(cols)]:
                    st.markdown(f"**{tpl.get('name', tid)}**")
                    st.caption(tpl.get('description', ''))
                    st.caption(f"⏰ {tpl.get('schedule', '')}")
                    if st.button(f'➕ 添加', key=f'tpl_{tid}'):
                        try:
                            scheduler.create_task_from_template(tid)
                            st.success(f'✅ 已添加 {tpl["name"]}')
                        except Exception as e:
                            st.error(f'添加失败: {e}')

        st.markdown('---')
        st.markdown('### 自定义任务')
        c_name = st.text_input('任务名称', key='c_name')
        c_desc = st.text_input('任务描述', key='c_desc')
        c_type = st.selectbox('任务类型', ['morning_brief', 'evening_review', 'weekly_report', 'custom'], key='c_type')
        if st.button('➕ 创建自定义任务', key='add_custom') and c_name:
            try:
                scheduler.create_custom_task(c_name, c_desc, schedule='custom')
                st.success(f'✅ 已创建 {c_name}')
            except Exception as e:
                st.error(f'创建失败: {e}')

    with tab2:
        st.markdown('### 📝 当前任务列表')
        tasks = scheduler.list_tasks()
        if tasks:
            for t in tasks:
                with st.container():
                    col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                    with col1:
                        status_icon = '✅ 活跃' if t.is_active else '⏸️ 暂停'
                        st.markdown(f"**{t.name}** ({t.task_type}) - {status_icon}")
                        if hasattr(t, 'last_run') and t.last_run:
                            st.caption(f"⏱️ 上次执行: {t.last_run}")
                        if hasattr(t, 'next_run') and t.next_run:
                            st.caption(f"⏭️ 下次执行: {t.next_run}")
                        if hasattr(t, 'results') and t.results:
                            st.caption(f"📊 历史结果: {len(t.results)} 条")
                    with col2:
                        if st.button('▶️ 执行', key=f'exec_{t.task_id}'):
                            with st.spinner(f'正在执行 {t.name}...'):
                                try:
                                    # V3.13: 调用 MainAgent 执行任务, 传入 qi_db 和 llm_config
                                    llm_config = {}
                                    if 'llm_config' in st.session_state:
                                        llm_config = st.session_state.llm_config
                                    qi_db = _qi_db if HAS_SQLITE_DB else None
                                    result = scheduler.execute_task(t, cache_manager=None, llm_config=llm_config, qi_db=qi_db)
                                    if result:
                                        st.success(f'✅ 执行完成')
                                        if hasattr(result, 'summary') and result.summary:
                                            st.markdown('**分析摘要:**')
                                            st.markdown(result.summary[:1000])
                                        if hasattr(result, 'data') and isinstance(result.data, dict):
                                            title = result.data.get('title', '')
                                            if title:
                                                st.caption(f'标题: {title}')
                                    else:
                                        st.warning('执行未返回结果')
                                except Exception as e:
                                    st.error(f'执行失败: {e}')
                    with col3:
                        if st.button('⏸️ 暂停' if t.is_active else '▶️ 恢复', key=f'toggle_{t.task_id}'):
                            try:
                                t.is_active = not t.is_active
                                scheduler._save_tasks()
                                st.rerun()
                            except Exception as e:
                                st.error(f'操作失败: {e}')
                    with col4:
                        if st.button('🗑️ 删除', key=f'del_{t.task_id}'):
                            try:
                                scheduler.delete_task(t.task_id)
                                st.success(f'已删除 {t.name}')
                                st.rerun()
                            except Exception as e:
                                st.error(f'删除失败: {e}')
                    st.markdown('---')
        else:
            st.info('暂无任务, 请先创建任务')

    with tab3:
        # ========== 升级版报告生成 (集成akshare+AI 6段式+Word/PDF导出) ==========
        try:
            from features.report_generator import render_report_ui
            render_report_ui()
        except ImportError as e:
            st.error(f"❌ 报告模块加载失败: {e}")
            st.info("请安装: pip install python-docx reportlab")
        except Exception as e:
            st.error(f"❌ 报告生成失败: {type(e).__name__}: {str(e)[:300]}")
            # 降级到原版本
            st.markdown('### 📊 自动报告生成 (降级版)')
            st.caption('基于当前市场数据自动生成投研报告')
            report_type = st.selectbox('报告类型', ['晨报', '盘后总结', '周报'], key='report_type_fallback')
            if st.button('📝 生成报告', key='gen_report_fallback'):
                with st.spinner('生成报告...'):
                    try:
                        generator = AutoReportGenerator()
                        from types import SimpleNamespace
                        now_str = datetime.now().strftime('%Y-%m-%d')
                        mock_result = SimpleNamespace(
                            title=f'{report_type} - {now_str}',
                            summary=f'基于当前市场数据的{report_type}自动分析。',
                            recommendation='建议关注大盘走势及板块轮动信号。',
                            reasoning='基于近期市场成交量、北向资金流向及板块轮动数据综合分析。',
                        )
                        report = generator.generate(report_type, mock_result)
                        st.markdown(report)
                    except Exception as e2:
                        st.error(f'降级版也失败: {e2}')

# ============== 页面：个人中心 ==============
elif page == '👤 个人中心':
    render_profile_page(_session_mgr, _db)

# ============== 页面：管理后台 ==============
elif page == '⚙️ 管理后台':
    if not _is_admin:
        st.error('⛔ 无权访问')
        st.stop()
    from admin.dashboard import render_admin_dashboard
    render_admin_dashboard(_db)

# ============== 页脚 ==============
st.markdown('---')
st.markdown(
    '<p style="text-align: center; color: #999; font-size: 0.85rem;">'
    '© 2026 慧点资本 (InsightQuant) | Fintech@外滩 第一届金融科技国际创新创业大赛<br/>'
    '项目编号：2026FINTECH-FINT-0093 | 数据来源：akshare 公开数据接口'
    '</p>',
    unsafe_allow_html=True
)
