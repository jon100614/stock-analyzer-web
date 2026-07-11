"""
繪圖模組

使用 matplotlib 繪製股票 K 線圖、技術指標與投資組合圖表。
"""

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
import numpy as np
from typing import Optional


def setup_chinese_font():
    """
    嘗試設定支援中文的字型（優先微軟正黑體）。
    """
    import matplotlib

    chinese_fonts = ["Microsoft JhengHei", "SimHei", "Noto Sans CJK TC", "WenQuanYi Micro Hei"]
    available_fonts = [f.name for f in matplotlib.font_manager.fontManager.ttflist]

    for font in chinese_fonts:
        if font in available_fonts:
            plt.rcParams["font.family"] = [font]
            plt.rcParams["axes.unicode_minus"] = False
            return

    # 若找不到中文字型，使用預設並顯示警告
    print("[警告] 未找到支援中文的字型，圖表中文可能顯示為方框。")


setup_chinese_font()


def plot_stock_chart(
    df: pd.DataFrame,
    symbol: str,
    show_volume: bool = True,
    show_indicators: bool = True,
    figsize: tuple[int, int] = (14, 10),
    save_path: Optional[str] = None,
) -> plt.Figure:
    """
    繪製股票技術分析圖表。

    Args:
        df: 包含 OHLCV 與技術指標的 DataFrame
        symbol: 股票代碼
        show_volume: 是否顯示成交量
        show_indicators: 是否顯示 RSI / MACD
        figsize: 圖表大小
        save_path: 若指定則儲存圖片

    Returns:
        matplotlib Figure 物件
    """
    df = df.copy()
    df.index = pd.to_datetime(df.index)

    # 決定子圖數量
    n_plots = 1
    if show_volume:
        n_plots += 1
    if show_indicators:
        n_plots += 2  # RSI + MACD

    fig, axes = plt.subplots(n_plots, 1, figsize=figsize, sharex=True,
                             gridspec_kw={"height_ratios": [3] + [1] * (n_plots - 1)})
    if n_plots == 1:
        axes = [axes]

    ax_idx = 0

    # 主圖：K 線與均線
    ax_price = axes[ax_idx]
    ax_price.plot(df.index, df["close"], label="收盤價", linewidth=1.5, color="black")

    if "ma_5" in df.columns:
        ax_price.plot(df.index, df["ma_5"], label="MA5", alpha=0.8, linewidth=0.8)
    if "ma_20" in df.columns:
        ax_price.plot(df.index, df["ma_20"], label="MA20", alpha=0.8, linewidth=0.8)
    if "ma_60" in df.columns:
        ax_price.plot(df.index, df["ma_60"], label="MA60", alpha=0.8, linewidth=0.8)

    # 布林通道
    if "bb_upper" in df.columns:
        ax_price.fill_between(df.index, df["bb_upper"], df["bb_lower"], alpha=0.1, color="blue", label="布林通道")
        ax_price.plot(df.index, df["bb_upper"], "--", color="blue", alpha=0.5, linewidth=0.7)
        ax_price.plot(df.index, df["bb_lower"], "--", color="blue", alpha=0.5, linewidth=0.7)

    ax_price.set_title(f"{symbol} 股票技術分析圖", fontsize=14)
    ax_price.set_ylabel("價格")
    ax_price.legend(loc="upper left")
    ax_price.grid(True, alpha=0.3)
    ax_idx += 1

    # 成交量
    if show_volume:
        ax_vol = axes[ax_idx]
        colors = ["red" if df["close"].iloc[i] >= df["open"].iloc[i] else "green"
                  for i in range(len(df))]
        ax_vol.bar(df.index, df["volume"], color=colors, alpha=0.7)
        ax_vol.set_ylabel("成交量")
        ax_vol.grid(True, alpha=0.3)
        ax_idx += 1

    # RSI
    if show_indicators and "rsi" in df.columns:
        ax_rsi = axes[ax_idx]
        ax_rsi.plot(df.index, df["rsi"], color="purple", label="RSI")
        ax_rsi.axhline(70, color="red", linestyle="--", alpha=0.7, label="超買 70")
        ax_rsi.axhline(30, color="green", linestyle="--", alpha=0.7, label="超賣 30")
        ax_rsi.fill_between(df.index, 30, 70, alpha=0.05, color="gray")
        ax_rsi.set_ylabel("RSI")
        ax_rsi.set_ylim(0, 100)
        ax_rsi.legend(loc="upper left")
        ax_rsi.grid(True, alpha=0.3)
        ax_idx += 1

    # MACD
    if show_indicators and "macd" in df.columns:
        ax_macd = axes[ax_idx]
        ax_macd.plot(df.index, df["macd"], label="MACD", color="blue")
        ax_macd.plot(df.index, df["macd_signal"], label="訊號線", color="red")
        colors_macd = ["red" if v >= 0 else "green" for v in df["macd_hist"]]
        ax_macd.bar(df.index, df["macd_hist"], color=colors_macd, alpha=0.5, label="柱狀圖")
        ax_macd.axhline(0, color="black", linewidth=0.5)
        ax_macd.set_ylabel("MACD")
        ax_macd.set_xlabel("日期")
        ax_macd.legend(loc="upper left")
        ax_macd.grid(True, alpha=0.3)

    plt.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
        print(f"[完成] 圖表已儲存: {save_path}")

    return fig


