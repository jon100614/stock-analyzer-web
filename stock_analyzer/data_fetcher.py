"""
股票資料獲取模組

使用 yfinance 作為主要資料源，支援多市場股票查詢。
針對台股補充台灣證交所公開資料。
"""

import yfinance as yf
import pandas as pd
import requests
from datetime import datetime
from typing import Optional

from .utils import normalize_symbol


def _try_fetch_history(ticker: str, period: str, interval: str) -> pd.DataFrame:
    """嘗試獲取單一 ticker 的歷史資料。"""
    stock = yf.Ticker(ticker)
    df = stock.history(period=period, interval=interval)
    return df


def fetch_stock_data(
    symbol: str,
    period: str = "1y",
    interval: str = "1d",
    market: str = "auto",
) -> pd.DataFrame:
    """
    獲取股票歷史價格資料。

    對於台股，會先嘗試 .TW（上市），若失敗則自動嘗試 .TWO（上櫃）。

    Args:
        symbol: 股票代碼，例如 "AAPL", "2330", "TSLA"
        period: 時間區間，例如 "1mo", "3mo", "1y", "5y"
        interval: 資料頻率，例如 "1d", "1wk", "1mo"
        market: 市場別，可選 "auto", "us", "tw", "hk"

    Returns:
        包含股票歷史價格的 DataFrame
    """
    ticker = normalize_symbol(symbol, market)
    tickers_to_try = [ticker]

    # 若為台股，增加 .TWO fallback
    if market == "tw" or (market == "auto" and ticker.endswith(".TW")):
        if not ticker.endswith(".TWO"):
            tickers_to_try.append(ticker.replace(".TW", ".TWO"))
        if ticker.endswith(".TW") and f"{symbol}.TWO" not in tickers_to_try:
            tickers_to_try.append(f"{symbol}.TWO")

    last_error = None
    for t in tickers_to_try:
        try:
            df = _try_fetch_history(t, period, interval)
            if not df.empty:
                df.index = pd.to_datetime(df.index)
                # 移除時區資訊，避免 Excel 匯出等後續處理出錯
                if df.index.tz is not None:
                    df.index = df.index.tz_localize(None)
                df.columns = [c.lower().replace(" ", "_") for c in df.columns]
                return df
        except Exception as e:
            last_error = e
            continue

    raise ValueError(
        f"無法獲取 {symbol} 的資料，已嘗試 {tickers_to_try}。"
        f"請確認代碼正確，台股上市請加 .TW，上櫃請加 .TWO。"
    )


def fetch_stock_info(symbol: str, market: str = "auto") -> dict:
    """
    獲取股票基本資訊。

    對於台股，會先嘗試 .TW（上市），若失敗則自動嘗試 .TWO（上櫃）。

    Args:
        symbol: 股票代碼
        market: 市場別

    Returns:
        股票基本資訊字典
    """
    ticker = normalize_symbol(symbol, market)
    tickers_to_try = [ticker]

    # 若為台股，增加 .TWO fallback
    if market == "tw" or (market == "auto" and ticker.endswith(".TW")):
        if not ticker.endswith(".TWO"):
            tickers_to_try.append(ticker.replace(".TW", ".TWO"))
        if ticker.endswith(".TW") and f"{symbol}.TWO" not in tickers_to_try:
            tickers_to_try.append(f"{symbol}.TWO")

    info = {}
    actual_ticker = ticker
    for t in tickers_to_try:
        try:
            stock = yf.Ticker(t)
            fetched = stock.info or {}
            if fetched:
                info = fetched
                actual_ticker = t
                break
        except Exception:
            continue

    # 整理重要欄位
    key_fields = [
        "symbol",
        "shortName",
        "longName",
        "sector",
        "industry",
        "country",
        "currency",
        "marketCap",
        "enterpriseValue",
        "trailingPE",
        "forwardPE",
        "priceToBook",
        "dividendYield",
        "trailingEps",
        "revenueGrowth",
        "profitMargins",
        "fiftyTwoWeekHigh",
        "fiftyTwoWeekLow",
        "fiftyDayAverage",
        "twoHundredDayAverage",
        "website",
    ]

    result = {"raw_symbol": symbol, "ticker": actual_ticker}
    for field in key_fields:
        result[field] = info.get(field, None)

    return result


def fetch_multiple_stocks(
    symbols: list[str],
    period: str = "1y",
    interval: str = "1d",
    market: str = "auto",
) -> dict[str, pd.DataFrame]:
    """
    批量獲取多檔股票資料。

    Args:
        symbols: 股票代碼列表
        period: 時間區間
        interval: 資料頻率
        market: 市場別

    Returns:
        Dict，key 為股票代碼，value 為 DataFrame
    """
    result = {}
    for symbol in symbols:
        try:
            df = fetch_stock_data(symbol, period, interval, market)
            result[symbol] = df
        except Exception as e:
            print(f"[警告] 獲取 {symbol} 失敗: {e}")
            result[symbol] = pd.DataFrame()
    return result


def fetch_dividends_and_splits(symbol: str, market: str = "auto") -> tuple[pd.Series, pd.Series]:
    """
    獲取股利和股票分割資料。

    Returns:
        (dividends, splits)
    """
    ticker = normalize_symbol(symbol, market)
    stock = yf.Ticker(ticker)
    return stock.dividends, stock.splits


def fetch_twse_fundamentals(stock_no: str) -> dict:
    """
    從台灣證交所取得台股基本面資料（本益比、殖利率、股價淨值比）。

    Args:
        stock_no: 台股數字代碼，例如 "2330"

    Returns:
        包含最新本益比、殖利率、股價淨值比的字典，若失敗則回傳空字典
    """
    try:
        today = datetime.now().strftime("%Y%m%d")
        url = f"https://www.twse.com.tw/rwd/zh/afterTrading/BWIBBU?date={today}&stockNo={stock_no}&response=json"
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        if data.get("stat") != "OK" or not data.get("data"):
            return {}

        # 取最後一筆（最新交易日）
        latest = data["data"][-1]
        # fields: ["日期","殖利率(%)","股利年度","本益比","股價淨值比","財報年/季"]
        return {
            "pe_ratio": float(latest[3]) if latest[3] else None,
            "dividend_yield": float(latest[1]) if latest[1] else None,
            "pb_ratio": float(latest[4]) if latest[4] else None,
            "dividend_year": latest[2] if len(latest) > 2 else None,
            "source": "twse",
        }
    except Exception:
        return {}
