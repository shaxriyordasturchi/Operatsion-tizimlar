from telegram import Bot
from telegram.error import TelegramError
import logging

# Telegram bot tokeningizni shu yerga yozing
TELEGRAM_TOKEN = "7899690264:AAH14dhEGOlvRoc4CageMH6WYROMEE5NmkY"
CHAT_ID = "-1002671611327"  # Sizga xabar yuboriladigan chat id (odatda adminning telegram idsi)

bot = Bot(token=TELEGRAM_TOKEN)

def send_telegram_message(message: str):
    try:
        bot.send_message(chat_id=CHAT_ID, text=message, parse_mode="HTML")
        print("✅ Xabar Telegramga yuborildi.")
    except TelegramError as e:
        logging.error(f"Telegramga xabar yuborishda xatolik yuz berdi: {e}")
        print("❌ Telegramga yuborishda muammo yuz berdi.")
