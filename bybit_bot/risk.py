from decimal import Decimal


def position_size_qty(
    balance: Decimal,
    risk_pct: Decimal,
    entry_price: Decimal,
    stop_loss_price: Decimal,
    qty_step: Decimal,
) -> Decimal:
    risk_amount = balance * (risk_pct / Decimal("100"))
    if entry_price <= 0 or risk_amount <= 0:
        return Decimal("0")
    distance = abs(entry_price - stop_loss_price)
    if distance <= 0:
        return Decimal("0")
    qty = risk_amount / distance
    if qty_step > 0:
        steps = int(float(qty / qty_step))
        qty = Decimal(str(steps * float(qty_step)))
    return max(Decimal("0"), qty)
