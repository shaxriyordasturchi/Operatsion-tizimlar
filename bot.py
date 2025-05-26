from telegram import Bot
from telegram.error import TelegramError
from config import 7899690264:AAH14dhEGOlvRoc4CageMH6WYROMEE5NmkY, -1002671611327

bot = Bot(token=7899690264:AAH14dhEGOlvRoc4CageMH6WYROMEE5NmkY)

def send_telegram_message(text):
    try:
        bot.send_message(chat_id=-1002671611327, text=text, parse_mode='HTML')
    except TelegramError as e:
        print("Telegram error:", e)
