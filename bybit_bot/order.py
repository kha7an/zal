"""
Otkrytie/zakrytie pozicij na Bybit: tol'ko market-order, bez SL/TP na birzhe.
Razmer pozicii — po risk % ot balansa i virtual'nomu rasstojaniju do SL (dlja rascheta qty).
"""
from decimal import Decimal

from bybit_bot import config
from bybit_bot.risk import position_size_qty


def _sl_price_for_size(entry: Decimal, side: str) -> Decimal:
    """Virtual'naja cena SL dlja rascheta qty (na birzhe SL/TP ne stavim)."""
    pct = config.STOP_LOSS_PCT / Decimal("100")
    if side == "Buy":
        return entry * (1 - pct)
    return entry * (1 + pct)


def prepare_open_order(
    balance_usdt: Decimal,
    entry_price: Decimal,
    qty_step: Decimal,
    side: str,
) -> dict:
    """Vozvraschaet dict s qty (stopLoss/takeProfit ne peredaem v API)."""
    sl_price = _sl_price_for_size(entry_price, side)
    qty = position_size_qty(
        balance=balance_usdt,
        risk_pct=config.RISK_PER_TRADE_PCT,
        entry_price=entry_price,
        stop_loss_price=sl_price,
        qty_step=qty_step,
    )
    return {"qty": str(round(qty, 8))}


def place_open_order(session, side: str, params: dict) -> dict:
    """Market-order bez SL/TP."""
    return session.place_order(
        category=config.CATEGORY,
        symbol=config.SYMBOL,
        orderType="Market",
        side=side,
        qty=params["qty"],
        positionIdx=0,
    )


def close_position(session, side: str, qty: str) -> dict:
    """Zakrytie pozicii: market order reduceOnly. side — protivopolozhnyj (Sell dlja long)."""
    close_side = "Sell" if side == "Buy" else "Buy"
    return session.place_order(
        category=config.CATEGORY,
        symbol=config.SYMBOL,
        orderType="Market",
        side=close_side,
        qty=qty,
        reduceOnly=True,
        positionIdx=0,
    )
