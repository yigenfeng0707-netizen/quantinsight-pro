# -*- coding: utf-8 -*-
"""
QuantInsight Pro - 鲁棒性工具模块
==================================

提供统一的回退/重试/超时/数据降级能力
"""
import functools
import time
import random
import logging
import threading
from typing import Callable, Any, Optional, Dict, List
import streamlit as st
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


# ============== 1. 超时装饰器 ==============

def timeout_decorator(timeout_secs: int = 10, fallback_value=None):
    """装饰器：函数执行超时则返回fallback_value"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            result = [fallback_value]
            exception = [None]

            def target():
                try:
                    result[0] = func(*args, **kwargs)
                except Exception as e:
                    exception[0] = e

            thread = threading.Thread(target=target, daemon=True)
            thread.start()
            thread.join(timeout_secs)

            if thread.is_alive():
                logger.warning(f"{func.__name__} 超时({timeout_secs}s)，使用fallback")
                return fallback_value
            if exception[0]:
                logger.warning(f"{func.__name__} 异常: {exception[0]}")
                return fallback_value
            return result[0]
        return wrapper
    return decorator


# ============== 2. 重试装饰器 ==============

def retry_decorator(max_retries: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """装饰器：失败自动重试（指数退避）"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            current_delay = delay
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        # 指数退避 + 随机抖动
                        sleep_time = current_delay + random.uniform(0, 0.5)
                        logger.info(f"{func.__name__} 第{attempt+1}次失败，{sleep_time:.1f}s后重试: {e}")
                        time.sleep(sleep_time)
                        current_delay *= backoff
            logger.error(f"{func.__name__} 全部{max_retries}次失败: {last_exception}")
            raise last_exception
        return wrapper
    return decorator


# ============== 3. Streamlit安全渲染 ==============

def safe_metric(label: str, value: Any, delta: Optional[Any] = None, fallback: str = '加载中'):
    """安全的st.metric，避免None/NaN报错"""
    try:
        if value is None or (isinstance(value, float) and np.isnan(value)):
            value_str = fallback
            delta_str = None
        else:
            value_str = str(value)
            delta_str = str(delta) if delta is not None else None
        st.metric(label, value_str, delta_str)
    except Exception as e:
        st.metric(label, fallback, None)


def safe_dataframe(df: Optional[pd.DataFrame], title: str = '', height: int = 400, fallback_msg: str = '暂无数据'):
    """安全的st.dataframe，处理None/空数据"""
    if df is None or (isinstance(df, pd.DataFrame) and df.empty):
        st.info(f"💡 {title}：{fallback_msg}")
        return
    try:
        st.dataframe(df, use_container_width=True, height=height)
    except Exception as e:
        st.error(f"数据渲染失败: {e}")


def safe_chart(chart_func: Callable, title: str = '', fallback_msg: str = '图表加载失败', **kwargs):
    """安全的图表渲染，自动捕获异常"""
    try:
        with st.spinner(f'加载{title}...'):
            chart_func(**kwargs)
    except Exception as e:
        st.warning(f"⚠️ {title}：{fallback_msg}")
        logger.warning(f"{title} 渲染失败: {e}")


# ============== 4. 数据回退/降级 ==============

def with_fallback(primary_func: Callable, fallback_value: Any, *args, **kwargs):
    """主函数失败时使用fallback值"""
    try:
        result = primary_func(*args, **kwargs)
        if result is None or (isinstance(result, (list, dict, pd.DataFrame)) and len(result) == 0):
            logger.info(f"{primary_func.__name__} 返回空，使用fallback")
            return fallback_value
        return result
    except Exception as e:
        logger.warning(f"{primary_func.__name__} 失败({e})，使用fallback")
        return fallback_value


# ============== 5. Streamlit重试按钮 ==============

def retry_button(label: str = '🔄 重试', key: Optional[str] = None) -> bool:
    """生成Streamlit重试按钮，返回是否被点击"""
    return st.button(label, key=key or f'retry_{random.randint(0, 99999)}')


# ============== 6. 股票代码标准化 ==============

def normalize_stock_code(code: str) -> str:
    """标准化股票代码：6位字符串"""
    if not code:
        return ''
    code = str(code).strip()
    # 移除前缀
    for prefix in ['SH', 'sh', 'SZ', 'sz']:
        if code.upper().startswith(prefix):
            code = code[2:]
            break
    # 补零
    code = code.zfill(6)
    return code


def is_valid_stock_code(code: str) -> bool:
    """验证股票代码合法性"""
    code = normalize_stock_code(code)
    if not code or len(code) != 6 or not code.isdigit():
        return False
    # 简单规则：6xxxxx=沪市, 0xxxxx/3xxxxx=深市
    if code[0] in ('0', '3', '6'):
        return True
    return False


# ============== 7. 示例数据生成 ==============

