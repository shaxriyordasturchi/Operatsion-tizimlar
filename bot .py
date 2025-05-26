from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackContext

TOKEN = "7817066006:AAHRcf_wJO4Kmq5PvOrdq5BPi_eyv5vYqaM"

def start(update: Update, context: CallbackContext):
    keyboard = [
        ['✅ Kirish', '❌ Chiqish'],
        ['📊 Hisobot', 'ℹ️ Yordam']
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)
    update.message.reply_text(
        "Salom! Quyidagi menyudan tanlang:",
        reply_markup=reply_markup
    )

def main():
    updater = Updater(TOKEN)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))

    print("Bot ishga tushdi...")
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
