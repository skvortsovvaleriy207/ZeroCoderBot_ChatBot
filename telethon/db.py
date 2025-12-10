# db.py
import aiosqlite
import logging

DB_NAME = "messages.db"

async def init_db():
    """Инициализация базы данных: создание таблицы messages, если она не существует."""
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY,
                chat_id INTEGER,
                sender TEXT,
                text TEXT,
                date TEXT,
                chat_title TEXT,
                is_summarized INTEGER DEFAULT 0
            )
        """)
        # Проверка и добавление колонок для существующих баз
        try:
            await db.execute("ALTER TABLE messages ADD COLUMN chat_title TEXT")
        except Exception:
            pass # Колонка уже существует
            
        try:
            await db.execute("ALTER TABLE messages ADD COLUMN is_summarized INTEGER DEFAULT 0")
        except Exception:
            pass # Колонка уже существует

        await db.commit()
    logging.info("База данных инициализирована.")

async def save_message(message_id, chat_id, sender, text, date, chat_title):
    """Сохранение сообщения в базу данных. Пропускает дубликаты по id."""
    async with aiosqlite.connect(DB_NAME) as db:
        try:
            await db.execute("""
                INSERT OR IGNORE INTO messages (id, chat_id, sender, text, date, chat_title, is_summarized)
                VALUES (?, ?, ?, ?, ?, ?, 0)
            """, (message_id, chat_id, sender, text, str(date), chat_title))
            await db.commit()
            # logging.info(f"Сообщение {message_id} сохранено в БД.")
        except Exception as e:
            logging.error(f"Ошибка при сохранении сообщения: {e}")
