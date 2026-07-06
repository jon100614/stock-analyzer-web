"""
技術分析頁面
"""

import streamlit as st
import pandas as pd

from stock_analyzer import fetch_stock_data, analyze_all_indicators, generate_signals, plot_stock_chart

st.title("📊 技術分析")

with st.sidebar:
    st.header("分析設定")
    symbol = st.text_input("股票代碼", value="AAPL", help="例如：AAPL、TSLA、2330、3138.TWO").upper().strip()
    market_options = {"自動判斷": "auto", "美國": "us", "台灣": "tw", "香港": "hk"}
    market_label = st.selectbox("市場", options=list(market_options.keys()), index=0,
                                help="自動判斷會優先視為台股。台股會先嘗試 .TW，失敗再嘗試 .TWO")
    market = market_options[market_label]
    period = st.selectbox("時間區間", options=["1mo", "3mo", "6mo", "1y", "2y"], index=2)

    st.header("指標參數")
    rsi_window = st.slider("RSI 週期", min_value=5, max_value=30, value=14)
    bb_window = st.slider("布林通道週期", min_value=10, max_value=50, value=20)
    bb_std = st.slider("布林通道標準差", min_value=1.0, max_value=3.0, value=2.0, step=0.1)

if st.button("分析", type="primary"):
    if not symbol:
        st.warning("請輸入股票代碼")
    else:
        with st.spinner("正在計算技術指標..."):
            try:
                df = fetch_stock_data(symbol, period=period, market=market)
                df = analyze_all_indicators(df)
                signals = generate_signals(df)

                # 最新訊號卡片
                st.subheader("最新訊號")
                c1, c2, c3, c4 = st.columns(4)
                with c1:
                    st.metric("收盤價", f"{signals['close']:.2f}")
                with c2:
                    st.metric("RSI", f"{signals['rsi']:.2f}")
                with c3:
                    st.metric("MACD", f"{signals['macd']:.4f}")
                with c4:
                    st.metric("日期", str(signals['date'])[:10])

                if signals["signals"]:
                    for sig in signals["signals"]:
                        st.info(sig)
                else:
                    st.info("無明顯訊號")

                # 圖表
                st.subheader("技術分析圖")
                fig = plot_stock_chart(df, symbol, figsize=(14, 10))
                st.pyplot(fig)

                # 指標資料表
                st.subheader("指標資料")
                cols = ["open", "high", "low", "close", "volume",
                        "ma_5", "ma_20", "ma_60", "rsi", "macd", "macd_signal",
                        "bb_upper", "bb_lower"]
                st.dataframe(df[cols].tail(30), width="stretch")

                # 匯出
                csv = df.to_csv(index=True).encode("utf-8-sig")
                st.download_button(
                    label="下載完整指標資料 CSV",
                    data=csv,
                    file_name=f"{symbol}_indicators.csv",
                    mime="text/csv",
                )

            except Exception as e:
                st.error(f"分析失敗：{e}")
