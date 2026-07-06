"""
股票分析網站 - 主頁

使用 Streamlit 建立的響應式網頁應用，支援電腦與手機瀏覽。
"""

import streamlit as st

st.set_page_config(
    page_title="股票分析網站",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

pg = st.navigation(
    [
        st.Page("pages/1_Stock_Query.py", title="股票查詢", icon="🔍"),
        st.Page("pages/2_Technical_Analysis.py", title="技術分析", icon="📊"),
        st.Page("pages/3_Fundamental_Analysis.py", title="基本面分析", icon="📑"),
        st.Page("pages/4_Portfolio.py", title="投資組合", icon="💼"),
        st.Page("pages/5_Stock_Screener.py", title="選股篩選", icon="🔎"),
    ],
    position="sidebar",
)

pg.run()
