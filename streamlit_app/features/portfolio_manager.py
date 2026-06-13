"""
QuantInsight Pro - 组合管理器 (Portfolio Manager)
===================================================

创建/管理投资组合, 实时盈亏, 风险指标.
对标 AI涨乐 的持仓管理功能.

License: MIT
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

DATA_DIR = Path(os.path.dirname(__file__)).parent.parent / "_portfolio_data"


@dataclass
class Holding:
    stock_code: str = ""
    stock_name: str = ""
    quantity: int = 0
    avg_cost: float = 0.0
    current_price: float = 0.0

    @property
    def market_value(self) -> float:
        return self.quantity * self.current_price

    @property
    def pnl(self) -> float:
        return self.quantity * (self.current_price - self.avg_cost)

    @property
    def pnl_pct(self) -> float:
        if self.avg_cost <= 0:
            return 0.0
        return (self.current_price - self.avg_cost) / self.avg_cost * 100


@dataclass
class Portfolio:
    name: str = "默认组合"
    holdings: list[Holding] = field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""

    @property
    def total_market_value(self) -> float:
        return sum(h.market_value for h in self.holdings)

    @property
    def total_cost(self) -> float:
        return sum(h.quantity * h.avg_cost for h in self.holdings)

    @property
    def total_pnl(self) -> float:
        return self.total_market_value - self.total_cost

    @property
    def total_pnl_pct(self) -> float:
        if self.total_cost <= 0:
            return 0.0
        return self.total_pnl / self.total_cost * 100

    def get_sector_concentration(self) -> dict:
        """行业集中度 (简化: 按名称猜测)"""
        return {"股票数": len(self.holdings)}

    def get_top_holdings(self, n: int = 5) -> list[Holding]:
        sorted_h = sorted(self.holdings, key=lambda h: h.market_value, reverse=True)
        return sorted_h[:n]


class PortfolioManager:
    """
    组合管理器

    使用示例:
        >>> pm = PortfolioManager()
        >>> pm.create_portfolio("我的组合")
        >>> pm.add_holding("我的组合", "600519", "贵州茅台", 100, 1680.0)
        >>> portfolio = pm.get_portfolio("我的组合")
    """

    def __init__(self, data_dir: str = None):
        self.data_dir = Path(data_dir) if data_dir else DATA_DIR
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self._portfolios: dict[str, Portfolio] = {}
        self._load_all()

    def _portfolio_path(self, name: str) -> Path:
        safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in name)
        return self.data_dir / f"{safe_name}.json"

    def _load_all(self):
        for f in self.data_dir.glob("*.json"):
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                holdings = [Holding(**h) for h in data.get("holdings", [])]
                p = Portfolio(
                    name=data.get("name", f.stem),
                    holdings=holdings,
                    created_at=data.get("created_at", ""),
                    updated_at=data.get("updated_at", ""),
                )
                self._portfolios[p.name] = p
            except Exception as e:
                logger.warning(f"加载组合 {f} 失败: {e}")

    def _save(self, portfolio: Portfolio):
        path = self._portfolio_path(portfolio.name)
        data = {
            "name": portfolio.name,
            "holdings": [asdict(h) for h in portfolio.holdings],
            "created_at": portfolio.created_at,
            "updated_at": datetime.now().isoformat(),
        }
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def create_portfolio(self, name: str) -> Portfolio:
        if name in self._portfolios:
            return self._portfolios[name]
        p = Portfolio(name=name, created_at=datetime.now().isoformat())
        self._portfolios[name] = p
        self._save(p)
        return p

    def get_portfolio(self, name: str) -> Optional[Portfolio]:
        return self._portfolios.get(name)

    def list_portfolios(self) -> list[str]:
        return list(self._portfolios.keys())

    def delete_portfolio(self, name: str):
        if name in self._portfolios:
            del self._portfolios[name]
            path = self._portfolio_path(name)
            if path.exists():
                path.unlink()

    def add_holding(self, portfolio_name: str, stock_code: str, stock_name: str,
                    quantity: int, avg_cost: float, current_price: float = 0.0):
        p = self._portfolios.get(portfolio_name)
        if p is None:
            p = self.create_portfolio(portfolio_name)

        # 查找或新增
        for h in p.holdings:
            if h.stock_code == stock_code:
                # 加仓: 加权平均成本
                total_qty = h.quantity + quantity
                h.avg_cost = (h.avg_cost * h.quantity + avg_cost * quantity) / total_qty
                h.quantity = total_qty
                if current_price > 0:
                    h.current_price = current_price
                self._save(p)
                return

        p.holdings.append(Holding(
            stock_code=stock_code, stock_name=stock_name,
            quantity=quantity, avg_cost=avg_cost, current_price=current_price or avg_cost,
        ))
        self._save(p)

    def remove_holding(self, portfolio_name: str, stock_code: str, quantity: int = 0):
        p = self._portfolios.get(portfolio_name)
        if p is None:
            return

        for i, h in enumerate(p.holdings):
            if h.stock_code == stock_code:
                if quantity <= 0 or quantity >= h.quantity:
                    p.holdings.pop(i)
                else:
                    h.quantity -= quantity
                break
        self._save(p)

    def update_prices(self, portfolio_name: str, price_map: dict[str, float]):
        p = self._portfolios.get(portfolio_name)
        if p is None:
            return
        for h in p.holdings:
            if h.stock_code in price_map:
                h.current_price = price_map[h.stock_code]
        self._save(p)

    def get_summary(self, portfolio_name: str) -> str:
        p = self.get_portfolio(portfolio_name)
        if p is None:
            return "组合不存在"

        lines = [f"### 💼 {p.name}\n"]
        lines.append(f"**总市值**: ¥{p.total_market_value:,.2f}")
        lines.append(f"**总成本**: ¥{p.total_cost:,.2f}")
        pnl_emoji = "📈" if p.total_pnl >= 0 else "📉"
        lines.append(f"**{pnl_emoji} 盈亏**: ¥{p.total_pnl:,.2f} ({p.total_pnl_pct:+.2f}%)\n")

        if p.holdings:
            lines.append("| 股票 | 持仓 | 成本 | 现价 | 盈亏 |")
            lines.append("|------|------|------|------|------|")
            for h in p.holdings:
                emoji = "🟢" if h.pnl >= 0 else "🔴"
                lines.append(
                    f"| {h.stock_name}({h.stock_code}) | {h.quantity} | "
                    f"¥{h.avg_cost:.2f} | ¥{h.current_price:.2f} | "
                    f"{emoji} ¥{h.pnl:,.0f} ({h.pnl_pct:+.1f}%) |"
                )

        return "\n".join(lines)
