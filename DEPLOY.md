# Zapusk na servere (postoanno)

## 1. Katalog i venv

```bash
cd /opt/zal
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 2. Fajl .env

```bash
cp .env.example .env
nano .env
```

Zapolni:
- `BYBIT_API_KEY` — kljuch s Bybit
- `BYBIT_API_SECRET` — secret s Bybit
- `BYBIT_TESTNET=false` dlja mainnet

Sohrani (Ctrl+O, Enter, Ctrl+X).

## 3. Proverka (bez servisa)

```bash
cd /opt/zal
source .venv/bin/activate
python -m bybit_bot.run_dry
python -m bybit_bot.run_live
```

## 4. Servis (rabotaet vsegda, perezapusk pri sboe)

```bash
sudo cp /opt/zal/bybit-bot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable bybit-bot
sudo systemctl start bybit-bot
```

Proverka:
```bash
sudo systemctl status bybit-bot
tail -f /opt/zal/bybit_bot.log
```

Ostanovit / zapustit snova:
```bash
sudo systemctl stop bybit-bot
sudo systemctl start bybit-bot
```

**Esli proekt v drugoj papke** (ne `/opt/zal`), otredi v `bybit-bot.service` stroki `WorkingDirectory` i `ExecStart` (put k proektu i k `.venv/bin/python`).

## 5. Pochemu ne otkrylas sdelka — smotrim logi

Kazhdyj zapusk zakanchivaetsja strokoj **ITOG** v loge: signal, pozicija, reshenie i prichina (esli sdelka ne sdelana).

```bash
# Poslednie itogi zapuskov (pochemu sdelka byla/ne byla)
grep "ITOG" /opt/zal/bybit_bot.log | tail -20

# Polnyj kontekst poslednego zapuska
grep -A 50 "LIVE: signal" /opt/zal/bybit_bot.log | tail -55
```

Razbor ITOG:
- `reshenie=hold` — bot nichego ne sdelal. Prichina v konce stroki: net signala (signal=0), uzhe v pozicii (derzhim), ili dr.
- `reshenie=open_long/open_short`, `Order otpravlen: da, OK` — order uspeshno otpravlen.
- `Order otpravlen: da, oshibka` — order otpravlen, no birzha vernula oshibku (retMsg podskazhet: margin, minOrderQty i t.p.).

Tekushhij signal i chto bot sdelal by sejchas (bez otpravki orderov):
```bash
cd /opt/zal && source .venv/bin/activate
python -m bybit_bot.check_signal   # signal po svecham, reshenija
python -m bybit_bot.run_dry       # + pozicija s birzhi, reshenie, qty
```
