"""
通用工具函數
"""

import os
import re
from datetime import datetime
from typing import Optional

import pandas as pd


def normalize_symbol(symbol: str, market: str = "auto") -> str:
    """
    正規化股票代碼，根據市場自動添加後綴。

    Args:
        symbol: 股票代碼，例如 "AAPL", "2330", "TSLA"
        market: 市場別，可選 "auto", "us", "tw", "hk"

    Returns:
        yfinance 可用的股票代碼
    """
    symbol = symbol.strip().upper()

    # 如果已經有後綴，直接返回
    if "." in symbol:
        return symbol

    if market == "us":
        return symbol
    elif market == "tw":
        # 台股上市 .TW，上櫃 .TWO
        return f"{symbol}.TW"
    elif market == "hk":
        # 港股代碼需要補零到 4 位數並加上 .HK
        return f"{int(symbol):04d}.HK"
    elif market == "auto":
        # 自動判斷：
        # - 4~6 位純數字優先視為台股（台股上市/上櫃/興櫃均為 4~6 位）
        # - 若需查港股，建議手動選擇 market="hk" 或輸入如 0700.HK
        if symbol.isdigit():
            return f"{symbol}.TW"
        return symbol
    else:
        return symbol


def parse_period(period: str) -> str:
    """
    驗證並標準化時間區間。
    """
    valid_periods = ["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"]
    period = period.lower().strip()
    if period not in valid_periods:
        raise ValueError(f"不支援的時間區間: {period}，請使用 {valid_periods}")
    return period


def export_to_csv(df: pd.DataFrame, filename: Optional[str] = None, output_dir: str = "output") -> str:
    """
    將 DataFrame 匯出為 CSV。

    Returns:
        匯出檔案的完整路徑
    """
    if filename is None:
        filename = f"stock_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

    if not filename.endswith(".csv"):
        filename += ".csv"

    os.makedirs(output_dir, exist_ok=True)
    filepath = os.path.join(output_dir, filename)
    df.to_csv(filepath, encoding="utf-8-sig", index=True)
    return filepath


def export_to_excel(
    data: dict[str, pd.DataFrame],
    filename: Optional[str] = None,
    output_dir: str = "output",
) -> str:
    """
    將多個 DataFrame 匯出到同一個 Excel 檔案的不同工作表。

    Args:
        data: Dict，key 為工作表名稱，value 為 DataFrame
        filename: 檔案名稱
        output_dir: 輸出目錄

    Returns:
        匯出檔案的完整路徑
    """
    if filename is None:
        filename = f"stock_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

    if not filename.endswith(".xlsx"):
        filename += ".xlsx"

    os.makedirs(output_dir, exist_ok=True)
    filepath = os.path.join(output_dir, filename)

    with pd.ExcelWriter(filepath, engine="openpyxl") as writer:
        for sheet_name, df in data.items():
            # 工作表名稱不能超過 31 字元
            safe_name = re.sub(r'[\\/*?:\[\]]', '_', sheet_name)[:31]
            df.to_excel(writer, sheet_name=safe_name, index=True)

    return filepath


def format_currency(value: Optional[float], currency: str = "USD") -> str:
    """
    格式化貨幣金額。
    """
    if value is None or pd.isna(value):
        return "N/A"
    return f"{currency} {value:,.2f}"


_CURRENCY_NAMES = {
    "TWD": "新台幣",
    "USD": "美元",
    "HKD": "港幣",
    "CNY": "人民幣",
    "JPY": "日圓",
    "EUR": "歐元",
    "GBP": "英鎊",
    "KRW": "韓元",
    "AUD": "澳幣",
    "CAD": "加幣",
    "SGD": "新加坡幣",
    "CHF": "瑞士法郎",
    "INR": "印度盧比",
    "THB": "泰銖",
    "MYR": "馬來西亞令吉",
    "VND": "越南盾",
    "IDR": "印尼盾",
    "PHP": "菲律賓披索",
}


def format_currency_name(currency_code: Optional[str]) -> str:
    """
    將貨幣代碼轉為中文名稱，避免瀏覽器自動翻譯將 TWD 誤譯為奇怪文字。
    """
    if not currency_code:
        return "N/A"
    code = str(currency_code).strip().upper()
    return _CURRENCY_NAMES.get(code, code)


def safe_get(dictionary: dict, key: str, default=None):
    """
    安全地從 dict 取值。
    """
    return dictionary.get(key, default) if dictionary else default
