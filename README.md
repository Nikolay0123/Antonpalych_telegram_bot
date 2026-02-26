## Telegram бот отеля «Антонпалыч»

Многоязычный Telegram‑бот для гостей отеля «Антонпалыч» на базе `aiogram 3` и Google Gemini.

### Основные возможности

- **Регистрация гостя**: запрос телефона (через кнопку c контактом) и номера комнаты, выбор языка интерфейса (🇷🇺/🇬🇧/🇨🇳).
- **Главное меню (ровно 7 кнопок)**:
  - **🍳 Заказать завтрак** – выбор даты, времени, блюд и количества порций, отправка заявки на кухню и сохранение в БД.
  - **🏛️ Экскурсии** – выбор экскурсии из JSON, даты/времени и количества человек, заявка в ресепшн.
  - **🚶 Заказать гида** – язык гида, длительность, тип (инд./групповой), пожелания по маршруту, заявка тур‑оператору.
  - **🏨 Забронировать номер (Bnovo)** – открытие ссылки/мини‑приложения Bnovo с передачей телефона и комнаты.
  - **🆘 Техподдержка / Сообщить о проблеме** – форма описания проблемы, выбор срочности, заявка в ресепшн.
  - **🧺 Смена полотенец/белья** – выбор типа, количества и удобного времени, заявка горничным.
  - **🤖 Задать вопрос ассистенту** – ИИ‑ассистент на Google Gemini с базой знаний об отеле.
- **Мультиязычность**: все тексты вынесены в `languages/*.json` (`ru`, `en`, `zh`).
- **Уведомления персоналу**: все заявки отправляются в Telegram‑группу ресепшн.
- **База данных**: SQLite (файл задаётся в `.env`) с таблицами пользователей и заявок.
- **Оценка качества**: после создания заявки/заказа пользователю предлагается оценка по шкале 1–5.

### Структура проекта

```text
telegram_hotel_bot/
  .env.example
  .gitignore
  README.md
  requirements.txt
  bot.py
  config.py
  database.py
  keyboards.py
  middlewares.py
  languages/
    __init__.py
    ru.json
    en.json
    zh.json
  handlers/
    __init__.py
    registration.py
    breakfast.py
    excursions.py
    guide.py
    bnovo.py
    support.py
    linen.py
    ai_assistant.py
  utils/
    __init__.py
    logger.py
    notifications.py
    validators.py
  data/
    menu_breakfast.json
    excursions.json
    hotel_info.json
```

### Установка и запуск

1. **Клонирование и окружение**

```bash
cd telegram_hotel_bot
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

2. **Создание `.env`**

Скопируйте `.env.example` в `.env` и заполните значения:

- **BOT_TOKEN** – токен Telegram‑бота.
- **GEMINI_API_KEY** – API‑ключ Google Gemini.
- **BNOVO_API_KEY / BNOVO_BASE_URL** – данные для Bnovo (URL виджета/мини‑приложения, опционально API).
- **RECEPTION_CHAT_ID** – ID Telegram‑чата/группы персонала (отрицательный ID для групп).
- **DATABASE_PATH** – путь к файлу SQLite (по умолчанию `database.sqlite3`).

3. **Запуск бота**

```bash
python bot.py
```

Бот запускается в режиме long‑polling. При первом входе пользователь проходит регистрацию и выбор языка.

### Как это работает (коротко)

- **Мультиязычность** – модуль `languages/__init__.py` загружает JSON‑файлы по коду языка (`ru/en/zh`). Middleware `LanguageMiddleware` подставляет язык пользователя в каждый хендлер.
- **Регистрация** – `handlers/registration.py`: `/start` → запрос телефона (кнопка с `request_contact`) → номер комнаты → выбор языка (inline‑кнопки) → запись пользователя в таблицу `users`.
- **Заказ завтраков / поддержка / смена белья** – соответствующие хендлеры создают записи в таблицах `breakfast_orders`, `support_tickets`, `linen_requests` и сразу отправляют красиво отформатированные уведомления в чат ресепшн через `utils/notifications.py`.
- **Интеграция Bnovo** – `handlers/bnovo.py` формирует URL на основе `BNOVO_BASE_URL` и передаёт телефон/комнату как GET‑параметры; дальше используется ваш виджет/мини‑приложение Bnovo.
- **ИИ‑ассистент** – `handlers/ai_assistant.py` читает `data/hotel_info.json`, формирует системный prompt и отправляет запрос к модели `gemini-2.0-flash` через REST API. Если ответ неудачен/пустой, бот предлагает обратиться на ресепшн.

### Безопасность и ограничения

- Все чувствительные данные хранятся только в `.env` и **не коммитятся** в репозиторий.
- Вводы пользователя валидируются (количество, номер комнаты и т.п.).
- Только зарегистрированные пользователи могут создавать заявки (контролируется `RegistrationRequiredMiddleware`).

---

## Telegram bot for “Antonpalych” Hotel (EN)

A multilingual Telegram bot for hotel guests, built with `aiogram 3` and Google Gemini.

### Features

- **Guest registration**: phone number (via contact button), room number, language selection (🇷🇺 / 🇬🇧 / 🇨🇳).
- **Main menu (exactly 7 buttons)** for:
  - **Breakfast orders**
  - **Excursions**
  - **City guide**
  - **Room booking via Bnovo**
  - **Support / problem reporting**
  - **Towels / linen change**
  - **AI assistant (Gemini)**
- **Multilanguage UI** from JSON files (`languages/*.json`).
- **Notifications** to a staff Telegram group.
- **SQLite database** for users and orders.
- **Service rating** after each request.

### Quick start

1. Install dependencies: `pip install -r requirements.txt`
2. Copy `.env.example` → `.env` and fill tokens/IDs.
3. Run the bot: `python bot.py`

The codebase is ready to be pushed to GitHub as a standalone project.

