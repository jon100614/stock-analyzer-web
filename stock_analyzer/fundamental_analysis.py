"""
基本面分析模組

使用 yfinance 取得公司基本面資料，包含本益比、EPS、營收等。
"""

import pandas as pd
import yfinance as yf

from .utils import format_currency_name, normalize_symbol, safe_get
from .data_fetcher import fetch_twse_fundamentals


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

    # 若為台股且 Yahoo Finance 缺少本益比/殖利率/淨值比，嘗試從證交所補充
    twse_data = {}
    if ticker.endswith(".TW") or ticker.endswith(".TWO"):
        stock_no = symbol.strip().replace(".TW", "").replace(".TWO", "")
        if stock_no.isdigit():
            twse_data = fetch_twse_fundamentals(stock_no)

    # 整理重點指標
    pe = safe_get(info, "trailingPE") or (twse_data.get("pe_ratio") if twse_data else None)
    pb = safe_get(info, "priceToBook") or (twse_data.get("pb_ratio") if twse_data else None)
    dividend_yield = safe_get(info, "dividendYield") or (twse_data.get("dividend_yield") if twse_data else None)

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
        "本益比 (Trailing P/E)": pe,
        "遠期本益比 (Forward P/E)": safe_get(info, "forwardPE"),
        "股價淨值比": pb,
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
        "股息率": dividend_yield,
        "52週最高價": safe_get(info, "fiftyTwoWeekHigh"),
        "52週最低價": safe_get(info, "fiftyTwoWeekLow"),
        "員工數": safe_get(info, "fullTimeEmployees"),
        "網站": safe_get(info, "website"),
    }

    if twse_data:
        fundamentals["資料來源"] = "Yahoo Finance + 台灣證交所"
    else:
        fundamentals["資料來源"] = "Yahoo Finance"

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

    # 資料來源標記
    source = summary.get("資料來源", "Yahoo Finance")

    # 將小數轉為百分比（Yahoo Finance 回傳的是小數）
    yahoo_percent_fields = ["營收成長率", "利潤率", "營業毛利率", "營業利益率", "ROE", "ROA"]
    for idx, row in df.iterrows():
        val = row["數值"]
        if row["項目"] in yahoo_percent_fields and isinstance(val, (int, float)):
            df.at[idx, "數值"] = f"{val * 100:.2f}%"
        elif row["項目"] == "股息率" and isinstance(val, (int, float)):
            # 台灣證交所已經是百分比數字，Yahoo Finance 是小數
            if source == "Yahoo Finance + 台灣證交所" and val > 0.5:
                df.at[idx, "數值"] = f"{val:.2f}%"
            else:
                df.at[idx, "數值"] = f"{val * 100:.2f}%"
        elif row["項目"] in ["市值", "企業價值"] and isinstance(val, (int, float)):
            df.at[idx, "數值"] = f"{val:,.0f}"
        elif row["項目"] in ["本益比 (Trailing P/E)", "遠期本益比 (Forward P/E)", "股價淨值比"] and isinstance(val, (int, float)):
            df.at[idx, "數值"] = f"{val:.2f}"

    # 將所有數值轉為字串，避免混合型別導致 Arrow 序列化問題
    df["數值"] = df["數值"].astype(str).replace("None", "N/A").replace("nan", "N/A")
    return df
