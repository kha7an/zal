"""
Boevoj zapusk: signal -> dejstvie -> realnyj order na Bybit.
Zapusk: python -m bybit_bot.run_live
"""
import urllib.request
import json
import pandas as pd

from bybit_bot import config
from bybit_bot.indicator import trend_meter_nr
from bybit_bot.signals import last_two_signals, decide_action
from bybit_bot.bybit_client import (
    get_wallet_balance,
    get_instrument_info,
    get_last_price,
    get_position_size,
    set_leverage,
    open_long,
    open_short,
    close_current_position,
)
from pybit.unified_trading import HTTP

from bybit_bot.log_helper import log

DIRECT_API_KEY = ""
DIRECT_API_SECRET = ""

BYBIT_KLINE = "https://api.bybit.com/v5/market/kline"


def fetch_klines(symbol: str, interval: str, limit: int = 200) -> pd.DataFrame:
    url = f"{BYBIT_KLINE}?category=linear&symbol={symbol}&interval={interval}&limit={limit}"
    with urllib.request.urlopen(url, timeout=15) as r:
        data = json.loads(r.read().decode())
    if data.get("retCode") != 0:
        raise RuntimeError(data.get("retMessage", "Bybit API error"))
    rows = data["result"]["list"]
    df = pd.DataFrame(
        rows,
        columns=["startTime", "open", "high", "low", "close", "volume", "turnover"],
    )
    df = df.astype({"open": float, "high": float, "low": float, "close": float})
    df = df.sort_values("startTime").reset_index(drop=True)
    df["date"] = pd.to_datetime(df["startTime"].astype(int), unit="ms")
    return df[["open", "high", "low", "close", "date"]]


def main():
    log("LIVE: signal -> reshenie -> order na Bybit")
    api_key = (DIRECT_API_KEY or "").strip() or (config.BYBIT_API_KEY or "")
    api_secret = (DIRECT_API_SECRET or "").strip() or (config.BYBIT_API_SECRET or "")
    if not api_key or not api_secret:
        log("BYBIT_API_KEY/BYBIT_API_SECRET ne zadany v .env")
        return
    session = HTTP(
        testnet=config.BYBIT_TESTNET,
        api_key=api_key,
        api_secret=api_secret,
        recv_window=20000,
    )
    mode = "TESTNET" if config.BYBIT_TESTNET else "REAL (mainnet)"
    log(f"Bybit: {mode}")
    log("")

    df = fetch_klines(config.SYMBOL, config.TIMEFRAME)
    res = trend_meter_nr(df)
    prev, now = last_two_signals(res["signal"])
    try:
        pos = get_position_size(session)
        balance = get_wallet_balance(session)
        price = get_last_price(session)
    except Exception as e:
        log(f"Oshibka Bybit: {e}")
        return

    position_side = "long" if pos and pos[0] == "Buy" else "short" if pos else None
    action = decide_action(now, prev, position_side)

    log(f"Signal: prev={prev}, now={now}")
    log(f"Pozicija na birzhe: {position_side or 'net'}")
    log(f"Reshenie: {action}")
    log(f"Balans: {balance:.2f} USDT, cena: {price}")
    log("")

    if action == "open_long":
        log("Dejstvie: otkryt LONG (market). Ustanavlivaem leverage i schitaem razmer pozicii...")
        try:
            set_leverage(session, config.LEVERAGE)
        except Exception as e:
            if "110043" not in str(e):
                raise
            log("Leverage uzhe vystavlen, prodolzhaem.")
        r = open_long(session)
        ret_code = r.get("retCode")
        ret_msg = r.get("retMsg", r)
        log(f"Rezultat otkrytija LONG: retCode={ret_code}, retMsg={ret_msg}")
        if ret_code == 0:
            log("  orderId: " + str(r.get("result", {}).get("orderId")))
        else:
            log("  Order NE sozdan (prover' retMsg, balans/marzhu/minOrderQty).")
    elif action == "open_short":
        log("Dejstvie: otkryt SHORT (market). Ustanavlivaem leverage i schitaem razmer pozicii...")
        try:
            set_leverage(session, config.LEVERAGE)
        except Exception as e:
            if "110043" not in str(e):
                raise
            log("Leverage uzhe vystavlen, prodolzhaem.")
        r = open_short(session)
        ret_code = r.get("retCode")
        ret_msg = r.get("retMsg", r)
        log(f"Rezultat otkrytija SHORT: retCode={ret_code}, retMsg={ret_msg}")
        if ret_code == 0:
            log("  orderId: " + str(r.get("result", {}).get("orderId")))
        else:
            log("  Order NE sozdan (prover' retMsg, balans/marzhu/minOrderQty).")
    elif action in ("close_long", "close_short"):
        log("Dejstvie: zakryt tekushhuju poziciju (market, reduceOnly)...")
        r = close_current_position(session)
        if r:
            ret_code = r.get("retCode")
            ret_msg = r.get("retMsg", r)
            log(f"Rezultat zakrytija: retCode={ret_code}, retMsg={ret_msg}")
            if ret_code == 0:
                log("  orderId: " + str(r.get("result", {}).get("orderId")))
        else:
            log("Zakryvat' nechego: pozicii ne bylo.")
    else:
        reason = ""
        if position_side is None:
            if now == 0:
                reason = "net polnogo signala (signal=0)"
            else:
                reason = f"signal={now}, pozicii net — reshenie hold po logike decide_action"
        elif position_side == "long" and now == 1:
            reason = "est LONG i signal=1 — derzhim po trendu"
        elif position_side == "short" and now == -1:
            reason = "est SHORT i signal=-1 — derzhim po trendu"
        else:
            reason = f"pozicija={position_side}, signal={now} — reshenie hold po logike decide_action"
        log(f"Hold — order NE otpravlen, prichina: {reason}.")


if __name__ == "__main__":
    main()
