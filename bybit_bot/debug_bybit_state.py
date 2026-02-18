"""
Diagnostika sostojanija na Bybit po tem zhe kljucham:
- pokazat' balans, pozicii, poslednie ordery po BTCUSDT (linear)

Zapusk na servere:
  cd /opt/zal
  source .venv/bin/activate
  python -m bybit_bot.debug_bybit_state
"""

from bybit_bot import config
from pybit.unified_trading import HTTP


def main():
    api_key = (config.BYBIT_API_KEY or "").strip()
    api_secret = (config.BYBIT_API_SECRET or "").strip()
    if not api_key or not api_secret:
        print("BYBIT_API_KEY/BYBIT_API_SECRET ne zadany v .env")
        return

    session = HTTP(
        testnet=config.BYBIT_TESTNET,
        api_key=api_key,
        api_secret=api_secret,
        recv_window=20000,
    )
    mode = "TESTNET" if config.BYBIT_TESTNET else "REAL (mainnet)"
    print(f"Bybit mode: {mode}")
    print(f"SYMBOL={config.SYMBOL}, CATEGORY={config.CATEGORY}")
    print()

    # Balans i pozicii
    try:
        w = session.get_wallet_balance(accountType="UNIFIED")
        print("get_wallet_balance(UNIFIED): retCode=", w.get("retCode"))
        if w.get("retCode") == 0:
            print("  raw:", w.get("result"))
    except Exception as e:
        print("Oshibka get_wallet_balance:", e)
    print()

    try:
        p = session.get_positions(category=config.CATEGORY, symbol=config.SYMBOL)
        print("get_positions:", "retCode=", p.get("retCode"))
        if p.get("retCode") == 0:
            print("  list:")
            for item in p.get("result", {}).get("list", []):
                print("   ", item)
    except Exception as e:
        print("Oshibka get_positions:", e)
    print()

    # Order history po etomu instrumentu
    try:
        oh = session.get_order_history(category=config.CATEGORY, symbol=config.SYMBOL, limit=20)
        print("get_order_history (poslednie 20): retCode=", oh.get("retCode"))
        if oh.get("retCode") == 0:
            print("  list (orderId, symbol, side, qty, status, createdTime):")
            for item in oh.get("result", {}).get("list", []):
                print(
                    "   ",
                    item.get("orderId"),
                    item.get("symbol"),
                    item.get("side"),
                    item.get("qty"),
                    item.get("orderStatus"),
                    item.get("createdTime"),
                )
    except Exception as e:
        print("Oshibka get_order_history:", e)


if __name__ == "__main__":
    main()

