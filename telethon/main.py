# main.py
import asyncio
import logging
from telethon import TelegramClient, events
from config import API_ID, API_HASH, SESSION_NAME
from db import init_db, save_message

# Настройка логирования
logging.basicConfig(format='[%(levelname)s] %(asctime)s - %(message)s', level=logging.INFO)

# Инициализация клиента
client = TelegramClient(SESSION_NAME, API_ID, API_HASH)

async def list_chats():
    """Получение и вывод списка доступных диалогов."""
    print("\n--- Список чатов ---")
    dialogs = await client.get_dialogs()
    for dialog in dialogs:
        print(f"ID: {dialog.id} | Title: {dialog.title}")
    return dialogs

async def dump_history(chat_id, limit=100):
    """Сбор последних N сообщений из выбранного чата и сохранение в БД."""
    print(f"\n--- Сбор истории из чата {chat_id} (последние {limit} сообщений) ---")
    try:
        # Получаем информацию о чате для заголовка
        chat = await client.get_entity(chat_id)
        chat_title = getattr(chat, 'title', 'Private Chat')

        count = 0
        async for message in client.iter_messages(chat_id, limit=limit):
            sender = await message.get_sender()
            sender_name = "Unknown"
            
            if sender:
                if hasattr(sender, 'first_name') and sender.first_name:
                    sender_name = sender.first_name
                    if hasattr(sender, 'last_name') and sender.last_name:
                        sender_name += f" {sender.last_name}"
                elif hasattr(sender, 'title') and sender.title:
                    sender_name = sender.title
                elif hasattr(sender, 'username') and sender.username:
                    sender_name = sender.username
            
            # Если отправитель все еще Unknown, но это канал, то отправитель - сам канал
            if sender_name == "Unknown" and chat_title:
                 sender_name = chat_title
            
            await save_message(
                message.id,
                chat_id,
                sender_name,
                message.text or "",
                message.date,
                chat_title
            )
            count += 1
        print(f"Сохранено {count} сообщений.")
    except Exception as e:
        logging.error(f"Ошибка при сборе истории: {e}")

@client.on(events.NewMessage)
async def handler(event):
    """Асинхронный обработчик новых сообщений."""
    try:
        chat = await event.get_chat()
        sender = await event.get_sender()
        sender_name = "Unknown"
        
        if sender:
            if hasattr(sender, 'first_name') and sender.first_name:
                sender_name = sender.first_name
                if hasattr(sender, 'last_name') and sender.last_name:
                    sender_name += f" {sender.last_name}"
            elif hasattr(sender, 'title') and sender.title:
                sender_name = sender.title
            elif hasattr(sender, 'username') and sender.username:
                sender_name = sender.username
        
        chat_title = getattr(chat, 'title', 'Private Chat')
        
        # Если отправитель все еще Unknown, но это канал, то отправитель - сам канал
        if sender_name == "Unknown" and chat_title:
                sender_name = chat_title

        # Логирование в консоль
        print(f"[{chat_title}] {sender_name}: {event.text}")

        # Сохранение в БД
        await save_message(
            event.id,
            event.chat_id,
            sender_name,
            event.text or "",
            event.date,
            chat_title
        )
    except Exception as e:
        logging.error(f"Ошибка в обработчике сообщений: {e}")

async def main():
    # Инициализация БД
    await init_db()

    # Запуск клиента
    print("Подключение к Telegram...")
    await client.start()
    print("Успешное подключение!")

    # 1. Получить список чатов
    dialogs = await list_chats()
    
    if not dialogs:
        print("Нет доступных диалогов.")
        return

    # Пример: выбор первого чата для дампа истории (или можно попросить пользователя ввести ID)
    # Для демонстрации возьмем "Избранное" (Saved Messages) или любой другой, если есть.
    # Но чтобы не спамить, просто предложим пользователю ввести ID, или возьмем первый попавшийся.
    # В рамках автоматического скрипта, давайте просто возьмем первый диалог.
    target_chat = dialogs[0]
    print(f"\nВыбран чат для сбора истории: {target_chat.title} (ID: {target_chat.id})")
    
    # 2. Собрать последние 100 сообщений
    await dump_history(target_chat.id, limit=100)

    # 3. Запуск live-слушателя
    print("\n--- Запуск прослушивания новых сообщений (Ctrl+C для выхода) ---")
    await client.run_until_disconnected()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nПрограмма остановлена пользователем.")
    except Exception as e:
        logging.error(f"Критическая ошибка: {e}")
