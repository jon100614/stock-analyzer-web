"""
股票查詢頁面

將股價、技術指標、基本面與大盤資訊整合在同一頁，類似看盤軟體版面。
"""

import streamlit as st
import pandas as pd
import yfinance as yf

from stock_analyzer import (
    fetch_stock_data,
    fetch_stock_info,
    fetch_fundamental_data,
    format_fundamental_summary,
)
from stock_analyzer.technical_analysis import analyze_all_indicators, generate_signals
from stock_analyzer.utils import format_currency_name, normalize_symbol

st.title("🔍 股票查詢")

# 側邊欄輸入
with st.sidebar:
    st.header("查詢設定")
    symbol = (
        st.text_input(
            "股票代碼",
            value="AAPL",
            help="例如：AAPL、TSLA、2330、2330.TW、3138.TWO、0700",
        )
        .upper()
        .strip()
    )
    market_options = {"自動判斷": "auto", "美國": "us", "台灣": "tw", "香港": "hk"}
    market_label = st.selectbox(
        "市場",
        options=list(market_options.keys()),
        index=0,
        help="自動判斷會優先視為台股。台股會先嘗試 .TW（上市），失敗再嘗試 .TWO（上櫃）",
    )
    market = market_options[market_label]
    period = st.selectbox(
        "時間區間",
        options=["1mo", "3mo", "6mo", "1y", "2y", "5y"],
        index=3,
    )
    interval = st.selectbox(
        "資料頻率",
        options=["1d", "1wk", "1mo"],
        index=0,
    )

    st.divider()
    st.caption("開啟網頁後直接輸入代碼即可查詢，所有資訊會顯示在同一頁。")


@st.cache_data(ttl=300)
def get_stock_data(symbol, market, period, interval):
    """快取股價資料"""
    return fetch_stock_data(symbol, period=period, interval=interval, market=market)


@st.cache_data(ttl=300)
def get_stock_info(symbol, market):
    """快取基本資料"""
    return fetch_stock_info(symbol, market=market)


@st.cache_data(ttl=300)
def get_fundamental_data(symbol, market):
    """快取基本面資料"""
    return fetch_fundamental_data(symbol, market=market)


@st.cache_data(ttl=300)
def get_index_data(index_symbol, period, interval):
    """快取大盤資料"""
    try:
        return fetch_stock_data(index_symbol, period=period, interval=interval, market="us")
    except Exception:
        return pd.DataFrame()


