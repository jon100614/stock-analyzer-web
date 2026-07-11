"""
AI 投資建議頁面

使用 Groq API 提供股票分析建議。API Key 由網站管理員在 Streamlit Cloud Secrets 設定。
"""

import streamlit as st
from groq import Groq

from stock_analyzer import fetch_stock_data, fetch_stock_info, fetch_fundamental_data
from stock_analyzer.technical_analysis import analyze_all_indicators, generate_signals
from stock_analyzer.utils import format_currency_name, format_large_number

st.title("🤖 AI 投資建議")

st.warning(
    "⚠️ 投資有風險，以下建議僅供參考，不構成任何投資建議。請自行判斷並承擔投資風險。",
    icon="⚠️",
)

# 從 Streamlit Secrets 讀取 API Key
try:
    api_key = st.secrets["GROQ_API_KEY"]
except Exception:
    api_key = None
    st.error(
        "⚠️ 此功能需要網站管理員在 Streamlit Cloud Secrets 設定 GROQ_API_KEY。"
        "請聯繫管理員或到 Groq (https://console.groq.com) 建立 API Key 後在 Streamlit Cloud 設定。"
    )


# 初始化 session state
if "run_analysis" not in st.session_state:
    st.session_state.run_analysis = False


def trigger_analysis():
    """設定觸發分析的標記"""
    st.session_state.run_analysis = True


# 側邊欄：分析設定
with st.sidebar:
    st.header("分析設定")

    symbol = st.text_input(
        "股票代碼",
        value="AAPL",
        help="例如：AAPL、TSLA、2330、2330.TW、0700。輸入後按 Enter 即可分析。",
        on_change=trigger_analysis,
    ).upper().strip()

    market_options = {"自動判斷": "auto", "美國": "us", "台灣": "tw", "香港": "hk"}
    market_label = st.selectbox(
        "市場",
        options=list(market_options.keys()),
        index=0,
        help="自動判斷會優先視為台股。台股會先嘗試 .TW（上市），失敗再嘗試 .TWO（上櫃）",
    )
    market = market_options[market_label]

    model_options = {
        "Llama 3.1 8B（快速）": "llama-3.1-8b-instant",
        "Llama 3.3 70B（較聰明）": "llama-3.3-70b-versatile",
        "Mixtral 8x7B": "mixtral-8x7b-32768",
    }
    model_label = st.selectbox("語言模型", options=list(model_options.keys()), index=1)
    model = model_options[model_label]

    question = st.text_area(
        "你想問什麼？",
        value="請分析這檔股票的技術面與基本面，並給出買入、賣出或觀望的建議。",
        help="可以輸入具體問題，例如：『這檔股票適合長期持有嗎？』",
    )

    st.button("問 AI", type="primary", on_click=trigger_analysis)


@st.cache_data(ttl=300)
def get_analysis_data(symbol, market):
    """取得分析所需資料"""
    info = fetch_stock_info(symbol, market=market)
    df = fetch_stock_data(symbol, period="1y", interval="1d", market=market)
    df = analyze_all_indicators(df)
    signals = generate_signals(df)
    latest = df.iloc[-1]

    try:
        fund = fetch_fundamental_data(symbol, market=market)
        fundamentals = fund["summary"]
    except Exception:
        fundamentals = {}

    return {
        "info": info,
        "latest": latest,
        "signals": signals,
        "fundamentals": fundamentals,
    }


def build_prompt(symbol, market, data, question):
    """建立給 LLM 的 prompt"""
    info = data["info"]
    latest = data["latest"]
    signals = data["signals"]
    fund = data["fundamentals"]

    prev_close = info.get("previousClose") or latest["close"]
    change = latest["close"] - prev_close if prev_close else 0
    change_pct = (change / prev_close * 100) if prev_close else 0

    signal_text = "\n".join([f"- {s}" for s in signals["signals"]]) or "暫無明確訊號"

    prompt = f"""你是一位專業的股票分析師，請根據以下資料回答使用者的問題。

## 股票資訊
- 代碼：{symbol}
- 市場：{market}
- 公司名稱：{info.get('longName') or info.get('shortName') or symbol}
- 產業：{info.get('industry') or 'N/A'}
- 產業別：{info.get('sector') or 'N/A'}
- 國家：{info.get('country') or 'N/A'}
- 貨幣：{format_currency_name(info.get('currency'))}

## 最新價格資料
- 最新價：{latest['close']:.2f}
- 漲跌：{change:+.2f} ({change_pct:+.2f}%)
- 成交量：{int(latest['volume']):,}
- MA5：{latest.get('ma_5', 0):.2f}
- MA20：{latest.get('ma_20', 0):.2f}
- MA60：{latest.get('ma_60', 0):.2f}
- RSI(14)：{signals['rsi']:.2f}
- MACD：{signals['macd']:.4f}
- 布林 %B：{latest.get('bb_percent', 0):.2f}

## 技術訊號
{signal_text}

## 基本面資料
- 市值：{format_large_number(fund.get('市值'))}
- 本益比 (Trailing P/E)：{fund.get('本益比 (Trailing P/E)') or 'N/A'}
- 遠期本益比：{fund.get('遠期本益比 (Forward P/E)') or 'N/A'}
- EPS (Trailing)：{fund.get('EPS (Trailing)') or 'N/A'}
- 股價淨值比：{fund.get('股價淨值比') or 'N/A'}
- ROE：{fund.get('ROE') or 'N/A'}
- 股息率：{fund.get('股息率') or 'N/A'}
- 52週最高：{fund.get('52週最高價') or 'N/A'}
- 52週最低：{fund.get('52週最低價') or 'N/A'}

## 使用者問題
{question}

## 回答要求
1. 請用繁體中文回答。
2. 先簡單總結股票目前的技術面與基本面狀況。
3. 根據資料給出明確建議：買入 / 賣出 / 觀望，並說明理由。
4. 列出主要風險與注意事項。
5. 最後必須強調：此分析僅供參考，不構成投資建議。
"""
    return prompt


# 主畫面：顯示分析結果
if st.session_state.run_analysis:
    st.session_state.run_analysis = False

    if not api_key:
        st.error("系統尚未設定 GROQ_API_KEY，請聯繫管理員。")
    elif not symbol:
        st.error("請輸入股票代碼")
    else:
        with st.spinner("正在分析資料並詢問 AI..."):
            try:
                data = get_analysis_data(symbol, market)
                prompt = build_prompt(symbol, market, data, question)

                client = Groq(api_key=api_key)
                response = client.chat.completions.create(
                    model=model,
                    messages=[
                        {
                            "role": "system",
                            "content": "你是一位謹慎的專業股票分析師，只根據提供的資料分析，不臆測未來，並且一定會提醒投資風險。",
                        },
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.3,
                    max_tokens=2000,
                )

                answer = response.choices[0].message.content

                st.subheader("AI 分析結果")
                st.markdown(answer)

                st.divider()
                st.warning(
                    "⚠️ 免責聲明：以上內容由 AI 根據歷史資料生成，僅供參考，不構成任何投資建議。投資有風險，決策請謹慎。",
                    icon="⚠️",
                )

            except Exception as e:
                st.error(f"分析失敗：{e}")
                st.info(
                    "常見原因：\n1. API Key 錯誤或額度用完\n2. 股票代碼無法取得資料\n3. 網路連線問題"
                )
