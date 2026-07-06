"""
選股篩選頁面
"""

import streamlit as st
import pandas as pd

from stock_analyzer import StockScreener

st.title("🔎 選股篩選")

with st.sidebar:
    st.header("篩選條件")
    symbols_text = st.text_area(
        "股票代碼列表",
        value="AAPL,MSFT,GOOGL,TSLA,AMZN,NVDA,META",
        help="以逗號分隔，例如：AAPL,MSFT,TSLA,2330,3138.TWO",
    )
    period = st.selectbox("分析區間", options=["3mo", "6mo", "1y", "2y"], index=2)
    market_options = {"自動判斷": "auto", "美國": "us", "台灣": "tw", "香港": "hk"}
    market_label = st.selectbox("市場", options=list(market_options.keys()), index=0,
                                help="自動判斷會優先視為台股。台股會先嘗試 .TW，失敗再嘗試 .TWO")
    market = market_options[market_label]

    enable_rsi = st.checkbox("啟用 RSI 條件", value=False)
    rsi_min = st.number_input("RSI 最小值", min_value=0.0, max_value=100.0, value=30.0)
    rsi_max = st.number_input("RSI 最大值", min_value=0.0, max_value=100.0, value=70.0)

    enable_ma = st.checkbox("啟用均線條件", value=False)
    ma_type = st.selectbox("條件", options=["股價在均線之上", "股價在均線之下"], index=0)
    ma_window = st.number_input("均線週期", min_value=5, max_value=200, value=20)

if st.button("開始篩選", type="primary"):
    symbols = [s.strip() for s in symbols_text.split(",") if s.strip()]
    if not symbols:
        st.warning("請輸入至少一檔股票代碼")
    else:
        screener = StockScreener()

        if enable_rsi:
            screener.add_condition("rsi", min_val=rsi_min, max_val=rsi_max)

        if enable_ma:
            op = ">" if ma_type == "股價在均線之上" else "<"
            screener.add_condition("close", operator=op, field=f"ma_{ma_window}")

        if not enable_rsi and not enable_ma:
            st.warning("請至少啟用一個篩選條件")
        else:
            with st.spinner("正在篩選，請稍候..."):
                results_df = screener.screen(symbols, period=period, market=market, verbose=False)

            if results_df.empty:
                st.info("沒有符合條件的股票")
            else:
                st.success(f"找到 {len(results_df)} 檔符合條件的股票")
                st.dataframe(results_df, width="stretch", hide_index=True)

                csv = results_df.to_csv(index=False).encode("utf-8-sig")
                st.download_button(
                    label="下載篩選結果 CSV",
                    data=csv,
                    file_name="screen_results.csv",
                    mime="text/csv",
                )
