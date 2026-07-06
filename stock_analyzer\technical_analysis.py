"""
技術指標分析模組

提供常見技術指標計算：移動平均線、RSI、MACD、布林通道。
"""

import pandas as pd
import numpy as np


def add_moving_averages(df: pd.DataFrame, windows: list[int] = None) -> pd.DataFrame:
    """
    計算移動平均線（SMA）。

    Args:
        df: 包含 close 欄位的 DataFrame
        windows: 移動平均週期列表，預設 [5, 10, 20, 60]

    Returns:
        添加 ma_5, ma_10 等欄位後的 DataFrame
    """
    if windows is None:
        windows = [5, 10, 20, 60]

    df = df.copy()
    for window in windows:
        df[f"ma_{window}"] = df["close"].rolling(window=window, min_periods=1).mean()
    return df


def add_ema(df: pd.DataFrame, window: int = 20) -> pd.DataFrame:
    """
    計算指數移動平均線（EMA）。
    """
    df = df.copy()
    df[f"ema_{window}"] = df["close"].ewm(span=window, adjust=False).mean()
    return df


def add_rsi(df: pd.DataFrame, window: int = 14) -> pd.DataFrame:
    """
    計算相對強弱指標（RSI）。

    Args:
        df: 包含 close 欄位的 DataFrame
        window: RSI 計算週期，預設 14

    Returns:
        添加 rsi 欄位的 DataFrame
    """
    df = df.copy()
    delta = df["close"].diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)

    avg_gain = gain.rolling(window=window, min_periods=1).mean()
    avg_loss = loss.rolling(window=window, min_periods=1).mean()

    rs = avg_gain / avg_loss
    df["rsi"] = 100 - (100 / (1 + rs))
    return df


def add_macd(
    df: pd.DataFrame,
    fast: int = 12,
    slow: int = 26,
    signal: int = 9,
) -> pd.DataFrame:
    """
    計算 MACD 指標。

    Args:
        df: 包含 close 欄位的 DataFrame
        fast: 快線週期
        slow: 慢線週期
        signal: 訊號線週期

    Returns:
        添加 macd, macd_signal, macd_hist 欄位的 DataFrame
    """
    df = df.copy()
    ema_fast = df["close"].ewm(span=fast, adjust=False).mean()
    ema_slow = df["close"].ewm(span=slow, adjust=False).mean()

    df["macd"] = ema_fast - ema_slow
    df["macd_signal"] = df["macd"].ewm(span=signal, adjust=False).mean()
    df["macd_hist"] = df["macd"] - df["macd_signal"]
    return df


def add_bollinger_bands(df: pd.DataFrame, window: int = 20, num_std: float = 2.0) -> pd.DataFrame:
    """
    計算布林通道。

    Args:
        df: 包含 close 欄位的 DataFrame
        window: 計算週期
        num_std: 標準差倍數

    Returns:
        添加 bb_middle, bb_upper, bb_lower, bb_width 欄位的 DataFrame
    """
    df = df.copy()
    sma = df["close"].rolling(window=window, min_periods=1).mean()
    std = df["close"].rolling(window=window, min_periods=1).std()

    df["bb_middle"] = sma
    df["bb_upper"] = sma + (std * num_std)
    df["bb_lower"] = sma - (std * num_std)
    df["bb_width"] = df["bb_upper"] - df["bb_lower"]
    df["bb_percent"] = (df["close"] - df["bb_lower"]) / df["bb_width"]
    return df


def add_volume_moving_average(df: pd.DataFrame, window: int = 20) -> pd.DataFrame:
    """
    計算成交量移動平均線。
    """
    df = df.copy()
    df[f"volume_ma_{window}"] = df["volume"].rolling(window=window, min_periods=1).mean()
    return df


def analyze_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    一次計算所有常用技術指標。

    Args:
        df: 包含 close, volume 欄位的 DataFrame

    Returns:
        添加所有指標欄位的 DataFrame
    """
    df = df.copy()
    df = add_moving_averages(df)
    df = add_ema(df)
    df = add_rsi(df)
    df = add_macd(df)
    df = add_bollinger_bands(df)
    df = add_volume_moving_average(df)

    # 添加漲跌幅
    df["daily_return"] = df["close"].pct_change()
    df["cumulative_return"] = (1 + df["daily_return"]).cumprod() - 1
    return df


def generate_signals(df: pd.DataFrame) -> dict:
    """
    根據技術指標產生簡易買賣訊號說明。

    Returns:
        包含最新訊號的字典
    """
    latest = df.iloc[-1]
    signals = []

    # RSI 訊號
    rsi = latest.get("rsi", np.nan)
    if not pd.isna(rsi):
        if rsi > 70:
            signals.append("RSI 超買 (>70)")
        elif rsi < 30:
            signals.append("RSI 超賣 (<30)")

    # MACD 訊號
    macd = latest.get("macd", np.nan)
    macd_signal = latest.get("macd_signal", np.nan)
    if not pd.isna(macd) and not pd.isna(macd_signal):
        if macd > macd_signal:
            signals.append("MACD 黃金交叉/多頭")
        else:
            signals.append("MACD 死亡交叉/空頭")

    # 布林通道
    close = latest.get("close", np.nan)
    bb_upper = latest.get("bb_upper", np.nan)
    bb_lower = latest.get("bb_lower", np.nan)
    if not pd.isna(close) and not pd.isna(bb_upper) and not pd.isna(bb_lower):
        if close > bb_upper:
            signals.append("股價突破布林上軌")
        elif close < bb_lower:
            signals.append("股價跌破布林下軌")

    # 移動平均線
    ma20 = latest.get("ma_20", np.nan)
    ma60 = latest.get("ma_60", np.nan)
    if not pd.isna(ma20) and not pd.isna(ma60):
        if ma20 > ma60:
            signals.append("MA20 在 MA60 之上（短多）")
        else:
            signals.append("MA20 在 MA60 之下（短空）")

    return {
        "date": latest.name,
        "close": close,
        "rsi": rsi,
        "macd": macd,
        "signals": signals,
    }
