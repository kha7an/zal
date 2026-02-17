import os
from decimal import Decimal

# Zagruzka .env iz kornja proekta
_env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
if os.path.isfile(_env_path):
    with open(_env_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                v = v.strip().replace("\r", "").replace("\n", "")
                os.environ.setdefault(k.strip(), v)

def _env(key: str, default: str = "") -> str:
    v = os.environ.get(key, default).strip()
    return v.replace("\r", "").replace("\n", "")

def _env_decimal(key: str, default: str = "0") -> Decimal:
    return Decimal(_env(key, default))

BYBIT_API_KEY = _env("BYBIT_API_KEY")
BYBIT_API_SECRET = _env("BYBIT_API_SECRET")
WEBHOOK_SECRET = _env("WEBHOOK_SECRET")
BYBIT_TESTNET = _env("BYBIT_TESTNET", "false").lower() in ("1", "true", "yes")

DAILY_PROFIT_TARGET_PCT = _env_decimal("DAILY_PROFIT_TARGET_PCT", "6")
RISK_PER_TRADE_PCT = _env_decimal("RISK_PER_TRADE_PCT", "30")
MAX_TRADES_PER_DAY = int(os.environ.get("MAX_TRADES_PER_DAY", "10") or "10")
MAX_OPEN_POSITIONS = int(os.environ.get("MAX_OPEN_POSITIONS", "2") or "2")
CATEGORY = "linear"

# Trend Meter NR
SYMBOL = _env("SYMBOL", "BTCUSDT")
TIMEFRAME = _env("TIMEFRAME", "D")

# Ordera: SL na birzhe ne stavim; STOP_LOSS_PCT — tol'ko dlja rascheta razmera qty
STOP_LOSS_PCT = _env_decimal("STOP_LOSS_PCT", "2")
LEVERAGE = int(os.environ.get("LEVERAGE", "10") or "10")
