from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
import sqlite3
from datetime import datetime
import pytz

TOKEN = "7817066006:AAHRcf_wJO4Kmq5PvOrdq5BPi_eyv5vYqaM"
DB_PATH = "worktime.db"
admin_chat_id = 7750409176  # ADMIN CHAT ID

# Vaqt funksiyasi
def get_current_time():
    tz = pytz.timezone("Asia/Tashkent")
    return datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")

# Chat ID ni saqlash
def save_chat_id(username, chat_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE employees SET chat_id = ? WHERE username = ?", (str(chat_id), username))
    conn.commit()
    conn.close()

# Login funksiyasi
def log_login(username):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    now = get_current_time()
    c.execute("SELECT firstname, lastname FROM employees WHERE username = ?", (username,))
    row = c.fetchone()
    if row:
        firstname, lastname = row
        c.execute("INSERT INTO attendance (username, firstname, lastname, login_time) VALUES (?, ?, ?, ?)",
                  (username, firstname, lastname, now))
        conn.commit()
    conn.close()
    return firstname, lastname, now

# Logout funksiyasi
def log_logout(username):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    now = get_current_time()
    c.execute("SELECT firstname, lastname FROM employees WHERE username = ?", (username,))
    row = c.fetchone()
    if row:
        firstname, lastname = row
        c.execute('''
            UPDATE attendance SET logout_time = ? 
            WHERE username = ? AND logout_time IS NULL
            ORDER BY login_time DESC LIMIT 1
        ''', (now, username))
        conn.commit()
    conn.close()
    return firstname, lastname, now

# Bugungi hisobot
def get_today_report():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT firstname, lastname, login_time, logout_time FROM attendance WHERE login_time >= date('now','start of day')")
    rows = c.fetchall()
    conn.close()

    report = "📅 Bugungi qatnashuv:\n\n"
    for fn, ln, li, lo in rows:
        report += f"👤 {fn} {ln}\n🔓 Kirish: {li}\n🔒 Chiqish: {lo or '🚪 Chiqmagan'}\n\n"
    return report if rows else "📭 Bugun hech kim ro‘yxatdan o‘tmagan."

# Start komandasi
def start(update: Update, context: CallbackContext):
    keyboard = [
        ['✅ Kirish', '❌ Chiqish'],
        ['📊 Hisobot', 'ℹ️ Yordam']
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    update.message.reply_text("Salom! Quyidagi menyudan tanlang:", reply_markup=reply_markup)

# Xabarlar boshqaruvi
def handle_message(update: Update, context: CallbackContext):
    msg = update.message.text
    chat_id = update.message.chat_id
    username = update.message.from_user.username

    if not username:
        update.message.reply_text("❗ Iltimos, Telegram username sozlang! (Settings → Username)")
        return

    if msg == '✅ Kirish':
        save_chat_id(username, chat_id)
        firstname, lastname, time = log_login(username)
        update.message.reply_text(f"✅ {firstname} {lastname} ishga kirdi\n🕒 {time}")
        # Adminni xabardor qilish
        context.bot.send_message(chat_id=admin_chat_id, text=f"🔔 {firstname} {lastname} ishga kirdi.\n🕒 {time}")

    elif msg == '❌ Chiqish':
        firstname, lastname, time = log_logout(username)
        update.message.reply_text(f"❌ {firstname} {lastname} ishdan chiqdi\n🕒 {time}")
        # Adminni xabardor qilish
        context.bot.send_message(chat_id=admin_chat_id, text=f"📤 {firstname} {lastname} ishdan chiqdi.\n🕒 {time}")

    elif msg == '📊 Hisobot':
        report = get_today_report()
        update.message.reply_text(report)

    elif msg == 'ℹ️ Yordam':
        update.message.reply_text("ℹ️ Buyruqlar:\n✅ Kirish – Ishga kirishni yozish\n❌ Chiqish – Ishdan chiqishni yozish\n📊 Hisobot – Bugungi qatnashuvni ko‘rish")

    else:
        update.message.reply_text("⚠️ Nomaʼlum buyruq. Iltimos menyudan foydalaning.")

# Botni ishga tushurish
def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    print("🤖 Telegram bot ishga tushdi...")
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
