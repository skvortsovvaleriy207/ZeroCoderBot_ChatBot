# ZeroCoderBot: GigaChat Summary Bot

Этот проект состоит из двух частей:
1.  **Telethon Script** (`telethon/`): Собирает сообщения из Telegram чатов в базу данных.
2.  **Summary Bot** (`ChatBot/`): Мониторит базу данных и присылает краткие выжимки (суммаризацию) новых сообщений через GigaChat.

## Требования

*   Python 3.10+
*   Telegram API ID и Hash (от [my.telegram.org](https://my.telegram.org))
*   Telegram Bot Token (от [@BotFather](https://t.me/BotFather))
*   GigaChat Credentials (от Sber Developers)

## Установка

1.  **Настройка окружения**:
    В корне проекта создан единый файл `.env`. Заполните его вашими данными:
    ```ini
    API_ID=ваш_api_id
    API_HASH=ваш_api_hash
    SESSION_NAME=my_session
    BOT_TOKEN=ваш_токен_бота
    GIGACHAT_CREDENTIALS=ваш_ключ_gigachat
    ```

2.  **Установка зависимостей**:

    *   **Telethon Script**:
        ```bash
        cd telethon
        python3 -m venv venv
        source venv/bin/activate
        pip install -r requirements.txt
        ```

    *   **Summary Bot**:
        ```bash
        cd ChatBot
        python3 -m venv venv
        source venv/bin/activate
        pip install -r requirements.txt
        ```

## Запуск

Для работы системы нужно запустить оба компонента в разных терминалах.

### 1. Запуск сборщика сообщений (Telethon)

Этот скрипт будет слушать новые сообщения в выбранном чате и сохранять их в базу данных.

```bash
cd telethon
./venv/bin/python main.py
```
*При первом запуске следуйте инструкциям в консоли для авторизации.*

### 2. Запуск бота-суммаризатора (ChatBot)

Этот бот будет читать базу данных и присылать вам выжимки.

```bash
cd ChatBot
./venv/bin/python bot.py
```

### 3. Использование

1.  Откройте вашего бота в Telegram.
2.  Отправьте команду `/start`.
3.  Нажмите кнопку **▶️ Запустить мониторинг**.
4.  Теперь, когда в чате, который слушает Telethon-скрипт, появится новое сообщение, бот пришлет вам его краткое содержание.
