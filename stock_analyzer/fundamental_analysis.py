"""
基本面分析模組

使用多資料源取得公司基本面資料，包含 Yahoo Finance、Finnhub、台灣證交所等。
當一個資料源找不到資料時，會自動嘗試其他資料源。
"""

import pandas as pd
import yfinance as yf
import streamlit as st

from .utils import format_currency_name, normalize_symbol, safe_get
from .data_fetcher import fetch_twse_fundamentals, fetch_tpex_fundamentals, fetch_finnhub_fundamentals


def _fetch_yahoo_info(ticker: str) -> dict:
    """從 Yahoo Finance 取得基本資訊，失敗回傳空字典"""
    try:
        stock = yf.Ticker(ticker)
        return stock.info or {}
    except Exception as e:
        return {"_error": str(e)}


def _fetch_yahoo_financials(ticker: str) -> tuple:
    """從 Yahoo Finance 取得財務報表，失敗回傳空 DataFrame"""
    income_stmt = pd.DataFrame()
    balance_sheet = pd.DataFrame()
    cash_flow = pd.DataFrame()
    try:
        stock = yf.Ticker(ticker)
        income_stmt = stock.income_stmt
    except Exception:
        pass
    try:
        stock = yf.Ticker(ticker)
        balance_sheet = stock.balance_sheet
    except Exception:
        pass
    try:
        stock = yf.Ticker(ticker)
        cash_flow = stock.cashflow
    except Exception:
        pass
    return income_stmt, balance_sheet, cash_flow


