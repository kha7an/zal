"""
Proverka signala kazhdyj den v 03:00 MSK (zakrytie dnevnoj svechi Bybit D = 00:00 UTC).
Zapusk: python -m bybit_bot.run_loop   (ostanovka: Ctrl+C)
"""
import time
from datetime import datetime, timedelta

try:
    from zoneinfo import ZoneInfo
except ImportError:
    from backports.zoneinfo import ZoneInfo

from bybit_bot.run_live import main as run_live_main
from bybit_bot.log_helper import log

MSK = ZoneInfo("Europe/Moscow")

# D-svecha na Bybit zakryvaetsja v 00:00 UTC = 03:00 MSK
CHECK_HOUR_MSK = 3
CHECK_MINUTE_MSK = 0


def next_run_msk():
    now = datetime.now(MSK)
    today_run = now.replace(hour=CHECK_HOUR_MSK, minute=CHECK_MINUTE_MSK, second=0, microsecond=0)
    if now <= today_run:
        return today_run
    return today_run + timedelta(days=1)


def main():
    log("Proverka signala: kazhdyj den v 03:00 MSK (posle zakrytija D-svechi 00:00 UTC)")
    log("Ostanovka: Ctrl+C")
    log("")
    while True:
        try:
            next_run = next_run_msk()
            now_msk = datetime.now(MSK)
            sec_to = (next_run - now_msk).total_seconds()
            if sec_to > 60:
                log(f"Sled. proverka: {next_run.strftime('%Y-%m-%d %H:%M:%S')} MSK cherez {int(sec_to // 3600)} ch {int((sec_to % 3600) // 60)} min")
                # Spim kuskami, no ne prouskaja okno <= 60 sek do zapuska
                sleep_sec = max(0, min(3600, sec_to - 60))
                time.sleep(sleep_sec)
                continue
            log("--- " + datetime.now(MSK).strftime("%Y-%m-%d %H:%M:%S MSK") + " ---")
            run_live_main()
        except KeyboardInterrupt:
            log("Ostanovleno.")
            break
        except Exception as e:
            log("Oshibka: " + str(e))
        log("")


if __name__ == "__main__":
    main()
