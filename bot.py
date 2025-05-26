from telegram import Bot

# Telegram Bot tokeningizni shu yerga yozing
TELEGRAM_BOT_TOKEN = "7817066006:AAHRcf_wJO4Kmq5PvOrdq5BPi_eyv5vYqaM"

# Telegram chat ID (o'zingizning user ID yoki guruh ID raqami)
CHAT_ID = 7750409176  # raqam ko'rinishida, masalan: 987654321

bot = Bot(token=TELEGRAM_BOT_TOKEN)

def send_telegram_message(message: str):
    """
    Telegramga xabar yuboruvchi funksiya.
    message - yuboriladigan matn (HTML formatda bo'lishi mumkin).
    """
    try:
        bot.send_message(chat_id=CHAT_ID, text=message, parse_mode="HTML")
        print("✅ Telegramga habar yuborildi!")
    except Exception as e:
        print(f"❌ Telegramga habar yuborishda xatolik yuz berdi: {e}")
