# 股票分析軟體 Stock Analyzer

一個使用 Python 開發的股票分析工具，提供三種使用方式：
1. **網頁版**（推薦）：使用 Streamlit 建立，支援電腦與手機瀏覽器
2. **命令列**：適合腳本化操作
3. **Jupyter Notebook**：適合研究與學習

資料源採用免費的 [yfinance](https://github.com/ranaroussi/yfinance)，可分析美股、台股、港股等多個市場。

## 功能特色

- ✅ 多市場股價查詢（美股、台股、港股等）
- ✅ 技術指標計算：MA、EMA、RSI、MACD、布林通道
- ✅ 基本面資料查詢：本益比、EPS、營收、股利等
- ✅ 投資組合分析：市值、損益、權重配置
- ✅ 選股篩選：可依 RSI、均線等條件篩選股票
- ✅ 資料匯出：支援 CSV 與 Excel
- ✅ 圖表繪製：K 線、技術指標、投資組合分析圖
- ✅ 響應式網頁：電腦、平板、手機都能使用

## 環境需求

- Python 3.8 或以上版本
- 建議使用 Python 3.10 ~ 3.12（本專案已在此範圍測試）

## 安裝方式

1. 確認你的 Python 版本：

```bash
python --version
```

2. 安裝相依套件：

```bash
pip install -r requirements.txt
```

如果你的電腦同時安裝多個 Python 版本，請使用對應的 pip，例如：

```bash
python -m pip install -r requirements.txt
# 或指定 Python 3.10
py -3.10 -m pip install -r requirements.txt
```

## 專案結構

```
stock_analyzer/
├── stock_analyzer/           # 核心分析套件
│   ├── __init__.py
│   ├── data_fetcher.py       # 股票資料獲取
│   ├── technical_analysis.py # 技術指標
│   ├── fundamental_analysis.py # 基本面分析
│   ├── portfolio.py          # 投資組合管理
│   ├── stock_screener.py     # 選股篩選
│   ├── plotter.py            # 繪圖
│   └── utils.py              # 工具函數
├── pages/                    # Streamlit 網頁頁面
│   ├── 1_Stock_Query.py
│   ├── 2_Technical_Analysis.py
│   ├── 3_Fundamental_Analysis.py
│   ├── 4_Portfolio.py
│   └── 5_Stock_Screener.py
├── app.py                    # Streamlit 網站主頁
├── main.py                   # 命令列介面
├── notebook.ipynb            # Jupyter Notebook 示範
├── requirements.txt          # 相依套件
├── .streamlit/config.toml    # Streamlit 設定
└── README.md                 # 本文件
```

## 網頁版使用方式（推薦）

### 在本機電腦執行

```bash
streamlit run app.py
```

執行後會自動開啟瀏覽器，網址通常是 `http://localhost:8501`。

如果你想讓同一區網內的手機也能連線，可以加上 `--server.address`：

```bash
streamlit run app.py --server.address 0.0.0.0 --server.port 8501
```

然後在手機瀏覽器輸入電腦的區網 IP，例如 `http://192.168.1.100:8501`。

### 網頁版頁面

- **首頁**：功能介紹
- **股價查詢**：輸入代碼查詢股價走勢與 K 線資料
- **技術分析**：MA、RSI、MACD、布林通道與訊號
- **基本面分析**：本益比、EPS、ROE 等財務數據
- **投資組合**：添加庫存，查看總市值、損益與配置
- **選股篩選**：根據條件一次篩選多檔股票

## 命令列使用方式

### 1. 查詢股價

```bash
python main.py price AAPL --period 1y
```

### 2. 查詢股票資訊

```bash
python main.py info TSLA
```

### 3. 技術指標分析

```bash
python main.py indicators MSFT --plot
```

### 4. 基本面分析

```bash
python main.py fundamental 2330 --market tw
```

### 5. 投資組合分析

```bash
python main.py portfolio --add AAPL,10,150 --add TSLA,5,200 --plot
```

### 6. 選股篩選

```bash
python main.py screen AAPL,MSFT,GOOGL,TSLA --rsi-min 30 --rsi-max 50 --above-ma 20
```

### 7. 批量匯出資料

```bash
python main.py export AAPL,TSLA,MSFT --format excel
```

## Jupyter Notebook 使用方式

開啟 `notebook.ipynb`，依照每個 Cell 的說明執行即可。Notebook 中已包含以下示範：

1. 載入套件與設定
2. 單檔股票價格查詢
3. 技術指標計算與訊號
4. 基本面資料查詢
5. 投資組合建立與分析
6. 選股篩選
7. 圖表繪製
8. 資料匯出

```bash
jupyter notebook notebook.ipynb
```

## 部署到雲端

### 方案一：Streamlit Community Cloud（最簡單、免費）

1. 將專案上傳到 GitHub
2. 前往 [share.streamlit.io](https://share.streamlit.io)
3. 連結 GitHub 帳號，選擇此專案
4. 設定 Main file path 為 `app.py`
5. 點擊 Deploy，幾分鐘後即可取得公開網址

### 方案二：Render（免費）

1. 將專案上傳到 GitHub
2. 前往 [render.com](https://render.com) 建立新的 Web Service
3. 選擇 Python 環境
4. Build Command：`pip install -r requirements.txt`
5. Start Command：`streamlit run app.py --server.port $PORT --server.address 0.0.0.0`

### 方案三：在本機長期運行供自己使用

如果你只是自己想用，最簡單的方式就是讓電腦一直跑著 `streamlit run app.py`，
然後透過區網 IP 或 ngrok 等工具從手機連線。

#### 使用 ngrok 讓手機從任何地方連線

```bash
# 1. 先安裝 ngrok 並註冊帳號
# 2. 在本機啟動 Streamlit
streamlit run app.py --server.port 8501

# 3. 在另一個終端機啟動 ngrok
ngrok http 8501
```

ngrok 會提供一個公開網址，手機輸入該網址即可使用。

## 市場代碼說明

- **美股**：直接使用代碼，例如 `AAPL`、`TSLA`、`MSFT`
- **台股**：
  - 上市股票：使用 4 位數代碼，例如 `2330`、`2317`，程式會自動加上 `.TW`
  - 上櫃股票：可使用 4 位數代碼，程式會自動嘗試 `.TW`，失敗後會自動嘗試 `.TWO`
  - 若要知道確切市場，可直接輸入 `3138.TWO`
- **港股**：建議手動選擇市場 `hk` 或輸入完整代碼，例如 `0700.HK`、`3690.HK`
- **Auto 模式說明**：4~6 位純數字會優先視為台股。若你主要查詢港股，請手動選擇 `hk` 市場

### 為什麼台股有時查不到？

Yahoo Finance 對台股的資料覆蓋不如美股完整，部分上櫃股票需要 `.TWO` 後綴。本程式已自動處理：
當 `.TW` 查不到時，會自動嘗試 `.TWO`。若仍查不到，可能是該股票已下市或 Yahoo Finance 無資料。

## 常見問題

### Windows 命令列中文顯示亂碼

如果在 Windows 命令提示字元或 PowerShell 中看到中文亂碼，這是控制台字型/編碼問題，並非程式錯誤。可嘗試：

1. 執行前切換為 UTF-8 編碼：
   ```cmd
   chcp 65001
   ```
2. 將控制台字型改為可顯示中文的字型（如 Microsoft JhengHei、Consolas 等）。
3. 或直接使用網頁版 / Jupyter Notebook，中文顯示會正常。

### Python 版本不一致

若 `python` 命令指向的 Python 版本與安裝套件的版本不同，可能會出現 `ModuleNotFoundError`。請確認執行程式與安裝套件使用的是同一個 Python，例如：

```bash
python -m pip install -r requirements.txt
python main.py price AAPL
streamlit run app.py
```

### 手機無法連到本機網站

1. 確認電腦與手機連到同一個 Wi-Fi
2. 使用 `ipconfig`（Windows）或 `ifconfig`（Mac/Linux）查詢電腦 IP
3. 啟動時加上 `--server.address 0.0.0.0`
4. 關閉 Windows 防火牆或允許 8501 port

## 注意事項

- 本軟體使用的資料來自 yfinance，可能會有延遲或資料不完整的情況。
- 台股與港股的資料覆蓋率可能不如美股完整。
- 所有分析結果僅供參考，不構成投資建議。

## 未來可擴充

- 整合更多資料源（如 FinMind、TWSE、Alpha Vantage）
- 加入更多技術指標（如 KD、威廉指標、OBV）
- 加入回測功能
- 加入產業比較與同業對標
- 加入使用者登入與資料儲存
