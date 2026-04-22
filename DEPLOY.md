# Deployment Guide

## Option 1: Render.com (Recommended - Free)

1. Зайди на https://render.com и зарегистрируйся через GitHub
2. Нажми "New +" → "Web Service"
3. Подключи репозиторий `ai-commerce-orchestrator`
4. Настройки:
   - **Name**: ai-commerce-orchestrator
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python main.py`
   - **Plan**: Free
5. Environment Variables:
   - `BOT_TOKEN`: 8190674168:AAE8mx2M_Z1s0pPx7p2SgA8jr19ZSx-vLlU
   - `DB_PATH`: commerce_orchestrator.db
   - `LOG_LEVEL`: info
6. Нажми "Create Web Service"

Бот запустится автоматически и будет работать 24/7 бесплатно.

## Option 2: Railway.app (Free)

1. Зайди на https://railway.app
2. "Start a New Project" → "Deploy from GitHub repo"
3. Выбери `ai-commerce-orchestrator`
4. Railway автоматически определит Python проект
5. Добавь Environment Variables в настройках:
   - `BOT_TOKEN`: 8190674168:AAE8mx2M_Z1s0pPx7p2SgA8jr19ZSx-vLlU
   - `DB_PATH`: commerce_orchestrator.db
   - `LOG_LEVEL`: info
6. Deploy запустится автоматически

## Option 3: Fly.io (Free)

1. Установи Fly CLI: https://fly.io/docs/hands-on/install-flyctl/
2. Зарегистрируйся: `flyctl auth signup`
3. В папке проекта:
```bash
cd "C:\Users\user\projects\projectsCODE/VS projects/ai-commerce-orchestrator"
flyctl launch
```
4. Следуй инструкциям, выбери регион
5. Установи secrets:
```bash
flyctl secrets set BOT_TOKEN=8190674168:AAE8mx2M_Z1s0pPx7p2SgA8jr19ZSx-vLlU
```
6. Deploy: `flyctl deploy`

## Option 4: Heroku (Платный, но надежный)

1. Зайди на https://heroku.com
2. Создай новое приложение
3. Подключи GitHub репозиторий
4. В Settings → Config Vars добавь:
   - `BOT_TOKEN`: 8190674168:AAE8mx2M_Z1s0pPx7p2SgA8jr19ZSx-vLlU
   - `DB_PATH`: commerce_orchestrator.db
   - `LOG_LEVEL`: info
5. В Deploy → Manual Deploy нажми "Deploy Branch"

## Рекомендация

**Используй Render.com** - самый простой вариант:
- Бесплатно
- Автоматический деплой при пуше в GitHub
- Логи в реальном времени
- Простой интерфейс

После деплоя бот будет работать 24/7, просто открой ссылку Render и он запустится.

## Важно

⚠️ **НЕ коммить .env файл с токеном в GitHub!**

Токен уже в .gitignore, но для безопасности:
1. Используй Environment Variables на хостинге
2. Никогда не пуши .env в публичный репозиторий
