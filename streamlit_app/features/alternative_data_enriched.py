# -*- coding: utf-8 -*-
"""另类数据仪表盘扩展模块 — SQLite 优先 + 按需加载"""

from __future__ import annotations

from typing import Any, Dict, Optional

import pandas as pd
import plotly.graph_objects as go


def _latest_from_series(d: dict) -> Optional[float]:
    if not d:
        return None
    try:
        last_key = sorted(d.keys())[-1]
        return float(d[last_key])
    except (TypeError, ValueError, IndexError):
        return None


def _latest_from_records(records: list, value_keys=("今值", "同比", "值", "value")) -> Optional[float]:
    if not records:
        return None
    row = records[-1]
    if not isinstance(row, dict):
        return None
    for k in value_keys:
        if k in row and row[k] not in (None, ""):
            try:
                return float(row[k])
            except (TypeError, ValueError):
                continue
    for v in row.values():
        try:
            return float(v)
        except (TypeError, ValueError):
            continue
    return None


def render_macro_snapshot_cards(st, brand: Dict[str, str]) -> None:
    """宏观缓存快览（SQLite / 刷新管道）"""
    from features.extended_data_sources import fetch_macro_from_sqlite

    res = fetch_macro_from_sqlite()
    if not res.ok:
        return

    metrics = []
    source = res.source

    if isinstance(res.data, dict) and "snapshot" in res.data:
        snap = res.data.get("snapshot") or {}
        indices = res.data.get("indices") or {}
        if isinstance(snap, dict):
            if "pmi" in snap:
                v = _latest_from_records(snap["pmi"])
                if v is not None:
                    metrics.append(("制造业 PMI", f"{v:.1f}", "荣枯线 50"))
            if "cpi" in snap:
                v = _latest_from_records(snap["cpi"])
                if v is not None:
                    metrics.append(("CPI 同比", f"{v:.2f}%", ""))
            if "m2" in snap:
                v = _latest_from_records(snap["m2"])
                if v is not None:
                    metrics.append(("M2 同比", f"{v:.2f}%", ""))
            if "gdp" in snap:
                v = _latest_from_records(snap["gdp"])
                if v is not None:
                    metrics.append(("GDP 同比", f"{v:.2f}%", ""))
        for name, series in (indices or {}).items():
            if len(metrics) >= 4:
                break
            v = _latest_from_series(series)
            if v is not None and not any(m[0] == name for m in metrics):
                metrics.append((name, f"{v:.2f}", ""))
    elif isinstance(res.data, dict):
        for key, records in res.data.items():
            if len(metrics) >= 4:
                break
            v = _latest_from_records(records if isinstance(records, list) else [])
            if v is not None:
                label = {"cpi": "CPI 同比", "pmi": "制造业 PMI", "m2": "M2 同比", "gdp": "GDP 同比"}.get(key, key.upper())
                metrics.append((label, f"{v:.2f}", ""))

    if not metrics:
        return

    st.markdown("#### 📦 宏观数据缓存快览")
    st.caption(f"数据源：{source}（定时刷新，页面秒开）")
    cols = st.columns(min(len(metrics), 4))
    for i, (label, val, hint) in enumerate(metrics[:4]):
        with cols[i]:
            st.metric(label, val, hint if hint else None)


def render_alt_data_extras(st, go_module, brand: Dict[str, str], dark_layout) -> None:
    """扩展另类数据：舆情 · 大宗 · 研报 · 卫星/活动指数"""
    from features.extended_data_sources import (
        fetch_block_deals,
        fetch_market_news,
        fetch_market_research_reports,
        fetch_satellite_activity_proxy,
        render_source_catalog_markdown,
    )

    go = go_module

    # --- 卫星 / 产经活动代理 ---
    sat = fetch_satellite_activity_proxy()
    if sat.ok and isinstance(sat.data, dict):
        st.markdown("#### 🛰️ 产经活动代理指数")
        st.caption(f"数据源：{sat.source} · 卫星/夜光/港口等另类数据融合演示")
        d = sat.data
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("工业活动指数", d.get("industrial_activity", "—"))
        c2.metric("港口吞吐指数", d.get("port_throughput", "—"))
        c3.metric("夜光同比", f"{d.get('nightlight_yoy', 0):+.2f}%")
        c4.metric("综合趋势", d.get("trend", "—"))
        c5, c6 = st.columns(2)
        c5.metric("施工强度", d.get("construction_intensity", "—"))
        c6.metric("原油库存指数", d.get("oil_storage", "—"))

    st.markdown("---")

    col_l, col_r = st.columns(2)

    with col_l:
        st.markdown("#### 📰 财经舆情")
        news = fetch_market_news(limit=12)
        st.caption(f"数据源：{news.source}")
        if news.ok and news.data is not None and len(news.data) > 0:
            df = news.data
            title_col = next((c for c in df.columns if "标题" in c or "title" in c.lower()), df.columns[0])
            show_cols = [title_col]
            for extra in ("来源", "时间", "发布时间", "日期"):
                if extra in df.columns:
                    show_cols.append(extra)
            st.dataframe(df[show_cols].head(10), use_container_width=True, hide_index=True)
        else:
            st.info("暂无新闻数据")

    with col_r:
        st.markdown("#### 📋 机构研报速览")
        rpt = fetch_market_research_reports(limit=10)
        st.caption(f"数据源：{rpt.source}")
        if rpt.ok and rpt.data is not None and len(rpt.data) > 0:
            st.dataframe(rpt.data.head(8), use_container_width=True, hide_index=True)
        else:
            st.info("暂无研报数据")

    st.markdown("---")

    st.markdown("#### 💼 大宗交易")
    blk = fetch_block_deals(limit=15)
    st.caption(f"数据源：{blk.source}")
    if blk.ok and blk.data is not None and len(blk.data) > 0:
        df = blk.data
        name_col = next((c for c in df.columns if "简称" in c or "名称" in c or "股票" in c), None)
        premium_col = next((c for c in df.columns if "折" in c or "溢价" in c), None)
        if name_col and premium_col:
            top = df.head(12)
            fig = go.Figure(layout=dark_layout)
            y_vals = pd.to_numeric(top[premium_col], errors="coerce").fillna(0)
            colors = [brand["neon_cyan"] if v >= 0 else "#FF4D6A" for v in y_vals]
            fig.add_trace(go.Bar(
                x=top[name_col].astype(str),
                y=y_vals,
                marker_color=colors,
                name="折溢价率(%)",
            ))
            fig.update_layout(title="大宗交易折溢价分布", yaxis_title="%", height=360, xaxis_tickangle=45)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.dataframe(df.head(12), use_container_width=True, hide_index=True)
    else:
        st.info("暂无大宗交易数据")

    with st.expander("📚 另类数据源清单（AFAC2026 差异化维度）", expanded=False):
        st.markdown(render_source_catalog_markdown())
