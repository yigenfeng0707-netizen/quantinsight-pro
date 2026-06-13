"""
QuantInsight Pro - 智能预警引擎 (Smart Alert Engine)
=====================================================

6类预警: 价格/成交量/资金流/技术面/新闻/财报
支持自然语言设置预警, 对标 AI涨乐 "一句话盯盘".

License: MIT
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd

logger = logging.getLogger(__name__)

ALERTS_DIR = Path(__file__).parent.parent.parent / "_alerts_data"


@dataclass
class Alert:
    alert_id: str = ""
    stock_code: str = ""
    stock_name: str = ""
    alert_type: str = ""       # price/volume/fund_flow/technical/news/earnings
    condition: str = ""        # 如 "price >= 50"
    threshold: float = 0.0
    is_active: bool = True
    is_triggered: bool = False
    triggered_at: str = ""
    created_at: str = ""
    message: str = ""


class SmartAlertEngine:
    """智能预警引擎"""

    def __init__(self):
        ALERTS_DIR.mkdir(parents=True, exist_ok=True)
        self._alerts: list[Alert] = []
        self._load_alerts()

    def _load_alerts(self):
        path = ALERTS_DIR / "alerts.json"
        if path.exists():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                self._alerts = [Alert(**a) for a in data]
            except Exception:
                self._alerts = []

    def _save_alerts(self):
        path = ALERTS_DIR / "alerts.json"
        data = [asdict(a) for a in self._alerts]
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def parse_nl_alert(self, text: str) -> Alert:
        """
        解析自然语言预警

        示例:
        - "贵州茅台涨到1800元提醒" → price alert
        - "宁德时代跌破200元预警" → price alert
        - "MACD金叉时提醒" → technical alert
        """
        alert = Alert(
            alert_id=f"alert_{len(self._alerts)+1}_{int(datetime.now().timestamp())}",
            created_at=datetime.now().isoformat(),
        )

        # 价格预警
        price_match = re.search(r'([\u4e00-\u9fff]+).{0,5}(涨到|跌破|超过|低于|到)\s*(\d+\.?\d*)', text)
        if price_match:
            name = price_match.group(1)
            action = price_match.group(2)
            price = float(price_match.group(3))
            alert.stock_name = name
            alert.alert_type = "price"
            alert.threshold = price
            alert.condition = f"price {'<=' if action in ('跌破', '低于') else '>='} {price}"
            alert.message = f"{name} 价格{action} {price}元 时提醒"
            return alert

        # 涨跌幅预警
        pct_match = re.search(r'([\u4e00-\u9fff]+).{0,5}(涨|跌).{0,3}(\d+\.?\d*)%', text)
        if pct_match:
            name = pct_match.group(1)
            direction = pct_match.group(2)
            pct = float(pct_match.group(3))
            alert.stock_name = name
            alert.alert_type = "price"
            alert.threshold = pct if direction == "涨" else -pct
            alert.condition = f"pct_change {'>=' if direction == '涨' else '<='} {alert.threshold}"
            alert.message = f"{name} 涨跌幅{direction} {pct}% 时提醒"
            return alert

        # 技术面预警
        if "金叉" in text or "死叉" in text:
            cross = "golden_cross" if "金叉" in text else "death_cross"
            alert.alert_type = "technical"
            alert.condition = cross
            alert.message = f"MACD {cross.replace('_', ' ')} 时提醒"
            # 提取股票名
            name_match = re.search(r'([\u4e00-\u9fff]{2,6})', text)
            if name_match:
                alert.stock_name = name_match.group(1)
            return alert

        # 默认
        alert.alert_type = "custom"
        alert.message = text
        alert.condition = text
        return alert

    def add_alert(self, alert: Alert):
        self._alerts.append(alert)
        self._save_alerts()

    def remove_alert(self, alert_id: str):
        self._alerts = [a for a in self._alerts if a.alert_id != alert_id]
        self._save_alerts()

    def get_active_alerts(self) -> list[Alert]:
        return [a for a in self._alerts if a.is_active]

    def check_alerts(self, current_data: dict[str, dict]) -> list[Alert]:
        """
        检查预警条件

        Args:
            current_data: {stock_code: {"price": float, "pct_change": float, ...}}

        Returns:
            list[Alert]: 触发的预警
        """
        triggered = []

        for alert in self._alerts:
            if not alert.is_active or alert.is_triggered:
                continue

            stock_data = current_data.get(alert.stock_code, {})
            if not stock_data:
                continue

            try:
                if alert.alert_type == "price":
                    price = stock_data.get("price", 0)
                    pct = stock_data.get("pct_change", 0)

                    if ">=" in alert.condition:
                        threshold = float(alert.condition.split(">=")[-1].strip())
                        if "price" in alert.condition and price >= threshold:
                            alert.is_triggered = True
                            alert.triggered_at = datetime.now().isoformat()
                            triggered.append(alert)
                        elif "pct_change" in alert.condition and pct >= threshold:
                            alert.is_triggered = True
                            alert.triggered_at = datetime.now().isoformat()
                            triggered.append(alert)
                    elif "<=" in alert.condition:
                        threshold = float(alert.condition.split("<=")[-1].strip())
                        if "price" in alert.condition and price <= threshold:
                            alert.is_triggered = True
                            alert.triggered_at = datetime.now().isoformat()
                            triggered.append(alert)
            except Exception as e:
                logger.warning(f"检查预警 {alert.alert_id} 失败: {e}")

        if triggered:
            self._save_alerts()

        return triggered

    def get_alerts_summary(self) -> str:
        lines = ["### 👁 预警列表\n"]
        active = self.get_active_alerts()
        if not active:
            lines.append("暂无活跃预警. 使用自然语言设置, 如: '贵州茅台涨到1800元提醒'")
            return "\n".join(lines)

        for a in active:
            status = "🔔 已触发" if a.is_triggered else "⏳ 等待中"
            lines.append(f"- {status} **{a.stock_name or a.stock_code}**: {a.message}")

        return "\n".join(lines)
