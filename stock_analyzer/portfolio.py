"""
投資組合分析模組

管理多檔股票庫存，計算總價值、損益、配置比例等。
"""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Optional

from .data_fetcher import fetch_stock_data, normalize_symbol
from .utils import format_currency


class Position:
    """單一股票庫存"""

    def __init__(self, symbol: str, shares: float, cost_basis: float, market: str = "auto"):
        self.symbol = symbol.upper().strip()
        self.shares = float(shares)
        self.cost_basis = float(cost_basis)
        self.market = market
        self.ticker = normalize_symbol(self.symbol, market)
        self._current_price: Optional[float] = None
        self._last_update: Optional[datetime] = None

    @property
    def cost_total(self) -> float:
        return self.shares * self.cost_basis

    @property
    def current_value(self) -> float:
        if self._current_price is None:
            self.update_price()
        return self.shares * (self._current_price or 0)

    @property
    def unrealized_pnl(self) -> float:
        return self.current_value - self.cost_total

    @property
    def unrealized_pnl_pct(self) -> float:
        if self.cost_total == 0:
            return 0.0
        return self.unrealized_pnl / self.cost_total

    def update_price(self) -> float:
        """更新最新價格，返回最新價"""
        try:
            df = fetch_stock_data(self.ticker, period="5d", interval="1d")
            self._current_price = float(df["close"].iloc[-1])
            self._last_update = datetime.now()
        except Exception as e:
            print(f"[警告] 更新 {self.symbol} 價格失敗: {e}")
            self._current_price = 0.0
        return self._current_price

    def to_dict(self) -> dict:
        return {
            "symbol": self.symbol,
            "ticker": self.ticker,
            "shares": self.shares,
            "cost_basis": self.cost_basis,
            "cost_total": self.cost_total,
            "current_price": self._current_price,
            "current_value": self.current_value,
            "unrealized_pnl": self.unrealized_pnl,
            "unrealized_pnl_pct": self.unrealized_pnl_pct,
        }


class Portfolio:
    """投資組合"""

    def __init__(self, name: str = "我的投資組合"):
        self.name = name
        self.positions: dict[str, Position] = {}

    def add_position(
        self,
        symbol: str,
        shares: float,
        cost_basis: float,
        market: str = "auto",
    ) -> Position:
        """
        添加或更新庫存。
        """
        symbol = symbol.upper().strip()
        if symbol in self.positions:
            pos = self.positions[symbol]
            # 加權平均成本
            total_cost = pos.cost_total + (shares * cost_basis)
            total_shares = pos.shares + shares
            pos.shares = total_shares
            pos.cost_basis = total_cost / total_shares if total_shares > 0 else 0
            pos.update_price()
        else:
            pos = Position(symbol, shares, cost_basis, market)
            pos.update_price()
            self.positions[symbol] = pos
        return pos

    def remove_position(self, symbol: str) -> bool:
        """
        移除庫存。
        """
        symbol = symbol.upper().strip()
        if symbol in self.positions:
            del self.positions[symbol]
            return True
        return False

    def update_all_prices(self) -> None:
        """
        更新所有庫存的最新價格。
        """
        for pos in self.positions.values():
            pos.update_price()

    def get_summary(self) -> pd.DataFrame:
        """
        取得投資組合摘要 DataFrame。
        """
        if not self.positions:
            return pd.DataFrame()

        self.update_all_prices()
        rows = [pos.to_dict() for pos in self.positions.values()]
        df = pd.DataFrame(rows)

        total_value = df["current_value"].sum()
        total_cost = df["cost_total"].sum()
        total_pnl = total_value - total_cost

        df["weight"] = df["current_value"] / total_value if total_value > 0 else 0
        df["unrealized_pnl_pct"] = df["unrealized_pnl_pct"].apply(lambda x: f"{x * 100:.2f}%")
        df["weight"] = df["weight"].apply(lambda x: f"{x * 100:.2f}%")

        # 加上總計列，數值欄位使用 NaN 避免混合型別
        import numpy as np
        total_row = {
            "symbol": "總計",
            "ticker": "",
            "shares": np.nan,
            "cost_basis": np.nan,
            "cost_total": total_cost,
            "current_price": np.nan,
            "current_value": total_value,
            "unrealized_pnl": total_pnl,
            "unrealized_pnl_pct": f"{(total_pnl / total_cost * 100):.2f}%" if total_cost > 0 else "0.00%",
            "weight": "100.00%",
        }
        df = pd.concat([df, pd.DataFrame([total_row])], ignore_index=True)
        return df

    def get_total_value(self) -> float:
        """取得投資組合總市值"""
        self.update_all_prices()
        return sum(pos.current_value for pos in self.positions.values())

    def get_total_pnl(self) -> float:
        """取得投資組合總損益"""
        self.update_all_prices()
        return sum(pos.unrealized_pnl for pos in self.positions.values())

    def get_historical_value(self, period: str = "1y") -> pd.DataFrame:
        """
        計算投資組合在一段時間內的歷史總價值。

        注意：此功能假設庫存數量在整段期間不變。
        """
        if not self.positions:
            return pd.DataFrame()

        portfolio_value = None
        for pos in self.positions.values():
            try:
                df = fetch_stock_data(pos.ticker, period=period, interval="1d")
                values = df["close"] * pos.shares
                if portfolio_value is None:
                    portfolio_value = values.to_frame(name=pos.symbol)
                else:
                    portfolio_value[pos.symbol] = values
            except Exception as e:
                print(f"[警告] 獲取 {pos.symbol} 歷史價格失敗: {e}")

        if portfolio_value is None:
            return pd.DataFrame()

        portfolio_value["total"] = portfolio_value.sum(axis=1)
        return portfolio_value

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "positions": {k: v.to_dict() for k, v in self.positions.items()},
            "total_value": self.get_total_value(),
            "total_pnl": self.get_total_pnl(),
        }
