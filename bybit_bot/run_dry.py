"""
Proverochnyj zapusk: signal, pozicija na Bybit, dejstvie i parametry ordara BEZ otpravki.
Zapusk: python -m bybit_bot.run_dry
"""
import urllib.request
import json
import time
import pandas as pd

from bybit_bot import config
from bybit_bot.indicator import trend_meter_nr
from bybit_bot.signals import last_two_signals, decide_action
from bybit_bot.bybit_client import (
    client,
    get_wallet_balance,
    get_instrument_info,
    get_last_price,
    get_position_size,
)
from pybit.unified_trading import HTTP

# Kljuchi naprjamuju (dlja proverki): zapolni i zapusti — budet ispolzovano vmesto .env
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
    print("Proverochnyj zapusk (ordera NE otpravljajutsja)...")
    # Real (mainnet) po umolchaniju; testnet tol'ko esli BYBIT_TESTNET=true v .env
    url = "https://api-testnet.bybit.com" if config.BYBIT_TESTNET else "https://api.bybit.com"
    mode = "TESTNET" if config.BYBIT_TESTNET else "REAL (mainnet)"
    print(f"Bybit URL: {url}  -> {mode}")
    api_key = (DIRECT_API_KEY or "").strip() or (config.BYBIT_API_KEY or "")
    api_secret = (DIRECT_API_SECRET or "").strip() or (config.BYBIT_API_SECRET or "")
    print(f"API key: {'zadan (' + str(len(api_key)) + ' simv)' if api_key else 'NET'}")
    print(f"API secret: {'zadan (' + str(len(api_secret)) + ' simv)' if api_secret else 'NET'}")
    print()

    # Klines + indikator
    df = fetch_klines(config.SYMBOL, config.TIMEFRAME)
    res = trend_meter_nr(df)
    prev, now = last_two_signals(res["signal"])
    signal_txt = {1: "Trend All Up", -1: "Trend All Down", 0: "no"}
    print(f"Signal: prev={prev}, now={now}  ({signal_txt.get(now, now)})")
    print()

    # Bybit: proverka raznyh zaprosov
    if (DIRECT_API_KEY or "").strip() or (DIRECT_API_SECRET or "").strip():
        print("Ispolzuem kljuchi iz run_dry (DIRECT_*)")
    if not api_key or not api_secret:
        print("BYBIT_API_KEY/BYBIT_API_SECRET ne zadany v .env i DIRECT_* pusty")
        return
    session = HTTP(
        testnet=config.BYBIT_TESTNET,
        api_key=api_key,
        api_secret=api_secret,
        recv_window=20000,
    )
    try:
        price = get_last_price(session)
        info = get_instrument_info(session)
        r = session.get_server_time()
        server_sec = int(r["result"]["timeSecond"])
        local_sec = int(time.time())
        diff_sec = abs(server_sec - local_sec)
        print(f"Vremja: server Bybit={server_sec}, lokalnoe={local_sec}, raznica={diff_sec} sek")
        if diff_sec > 5:
            print("  VNIMANIE: raznica > 5 sek — sinhroniziruj vremja v Windows (Settings -> Time -> Sync now)")
    except Exception as e:
        print(f"Oshibka (publichnye): {e}")
        return
    print("Publichnye zaprosy (cena, instrument): OK")
    tests = [
        ("get_api_key_information", lambda: session.get_api_key_information()),
        ("get_uid_wallet_type", lambda: session.get_uid_wallet_type()),
        ("get_account_info", lambda: session.get_account_info()),
        ("get_wallet_balance(UNIFIED)", lambda: session.get_wallet_balance(accountType="UNIFIED")),
        ("get_positions(linear)", lambda: session.get_positions(category="linear", symbol=config.SYMBOL)),
        ("get_coin_balance(UNIFIED)", lambda: session.get_coins_balance(accountType="UNIFIED")),
    ]
    for name, fn in tests:
        try:
            r = fn()
            code = r.get("retCode", "?")
            print(f"  {name}: OK (retCode={code})")
        except Exception as e:
            msg = str(e).replace("\u2192", "->")
            err = "ErrCode: 10003" in msg or "10003" in msg or "401" in msg
            print(f"  {name}: FAIL - {msg[:80]}{'...' if len(msg) > 80 else ''}")
    ok = False
    try:
        pos = get_position_size(session)
        balance = get_wallet_balance(session)
        ok = True
    except Exception as e:
        msg = str(e).replace("\u2192", "->")
        print(f"Oshibka (pozicija/balans): {msg}")
    if not ok:
        return

    position_side = None
    if pos:
        position_side = "long" if pos[0] == "Buy" else "short"
        print(f"Pozicija na birzhe: {position_side}, size={pos[1]}")
    else:
        print("Pozicija na birzhe: net")
    print(f"Balans USDT: {balance:.2f}, cena {config.SYMBOL}: {price}")
    print()

    action = decide_action(now, prev, position_side)
    print(f"Reshenie: {action}")
    print()

    if action == "open_long":
        from bybit_bot.order import prepare_open_order
        params = prepare_open_order(balance, price, info["qty_step"], "Buy")
        print("DRY RUN: otkrylos by LONG")
        print(f"  side=Buy  qty={params['qty']}  (ordera ne otpravlen)")
    elif action == "open_short":
        from bybit_bot.order import prepare_open_order
        params = prepare_open_order(balance, price, info["qty_step"], "Sell")
        print("DRY RUN: otkrylos by SHORT")
        print(f"  side=Sell  qty={params['qty']}  (ordera ne otpravlen)")
    elif action in ("close_long", "close_short"):
        print("DRY RUN: zakrylos by pozicija (ordera ne otpravlen)")
    else:
        print("Hold — nichego ne delaem.")

    print()
    print("Eto byl proverochnyj rezhim (ordera NE otpravleny).")
    print("Boevoj zapusk (otpravka orderov):")
    print("  - razovo:     python -m bybit_bot.run_live")
    print("  - kazhdyj den v 03:00 MSK: python -m bybit_bot.run_loop")


if __name__ == "__main__":
    main()
