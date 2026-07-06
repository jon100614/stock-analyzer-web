"""
Stock Analyzer - 股票分析工具包

一個簡單但完整的股票分析工具，支援：
- 多市場股價查詢（美股、台股、港股等）
- 技術指標計算（MA、RSI、MACD、布林通道）
- 基本面資料查詢
- 投資組合分析
- 選股篩選
- 資料匯出
"""

from .data_fetcher import (
    fetch_stock_data,
    fetch_stock_info,
    fetch_multiple_stocks,
    normalize_symbol,
)
from .technical_analysis import (
    add_moving_averages,
    add_ema,
    add_rsi,
    add_macd,
    add_bollinger_bands,
    add_volume_moving_average,
    analyze_all_indicators,
    generate_signals,
)
from .fundamental_analysis import fetch_fundamental_data, format_fundamental_summary
from .portfolio import Portfolio
from .stock_screener import StockScreener
from .plotter import plot_stock_chart, plot_portfolio
from .utils import export_to_csv, export_to_excel

__version__ = "0.1.0"
__all__ = [
    "fetch_stock_data",
    "fetch_stock_info",
    "fetch_multiple_stocks",
    "normalize_symbol",
    "add_moving_averages",
    "add_ema",
    "add_rsi",
    "add_macd",
    "add_bollinger_bands",
    "add_volume_moving_average",
    "analyze_all_indicators",
    "generate_signals",
    "fetch_fundamental_data",
    "format_fundamental_summary",
    "Portfolio",
    "StockScreener",
    "plot_stock_chart",
    "plot_portfolio",
    "export_to_csv",
    "export_to_excel",
]
