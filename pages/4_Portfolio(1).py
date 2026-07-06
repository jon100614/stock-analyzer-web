"""
投資組合分析頁面
"""

import streamlit as st
import pandas as pd

from stock_analyzer import Portfolio, plot_portfolio, export_to_csv, export_to_excel

st.title("💼 投資組合分析")

# 初始化投資組合
if "portfolio" not in st.session_state:
    st.session_state.portfolio = Portfolio(name="我的投資組合")

portfolio = st.session_state.portfolio

# 側邊欄：添加庫存
with st.sidebar:
    st.header("添加庫存")
    new_symbol = st.text_input("股票代碼", value="AAPL", help="例如：AAPL、TSLA、2330、3138.TWO").upper().strip()
    new_shares = st.number_input("股數", min_value=0.0, value=10.0, step=1.0)
    new_cost = st.number_input("成本價", min_value=0.0, value=150.0, step=1.0)
    market_options = {"自動判斷": "auto", "美國": "us", "台灣": "tw", "香港": "hk"}
    new_market_label = st.selectbox("市場", options=list(market_options.keys()), index=0,
                                    help="自動判斷會優先視為台股。台股會先嘗試 .TW，失敗再嘗試 .TWO")
    new_market = market_options[new_market_label]

    if st.button("添加"):
        if new_symbol and new_shares > 0 and new_cost > 0:
            portfolio.add_position(new_symbol, new_shares, new_cost, market=new_market)
            st.success(f"已添加 {new_symbol}")
            st.rerun()
        else:
            st.warning("請輸入完整資料")

    if st.button("清空投資組合"):
        st.session_state.portfolio = Portfolio(name="我的投資組合")
        st.rerun()

# 顯示投資組合
if not portfolio.positions:
    st.info("請從左側添加股票庫存")
else:
    with st.spinner("正在計算投資組合..."):
        try:
            summary = portfolio.get_summary()

            st.subheader("投資組合摘要")
            st.dataframe(summary, width="stretch", hide_index=True)

            # 總計指標
            total_value = portfolio.get_total_value()
            total_pnl = portfolio.get_total_pnl()
            total_cost = summary[summary["symbol"] == "總計"]["cost_total"].values[0]

            c1, c2, c3 = st.columns(3)
            with c1:
                st.metric("總市值", f"{total_value:,.2f}")
            with c2:
                st.metric("總損益", f"{total_pnl:,.2f}", delta=f"{total_pnl/total_cost*100:.2f}%")
            with c3:
                st.metric("總成本", f"{total_cost:,.2f}")

            # 圖表
            st.subheader("投資組合圖表")
            fig = plot_portfolio(portfolio, kind="both", figsize=(14, 6))
            st.pyplot(fig)

            # 歷史價值
            st.subheader("近一年歷史總價值")
            hist = portfolio.get_historical_value(period="1y")
            if not hist.empty:
                st.line_chart(hist[["total"]], width="stretch")
            else:
                st.info("無法取得歷史價值")

            # 匯出
            col1, col2 = st.columns(2)
            with col1:
                csv = summary.to_csv(index=False).encode("utf-8-sig")
                st.download_button("下載摘要 CSV", csv, "portfolio_summary.csv", "text/csv")

        except Exception as e:
            st.error(f"計算投資組合失敗：{e}")
