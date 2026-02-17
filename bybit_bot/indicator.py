"""
Trend Meter NR (No Repaint) — порт с Pine v4.
Исходник: study(title="Trend Meter (No Repaint)", shorttitle="Trend Meter NR", overlay=false)
WaveTrend n1=9, n2=12; MA 5/11, 13/36; RSI 5, level 50. Подтверждение по [1] и [2] (no repaint).
"""
import numpy as np
import pandas as pd


def _ema(series: pd.Series, length: int) -> pd.Series:
    return series.ewm(span=length, adjust=False).mean()


def _sma(series: pd.Series, length: int) -> pd.Series:
    return series.rolling(window=length).mean()


def _rsi(close: pd.Series, length: int) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = (-delta).clip(lower=0)
    avg_gain = gain.ewm(span=length, adjust=False).mean()
    avg_loss = loss.ewm(span=length, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def trend_meter_nr(df: pd.DataFrame) -> pd.DataFrame:
    """
    df: OHLC с колонками open, high, low, close (и опционально timestamp).
    Возвращает тот же DataFrame с колонками signal, TrendBar1Confirmed, TrendBar2Confirmed, TrendBar3Confirmed.
    signal: 1 = Trend All Up, -1 = Trend All Down, 0 = нет полного совпадения.
    """
    high = df["high"].astype(float)
    low = df["low"].astype(float)
    close = df["close"].astype(float)
    ap = (high + low + close) / 3.0

    n1, n2 = 9, 12
    esa = _ema(ap, n1)
    de = _ema((ap - esa).abs(), n1)
    ci = (ap - esa) / (0.015 * de.replace(0, np.nan))
    tci = _ema(ci, n2)
    wt1 = tci
    wt2 = _sma(wt1, 3)

    ma1 = _ema(close, 5)
    ma2 = _ema(close, 11)
    ma3 = _ema(close, 13)
    ma4 = _sma(close, 36)

    wt1_prev1 = wt1.shift(1)
    wt1_prev2 = wt1.shift(2)
    wt2_prev1 = wt2.shift(1)
    wt2_prev2 = wt2.shift(2)
    WTCrossUpConfirmed = (wt1_prev1 > wt2_prev1) & (wt1_prev2 <= wt2_prev2)
    WTCrossDownConfirmed = (wt1_prev1 < wt2_prev1) & (wt1_prev2 >= wt2_prev2)

    ma1_1, ma1_2 = ma1.shift(1), ma1.shift(2)
    ma2_1, ma2_2 = ma2.shift(1), ma2.shift(2)
    TB1CrossUpConfirmed = (ma1_1 > ma2_1) & (ma1_2 <= ma2_2)
    TB1CrossDownConfirmed = (ma1_1 < ma2_1) & (ma1_2 >= ma2_2)

    ma3_1, ma3_2 = ma3.shift(1), ma3.shift(2)
    ma4_1, ma4_2 = ma4.shift(1), ma4.shift(2)
    TB2CrossUpConfirmed = (ma3_1 > ma4_1) & (ma3_2 <= ma4_2)
    TB2CrossDownConfirmed = (ma3_1 < ma4_1) & (ma3_2 >= ma4_2)

    RSI5 = _rsi(close, 5)
    TrendBar3Confirmed = np.where(RSI5 > 50, 1, -1)

    TrendBar1Confirmed = np.zeros(len(df), dtype=int)
    TrendBar2Confirmed = np.zeros(len(df), dtype=int)
    for i in range(1, len(df)):
        if TB1CrossUpConfirmed.iloc[i]:
            TrendBar1Confirmed[i] = 1
        elif TB1CrossDownConfirmed.iloc[i]:
            TrendBar1Confirmed[i] = -1
        else:
            TrendBar1Confirmed[i] = TrendBar1Confirmed[i - 1] if TrendBar1Confirmed[i - 1] != 0 else 0
        if TB2CrossUpConfirmed.iloc[i]:
            TrendBar2Confirmed[i] = 1
        elif TB2CrossDownConfirmed.iloc[i]:
            TrendBar2Confirmed[i] = -1
        else:
            TrendBar2Confirmed[i] = TrendBar2Confirmed[i - 1] if TrendBar2Confirmed[i - 1] != 0 else 0

    TrendAllUpConfirmed = (TrendBar1Confirmed == 1) & (TrendBar2Confirmed == 1) & (TrendBar3Confirmed == 1)
    TrendAllDownConfirmed = (TrendBar1Confirmed == -1) & (TrendBar2Confirmed == -1) & (TrendBar3Confirmed == -1)
    signal = np.where(TrendAllUpConfirmed, 1, np.where(TrendAllDownConfirmed, -1, 0))

    out = df.copy()
    out["TrendBar1Confirmed"] = TrendBar1Confirmed
    out["TrendBar2Confirmed"] = TrendBar2Confirmed
    out["TrendBar3Confirmed"] = TrendBar3Confirmed
    out["signal"] = signal
    out["WTCrossUpConfirmed"] = WTCrossUpConfirmed
    out["WTCrossDownConfirmed"] = WTCrossDownConfirmed
    return out


def last_signal(df: pd.DataFrame) -> int:
    """Последний сигнал: 1 = long, -1 = short, 0 = нет сигнала. df — OHLC (open, high, low, close)."""
    if df.empty:
        return 0
    res = trend_meter_nr(df)
    return int(res["signal"].iloc[-1])
