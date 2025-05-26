from telegram import Bot
from telegram.error import TelegramError

# Mana bu yerga o'zingizning bot tokeningizni joylashtiring
TELEGRAM_BOT_TOKEN = "7817066006:AAHRcf_wJO4Kmq5PvOrdq5BPi_eyv5vYqaM"

# Mana bu yerga o'zingizning Telegram chat ID raqamingizni kiriting (raqam ko'rinishida)
# Agar shaxsiy chat bo'lsa, user ID, guruh bo'lsa, - bilan boshlanadigan raqam bo'ladi.
CHAT_ID =952580219 # misol uchun: 987654321 yoki -123456789

bot = Bot(token=7817066006:AAHRcf_wJO4Kmq5PvOrdq5BPi_eyv5vYqaM)

def send_telegram_message(text: str):
    """
    Telegramga xabar yuboruvchi funksya.
    text: yuboriladigan matn (HTML parse mode bilan qo'llanadi)
    """
    try:
        bot.send_message(952580219, text=text, parse_mode="HTML")
        print("✅ Telegramga xabar yuborildi.")
    except TelegramError as e:
        print(f"❌ Telegramga yuborishda muammo yuz berdi: {e}")

# --- Diagnostic uchun mustaqil ishga tushirish qismi ---

if __name__ == "__main__":
    test_text = "🚀 <b>Bot test xabari</b> yuborilmoqda..."
    send_telegram_message(test_text)