SAMPLE_INDUSTRIES = [
    {'name': '人工智能', 'change_pct': 3.45, 'leader': '科大讯飞', 'leader_pct': 7.23, 'volume': 234.5},
    {'name': '新能源', 'change_pct': 2.87, 'leader': '宁德时代', 'leader_pct': 4.56, 'volume': 189.3},
    {'name': '半导体', 'change_pct': 2.34, 'leader': '中芯国际', 'leader_pct': 5.12, 'volume': 156.7},
    {'name': '医药生物', 'change_pct': 1.23, 'leader': '恒瑞医药', 'leader_pct': 3.45, 'volume': 98.4},
    {'name': '银行', 'change_pct': 0.45, 'leader': '招商银行', 'leader_pct': 1.23, 'volume': 234.5},
    {'name': '房地产', 'change_pct': -0.87, 'leader': '万科A', 'leader_pct': -1.45, 'volume': 67.8},
    {'name': '钢铁', 'change_pct': -1.23, 'leader': '宝钢股份', 'leader_pct': -1.89, 'volume': 45.6},
    {'name': '煤炭', 'change_pct': -1.56, 'leader': '中国神华', 'leader_pct': -2.12, 'volume': 34.5},
]

SAMPLE_STOCKS = [
    {'code': '600519', 'name': '贵州茅台', 'price': 1645.30, 'change_pct': -1.23, 'pe': 28.5, 'pb': 8.9, 'roe': 31.2},
    {'code': '000858', 'name': '五粮液', 'price': 142.50, 'change_pct': -2.10, 'pe': 16.8, 'pb': 4.2, 'roe': 25.1},
    {'code': '000333', 'name': '美的集团', 'price': 78.90, 'change_pct': 1.45, 'pe': 14.3, 'pb': 3.1, 'roe': 21.5},
    {'code': '600276', 'name': '恒瑞医药', 'price': 48.20, 'change_pct': 3.45, 'pe': 35.6, 'pb': 5.8, 'roe': 16.2},
    {'code': '002594', 'name': '比亚迪', 'price': 256.80, 'change_pct': 2.34, 'pe': 22.4, 'pb': 4.5, 'roe': 18.9},
    {'code': '300750', 'name': '宁德时代', 'price': 198.50, 'change_pct': 4.56, 'pe': 19.8, 'pb': 4.8, 'roe': 22.3},
    {'code': '688981', 'name': '中芯国际', 'price': 56.70, 'change_pct': 5.12, 'pe': 45.6, 'pb': 3.2, 'roe': 7.1},
    {'code': '002230', 'name': '科大讯飞', 'price': 48.90, 'change_pct': 7.23, 'pe': 89.5, 'pb': 5.6, 'roe': 6.3},
    {'code': '600036', 'name': '招商银行', 'price': 38.20, 'change_pct': 1.23, 'pe': 6.8, 'pb': 1.1, 'roe': 16.8},
    {'code': '000002', 'name': '万科A', 'price': 7.85, 'change_pct': -1.45, 'pe': 9.2, 'pb': 0.6, 'roe': 6.5},
]

SAMPLE_NEWS = [
    {'title': '央行下调存款准备金率0.25个百分点，释放长期资金约5000亿元', 'time': '09:30', 'source': '央行', 'tag': '宏观'},
    {'title': '5月社融数据超预期，信贷结构持续优化', 'time': '10:15', 'source': '央行', 'tag': '宏观'},
    {'title': 'A股三大指数集体高开，沪指涨0.85%', 'time': '09:30', 'source': '证券时报', 'tag': '市场'},
    {'title': '北向资金大幅净流入，外资看好A股配置价值', 'time': '11:20', 'source': '上海证券报', 'tag': '资金'},
    {'title': '人工智能板块持续走强，科大讯飞涨停', 'time': '13:45', 'source': '财联社', 'tag': '行业'},
]


def get_sample_industries() -> List[Dict]:
    """获取示例行业数据"""
    return [dict(item) for item in SAMPLE_INDUSTRIES]


def get_sample_stocks() -> List[Dict]:
    """获取示例股票数据"""
    return [dict(item) for item in SAMPLE_STOCKS]


def get_sample_news() -> List[Dict]:
    """获取示例新闻"""
    return [dict(item) for item in SAMPLE_NEWS]


# ============== 8. 缓存工具 ==============

def cached_with_ttl(ttl_secs: int = 300):
    """带TTL的缓存装饰器"""
    def decorator(func):
        cache_key = f'cache_{func.__module__}_{func.__name__}'
        cache_time_key = f'{cache_key}_time'

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            now = time.time()
            cache_time = st.session_state.get(cache_time_key, 0)
            if now - cache_time < ttl_secs and cache_key in st.session_state:
                return st.session_state[cache_key]
            result = func(*args, **kwargs)
            st.session_state[cache_key] = result
            st.session_state[cache_time_key] = now
            return result
        return wrapper
    return decorator
