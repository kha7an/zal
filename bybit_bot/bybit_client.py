"""
Klient Bybit: balans, instrument, cena, leverage, vyzov order.py dlja otkrytija/zakrytija.
"""
from decimal import Decimal

from pybit.unified_trading import HTTP

from bybit_bot import config
from bybit_bot.order import prepare_open_order, place_open_order, close_position


def client() -> HTTP:
    return HTTP(
        testnet=config.BYBIT_TESTNET,
        api_key=config.BYBIT_API_KEY,
        api_secret=config.BYBIT_API_SECRET,
        recv_window=20000,
    )


def get_wallet_balance(session: HTTP) -> Decimal:
    """Balans USDT (equity) dlja linear — accountType UNIFIED."""
    r = session.get_wallet_balance(accountType="UNIFIED")
    if r["retCode"] != 0:
        raise RuntimeError(r.get("retMsg", "Bybit API error"))
    for coin in r["result"]["list"][0].get("coin", []):
        if coin["coin"] == "USDT":
            return Decimal(coin.get("equity", "0") or "0")
    return Decimal("0")


def get_instrument_info(session: HTTP) -> dict:
    """Lot size (qty step, min order qty) i tick size."""
    r = session.get_instruments_info(category=config.CATEGORY, symbol=config.SYMBOL)
    if r["retCode"] != 0 or not r["result"]["list"]:
        raise RuntimeError("Instrument not found")
    f = r["result"]["list"][0].get("lotSizeFilter", {})
    return {
        "qty_step": Decimal(f.get("qtyStep", "0.001")),
        "min_order_qty": Decimal(f.get("minOrderQty", "0.001")),
    }


def get_last_price(session: HTTP) -> Decimal:
    """Poslednjaja cena (dlja vhoda i rascheta SL/TP)."""
    r = session.get_tickers(category=config.CATEGORY, symbol=config.SYMBOL)
    if r["retCode"] != 0 or not r["result"]["list"]:
        raise RuntimeError("Ticker not found")
    return Decimal(r["result"]["list"][0]["lastPrice"])


def set_leverage(session: HTTP, leverage: int) -> dict:
    return session.set_leverage(category=config.CATEGORY, symbol=config.SYMBOL, buyLeverage=str(leverage), sellLeverage=str(leverage))


def _cap_qty_by_margin(qty: Decimal, entry: Decimal, balance: Decimal, leverage: int, qty_step: Decimal) -> Decimal:
    """Umen'shaem qty, esli margin prevyshaet 95% balansa."""
    margin_need = qty * entry / leverage
    if margin_need <= balance * Decimal("0.95"):
        return qty
    max_qty = balance * Decimal("0.95") * leverage / entry
    if qty_step > 0:
        steps = int(float(max_qty / qty_step))
        max_qty = Decimal(str(steps * float(qty_step)))
    return min(qty, max(max_qty, Decimal("0")))


def open_long(session: HTTP) -> dict:
    """Otkryt long: balans -> qty po risku, s ogranicheniem po marzhe."""
    balance = get_wallet_balance(session)
    entry = get_last_price(session)
    info = get_instrument_info(session)
    params = prepare_open_order(balance, entry, info["qty_step"], "Buy")
    qty = Decimal(params["qty"])
    qty = _cap_qty_by_margin(qty, entry, balance, config.LEVERAGE, info["qty_step"])
    params["qty"] = str(round(qty, 8))
    if qty < info["min_order_qty"]:
        return {"retCode": -1, "retMsg": "qty < minOrderQty (ili nedostatochno margin)"}
    return place_open_order(session, "Buy", params)


def open_short(session: HTTP) -> dict:
    """Otkryt short: to zhe, s ogranicheniem po marzhe."""
    balance = get_wallet_balance(session)
    entry = get_last_price(session)
    info = get_instrument_info(session)
    params = prepare_open_order(balance, entry, info["qty_step"], "Sell")
    qty = Decimal(params["qty"])
    qty = _cap_qty_by_margin(qty, entry, balance, config.LEVERAGE, info["qty_step"])
    params["qty"] = str(round(qty, 8))
    if qty < info["min_order_qty"]:
        return {"retCode": -1, "retMsg": "qty < minOrderQty (ili nedostatochno margin)"}
    return place_open_order(session, "Sell", params)


def get_position_size(session: HTTP) -> tuple[str, str] | None:
    """(side, size) tekushhej pozicii po simvolu ili None."""
    r = session.get_positions(category=config.CATEGORY, symbol=config.SYMBOL)
    if r["retCode"] != 0:
        raise RuntimeError(r.get("retMsg", "Bybit API error"))
    for p in r["result"]["list"]:
        size = Decimal(p.get("size", "0") or "0")
        if size > 0:
            side = "Buy" if p.get("side") == "Buy" else "Sell"
            return (side, str(size))
    return None


def close_current_position(session: HTTP) -> dict | None:
    """Zakryt tekushhuju poziciju marketom. None esli pozicii net."""
    pos = get_position_size(session)
    if not pos:
        return None
    side, qty = pos
    return close_position(session, side, qty)
