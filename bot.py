import sqlite3
from datetime import datetime
import pandas as pd
from telegram import Bot, Update
from telegram.ext import CommandHandler, MessageHandler, Filters, Updater, CallbackContext
def get_current_time_tashkent():
    tz = pytz.timezone('Asia/Tashkent')

# ====== CONFIGURATION ======
TELEGRAM_BOT_TOKEN = "7817066006:AAHRcf_wJO4Kmq5PvOrdq5BPi_eyv5vYqaM"
ADMIN_IDS = [7750409176]  # Replace with your Telegram user ID

bot = Bot(token=TELEGRAM_BOT_TOKEN)
DB_PATH = "employees.db"

# ====== DATABASE INIT ======
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

# ====== BOT COMMANDS ======

def start(update: Update, context: CallbackContext):
    update.message.reply_text("👋 Xush kelibsiz! /salary, /report, /add_user, /remove_user buyrug'idan foydalaning.")

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
    except Exception as e:
        update.message.reply_text("⚠️ Foydalanuvchi qo‘shishda xatolik: /add_user username ism familiya")

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
        update.message.reply_text("⚠️ Foydalanuvchini o‘chirishda xatolik: /remove_user username")

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
        return update.message.reply_text("🗂️ Hozircha ma'lumot yo‘q.")
    file_path = "/tmp/hisobot.xlsx"
    df.to_excel(file_path, index=False)
    update.message.reply_document(document=open(file_path, 'rb'), filename="hisobot.xlsx")

# ====== ATTENDANCE LOGGING EXAMPLE FUNCTION ======
def log_attendance(username, action="login"):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    if action == "login":
        c.execute("INSERT INTO attendance (username, login_time) VALUES (?, ?)", (username, now))
    elif action == "logout":
        c.execute("UPDATE attendance SET logout_time = ? WHERE username = ? AND logout_time IS NULL", (now, username))
    conn.commit()
    conn.close()

# ====== MAIN ======
def main():
    init_db()
    updater = Updater(TELEGRAM_BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("salary", salary))
    dp.add_handler(CommandHandler("add_user", add_user))
    dp.add_handler(CommandHandler("remove_user", remove_user))
    dp.add_handler(CommandHandler("report", report))

    updater.start_polling()
    updater.idle()

main()
