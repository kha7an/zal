"""
Логика открытия и закрытия по сигналу Trend Meter NR.
Держим позицию только пока есть полный сигнал (1 или -1).
Закрываем сразу, как только сигнала нет (0) — не ждём противоположного.
"""
from typing import Literal

Action = Literal["open_long", "open_short", "close_long", "close_short", "hold"]
PositionSide = Literal["long", "short", None]


def decide_action(
    signal_now: int,
    signal_prev: int,
    position_side: PositionSide,
) -> Action:
    """
    signal: 1 = Up, -1 = Down, 0 = net. Pri 0 zakryvaem srazu, ne zhdjom.
    """
    if position_side == "long":
        if signal_now == 1:
            return "hold"
        return "close_long"  # 0 ili -1 — zakryt' srazu

    if position_side == "short":
        if signal_now == -1:
            return "hold"
        return "close_short"  # 0 ili 1 — zakryt' srazu

    # position_side is None
    # Esli pozicii net, a signal polnyj (1 ili -1) — otkryvaem, nezavisimo ot predydushhego.
    if signal_now == 1:
        return "open_long"
    if signal_now == -1:
        return "open_short"
    return "hold"


def last_two_signals(signal_series) -> tuple[int, int]:
    """signal_series — колонка signal из trend_meter_nr (или список). Возвращает (prev, now)."""
    n = len(signal_series)
    if n == 0:
        return (0, 0)
    now = int(signal_series.iloc[-1] if hasattr(signal_series, "iloc") else signal_series[-1])
    if n < 2:
        return (0, now)
    prev = int(signal_series.iloc[-2] if hasattr(signal_series, "iloc") else signal_series[-2])
    return (prev, now)