def fetch_fundamental_data(symbol: str, market: str = "auto") -> dict:
    """
    獲取股票基本面資料。

    會依序嘗試多個資料源：
    1. Yahoo Finance
    2. 台灣證交所（台股）
    3. Finnhub（美股/港股）

    Args:
        symbol: 股票代碼
        market: 市場別

    Returns:
        整理後的基本面資料字典，一定包含 summary 欄位
    """
    ticker = normalize_symbol(symbol, market)
    tickers_to_try = [ticker]

    # 台股自動嘗試 .TW 與 .TWO
    if market == "tw" or (market == "auto" and ticker.endswith(".TW")):
        if not ticker.endswith(".TWO"):
            tickers_to_try.append(ticker.replace(".TW", ".TWO"))
        if ticker.endswith(".TW") and f"{symbol}.TWO" not in tickers_to_try:
            tickers_to_try.append(f"{symbol}.TWO")

    query_status = []

    # 1. Yahoo Finance（嘗試多個 ticker）
    info = {}
    actual_ticker = ticker
    for t in tickers_to_try:
        info = _fetch_yahoo_info(t)
        yahoo_error = info.pop("_error", None)
        # 認定成功需要至少有名稱或市值等關鍵欄位
        if info and (info.get("longName") or info.get("shortName") or info.get("marketCap")):
            query_status.append(f"Yahoo Finance ({t}): 成功")
            actual_ticker = t
            break
        else:
            query_status.append(f"Yahoo Finance ({t}): 失敗 ({yahoo_error or '無資料'})")

    # 財務報表
    income_stmt, balance_sheet, cash_flow = _fetch_yahoo_financials(actual_ticker)

    # 使用實際找到資料的 ticker
    ticker = actual_ticker

    # 2. 根據市場選擇替代資料源
    twse_data = {}
    tpex_data = {}
    finnhub_data = {}

    # 台股：同時嘗試證交所（上市）與櫃買中心（上櫃）
    if ticker.endswith(".TW") or ticker.endswith(".TWO") or market == "tw":
        stock_no = symbol.strip().replace(".TW", "").replace(".TWO", "")
        if stock_no.isdigit():
            try:
                twse_data = fetch_twse_fundamentals(stock_no)
                if twse_data:
                    query_status.append("台灣證交所: 成功")
                else:
                    query_status.append("台灣證交所: 無資料")
            except Exception as e:
                query_status.append(f"台灣證交所: 失敗 ({e})")

            try:
                tpex_data = fetch_tpex_fundamentals(stock_no)
                if tpex_data:
                    query_status.append("櫃買中心: 成功")
                else:
                    query_status.append("櫃買中心: 無資料")
            except Exception as e:
                query_status.append(f"櫃買中心: 失敗 ({e})")

    # 美股/港股：嘗試從 Finnhub 補充
    if not ticker.endswith(".TW") and not ticker.endswith(".TWO"):
        try:
            finnhub_key = st.secrets.get("FINNHUB_API_KEY") if hasattr(st, "secrets") else None
            if finnhub_key:
                finnhub_data = fetch_finnhub_fundamentals(ticker, finnhub_key)
                if finnhub_data:
                    query_status.append("Finnhub: 成功")
                else:
                    query_status.append("Finnhub: 無資料")
            else:
                query_status.append("Finnhub: 未設定 API Key")
        except Exception as e:
            query_status.append(f"Finnhub: 失敗 ({e})")

    # 整理重點指標（優先使用 Yahoo Finance，缺失則用替代資料源）
    pe = safe_get(info, "trailingPE") or twse_data.get("pe_ratio") or tpex_data.get("pe_ratio") or finnhub_data.get("pe_ratio")
    pb = safe_get(info, "priceToBook") or twse_data.get("pb_ratio") or tpex_data.get("pb_ratio") or finnhub_data.get("pb_ratio")
    dividend_yield = safe_get(info, "dividendYield") or twse_data.get("dividend_yield") or tpex_data.get("dividend_yield") or finnhub_data.get("dividend_yield")

    fundamentals = {
        "代碼": symbol,
        "YF 代碼": ticker,
        "公司名稱": safe_get(info, "longName") or safe_get(info, "shortName"),
        "產業": safe_get(info, "industry"),
        "產業別": safe_get(info, "sector"),
        "國家": safe_get(info, "country"),
        "貨幣": format_currency_name(safe_get(info, "currency")),
        "市值": safe_get(info, "marketCap") or finnhub_data.get("market_cap"),
        "企業價值": safe_get(info, "enterpriseValue"),
        "本益比 (Trailing P/E)": pe,
        "遠期本益比 (Forward P/E)": safe_get(info, "forwardPE"),
        "股價淨值比": pb,
        "EPS (Trailing)": safe_get(info, "trailingEps") or finnhub_data.get("eps"),
        "EPS (Forward)": safe_get(info, "forwardEps"),
        "營收成長率": safe_get(info, "revenueGrowth") or finnhub_data.get("revenue_growth"),
        "利潤率": safe_get(info, "profitMargins") or finnhub_data.get("profit_margin"),
        "營業毛利率": safe_get(info, "grossMargins"),
        "營業利益率": safe_get(info, "operatingMargins"),
        "ROE": safe_get(info, "returnOnEquity") or finnhub_data.get("roe"),
        "ROA": safe_get(info, "returnOnAssets") or finnhub_data.get("roa"),
        "負債權益比": safe_get(info, "debtToEquity"),
        "速動比率": safe_get(info, "quickRatio"),
        "流動比率": safe_get(info, "currentRatio"),
        "股息率": dividend_yield,
        "52週最高價": safe_get(info, "fiftyTwoWeekHigh") or finnhub_data.get("52_week_high"),
        "52週最低價": safe_get(info, "fiftyTwoWeekLow") or finnhub_data.get("52_week_low"),
        "員工數": safe_get(info, "fullTimeEmployees"),
        "網站": safe_get(info, "website"),
    }

    sources = ["Yahoo Finance"]
    if twse_data:
        sources.append("台灣證交所")
    if tpex_data:
        sources.append("櫃買中心")
    if finnhub_data:
        sources.append("Finnhub")
    fundamentals["資料來源"] = " + ".join(sources) if (info or twse_data or tpex_data or finnhub_data) else "無可用資料源"
    fundamentals["查詢狀態"] = " | ".join(query_status)

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
    percent_fields = ["營收成長率", "利潤率", "營業毛利率", "營業利益率", "ROE", "ROA"]
    for idx, row in df.iterrows():
        val = row["數值"]
        if row["項目"] in percent_fields and isinstance(val, (int, float)):
            df.at[idx, "數值"] = f"{val * 100:.2f}%"
        elif row["項目"] == "股息率" and isinstance(val, (int, float)):
            # 各資料源皆回傳百分比數字
            df.at[idx, "數值"] = f"{val:.2f}%"
        elif row["項目"] in ["市值", "企業價值"] and isinstance(val, (int, float)):
            df.at[idx, "數值"] = f"{val:,.0f}"
        elif row["項目"] in ["本益比 (Trailing P/E)", "遠期本益比 (Forward P/E)", "股價淨值比"] and isinstance(val, (int, float)):
            df.at[idx, "數值"] = f"{val:.2f}"

    # 將所有數值轉為字串，避免混合型別導致 Arrow 序列化問題
    df["數值"] = df["數值"].astype(str).replace("None", "N/A").replace("nan", "N/A")
    return df
