from telegram import Bot
from telegram.error import TelegramError
from config import BOT_TOKEN, ADMIN_CHAT_ID

bot = Bot(token=BOT_TOKEN)

def send_telegram_message(text):
    try:
        bot.send_message(chat_id=ADMIN_CHAT_ID, text=text, parse_mode='HTML')
    except TelegramError as e:
        print("Telegram error:", e)