def plot_portfolio(
    portfolio,
    kind: str = "both",
    figsize: tuple[int, int] = (14, 6),
    save_path: Optional[str] = None,
) -> plt.Figure:
    """
    繪製投資組合圖表。

    Args:
        portfolio: Portfolio 物件
        kind: "value" (歷史價值), "weight" (權重餅圖), "both" (兩者)
        figsize: 圖表大小
        save_path: 儲存路徑

    Returns:
        matplotlib Figure 物件
    """
    if kind == "value":
        fig, axes = plt.subplots(1, 1, figsize=figsize)
        axes = [axes]
    elif kind == "weight":
        fig, axes = plt.subplots(1, 1, figsize=figsize)
        axes = [axes]
    else:
        fig, axes = plt.subplots(1, 2, figsize=figsize)

    # 權重餅圖
    if kind in ("weight", "both"):
        summary = portfolio.get_summary()
        if summary.empty or len(summary) <= 1:
            print("[警告] 投資組合為空，無法繪製圖表。")
            return fig

        # 排除總計列
        summary = summary[summary["symbol"] != "總計"].copy()
        summary["weight_num"] = summary["weight"].str.replace("%", "").astype(float)

        ax = axes[0] if kind == "both" else axes[0]
        colors = plt.cm.tab20(np.linspace(0, 1, len(summary)))
        ax.pie(
            summary["weight_num"],
            labels=summary["symbol"],
            autopct="%1.1f%%",
            startangle=90,
            colors=colors,
        )
        ax.set_title(f"{portfolio.name} 配置權重")

    # 歷史價值
    if kind in ("value", "both"):
        hist = portfolio.get_historical_value(period="1y")
        ax = axes[1] if kind == "both" else axes[0]

        if not hist.empty and "total" in hist.columns:
            ax.plot(hist.index, hist["total"], label="總市值", linewidth=2)
            for col in hist.columns:
                if col != "total":
                    ax.plot(hist.index, hist[col], label=col, alpha=0.7)
            ax.set_title(f"{portfolio.name} 歷史總價值")
            ax.set_xlabel("日期")
            ax.set_ylabel("價值")
            ax.legend(loc="upper left")
            ax.grid(True, alpha=0.3)
        else:
            ax.text(0.5, 0.5, "無法取得歷史價值", ha="center", va="center", transform=ax.transAxes)

    plt.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
        print(f"[完成] 圖表已儲存: {save_path}")

    return fig
