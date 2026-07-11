"""
基本面分析頁面
"""

import streamlit as st
import pandas as pd

from stock_analyzer import fetch_fundamental_data, format_fundamental_summary
from stock_analyzer.utils import format_large_number

st.title("📑 基本面分析")

# 初始化 session state
if "fundamental_run" not in st.session_state:
    st.session_state.fundamental_run = False


def trigger_fundamental():
    """觸發基本面查詢"""
    st.session_state.fundamental_run = True


with st.sidebar:
    st.header("查詢設定")
    symbol = st.text_input(
        "股票代碼",
        value="AAPL",
        help="例如：AAPL、MSFT、2330、3138.TWO。輸入後按 Enter 或點查詢基本面。",
        on_change=trigger_fundamental,
    ).upper().strip()
    market_options = {"自動判斷": "auto", "美國": "us", "台灣": "tw", "香港": "hk"}
    market_label = st.selectbox("市場", options=list(market_options.keys()), index=0,
                                help="自動判斷會優先視為台股。台股會先嘗試 .TW，失敗再嘗試 .TWO")
    market = market_options[market_label]

    st.button("查詢基本面", type="primary", on_click=trigger_fundamental)

if st.session_state.fundamental_run:
    st.session_state.fundamental_run = False
    if not symbol:
        st.warning("請輸入股票代碼")
    else:
        with st.spinner("正在獲取基本面資料..."):
            try:
                data = fetch_fundamental_data(symbol, market=market)
                summary = format_fundamental_summary(data)

                st.subheader(f"{symbol} 基本面摘要")
                st.dataframe(summary, width="stretch", hide_index=True)

                # 查詢狀態
                s = data["summary"]
                status = s.get("查詢狀態", "")
                if status:
                    st.caption(f"📡 {status}")

                # 關鍵指標卡片
                st.subheader("關鍵指標")
                c1, c2, c3, c4 = st.columns(4)
                with c1:
                    pe = s.get("本益比 (Trailing P/E)")
                    st.metric("本益比", f"{pe:.2f}" if isinstance(pe, (int, float)) else "N/A")
                with c2:
                    pb = s.get("股價淨值比")
                    st.metric("股價淨值比", f"{pb:.2f}" if isinstance(pb, (int, float)) else "N/A")
                with c3:
                    dy = s.get("股息率")
                    if isinstance(dy, str) and dy.endswith("%"):
                        dy_display = dy
                    elif isinstance(dy, (int, float)):
                        dy_display = f"{dy:.2f}%"
                    else:
                        dy_display = "N/A"
                    st.metric("股息率", dy_display)
                with c4:
                    mc = s.get("市值")
                    st.metric("市值", format_large_number(mc))

                # 財務報表
                tabs = st.tabs(["損益表", "資產負債表", "現金流量表"])
                with tabs[0]:
                    income = data.get("income_stmt")
                    if income is not None and not income.empty:
                        st.dataframe(income, width="stretch")
                    else:
                        st.info("無損益表資料")

                with tabs[1]:
                    balance = data.get("balance_sheet")
                    if balance is not None and not balance.empty:
                        st.dataframe(balance, width="stretch")
                    else:
                        st.info("無資產負債表資料")

                with tabs[2]:
                    cash = data.get("cash_flow")
                    if cash is not None and not cash.empty:
                        st.dataframe(cash, width="stretch")
                    else:
                        st.info("無現金流量表資料")

            except Exception as e:
                st.error(f"獲取基本面資料失敗：{e}")
