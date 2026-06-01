# NeoCard

**NeoCard** — production-ready платформа цифровых визиток с веб/PWA клиентом, Google OAuth, JWT-сессиями и AI-модулем.

## Возможности

- Регистрация через **Google OAuth**
- Неограниченное число визиток с публичными страницами
- Шаринг: ссылка, QR-код, соцсети, vCard
- 4 шаблона: Modern Blue, Business Dark, Minimal White, Gradient Purple
- AI: биография, анализ профиля, карьерный помощник, генератор навыков
- Статистика: просмотры, сохранения, QR-сканы, график активности
- Роли **User** и **Admin** (админ-панель, модерация, жалобы)
- Mobile First + **PWA**
- Безопасность: JWT, валидация, bleach (XSS), SQLAlchemy (SQL injection), rate limit, security headers, CORS

## Стек

| Слой | Технологии |
|------|------------|
| Frontend | HTML5, CSS3, Vanilla JS, PWA |
| Backend | Python 3.11, FastAPI, SQLAlchemy |
| БД | SQLite |
| Auth | Google OAuth 2.0, JWT Access + Refresh |

## Структура проекта

```
NeoCard2/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app + static frontend
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── models/              # User, Card, Analytics, Report
│   │   ├── schemas/
│   │   ├── routers/             # auth, cards, ai, admin
│   │   ├── services/
│   │   ├── middleware/
│   │   └── utils/
│   ├── requirements.txt
│   └── run.py
├── frontend/
│   ├── index.html               # Onboarding
│   ├── pages/                   # Dashboard, editor, card, AI, admin...
│   ├── css/
│   ├── js/
│   ├── manifest.json
│   └── sw.js
├── .env.example
└── README.md
```

## Быстрый старт

### 1. Требования

- Python 3.11+
- Google Cloud OAuth credentials

### 2. Установка

```bash
cd backend
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/macOS:
# source venv/bin/activate

pip install -r requirements.txt
cp ../.env.example .env
```

### 3. Настройка `.env`

Отредактируйте `backend/.env`:

```env
SECRET_KEY=your-long-random-secret
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
GOOGLE_REDIRECT_URI=http://localhost:8000/api/auth/google/callback
FRONTEND_URL=http://localhost:8000
ADMIN_EMAILS=your@gmail.com
OPENAI_API_KEY=          # опционально — без ключа AI использует умные fallback-ответы
```

**Google OAuth:**

1. [Google Cloud Console](https://console.cloud.google.com/apis/credentials) → Create OAuth Client ID (Web)
2. Authorized redirect URI: `http://localhost:8000/api/auth/google/callback`
3. Скопируйте Client ID и Secret в `.env`

### 4. Запуск

```bash
cd backend
python run.py
```

Откройте: **http://localhost:8000**

- Swagger API: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API Documentation

После запуска доступна интерактивная документация:

| URL | Описание |
|-----|----------|
| `/docs` | Swagger UI |
| `/redoc` | ReDoc |
| `/openapi.json` | OpenAPI schema |

### Основные эндпоинты

| Метод | Путь | Описание |
|-------|------|----------|
| GET | `/api/auth/google/url` | URL для Google OAuth |
| GET | `/api/auth/google/callback` | OAuth callback |
| POST | `/api/auth/refresh` | Обновление access token |
| POST | `/api/auth/logout` | Выход (revoke refresh) |
| GET | `/api/cards/dashboard` | Dashboard stats |
| GET/POST | `/api/cards` | Список / создание |
| GET | `/api/cards/public/{slug}` | Публичная визитка |
| POST | `/api/ai/bio` | AI биография |
| GET | `/api/admin/users` | Админ: пользователи |

## Deployment Guide

### Production checklist

1. Установите сильный `SECRET_KEY` (64+ символов)
2. Используйте HTTPS (nginx/Caddy + Let's Encrypt)
3. Смените `DATABASE_URL` на PostgreSQL для высокой нагрузки (потребуется смена драйвера)
4. Обновите `GOOGLE_REDIRECT_URI` и `FRONTEND_URL` на production домен
5. Настройте `CORS_ORIGINS` только на ваш домен
6. Запускайте через **gunicorn + uvicorn workers**:

```bash
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
```

### Docker (пример)

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ .
COPY frontend/ /app/../frontend/
ENV PYTHONPATH=/app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Nginx reverse proxy

```nginx
server {
    listen 443 ssl;
    server_name neocard.example.com;
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Безопасность

- **SQL Injection**: SQLAlchemy ORM, параметризованные запросы
- **XSS**: bleach sanitization на входе
- **JWT**: Access (30 мин) + Refresh (30 дней), rotation при refresh
- **Rate limiting**: 120 req/min per IP (настраивается)
- **Security headers**: X-Frame-Options, CSP-ready headers, HSTS (при HTTPS)
- **CORS**: whitelist origins
- **Input validation**: Pydantic schemas

> CSRF: API использует Bearer JWT (не cookie-based auth), что снижает риск CSRF для API. Для cookie-сессий потребуется CSRF-токен.

## AI Module

При наличии `OPENAI_API_KEY` используется LLM. Без ключа — интеллектуальные шаблонные ответы на основе контекста (профессия, навыки, заполненность полей).

## Лицензия

Proprietary — NeoCard © 2025
