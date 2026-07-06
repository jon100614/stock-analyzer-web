"""
選股篩選模組

根據用戶定義的條件，對多檔股票進行篩選。
"""

import pandas as pd
import numpy as np
from typing import Callable

from .data_fetcher import fetch_stock_data, fetch_stock_info
from .technical_analysis import analyze_all_indicators


class StockScreener:
    """
    股票篩選器。

    使用範例：
        screener = StockScreener()
        screener.add_condition("rsi", min_val=30, max_val=50)
        screener.add_condition("ma_20", operator=">", field="close")
        results = screener.screen(["AAPL", "TSLA", "MSFT"])
    """

    def __init__(self):
        self.conditions: list[dict] = []

    def add_condition(
        self,
        indicator: str,
        min_val: float = None,
        max_val: float = None,
        operator: str = None,
        field: str = None,
        value: float = None,
    ) -> "StockScreener":
        """
        添加篩選條件。

        Args:
            indicator: 指標名稱，例如 "rsi", "ma_20", "close"
            min_val: 最小值（包含）
            max_val: 最大值（包含）
            operator: 比較運算子，例如 ">", "<", ">=", "<=", "=="
            field: 用於比較的欄位名稱，例如與 close 比較
            value: 用於比較的數值
        """
        self.conditions.append({
            "indicator": indicator,
            "min_val": min_val,
            "max_val": max_val,
            "operator": operator,
            "field": field,
            "value": value,
        })
        return self

    def add_custom_condition(self, func: Callable[[pd.DataFrame], bool]) -> "StockScreener":
        """
        添加自訂篩選函數。

        Args:
            func: 接受 DataFrame，返回 bool 的函數
        """
        self.conditions.append({"custom": func})
        return self

    def _check_conditions(self, df: pd.DataFrame) -> bool:
        """檢查單一股票是否符合所有條件"""
        if df.empty:
            return False

        latest = df.iloc[-1]

        for condition in self.conditions:
            if "custom" in condition:
                try:
                    if not condition["custom"](df):
                        return False
                except Exception:
                    return False
                continue

            indicator = condition["indicator"]
            if indicator not in df.columns:
                return False

            val = latest.get(indicator, np.nan)
            if pd.isna(val):
                return False

            # 範圍條件
            if condition["min_val"] is not None and val < condition["min_val"]:
                return False
            if condition["max_val"] is not None and val > condition["max_val"]:
                return False

            # 比較條件
            op = condition.get("operator")
            if op:
                compare_to = condition.get("value")
                if compare_to is None and condition.get("field"):
                    compare_to = latest.get(condition["field"], np.nan)

                if pd.isna(compare_to):
                    return False

                if op == ">" and not (val > compare_to):
                    return False
                elif op == "<" and not (val < compare_to):
                    return False
                elif op == ">=" and not (val >= compare_to):
                    return False
                elif op == "<=" and not (val <= compare_to):
                    return False
                elif op == "==" and not (val == compare_to):
                    return False

        return True

    def screen(
        self,
        symbols: list[str],
        period: str = "1y",
        market: str = "auto",
        verbose: bool = True,
    ) -> pd.DataFrame:
        """
        對股票列表進行篩選。

        Args:
            symbols: 股票代碼列表
            period: 歷史資料區間
            market: 市場別
            verbose: 是否顯示進度

        Returns:
            符合條件的股票摘要 DataFrame
        """
        results = []

        for symbol in symbols:
            if verbose:
                print(f"[分析中]: {symbol}")

            try:
                df = fetch_stock_data(symbol, period=period, market=market)
                df = analyze_all_indicators(df)

                if self._check_conditions(df):
                    latest = df.iloc[-1]
                    results.append({
                        "symbol": symbol,
                        "close": latest["close"],
                        "rsi": latest.get("rsi", np.nan),
                        "ma_20": latest.get("ma_20", np.nan),
                        "ma_60": latest.get("ma_60", np.nan),
                        "macd": latest.get("macd", np.nan),
                        "bb_upper": latest.get("bb_upper", np.nan),
                        "bb_lower": latest.get("bb_lower", np.nan),
                        "volume": latest.get("volume", np.nan),
                    })
            except Exception as e:
                if verbose:
                    print(f"[警告] {symbol} 分析失敗: {e}")
                continue

        if not results:
            return pd.DataFrame()

        return pd.DataFrame(results)

    def quick_screen(
        self,
        symbols: list[str],
        min_rsi: float = None,
        max_rsi: float = None,
        above_ma: int = None,
        period: str = "1y",
        market: str = "auto",
    ) -> pd.DataFrame:
        """
        快速篩選常用條件。

        Args:
            symbols: 股票代碼列表
            min_rsi: RSI 最小值
            max_rsi: RSI 最大值
            above_ma: 股價在多少日均線之上，例如 20
        """
        self.conditions = []

        if min_rsi is not None or max_rsi is not None:
            self.add_condition("rsi", min_val=min_rsi, max_val=max_rsi)

        if above_ma is not None:
            self.add_condition("close", operator=">", field=f"ma_{above_ma}")

        return self.screen(symbols, period=period, market=market)
