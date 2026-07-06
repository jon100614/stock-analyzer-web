"""
基本面分析模組

使用 yfinance 取得公司基本面資料，包含本益比、EPS、營收等。
"""

import pandas as pd
import yfinance as yf

from .utils import format_currency_name, normalize_symbol, safe_get


def fetch_fundamental_data(symbol: str, market: str = "auto") -> dict:
    """
    獲取股票基本面資料。

    Args:
        symbol: 股票代碼
        market: 市場別

    Returns:
        整理後的基本面資料字典
    """
    ticker = normalize_symbol(symbol, market)
    stock = yf.Ticker(ticker)
    info = stock.info or {}

    # 取得損益表、資產負債表、現金流量表（若可用）
    try:
        income_stmt = stock.income_stmt
    except Exception:
        income_stmt = pd.DataFrame()

    try:
        balance_sheet = stock.balance_sheet
    except Exception:
        balance_sheet = pd.DataFrame()

    try:
        cash_flow = stock.cashflow
    except Exception:
        cash_flow = pd.DataFrame()

    # 整理重點指標
    fundamentals = {
        "代碼": symbol,
        "YF 代碼": ticker,
        "公司名稱": safe_get(info, "longName") or safe_get(info, "shortName"),
        "產業": safe_get(info, "industry"),
        "產業別": safe_get(info, "sector"),
        "國家": safe_get(info, "country"),
        "貨幣": format_currency_name(safe_get(info, "currency")),
        "市值": safe_get(info, "marketCap"),
        "企業價值": safe_get(info, "enterpriseValue"),
        "本益比 (Trailing P/E)": safe_get(info, "trailingPE"),
        "遠期本益比 (Forward P/E)": safe_get(info, "forwardPE"),
        "股價淨值比": safe_get(info, "priceToBook"),
        "EPS (Trailing)": safe_get(info, "trailingEps"),
        "EPS (Forward)": safe_get(info, "forwardEps"),
        "營收成長率": safe_get(info, "revenueGrowth"),
        "利潤率": safe_get(info, "profitMargins"),
        "營業毛利率": safe_get(info, "grossMargins"),
        "營業利益率": safe_get(info, "operatingMargins"),
        "ROE": safe_get(info, "returnOnEquity"),
        "ROA": safe_get(info, "returnOnAssets"),
        "負債權益比": safe_get(info, "debtToEquity"),
        "速動比率": safe_get(info, "quickRatio"),
        "流動比率": safe_get(info, "currentRatio"),
        "股息率": safe_get(info, "dividendYield"),
        "52週最高價": safe_get(info, "fiftyTwoWeekHigh"),
        "52週最低價": safe_get(info, "fiftyTwoWeekLow"),
        "員工數": safe_get(info, "fullTimeEmployees"),
        "網站": safe_get(info, "website"),
    }

    return {
        "summary": fundamentals,
        "income_stmt": income_stmt,
        "balance_sheet": balance_sheet,
        "cash_flow": cash_flow,
    }


def format_fundamental_summary(data: dict) -> pd.DataFrame:
    """
    將基本面摘要整理成易讀的 DataFrame。

    Returns:
        兩欄 DataFrame：項目、數值
    """
    summary = data.get("summary", {})
    df = pd.DataFrame(list(summary.items()), columns=["項目", "數值"])

    # 將小數轉為百分比
    percent_fields = ["營收成長率", "利潤率", "營業毛利率", "營業利益率", "ROE", "ROA", "股息率"]
    for idx, row in df.iterrows():
        if row["項目"] in percent_fields and isinstance(row["數值"], (int, float)):
            df.at[idx, "數值"] = f"{row['數值'] * 100:.2f}%"
        elif row["項目"] in ["市值", "企業價值"] and isinstance(row["數值"], (int, float)):
            df.at[idx, "數值"] = f"{row['數值']:,.0f}"

    # 將所有數值轉為字串，避免混合型別導致 Arrow 序列化問題
    df["數值"] = df["數值"].astype(str).replace("None", "N/A").replace("nan", "N/A")
    return df
