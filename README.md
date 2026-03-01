# 🔮 Enigma — AI-агент для обработки обращений

> Умная система технической поддержки для компании **ЭРИС** (производитель газоанализаторов): автоматически принимает письма и сообщения из Telegram, анализирует их с помощью LLM, создаёт тикеты и уведомляет команду — всё в одном контейнере.

---

## 📋 Содержание

- [Обзор архитектуры](#-обзор-архитектуры)
- [Возможности](#-возможности)
- [Стек технологий](#-стек-технологий)
- [Быстрый старт](#-быстрый-старт)
- [Переменные окружения](#-переменные-окружения)
- [API Reference](#-api-reference)
- [База знаний (RAG)](#-база-знаний-rag)
- [Telegram-интеграция](#-telegram-интеграция)
- [Email-воркер (IMAP)](#-email-воркер-imap)
- [AI-анализатор](#-ai-анализатор)
- [Схема базы данных](#-схема-базы-данных)
- [Тесты и CI](#-тесты-и-ci)
- [Структура проекта](#-структура-проекта)

---

## 🏗 Обзор архитектуры

```
                 ┌────────────────────────────────────────────────┐
                 │                  docker-compose                 │
                 │                                                 │
  📧 Email  ────▶│  email_worker  ──┐                             │
                 │  (IMAP polling)  │                             │
                 │                  ▼                             │
  📱 Telegram ──▶│  bot_service  ──▶│  backend (FastAPI)         │
                 │  (long polling)  │      │                      │
                 │                  │      ▼                      │
  🌐 Frontend ──▶│  Flutter Web  ──▶│  PostgreSQL + pgvector      │
                 │                  │      │                      │
                 │                  └──────▶  AI (Groq LLaMA)    │
                 └────────────────────────────────────────────────┘
```

Система состоит из **5 Docker-сервисов**:

| Сервис | Назначение |
|--------|------------|
| `db` | PostgreSQL 15 с расширением pgvector |
| `db_init` | Одноразовая миграция схемы (`init.sql`) |
| `backend` | FastAPI REST API — ядро системы |
| `bot` | Telegram-бот (long polling) |
| `email_worker` | IMAP-воркер входящей почты |
| `frontend` | Flutter Web, собирается в nginx-контейнер |

---

## ✨ Возможности

### 📥 Многоканальный приём обращений
- **Email** — автоматический сбор непрочитанных писем по IMAP с настраиваемым интервалом опроса
- **Telegram** — публикация тикетов в каналы/группы с поддержкой linked discussion (обсуждения прямо под постом)
- **Web** — ручное создание тикетов через REST API или Flutter-интерфейс

### 🤖 AI-анализ обращений (Groq + LLaMA 3.3 70B)
Для каждого входящего обращения автоматически извлекаются:
- **ФИО**, телефон, email клиента
- **Заводские номера** и модели приборов
- **Тональность** (Позитив / Нейтрально / Негатив)
- **Категория**: Неисправность, Калибровка, Документация, Интеграция, Доступ, Общий вопрос
- **Краткое резюме** проблемы
- **Готовый черновик ответа** от лица службы поддержки

### 📚 RAG — семантический поиск по базе знаний
- Загрузка документов форматов `.txt`, `.docx`, `.pdf` (до 20 МБ)
- Разбивка на чанки и векторизация через `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`
- Хранение эмбеддингов в **pgvector** с IVFFlat-индексом
- Автоматическая инжекция релевантного контекста в промпт LLM

### 📊 Управление тикетами
- Фильтрация по статусу, тональности, категории, полнотекстовый поиск
- Статусы: `Новое` → `В работе` → `Закрыто`
- Таймлайн событий: взял в работу, передал, отказался

### 🔔 Telegram-уведомления команды
- Публикация новых тикетов в зарегистрированные каналы
- Inline-кнопки «✅ Взять в работу» / «❌ Отказаться от запроса»
- Живой таймлайн в обсуждениях — обновляется при каждом действии
- Безопасная привязка каналов через одноразовые UUID-токены (TTL: 10 мин)

### 🔁 Fallback без AI
При недоступности Groq API система автоматически переключается на встроенный **keyword-анализатор** на основе регулярных выражений — нулевой простой.

---

## 🛠 Стек технологий

| Слой | Технология |
|------|-----------|
| Backend | **FastAPI** 0.111+, Python 3.12, SQLAlchemy 2.x |
| AI | **Groq API** (LLaMA 3.3 70b versatile) |
| Embeddings | `sentence-transformers` (MiniLM-L12-v2, 384d) |
| Vector DB | **PostgreSQL 15** + **pgvector** |
| Telegram | `httpx` (async long polling), Bot API |
| Email | `imaplib` (IMAP4 SSL) |
| Frontend | **Flutter Web** → nginx |
| Infra | **Docker Compose** v3.8 |
| CI | **GitHub Actions** (pytest, ruff, codecov) |

---

## 🚀 Быстрый старт

### 1. Клонируйте репозиторий

```bash
git clone <repo-url>
cd enigma-AI-agent-for-messages
```

### 2. Создайте `.env`

```bash
cp .env.example .env
# Откройте .env и заполните обязательные переменные (см. раздел ниже)
```

### 3. Запустите

```bash
docker compose up --build
```

После запуска:
- **API**: http://localhost:8000
- **Swagger UI**: http://localhost:8000/docs
- **Frontend**: http://localhost:8080
- **Health check**: http://localhost:8000/health

### 4. Убедитесь, что всё работает

```bash
curl http://localhost:8000/health
# {"status": "ok", "version": "2.0.0"}
```

---

## ⚙️ Переменные окружения

Создайте файл `.env` в корне проекта:

```dotenv
# ── Обязательные ──────────────────────────────────────────────────────────────

# Токен Telegram-бота (получить у @BotFather)
TELEGRAM_BOT_TOKEN=123456789:AAxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# API-ключ Groq (https://console.groq.com)
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxxxxxxxx

# ── Email (IMAP) — опционально ────────────────────────────────────────────────
IMAP_HOST=mail.example.com
IMAP_PORT=993
IMAP_USER=support@example.com
IMAP_PASSWORD=your_email_password
IMAP_MAILBOX=INBOX
IMAP_POLL_INTERVAL=60        # секунды между проверками

# ── SMTP (исходящая почта) — опционально ──────────────────────────────────────
SMTP_HOST=mail.example.com
SMTP_PORT=587
SMTP_USER=support@example.com
SMTP_PASSWORD=your_email_password
SMTP_FROM=support@example.com
```

> **Примечание:** если `IMAP_HOST` не задан, email-воркер просто не запускается — остальные сервисы работают в штатном режиме.

---

## 📡 API Reference

Полная интерактивная документация — **Swagger UI** по адресу `/docs`.

### Тикеты

| Метод | Эндпоинт | Описание |
|-------|----------|----------|
| `GET` | `/tickets` | Список тикетов (фильтры: `status`, `tone`, `category`, `search`) |
| `GET` | `/tickets/{id}` | Один тикет |
| `POST` | `/tickets` | Создать тикет вручную |
| `PATCH` | `/tickets/{id}` | Обновить поля тикета |

### Анализ

| Метод | Эндпоинт | Описание |
|-------|----------|----------|
| `POST` | `/analyze` | Проанализировать текст через AI и получить структурированный результат |

### База знаний

| Метод | Эндпоинт | Описание |
|-------|----------|----------|
| `GET` | `/knowledge` | Список загруженных документов |
| `POST` | `/knowledge/upload` | Загрузить документ (async, возвращает `job_id`) |
| `GET` | `/knowledge/status/{job_id}` | Статус обработки документа |
| `GET` | `/knowledge/jobs` | Все задачи обработки |
| `GET` | `/knowledge/debug` | Диагностика: кол-во чанков по источникам |
| `DELETE` | `/knowledge/{source}` | Удалить документ из базы знаний |

### Telegram

| Метод | Эндпоинт | Описание |
|-------|----------|----------|
| `POST` | `/telegram/link-token` | Сгенерировать одноразовый токен для привязки канала |
| `GET` | `/telegram/channels` | Список активных каналов |

---

## 📚 База знаний (RAG)

Система поддерживает загрузку документов для обогащения контекста AI-ответов.

### Поддерживаемые форматы
- `.txt` — plain text
- `.docx` — Microsoft Word
- `.pdf` — PDF-документы (до 20 МБ)

### Как работает

```
Документ (.pdf/.docx/.txt)
        │
        ▼
  Разбивка на чанки
        │
        ▼
  Векторизация (MiniLM-L12-v2, 384 измерения)
        │
        ▼
  Сохранение в PostgreSQL (pgvector, IVFFlat-индекс)
        │
        ▼
  При анализе обращения: cosine similarity search → top-4 чанка
        │
        ▼
  Инжекция контекста в system prompt LLM
```

### Пример загрузки документа

```bash
# Загрузить документ
curl -X POST http://localhost:8000/knowledge/upload \
  -F "file=@руководство_дгс230.pdf"
# Ответ: {"job_id": "uuid", "source": "руководство_дгс230.pdf"}

# Проверить статус
curl http://localhost:8000/knowledge/status/<job_id>
# Ответ: {"status": "done", "chunks": 47, ...}
```

---

## 📱 Telegram-интеграция

### Привязка канала

1. Создайте одноразовый токен через API:
   ```bash
   curl -X POST http://localhost:8000/telegram/link-token
   # {"token": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx", "expires_at": "..."}
   ```

2. Отправьте токен в нужный Telegram-канал или группу. Бот подтвердит привязку:
   ```
   ✅ Канал подтверждён. Начинаю присылать новые заявки.
   ```

3. Токен действителен **10 минут** и используется одноразово.

### Жизненный цикл тикета в Telegram

```
Новый тикет создан
      │
      ▼
📢 Пост в канале с кнопкой [✅ Взять в работу]
      │
      ▼  (Telegram linked discussion)
💬 Комментарий с таймлайном: "Принято"
      │
      ▼  (оператор нажимает кнопку)
✅ Пост обновляется: "👤 В работе: @username"
   Таймлайн обновляется: "• 2026-01-01T10:00 — взял: @username"
   Кнопка меняется на [❌ Отказаться от запроса]
      │
      ▼  (другой оператор нажимает Взять)
🔄 "Перевзято (было: @prev_user)"
```

---

## 📧 Email-воркер (IMAP)

Воркер запускается как отдельный контейнер и работает в бесконечном цикле:

1. Подключается к IMAP-серверу по SSL
2. Ищет непрочитанные письма (`UNSEEN`)
3. Парсит заголовки (`Subject`, `From`) и извлекает текстовое тело (предпочитает `text/plain` → `text/html`)
4. Передаёт полный текст в `TicketService.create_from_email()`
5. AI анализирует письмо и создаёт структурированный тикет
6. Отправляет уведомление в Telegram
7. Помечает письмо как прочитанное (`\Seen`) **только после успешной обработки**

> Если обработка письма упала с ошибкой — оно **не** помечается прочитанным и будет обработано при следующем цикле.

---

## 🤖 AI-анализатор

### Основной режим — Groq API (LLaMA 3.3 70B)

```python
# Возвращаемая структура
{
  "full_name":      "Иванов Иван Иванович",
  "phone":          "+7 (495) 123-45-67",
  "email":          "ivan@example.com",
  "device_numbers": "2411-08731",
  "device_type":    "ДГС-230/CH4",
  "emotional_tone": "Негатив",          # Позитив | Нейтрально | Негатив
  "category":       "Неисправность",    # 6 категорий
  "issue_summary":  "Прибор не запускается после скачка напряжения",
  "ai_response":    "Уважаемый(-ая) клиент!..."
}
```

### Резервный режим — Keyword-анализатор

При недоступности Groq API автоматически активируется встроенный анализатор на регулярных выражениях (`TextAnalyzer`):

- Определяет тональность по словарям позитивных/негативных слов
- Классифицирует по ключевым словам (Калибровка, Неисправность, Документация...)
- Извлекает заводские номера приборов (поддерживает форматы: `А-12345`, `2411-08731`, etc.)
- Достаёт контактные данные через regex
- Генерирует шаблонный ответ по категории

---

## 🗄 Схема базы данных

```sql
tickets                    -- основная таблица обращений
  ├── id, created_at
  ├── full_name, facility, phone, email
  ├── device_numbers, device_type
  ├── emotional_tone, category
  ├── issue_summary, original_text, ai_response
  └── status ('Новое' | 'В работе' | 'Закрыто')

knowledge_chunks           -- чанки базы знаний
  ├── id, source, chunk_index
  ├── chunk_text
  └── embedding vector(384) -- IVFFlat-индекс для cosine search

telegram_channels          -- зарегистрированные каналы/группы
  └── chat_id, type, title, active

telegram_link_tokens       -- одноразовые UUID-токены привязки
  └── token, expires_at, consumed_at

telegram_ticket_bindings   -- привязка тикета к сообщению в канале
  └── ticket_id, channel_chat_id, channel_message_id,
      discussion_chat_id, timeline_message_id, assignee

ticket_events              -- таймлайн событий
  └── ticket_id, ts, type ('created'|'taken'|'released'|'retaken'), by, prev
```

---

## 🧪 Тесты и CI

### Запуск тестов локально

```bash
cd backend
pip install -r requirements-test.txt
pytest
```

### Что покрыто тестами

- `test_analyzer.py` — keyword-анализатор
- `test_store.py` — CRUD тикетов
- `test_ticket_service.py` — бизнес-логика тикетов
- `test_schemas.py` — pydantic-схемы
- `test_bot_service.py` — логика Telegram-бота
- `test_telegram_store.py` / `test_telegram_ticket_store.py` — хранилища
- `test_telegram_routes.py` / `test_telegram_notifier.py` — роуты и нотификации
- `test_api_integration.py` — интеграционные тесты API

### GitHub Actions CI (`.github/workflows/backend-ci.yml`)

Запускается при каждом push и PR:

```
checkout → Python 3.12 → pip install → ruff lint → pytest → codecov upload
```

---

## 📁 Структура проекта

```
enigma/
├── docker-compose.yml
├── init.sql                        # Идемпотентная миграция схемы + seed-данные (30 тикетов)
├── .env                            # (создать вручную)
├── data/
│   ├── telegram_channels.json      # Персистентное хранилище каналов
│   └── telegram_tickets.json       # Хранилище привязок тикетов
│
├── backend/
│   ├── app/
│   │   ├── main.py                 # Точка входа FastAPI
│   │   ├── api/routes/
│   │   │   ├── tickets.py          # CRUD тикетов
│   │   │   ├── analyze.py          # AI-анализ текста
│   │   │   ├── knowledge.py        # Управление базой знаний
│   │   │   ├── telegram.py         # Привязка каналов
│   │   │   └── utility.py          # Вспомогательные эндпоинты
│   │   ├── services/
│   │   │   ├── ai_analyzer.py      # Groq API + fallback
│   │   │   ├── analyzer.py         # Keyword-анализатор (regex)
│   │   │   ├── ticket_service.py   # Бизнес-логика тикетов
│   │   │   └── telegram_notifier.py # Отправка уведомлений
│   │   ├── bot/
│   │   │   └── bot_service.py      # Telegram long polling
│   │   ├── email/
│   │   │   └── imap_worker.py      # IMAP email worker
│   │   ├── knowledge/
│   │   │   ├── retriever.py        # Семантический поиск (pgvector)
│   │   │   └── loader.py           # Загрузка и чанкинг документов
│   │   └── core/
│   │       ├── config.py           # Pydantic Settings
│   │       ├── db.py               # SQLAlchemy engine/session
│   │       ├── models.py           # ORM-модели
│   │       └── store.py / telegram_store.py / telegram_ticket_store.py
│   └── tests/                      # Pytest test suite
│
└── frontend/                       # Flutter Web приложение
    ├── lib/
    │   ├── main.dart
    │   ├── core/                   # HTTP-клиент, конфигурация
    │   └── features/               # Экраны и компоненты UI
    └── windows/runner/             # Windows runner (если нужен desktop)
```

---

## 🔐 Безопасность

- Токены привязки Telegram-каналов — одноразовые UUID, TTL 10 минут
- Пароли и ключи — только через `.env` (не коммитить в репозиторий!)
- IMAP-соединение только через SSL (порт 993 по умолчанию)
- Письма помечаются прочитанными только при успешной обработке

---

## 📝 Лицензия

Проект разработан для внутреннего использования компании ЭРИС.

---

<div align="center">
  <strong>Enigma</strong> — от письма до тикета за секунды 🚀
</div>
