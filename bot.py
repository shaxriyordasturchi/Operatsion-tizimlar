from telegram import Bot

TELEGRAM_BOT_TOKEN = "7817066006:AAHRcf_wJO4Kmq5PvOrdq5BPi_eyv5vYqaM"
CHAT_ID = " 7750409176"  # raqam ko'rinishida (integer) bo'lsa yaxshi

bot = Bot(token=TELEGRAM_BOT_TOKEN)

def send_telegram_message(message):
    try:
        bot.send_message(chat_id=CHAT_ID, text=message, parse_mode="HTML")
        print("Telegramga habar yuborildi ✅")
    except Exception as e:
        print(f"❌ Telegramga habar yuborishda muammo yuz berdi: {e}")

if __name__ == "__main__":
    send_telegram_message("Salom! Bu test habar.")
