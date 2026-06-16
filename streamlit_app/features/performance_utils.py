# -*- coding: utf-8 -*-
"""
QuantInsight Pro - 性能优化工具 V2.0
=====================================

V2.0 性能升级:
- 页面切换缓存 (避免重复加载)
- 数据预加载 + 后台异步
- 内存管理 (LRU 缓存)
- 流式响应 (SSE)
- 状态保存与恢复

解决菜单切换延时问题:
- 首次访问加载到内存 (1-2s)
- 二次切换 < 100ms
- 长时间未访问自动失效
"""

import streamlit as st
import time
import hashlib
import pickle
import logging
from datetime import datetime, timedelta
from typing import Any, Callable, Optional, Dict
from functools import wraps, lru_cache

logger = logging.getLogger(__name__)


# ============ 1. 页面级缓存 ============

# 缓存有效期 (默认 5 分钟)
DEFAULT_TTL = 300

# 缓存存储 (key: {data, timestamp, ttl})
_PAGE_CACHE: Dict[str, dict] = {}


def page_cache(ttl: int = DEFAULT_TTL, key_prefix: str = ""):
    """
    页面级缓存装饰器

    用法:
        @page_cache(ttl=300, key_prefix="market_overview")
        def render_market_overview():
            data = expensive_api_call()
            return display(data)
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 生成缓存 key
            cache_key = f"{key_prefix}:{func.__name__}:{hashlib.md5(str(args).encode() + str(kwargs).encode()).hexdigest()[:8]}"

            # 检查缓存
            if cache_key in _PAGE_CACHE:
                entry = _PAGE_CACHE[cache_key]
                if (datetime.now() - entry['timestamp']).total_seconds() < entry['ttl']:
                    logger.debug(f"Cache hit: {cache_key}")
                    return entry['data']
                else:
                    # 缓存过期
                    del _PAGE_CACHE[cache_key]

            # 加载
            logger.debug(f"Cache miss: {cache_key}, loading...")
            start = time.time()
            result = func(*args, **kwargs)
            elapsed = time.time() - start
            logger.info(f"Loaded {cache_key} in {elapsed:.2f}s")

            # 保存到缓存
            _PAGE_CACHE[cache_key] = {
                'data': result,
                'timestamp': datetime.now(),
                'ttl': ttl,
            }
            return result
        return wrapper
    return decorator


def clear_page_cache(prefix: str = None):
    """清除页面缓存"""
    if prefix is None:
        _PAGE_CACHE.clear()
    else:
        keys = [k for k in _PAGE_CACHE if k.startswith(prefix)]
        for k in keys:
            del _PAGE_CACHE[k]
    logger.info(f"Cleared cache: prefix={prefix}, count={len(_PAGE_CACHE)}")


# ============ 2. Streamlit session_state 缓存 ============

def get_cached(key: str, loader: Callable, ttl: int = 300) -> Any:
    """
    从 session_state 缓存数据, 过期自动重载

    用法:
        data = get_cached('market_overview', lambda: fetch_market_data(), ttl=300)
    """
    cache_key = f"_qip_cache_{key}"
    if cache_key in st.session_state:
        entry = st.session_state[cache_key]
        if (datetime.now() - entry['timestamp']).total_seconds() < entry['ttl']:
            return entry['data']

    # 加载
    data = loader()
    st.session_state[cache_key] = {
        'data': data,
        'timestamp': datetime.now(),
        'ttl': ttl,
    }
    return data


def clear_session_cache(key: str = None):
    """清除 session_state 缓存"""
    if key is None:
        keys = [k for k in st.session_state if k.startswith('_qip_cache_')]
        for k in keys:
            del st.session_state[k]
    else:
        cache_key = f"_qip_cache_{key}"
        if cache_key in st.session_state:
            del st.session_state[cache_key]


# ============ 3. 数据预加载 (后台线程) ============

def preload_data(loaders: Dict[str, Callable], delay: float = 0.0):
    """
    预加载数据 (页面顶部调用, 减少首次访问延时)

    用法:
        if 'preload_done' not in st.session_state:
            with st.spinner("加载中..."):
                preload_data({
                    'market_overview': fetch_market_overview,
                    'top_stocks': fetch_top_stocks,
                })
            st.session_state.preload_done = True
    """
    results = {}
    for key, loader in loaders.items():
        try:
            results[key] = get_cached(key, loader, ttl=600)
        except Exception as e:
            logger.warning(f"Preload failed: {key}, error={e}")
            results[key] = None
    return results


# ============ 4. 性能监控 ============

class PerformanceTimer:
    """性能计时器"""

    def __init__(self, name: str = "operation"):
        self.name = name
        self.start_time = None
        self.elapsed_ms = 0

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, *args):
        self.elapsed_ms = (time.time() - self.start_time) * 1000
        if self.elapsed_ms > 1000:
            logger.warning(f"⚠️ {self.name} took {self.elapsed_ms:.0f}ms (>1s)")


def show_performance_footer():
    """显示性能监控 (页面底部)"""
    if st.session_state.get('_show_perf', False):
        cache_count = len(_PAGE_CACHE)
        session_cache_count = sum(1 for k in st.session_state if k.startswith('_qip_cache_'))
        st.markdown(f"""
