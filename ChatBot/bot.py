import telebot
from telebot.async_telebot import AsyncTeleBot
from telebot import types
import os
import asyncio
import aiosqlite
from dotenv import load_dotenv, find_dotenv
from gigachat_api import GigaChat

# Load environment variables
load_dotenv(find_dotenv())

BOT_TOKEN = os.getenv('BOT_TOKEN')
GIGACHAT_CREDENTIALS = os.getenv('GIGACHAT_CREDENTIALS')
DB_PATH = "../telethon/messages.db"

if not BOT_TOKEN:
    print("Error: BOT_TOKEN not found in .env file.")
    exit(1)

if not GIGACHAT_CREDENTIALS:
    print("Warning: GIGACHAT_CREDENTIALS not found in .env file. GigaChat features will not work.")

bot = AsyncTeleBot(BOT_TOKEN)
gigachat = GigaChat(GIGACHAT_CREDENTIALS) if GIGACHAT_CREDENTIALS else None

# Store subscribed users (in memory for now, ideally should be in DB)
subscribed_users = set()

class DatabaseHandler:
    def __init__(self, db_path):
        self.db_path = db_path

    async def init_db(self):
        # We rely on the telethon script to init the DB, but we can ensure the column exists just in case
        async with aiosqlite.connect(self.db_path) as db:
            try:
                await db.execute("ALTER TABLE messages ADD COLUMN is_summarized INTEGER DEFAULT 0")
                await db.commit()
            except Exception:
                pass # Column likely exists

    async def get_new_messages(self):
        async with aiosqlite.connect(self.db_path) as db:
            # Select messages where is_summarized is 0 or NULL
            cursor = await db.execute("""
                SELECT id, sender, text, chat_title 
                FROM messages 
                WHERE is_summarized = 0 OR is_summarized IS NULL
                ORDER BY date ASC
            """)
            rows = await cursor.fetchall()
            return rows

    async def mark_as_processed(self, message_id):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("UPDATE messages SET is_summarized = 1 WHERE id = ?", (message_id,))
            await db.commit()

db_handler = DatabaseHandler(DB_PATH)

def create_main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("▶️ Запустить мониторинг")
    btn2 = types.KeyboardButton("⏹ Остановить мониторинг")
    markup.add(btn1, btn2)
    return markup

@bot.message_handler(commands=['start'])
async def send_welcome(message):
    await bot.reply_to(message, "Привет! Я бот-суммаризатор. Я буду следить за новыми сообщениями в базе и присылать тебе выжимку.", reply_markup=create_main_menu())

@bot.message_handler(func=lambda message: message.text == "▶️ Запустить мониторинг")
async def start_monitoring(message):
    subscribed_users.add(message.chat.id)
    await bot.reply_to(message, "Мониторинг запущен! Я буду присылать выжимки новых сообщений.")

@bot.message_handler(func=lambda message: message.text == "⏹ Остановить мониторинг")
async def stop_monitoring(message):
    if message.chat.id in subscribed_users:
        subscribed_users.remove(message.chat.id)
    await bot.reply_to(message, "Мониторинг остановлен.")

async def process_updates():
    """Background task to check for new messages and send summaries."""
    while True:
        if not subscribed_users:
            await asyncio.sleep(5)
            continue

        try:
            new_messages = await db_handler.get_new_messages()
            
            for msg_id, sender, text, chat_title in new_messages:
                if not text:
                    await db_handler.mark_as_processed(msg_id)
                    continue

                # Prepare prompt for summarization
                prompt = f"Сделай краткую выжимку (суммаризацию) следующего сообщения из чата '{chat_title}' от пользователя '{sender}':\n\n{text}"
                
                # Call GigaChat (sync call in executor)
                if gigachat:
                    loop = asyncio.get_running_loop()
                    summary = await loop.run_in_executor(None, gigachat.get_chat_response, prompt)
                    
                    response_text = f"📢 **Новое сообщение в {chat_title}**\n👤 **От:** {sender}\n\n📝 **Выжимка:**\n{summary}"
                else:
                    response_text = f"📢 **Новое сообщение в {chat_title}**\n👤 **От:** {sender}\n\n(GigaChat не настроен, оригинал):\n{text}"

                # Send to all subscribed users
                for user_id in subscribed_users:
                    try:
                        await bot.send_message(user_id, response_text, parse_mode='Markdown')
                    except Exception as e:
                        print(f"Failed to send to {user_id}: {e}")

                # Mark as processed
                await db_handler.mark_as_processed(msg_id)
                
                # Small delay to avoid hitting rate limits too hard
                await asyncio.sleep(1)

        except Exception as e:
            print(f"Error in update loop: {e}")
        
        await asyncio.sleep(10) # Check every 10 seconds

async def main():
    await db_handler.init_db()
    
    # Start background task
    asyncio.create_task(process_updates())
    
    print("Bot is running...")
    await bot.infinity_polling()

if __name__ == '__main__':
    asyncio.run(main())
