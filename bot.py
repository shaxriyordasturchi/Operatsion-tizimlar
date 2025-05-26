import sqlite3
import pandas as pd
from datetime import datetime
import pytz
from telegram import Bot, Update, ReplyKeyboardMarkup
from telegram.ext import CommandHandler, MessageHandler, Filters, Updater, CallbackContext

# Vaqt zonasi
def get_current_time_tashkent():
    tz = pytz.timezone('Asia/Tashkent')
    return datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")

# CONFIG
TELEGRAM_BOT_TOKEN = "7817066006:AAHRcf_wJO4Kmq5PvOrdq5BPi_eyv5vYqaM"
ADMIN_IDS = [ 7750409176]  # O'zingizning Telegram ID'ingizni yozing
bot = Bot(token=TELEGRAM_BOT_TOKEN)
DB_PATH = "employees.db"

# DATABASE INIT
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY,
        fullname TEXT,
        salary INTEGER DEFAULT 0
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS attendance (
        username TEXT,
        login_time TEXT,
        logout_time TEXT
    )''')
    conn.commit()
    conn.close()

# START WITH MENU
def start(update: Update, context: CallbackContext):
    keyboard = [
        ["👤 Maoshni ko‘rish", "📥 Hisobot"],
        ["➕ Foydalanuvchi qo‘shish", "❌ Foydalanuvchini o‘chirish"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    update.message.reply_text("👋 Xush kelibsiz! Quyidagi menyudan tanlang:", reply_markup=reply_markup)

# MAOSH
def salary(update: Update, context: CallbackContext):
    username = update.message.from_user.username
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT salary FROM users WHERE username = ?", (username,))
    result = c.fetchone()
    conn.close()
    if result:
        update.message.reply_text(f"💰 Sizning maoshingiz: {result[0]:,} so'm")
    else:
        update.message.reply_text("❌ Siz ro'yxatdan o'tmagansiz.")

# ADD USER
def add_user(update: Update, context: CallbackContext):
    if update.message.from_user.id not in ADMIN_IDS:
        return update.message.reply_text("❌ Sizga ruxsat yo‘q.")
    try:
        username, firstname, lastname = context.args
        fullname = f"{firstname} {lastname}"
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("INSERT INTO users (username, fullname) VALUES (?, ?)", (username, fullname))
        conn.commit()
        conn.close()
        update.message.reply_text(f"✅ {fullname} ({username}) tizimga qo‘shildi.")
    except:
        update.message.reply_text("⚠️ To‘g‘ri format: /add_user username ism familiya")

# REMOVE USER
def remove_user(update: Update, context: CallbackContext):
    if update.message.from_user.id not in ADMIN_IDS:
        return update.message.reply_text("❌ Sizga ruxsat yo‘q.")
    try:
        username = context.args[0]
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("DELETE FROM users WHERE username = ?", (username,))
        conn.commit()
        conn.close()
        update.message.reply_text(f"🗑️ {username} tizimdan o‘chirildi.")
    except:
        update.message.reply_text("⚠️ To‘g‘ri format: /remove_user username")

# HISOBOT
def report(update: Update, context: CallbackContext):
    if update.message.from_user.id not in ADMIN_IDS:
        return update.message.reply_text("❌ Sizga ruxsat yo‘q.")
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query('''
        SELECT u.fullname, u.username, u.salary, a.login_time, a.logout_time
        FROM users u
        LEFT JOIN attendance a ON u.username = a.username
    ''', conn)
    conn.close()
    if df.empty:
        return update.message.reply_text("🗂️ Ma'lumot topilmadi.")
    file_path = "/tmp/hisobot.xlsx"
    df.to_excel(file_path, index=False)
    update.message.reply_document(document=open(file_path, 'rb'), filename="hisobot.xlsx")

# BUTTON FUNCTION
def handle_buttons(update: Update, context: CallbackContext):
    text = update.message.text
    if text == "👤 Maoshni ko‘rish":
        salary(update, context)
    elif text == "📥 Hisobot":
        report(update, context)
    elif text == "➕ Foydalanuvchi qo‘shish":
        update.message.reply_text("Format: /add_user username ism familiya")
    elif text == "❌ Foydalanuvchini o‘chirish":
        update.message.reply_text("Format: /remove_user username")
    else:
        update.message.reply_text("🤖 Noma'lum buyruq.")

# MAIN
def main():
    init_db()
    updater = Updater(TELEGRAM_BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("salary", salary))
    dp.add_handler(CommandHandler("add_user", add_user))
    dp.add_handler(CommandHandler("remove_user", remove_user))
    dp.add_handler(CommandHandler("report", report))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_buttons))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
   
