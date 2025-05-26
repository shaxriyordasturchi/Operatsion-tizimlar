from telegram import Bot

# Telegram bot tokeningizni shu yerga yozing
TELEGRAM_BOT_TOKEN = "7817066006:AAHRcf_wJO4Kmq5PvOrdq5BPi_eyv5vYqaM"

# Telegram chat ID (bu sizning shaxsiy user ID yoki guruh ID bo'lishi mumkin)
# Guruh IDsi odatda -100 bilan boshlanadi va uzun raqam bo'ladi.
CHAT_ID = -1002671611327  # o'zingizga mos raqam qo'ying

# Botni yaratamiz
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

# Agar shu fayl to'g'ridan-to'g'ri ishga tushirilsa, test xabarini yuboramiz
if __name__ == "__main__":
    send_telegram_message("🚀 Bot ishlayapti! Test xabari.")
