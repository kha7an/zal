# Настройка Git и деплой на сервер

## 1. Установи Git (если ещё нет)

- Windows: https://git-scm.com/download/win
- После установки перезапусти терминал.

## 2. На ПК (в папке проекта)

```powershell
cd C:\Users\alia8\PycharmProjects\PythonProject2

git init
git add .gitignore bybit_bot requirements.txt
# если есть Docker:
# git add Dockerfile docker-compose.yml
git status
git commit -m "bybit bot: indicator, signals, run_live, run_loop, logs"
```

## 3. Создай репозиторий на GitHub/GitLab

- GitHub: https://github.com/new — создай репо (например `bybit-bot`), **без** README.
- Скопируй URL репо (HTTPS или SSH), например: `https://github.com/TVOJ_LOGIN/bybit-bot.git`

## 4. Подключи remote и запушь

```powershell
git remote add origin https://github.com/TVOJ_LOGIN/bybit-bot.git
git branch -M main
git push -u origin main
```

(Подставь свой URL и логин.)

## 5. На сервере (первый раз — клонирование)

```bash
# если папка /opt/bybit-bot уже есть и там старый код:
cd /opt
mv bybit-bot bybit-bot.old

git clone https://github.com/TVOJ_LOGIN/bybit-bot.git bybit-bot
cd bybit-bot
```

Создай `.env` на сервере (ключи Bybit и т.д.):

```bash
nano .env
# вставь BYBIT_API_KEY=... BYBIT_API_SECRET=... и т.д.
```

Установи зависимости и проверь:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m bybit_bot.run_dry
```

## 6. Обновление кода на сервере (после изменений на ПК)

На ПК:
```powershell
git add -A
git commit -m "описание изменений"
git push
```

На сервере:
```bash
cd /opt/bybit-bot
git pull
```

**Важно:** `.env` в репозиторий не попадает (он в .gitignore). На сервере он должен быть создан вручную один раз.
