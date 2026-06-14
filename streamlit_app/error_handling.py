"""
QuantInsight Pro - Error Handling Utilities
==============================================

Reusable decorators and components for robust error handling:
- safe_api_call: retry decorator with fallback
- CircuitBreaker: prevent cascade failures
- show_error_card: user-friendly error display with retry

License: MIT
"""

import time
import logging
from functools import wraps
from typing import Any, Callable, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


def safe_api_call(fallback=None, retries: int = 2, delay: float = 1.0, timeout: float = 30.0):
    """
    Decorator for safe API calls with retry and fallback.

    Usage:
        @safe_api_call(fallback=lambda: pd.DataFrame(), retries=2)
        def load_data():
            return ak.stock_zh_index_daily(symbol='sh000300')
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(retries + 1):
                try:
                    result = func(*args, **kwargs)
                    return result
                except Exception as e:
                    last_error = e
                    logger.warning(
                        f"[safe_api_call] {func.__name__} attempt {attempt+1}/{retries+1} failed: {e}"
                    )
                    if attempt < retries:
                        time.sleep(delay * (attempt + 1))
            # All retries exhausted
            if fallback is not None:
                if callable(fallback):
                    return fallback()
                return fallback
            logger.error(f"[safe_api_call] {func.__name__} all retries exhausted: {last_error}")
            raise last_error
        return wrapper
    return decorator


class CircuitBreaker:
    """
    Simple circuit breaker for external API calls.

    States:
    - CLOSED: Normal operation, calls pass through
    - OPEN: Failures exceeded threshold, calls are blocked
    - HALF_OPEN: After cooldown, allow one test call

    Usage:
        breaker = CircuitBreaker(failure_threshold=5, recovery_timeout=60)
        result = breaker.call(some_api_function, arg1, arg2)
    """

    CLOSED = 'closed'
    OPEN = 'open'
    HALF_OPEN = 'half_open'

    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = self.CLOSED

    def call(self, func: Callable, *args, fallback=None, **kwargs) -> Any:
        if self.state == self.OPEN:
            if self.last_failure_time and \
               datetime.now() - self.last_failure_time > timedelta(seconds=self.recovery_timeout):
                self.state = self.HALF_OPEN
            else:
                if fallback is not None:
                    return fallback() if callable(fallback) else fallback
                raise RuntimeError(f"Circuit breaker is OPEN for {func.__name__}")

        try:
            result = func(*args, **kwargs)
            if self.state == self.HALF_OPEN:
                self._reset()
            return result
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = datetime.now()
            if self.failure_count >= self.failure_threshold:
                self.state = self.OPEN
                logger.warning(f"Circuit breaker OPENED for {func.__name__} after {self.failure_count} failures")
            if fallback is not None:
                return fallback() if callable(fallback) else fallback
            raise

    def _reset(self):
        self.state = self.CLOSED
        self.failure_count = 0
        self.last_failure_time = None

    @property
    def is_open(self) -> bool:
        return self.state == self.OPEN


def show_error_card(message: str, retry_func: Optional[Callable] = None, details: str = ''):
    """
    Render a user-friendly error card in Streamlit.

    Args:
        message: User-friendly error message
        retry_func: Optional function to call on retry button click
        details: Optional technical details (shown in expander)
    """
    import streamlit as st

    st.markdown(f"""
    <div style="
        background: rgba(231, 111, 81, 0.1);
        border: 1px solid rgba(231, 111, 81, 0.3);
        border-radius: 12px;
        padding: 1.2rem;
        margin: 1rem 0;
        border-left: 4px solid #E76F51;
    ">
        <div style="font-size: 1.1rem; color: #E76F51; font-weight: 600;">
            ⚠️ 数据加载异常
        </div>
        <div style="color: #999; margin-top: 0.5rem;">
            {message}
        </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([1, 3])
    with col1:
        if retry_func and st.button('🔄 重试', key=f'retry_{id(retry_func)}'):
            retry_func()
    with col2:
        if details:
            with st.expander('🔍 技术详情'):
                st.code(details, language='text')


def show_loading_skeleton(n_rows: int = 3, n_cols: int = 4):
    """Show skeleton loading placeholders"""
    import streamlit as st

    cols = st.columns(n_cols)
    placeholders = []
    for col in cols:
        with col:
            for _ in range(n_rows):
                placeholders.append(st.empty())
                st.markdown('<div style="height: 0.5rem"></div>', unsafe_allow_html=True)
    return placeholders
