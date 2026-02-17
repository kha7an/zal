"""
Проверка работы индикатора и логики решений на реальных дневных свечах Bybit (BTCUSDT).
Запуск: python -m bybit_bot.check_signal
"""
import urllib.request
import json
import pandas as pd
from datetime import datetime

from bybit_bot.config import SYMBOL, TIMEFRAME
from bybit_bot.indicator import trend_meter_nr
from bybit_bot.signals import last_two_signals, decide_action


def replay_trades(res: pd.DataFrame) -> pd.DataFrame:
    """Po baram: signal, action, position posle. Pri close — sledujushhee dejstvie mozhet byt' open v protivopolozhnuju storonu."""
    signals = res["signal"].astype(int)
    dates = res["date"]
    close = res["close"]
    position = None
    rows = []
    for i in range(len(res)):
        signal_now = int(signals.iloc[i])
        signal_prev = int(signals.iloc[i - 1]) if i > 0 else 0
        action = decide_action(signal_now, signal_prev, position)
        if action == "close_long":
            position = None
            next_action = decide_action(signal_now, signal_prev, None)
            if next_action == "open_short":
                position = "short"
                action = "close_long -> open_short"
            else:
                action = "close_long"
        elif action == "close_short":
            position = None
            next_action = decide_action(signal_now, signal_prev, None)
            if next_action == "open_long":
                position = "long"
                action = "close_short -> open_long"
            else:
                action = "close_short"
        elif action == "open_long":
            position = "long"
        elif action == "open_short":
            position = "short"
        rows.append({
            "date": dates.iloc[i],
            "close": close.iloc[i],
            "signal": signal_now,
            "action": action,
            "position_after": position if position else "flat",
        })
    return pd.DataFrame(rows)


BYBIT_KLINE = "https://api.bybit.com/v5/market/kline"


def fetch_klines(symbol: str = "BTCUSDT", interval: str = "D", limit: int = 200) -> pd.DataFrame:
    url = f"{BYBIT_KLINE}?category=linear&symbol={symbol}&interval={interval}&limit={limit}"
    with urllib.request.urlopen(url, timeout=15) as r:
        data = json.loads(r.read().decode())
    if data.get("retCode") != 0:
        raise RuntimeError(data.get("retMessage", "Bybit API error"))
    rows = data["result"]["list"]
    # Bybit: [startTime, open, high, low, close, volume, turnover], newest first
    df = pd.DataFrame(
        rows,
        columns=["startTime", "open", "high", "low", "close", "volume", "turnover"],
    )
    df = df.astype({"open": float, "high": float, "low": float, "close": float})
    df = df.sort_values("startTime").reset_index(drop=True)
    df["date"] = pd.to_datetime(df["startTime"].astype(int), unit="ms")
    return df[["open", "high", "low", "close", "date"]]


def main():
    print(f"Загрузка {SYMBOL} {TIMEFRAME} с Bybit...")
    df = fetch_klines(SYMBOL, TIMEFRAME)
    print(f"Свечей: {len(df)}, период: {df['date'].iloc[0].date()} — {df['date'].iloc[-1].date()}\n")

    res = trend_meter_nr(df)
    prev, now = last_two_signals(res["signal"])
    action_none = decide_action(now, prev, None)
    action_long = decide_action(now, prev, "long")
    action_short = decide_action(now, prev, "short")

    signal_label = {1: "Trend All Up", -1: "Trend All Down", 0: "no"}
    print("Последние 5 свечей (индикатор):")
    print("-" * 70)
    tail = res.tail(5)[["date", "close", "TrendBar1Confirmed", "TrendBar2Confirmed", "TrendBar3Confirmed", "signal"]]
    tail["signal_txt"] = tail["signal"].map(signal_label)
    for _, row in tail.iterrows():
        print(
            f"  {row['date'].strftime('%Y-%m-%d')}  close={row['close']:.0f}  "
            f"TB1={row['TrendBar1Confirmed']:>2}  TB2={row['TrendBar2Confirmed']:>2}  TB3={row['TrendBar3Confirmed']:>2}  "
            f"-> {row['signal_txt']}"
        )
    print("-" * 70)
    print(f"  signal_prev={prev}, signal_now={now}  ({signal_label.get(now, now)})")
    print()

    # Kogda kakie signaly byli (vse svechi gde signal != 0)
    with_signal = res[res["signal"] != 0].copy()
    with_signal["signal_txt"] = with_signal["signal"].map(signal_label)
    print("Istorija signalov (vse svechi Trend All Up / Trend All Down):")
    print("-" * 70)
    if with_signal.empty:
        print("  Net svechej s polnym signalom.")
    else:
        for _, row in with_signal.iterrows():
            print(f"  {row['date'].strftime('%Y-%m-%d')}  close={row['close']:.0f}  -> {row['signal_txt']}")
        up_count = (with_signal["signal"] == 1).sum()
        down_count = (with_signal["signal"] == -1).sum()
        print("-" * 70)
        print(f"  Trend All Up:   {up_count} svechej")
        print(f"  Trend All Down: {down_count} svechej")
    print()

    # Replay: chto i kak bylo by (po dnjam)
    replay = replay_trades(res)
    replay["date_str"] = replay["date"].dt.strftime("%Y-%m-%d")
    signal_txt = {1: "Up", -1: "Down", 0: "no"}
    replay["signal_txt"] = replay["signal"].map(signal_txt)
    # Slice 2026-01-06 .. 2026-02-12 (period kotoryj ty pokazal)
    mask = (replay["date_str"] >= "2026-01-06") & (replay["date_str"] <= "2026-02-12")
    slice_replay = replay.loc[mask]
    print("Replay 2026-01-06 .. 2026-02-12 (chto i kak bylo by):")
    print("-" * 70)
    for _, row in slice_replay.iterrows():
        print(f"  {row['date_str']}  close={row['close']:.0f}  signal={row['signal_txt']:3}  action={str(row['action']):25}  posle={row['position_after']}")
    print("-" * 70)
    print()

    print("Reshenija:")
    print(f"  Net pozicii  -> {action_none}")
    print(f"  V longe     -> {action_long}")
    print(f"  V shorte     -> {action_short}")
    print()
    last_date = res["date"].iloc[-1].strftime("%Y-%m-%d")
    print(f"Последняя свеча: {last_date}. Запуск в течение дня использует закрытую дневную свечу (no repaint).")


if __name__ == "__main__":
    main()