if st.button("查詢", type="primary") or symbol:
    if not symbol:
        st.warning("請輸入股票代碼")
    else:
        with st.spinner("正在獲取資料..."):
            try:
                # 基本資訊
                info = get_stock_info(symbol, market)
                ticker = info.get("ticker") or normalize_symbol(symbol, market)
                name = info.get("longName") or info.get("shortName") or symbol
                currency = format_currency_name(info.get("currency"))

                # 股價資料
                df = get_stock_data(symbol, market, period, interval)
                df = analyze_all_indicators(df)
                latest = df.iloc[-1]
                prev_close = info.get("previousClose") or df["close"].iloc[-2]

                # 計算漲跌
                change = latest["close"] - prev_close if prev_close else 0
                change_pct = (change / prev_close * 100) if prev_close else 0

                # 標題區
                st.header(f"{name} ({ticker})")
                st.caption(
                    f"{info.get('industry') or ''} / {info.get('sector') or ''} / {info.get('country') or ''}"
                )

                # 關鍵報價指標
                col1, col2, col3, col4, col5, col6 = st.columns(6)
                with col1:
                    st.metric("最新價", f"{latest['close']:,.2f}")
                with col2:
                    st.metric("漲跌", f"{change:+,.2f}", f"{change_pct:+.2f}%")
                with col3:
                    st.metric("成交量", f"{int(latest['volume']):,}")
                with col4:
                    st.metric("開盤", f"{info.get('open') or latest['open']:,.2f}")
                with col5:
                    st.metric(
                        "最高",
                        f"{info.get('dayHigh') or df['high'].max():,.2f}",
                    )
                with col6:
                    st.metric(
                        "最低",
                        f"{info.get('dayLow') or df['low'].min():,.2f}",
                    )

                # 主畫面：走勢圖 + 右側資訊
                chart_col, info_col = st.columns([3, 1])

                with chart_col:
                    st.subheader("股價走勢")
                    chart_df = df[["close", "ma_5", "ma_20", "ma_60"]].rename(
                        columns={
                            "close": "收盤價",
                            "ma_5": "MA5",
                            "ma_20": "MA20",
                            "ma_60": "MA60",
                        }
                    )
                    st.line_chart(chart_df, use_container_width=True)

                    st.subheader("成交量")
                    vol_df = df[["volume", "volume_ma_20"]].rename(
                        columns={"volume": "成交量", "volume_ma_20": "量MA20"}
                    )
                    st.bar_chart(vol_df, use_container_width=True)

                with info_col:
                    st.subheader("技術指標")
                    signals = generate_signals(df)
                    st.metric("RSI (14)", f"{signals['rsi']:.2f}")
                    st.metric("MACD", f"{signals['macd']:.4f}")
                    st.metric("布林 %B", f"{latest.get('bb_percent', 0):.2f}")

                    st.divider()
                    st.subheader("訊號")
                    if signals["signals"]:
                        for sig in signals["signals"]:
                            st.write(f"• {sig}")
                    else:
                        st.write("暫無明確訊號")

                    st.divider()
                    st.subheader("報價摘要")
                    st.metric("市值", f"{info.get('marketCap') or 0:,.0f}")
                    st.metric("本益比", info.get("trailingPE") or "N/A")
                    st.metric("EPS", info.get("trailingEps") or "N/A")
                    st.metric("52週最高", info.get("fiftyTwoWeekHigh") or "N/A")
                    st.metric("52週最低", info.get("fiftyTwoWeekLow") or "N/A")

                # 大盤走勢
                st.subheader("大盤走勢")
                index_map = {
                    "us": "^GSPC",  # S&P 500
                    "tw": "^TWII",  # 加權指數
                    "hk": "^HSI",  # 恆生指數
                }
                if market in index_map:
                    index_df = get_index_data(index_map[market], period, interval)
                    if not index_df.empty:
                        st.line_chart(
                            index_df[["close"]].rename(columns={"close": "大盤收盤"}),
                            use_container_width=True,
                    )
                    else:
                        st.info("大盤資料暫時無法取得")
                else:
                    # 自動判斷時依貨幣猜測
                    if currency == "新台幣":
                        idx = "^TWII"
                    elif currency == "港幣":
                        idx = "^HSI"
                    else:
                        idx = "^GSPC"
                    index_df = get_index_data(idx, period, interval)
                    if not index_df.empty:
                        st.line_chart(
                            index_df[["close"]].rename(columns={"close": "大盤收盤"}),
                            use_container_width=True,
                        )
                    else:
                        st.info("大盤資料暫時無法取得")

                # 基本面摘要
                st.subheader("基本面摘要")
                try:
                    fund = get_fundamental_data(symbol, market)
                    summary_df = format_fundamental_summary(fund)
                    st.dataframe(summary_df, use_container_width=True, hide_index=True)
                except Exception as e:
                    st.warning(f"基本面資料取得失敗：{e}")

                # K 線資料表
                st.subheader("K 線資料")
                display_df = df.tail(50).copy()
                display_df = display_df.round(2)
                st.dataframe(display_df, use_container_width=True)

                # 匯出
                csv = df.to_csv(index=True).encode("utf-8-sig")
                st.download_button(
                    label="下載 CSV",
                    data=csv,
                    file_name=f"{symbol}_price.csv",
                    mime="text/csv",
                )

            except Exception as e:
                st.error(f"獲取資料失敗：{e}")
