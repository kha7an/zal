"""
Zapis v fajl bybit_bot.log v korne proekta + vyvod v konsol.
Posle perezahoda na server: tail -f bybit_bot.log ili cat bybit_bot.log
"""
import os
import logging

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_FILE = os.path.join(_PROJECT_ROOT, "bybit_bot.log")

_logger = None


def _setup():
    global _logger
    if _logger is not None:
        return _logger
    _logger = logging.getLogger("bybit_bot")
    _logger.setLevel(logging.INFO)
    if _logger.handlers:
        return _logger
    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
    fh = logging.FileHandler(LOG_FILE, encoding="utf-8", mode="a")
    fh.setFormatter(fmt)
    _logger.addHandler(fh)
    ch = logging.StreamHandler()
    ch.setFormatter(fmt)
    _logger.addHandler(ch)
    return _logger


def log(msg: str) -> None:
    _setup().info(msg)
