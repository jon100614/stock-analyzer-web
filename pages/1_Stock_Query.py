"""
股票查詢頁面 - 線上看盤風格

整合股價、技術指標、基本面與大盤資訊在同一頁，採用深色看盤介面。
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

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
    st.caption("輸入代碼後按查詢，所有資訊會顯示在同一頁。")


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


def create_trading_chart(df, name, ticker):
    """建立線上看盤風格多子圖圖表"""
    # 子圖布局：主圖、成交量、RSI、MACD
    fig = make_subplots(
        rows=4,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        row_heights=[0.5, 0.15, 0.15, 0.2],
        subplot_titles=(f"{name} ({ticker}) - K線與均線", "成交量", "RSI", "MACD"),
    )

    # 主圖：K線
    fig.add_trace(
        go.Candlestick(
            x=df.index,
            open=df["open"],
            high=df["high"],
            low=df["low"],
            close=df["close"],
            name="K線",
            increasing_line_color="#ff4d4d",
            decreasing_line_color="#00c853",
            increasing_fillcolor="#ff4d4d",
            decreasing_fillcolor="#00c853",
        ),
        row=1,
        col=1,
    )

    # 主圖：移動平均線
    colors_ma = {"ma_5": "#ffd700", "ma_20": "#00d4ff", "ma_60": "#ff69b4"}
    for col, color in colors_ma.items():
        if col in df.columns:
            fig.add_trace(
                go.Scatter(
                    x=df.index,
                    y=df[col],
                    name=col.upper().replace("MA_", "MA"),
                    line=dict(color=color, width=1.2),
                ),
                row=1,
                col=1,
            )

    # 成交量
    colors_vol = [
        "#ff4d4d" if df["close"].iloc[i] >= df["open"].iloc[i] else "#00c853"
        for i in range(len(df))
    ]
    fig.add_trace(
        go.Bar(
            x=df.index,
            y=df["volume"],
            name="成交量",
            marker_color=colors_vol,
        ),
        row=2,
        col=1,
    )

    # RSI
    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df["rsi"],
            name="RSI",
            line=dict(color="#00d4ff", width=1.2),
        ),
        row=3,
        col=1,
    )
    fig.add_hline(y=70, line=dict(color="#ff4d4d", dash="dash", width=1), row=3, col=1)
    fig.add_hline(y=30, line=dict(color="#00c853", dash="dash", width=1), row=3, col=1)

    # MACD
    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df["macd"],
            name="MACD",
            line=dict(color="#00d4ff", width=1.2),
        ),
        row=4,
        col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df["macd_signal"],
            name="訊號線",
            line=dict(color="#ff69b4", width=1.2),
        ),
        row=4,
        col=1,
    )
    colors_macd = ["#ff4d4d" if v >= 0 else "#00c853" for v in df["macd_hist"]]
    fig.add_trace(
        go.Bar(
            x=df.index,
            y=df["macd_hist"],
            name="MACD柱",
            marker_color=colors_macd,
        ),
        row=4,
        col=1,
    )

    # 深色主題布局
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#0f0f0f",
        font=dict(color="#e0e0e0", size=11),
        xaxis_rangeslider_visible=False,
        height=800,
        margin=dict(l=40, r=40, t=50, b=40),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            bgcolor="rgba(0,0,0,0.5)",
        ),
        hovermode="x unified",
    )

    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor="#2a2a2a")
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor="#2a2a2a")
    fig.update_yaxes(title_text="價格", row=1, col=1)
    fig.update_yaxes(title_text="成交量", row=2, col=1)
    fig.update_yaxes(title_text="RSI", row=3, col=1)
    fig.update_yaxes(title_text="MACD", row=4, col=1)

    return fig


# 輸入代碼後自動查詢（按 Enter 或點其他地方即觸發）
if symbol:
    with st.spinner("正在獲取資料..."):
            try:
                info = get_stock_info(symbol, market)
                ticker = info.get("ticker") or normalize_symbol(symbol, market)
                name = info.get("longName") or info.get("shortName") or symbol
                currency = format_currency_name(info.get("currency"))

                df = get_stock_data(symbol, market, period, interval)
                df = analyze_all_indicators(df)
                latest = df.iloc[-1]
                prev_close = info.get("previousClose") or df["close"].iloc[-2]

                change = latest["close"] - prev_close if prev_close else 0
                change_pct = (change / prev_close * 100) if prev_close else 0

                # 頂部報價列 - 線上看盤風格
                st.markdown(
                    f"""
                    <div style="background-color:#1a1a1a; padding:15px; border-radius:8px; border-left:4px solid #00d4ff;">
                        <span style="font-size:24px; font-weight:bold; color:#ffffff;">{name}</span>
                        <span style="font-size:18px; color:#888888;"> {ticker}</span>
                        <span style="font-size:14px; color:#888888;"> | {info.get('industry') or ''} {info.get('sector') or ''}</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                quote_cols = st.columns(6)
                quote_items = [
                    ("最新價", f"{latest['close']:,.2f}", f"{change:+,.2f} ({change_pct:+.2f}%)"),
                    ("開盤", f"{info.get('open') or latest['open']:,.2f}", ""),
                    ("最高", f"{info.get('dayHigh') or df['high'].max():,.2f}", ""),
                    ("最低", f"{info.get('dayLow') or df['low'].min():,.2f}", ""),
                    ("成交量", f"{int(latest['volume']):,}", ""),
                    ("貨幣", currency, ""),
                ]
                for col, (label, value, delta) in zip(quote_cols, quote_items):
                    with col:
                        if delta:
                            color = "#ff4d4d" if change >= 0 else "#00c853"
                            st.markdown(
                                f"""
                                <div style="text-align:center; padding:10px; background-color:#0f0f0f; border-radius:5px;">
                                    <div style="font-size:12px; color:#888888;">{label}</div>
                                    <div style="font-size:20px; font-weight:bold; color:{color};">{value}</div>
                                    <div style="font-size:12px; color:{color};">{delta}</div>
                                </div>
                                """,
                                unsafe_allow_html=True,
                            )
                        else:
                            st.markdown(
                                f"""
                                <div style="text-align:center; padding:10px; background-color:#0f0f0f; border-radius:5px;">
                                    <div style="font-size:12px; color:#888888;">{label}</div>
                                    <div style="font-size:18px; font-weight:bold; color:#ffffff;">{value}</div>
                                </div>
                                """,
                                unsafe_allow_html=True,
                            )

                st.markdown("---")

                # 主區域：圖表 + 右側資訊
                chart_col, info_col = st.columns([4, 1])

                with chart_col:
                    fig = create_trading_chart(df, name, ticker)
                    st.plotly_chart(fig, use_container_width=True)

                with info_col:
                    st.subheader("技術訊號")
                    signals = generate_signals(df)
                    if signals["signals"]:
                        for sig in signals["signals"]:
                            st.write(f"• {sig}")
                    else:
                        st.write("暫無明確訊號")

                    st.divider()
                    st.subheader("技術指標")
                    st.metric("RSI (14)", f"{signals['rsi']:.2f}")
                    st.metric("MACD", f"{signals['macd']:.4f}")
                    st.metric("布林 %B", f"{latest.get('bb_percent', 0):.2f}")
                    st.metric("MA5", f"{latest.get('ma_5', 0):.2f}")
                    st.metric("MA20", f"{latest.get('ma_20', 0):.2f}")
                    st.metric("MA60", f"{latest.get('ma_60', 0):.2f}")

                    st.divider()
                    st.subheader("基本面")
                    try:
                        fund = get_fundamental_data(symbol, market)
                        summary = fund["summary"]
                        st.metric("市值", f"{summary.get('市值') or 0:,.0f}")
                        st.metric("本益比", summary.get("本益比 (Trailing P/E)") or "N/A")
                        st.metric("EPS", summary.get("EPS (Trailing)") or "N/A")
                        st.metric("52週最高", summary.get("52週最高價") or "N/A")
                        st.metric("52週最低", summary.get("52週最低價") or "N/A")
                    except Exception:
                        st.write("基本面資料暫時無法取得")

                # 大盤走勢
                st.markdown("---")
                st.subheader("大盤走勢")
                index_map = {"us": "^GSPC", "tw": "^TWII", "hk": "^HSI"}
                if market in index_map:
                    idx = index_map[market]
                elif currency == "新台幣":
                    idx = "^TWII"
                elif currency == "港幣":
                    idx = "^HSI"
                else:
                    idx = "^GSPC"

                index_df = get_index_data(idx, period, interval)
                if not index_df.empty:
                    fig_idx = go.Figure()
                    fig_idx.add_trace(
                        go.Scatter(
                            x=index_df.index,
                            y=index_df["close"],
                            name="大盤收盤",
                            line=dict(color="#00d4ff", width=1.5),
                            fill="tozeroy",
                            fillcolor="rgba(0, 212, 255, 0.1)",
                        )
                    )
                    fig_idx.update_layout(
                        template="plotly_dark",
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="#0f0f0f",
                        font=dict(color="#e0e0e0"),
                        height=300,
                        margin=dict(l=40, r=40, t=30, b=40),
                        xaxis_rangeslider_visible=False,
                    )
                    fig_idx.update_xaxes(showgrid=True, gridcolor="#2a2a2a")
                    fig_idx.update_yaxes(showgrid=True, gridcolor="#2a2a2a")
                    st.plotly_chart(fig_idx, use_container_width=True)
                else:
                    st.info("大盤資料暫時無法取得")

                # K線資料表
                st.markdown("---")
                st.subheader("K線資料")
                display_df = df.tail(50).copy().round(2)
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