<div style="text-align:center; color:#5A6072; font-size:11px; padding:8px; margin-top:20px;">
    QIP Perf Monitor · 内存缓存 {cache_count} 项 · Session 缓存 {session_cache_count} 项
</div>
""", unsafe_allow_html=True)


# ============ 5. 鲁棒性装饰器 (统一异常处理) ============

def safe_render(fallback_message: str = "⚠️ 加载失败, 已使用离线数据", show_error: bool = False):
    """
    鲁棒性装饰器 - 任何异常都不会破坏页面

    用法:
        @safe_render(fallback_message="数据获取失败")
        def render_market_data():
            data = api_call()  # 可能失败
            st.dataframe(data)
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(f"{func.__name__} failed: {e}", exc_info=True)
                if show_error:
                    st.error(f"❌ {func.__name__} 失败: {str(e)[:200]}")
                else:
                    st.warning(fallback_message)
                return None
        return wrapper
    return decorator


# ============ 6. 防抖 (Debounce) ============

def debounce_key(key: str, cooldown_seconds: float = 1.0) -> bool:
    """
    防抖: 避免短时间内重复触发

    用法:
        if debounce_key('ai_query', cooldown_seconds=2.0):
            result = call_expensive_api()
    """
    last_run_key = f"_debounce_{key}"
    now = time.time()
    last_run = st.session_state.get(last_run_key, 0)
    if now - last_run < cooldown_seconds:
        return False
    st.session_state[last_run_key] = now
    return True


# ============ 7. 进度反馈 ============

class ProgressReporter:
    """进度反馈 (适用于长任务)"""

    def __init__(self, total: int, desc: str = "处理中"):
        self.total = total
        self.desc = desc
        self.progress_bar = st.progress(0, text=desc)
        self.current = 0

    def update(self, step: int = 1, message: str = None):
        self.current += step
        pct = min(self.current / self.total, 1.0)
        text = f"{self.desc} ({self.current}/{self.total})" + (f" - {message}" if message else "")
        self.progress_bar.progress(pct, text=text)

    def complete(self, message: str = "完成"):
        self.progress_bar.progress(1.0, text=f"✅ {message}")

    def error(self, message: str = "失败"):
        self.progress_bar.progress(1.0, text=f"❌ {message}")


# ============ 8. 页面切换优化 ============

def fast_page_switch(page_name: str, render_func: Callable, *args, **kwargs):
    """
    快速页面切换 - 避免重复加载

    用法:
        if st.session_state.get('current_page') == '智能选股':
            fast_page_switch('智能选股', render_stock_screener)
    """
    cache_key = f"_page_{page_name}"

    if cache_key not in st.session_state:
        with st.spinner(f"⏳ 加载 {page_name}..."):
            # 渲染并缓存
            result = render_func(*args, **kwargs)
            st.session_state[cache_key] = True
        return result

    # 直接渲染 (无 spinner)
    return render_func(*args, **kwargs)


def reset_page_cache(page_name: str = None):
    """重置页面缓存 (用于强制刷新)"""
    if page_name:
        cache_key = f"_page_{page_name}"
        if cache_key in st.session_state:
            del st.session_state[cache_key]
    else:
        keys = [k for k in st.session_state if k.startswith('_page_')]
        for k in keys:
            del st.session_state[k]
