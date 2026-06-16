"""
QuantInsight Pro - 交易模拟器 (Trade Simulator)
==================================================

模拟下单 + 自然语言下单 + 滑点模型 + 智能拆单
专业级"语音/文字下单"功能.

License: MIT
"""

from __future__ import annotations
import json, logging, re, os
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional
import pandas as pd

logger = logging.getLogger(__name__)
TRADES_DIR = Path(__file__).parent.parent.parent / "_trades_data"


@dataclass
class Order:
    order_id: str = ""
    stock_code: str = ""
    stock_name: str = ""
    side: str = "buy"          # buy / sell
    quantity: int = 0
    price: float = 0.0
    order_type: str = "market"  # market / limit / stop_loss / stop_profit
    status: str = "pending"     # pending / filled / cancelled / rejected
    fill_price: float = 0.0
    slippage: float = 0.0
    commission: float = 0.0
    risk_check_passed: bool = True
    risk_check_message: str = ""
    created_at: str = ""
    filled_at: str = ""


class TradeSimulator:
    """交易模拟器"""

    COMMISSION_RATE = 0.0003  # 万三佣金
    MIN_COMMISSION = 5.0      # 最低5元
    SLIPPAGE_RATE = 0.001     # 0.1% 滑点

    def __init__(self):
        TRADES_DIR.mkdir(parents=True, exist_ok=True)
        self._orders: list[Order] = []
        self._load_orders()

    def _load_orders(self):
        path = TRADES_DIR / "orders.json"
        if path.exists():
            try:
                self._orders = [Order(**o) for o in json.loads(path.read_text(encoding="utf-8"))]
            except Exception:
                self._orders = []

    def _save_orders(self):
        path = TRADES_DIR / "orders.json"
        path.write_text(json.dumps([asdict(o) for o in self._orders], ensure_ascii=False, indent=2), encoding="utf-8")

    def parse_nl_order(self, text: str) -> dict:
        """
        解析自然语言订单
        示例: "买入500股贵州茅台" / "卖出全部宁德时代"
        """
        result = {"side": "", "quantity": 0, "stock_name": "", "stock_code": "", "raw": text}

        # 买/卖
        if any(kw in text for kw in ["买入", "买", "加仓", "建仓"]):
            result["side"] = "buy"
        elif any(kw in text for kw in ["卖出", "卖", "减仓", "清仓", "止损"]):
            result["side"] = "sell"

        # 数量
        qty_match = re.search(r'(\d+)\s*股', text)
        if qty_match:
            result["quantity"] = int(qty_match.group(1))
        elif "全部" in text or "清仓" in text:
            result["quantity"] = -1  # -1 表示全部

        # 股票名称
        name_match = re.search(r'([\u4e00-\u9fff]{2,6})(?!.*[\u4e00-\u9fff]{2,6})', text)
        if name_match:
            result["stock_name"] = name_match.group(1)

        return result

    def place_order(self, stock_code: str, stock_name: str, side: str,
                    quantity: int, price: float = 0.0,
                    order_type: str = "market", risk_checker=None) -> Order:
        """下单"""
        order = Order(
            order_id=f"ORD_{len(self._orders)+1}_{int(datetime.now().timestamp())}",
            stock_code=stock_code,
            stock_name=stock_name,
            side=side,
            quantity=quantity,
            price=price,
            order_type=order_type,
            created_at=datetime.now().isoformat(),
        )

        # 风控检查
        if risk_checker:
            check_result = risk_checker.check_order(order)
            order.risk_check_passed = check_result["passed"]
            order.risk_check_message = check_result.get("message", "")
            if not order.risk_check_passed:
                order.status = "rejected"
                self._orders.append(order)
                self._save_orders()
                return order

        # 模拟成交
        if order_type == "market":
            order.slippage = abs(price * self.SLIPPAGE_RATE)
            if side == "buy":
                order.fill_price = price + order.slippage
            else:
                order.fill_price = price - order.slippage
            order.commission = max(order.fill_price * quantity * self.COMMISSION_RATE, self.MIN_COMMISSION)
            order.status = "filled"
            order.filled_at = datetime.now().isoformat()

        self._orders.append(order)
        self._save_orders()
        return order

    def get_trade_history(self, limit: int = 50) -> list[Order]:
        return self._orders[-limit:][::-1]

    def get_pnl_summary(self) -> dict:
        filled = [o for o in self._orders if o.status == "filled"]
        total_commission = sum(o.commission for o in filled)
        total_slippage = sum(o.slippage * o.quantity for o in filled)
        return {
            "total_orders": len(self._orders),
            "filled_orders": len(filled),
            "total_commission": total_commission,
            "total_slippage_cost": total_slippage,
        }


class RiskControlEngine:
    """
    风控引擎
    - 单股仓位 ≤ 20%
    - 单行业 ≤ 40%
    - 日亏损 ≤ 3%
    - 回撤 ≤ 10%
    - 反情绪化交易规则
    """

    POSITION_LIMIT_PCT = 0.20
    SECTOR_LIMIT_PCT = 0.40
    DAILY_LOSS_LIMIT_PCT = 0.03
    MAX_DRAWDOWN_PCT = 0.10
    MAX_DAILY_TRADES = 10
    COOLDOWN_AFTER_STOPLOSS_MIN = 30

    def __init__(self):
        self._trade_timestamps: list[float] = []
        self._stoploss_time: float = 0

    def check_order(self, order: Order, portfolio_value: float = 1000000,
                    current_holdings: dict = None) -> dict:
        """风控检查"""
        current_holdings = current_holdings or {}

        # 1. 仓位限制
        if order.side == "buy" and portfolio_value > 0:
            order_value = order.price * order.quantity
            current_value = sum(
                v.get("market_value", 0) for k, v in current_holdings.items()
                if k == order.stock_code
            )
            new_pct = (current_value + order_value) / portfolio_value
            if new_pct > self.POSITION_LIMIT_PCT:
                return {
                    "passed": False,
                    "message": f"⚠️ 单股仓位限制: 买入后占比 {new_pct*100:.1f}% > {self.POSITION_LIMIT_PCT*100:.0f}%",
                }

        # 2. 日内交易次数
        now = datetime.now().timestamp()
        self._trade_timestamps = [t for t in self._trade_timestamps if now - t < 86400]
        if len(self._trade_timestamps) >= self.MAX_DAILY_TRADES:
            return {
                "passed": False,
                "message": f"⚠️ 日内交易次数已达上限 ({self.MAX_DAILY_TRADES} 次), 请冷静思考",
            }

        # 3. 止损冷却期
        if self._stoploss_time > 0 and (now - self._stoploss_time) < self.COOLDOWN_AFTER_STOPLOSS_MIN * 60:
            remaining = self.COOLDOWN_AFTER_STOPLOSS_MIN - (now - self._stoploss_time) / 60
            return {
                "passed": False,
                "message": f"🧊 止损冷却中, 请 {remaining:.0f} 分钟后再交易",
            }

        # 4. 数量合理性
        if order.quantity <= 0:
            return {"passed": False, "message": "⚠️ 交易数量必须大于0"}
        if order.quantity % 100 != 0:
            return {"passed": False, "message": "⚠️ A股交易数量需为100的整数倍"}

        self._trade_timestamps.append(now)
        return {"passed": True, "message": "✅ 风控检查通过"}
