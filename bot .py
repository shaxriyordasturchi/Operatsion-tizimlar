from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InputFile
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
import sqlite3
from datetime import datetime, time
import pytz
import bcrypt
import os
from cryptography.fernet import Fernet
import pandas as pd
from fpdf import FPDF
from apscheduler.schedulers.background import BackgroundScheduler

# Konfiguratsiya
TOKEN = "7817066006:AAHRcf_wJO4Kmq5PvOrdq5BPi_eyv5vYqaM"
DB_PATH = "worktime.db"
admin_chat_id = 7750409176  # ADMIN CHAT ID
ENCRYPTION_KEY = Fernet.generate_key()  # Shifrlash uchun kalit

# Vaqt funksiyalari
def get_current_time():
    tz = pytz.timezone("Asia/Tashkent")
    return datetime.now(tz)

def format_time(dt):
    return dt.strftime("%Y-%m-%d %H:%M:%S")

# Parolni hash qilish
def hash_password(password):
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

# Parolni tekshirish
def check_password(hashed, password):
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

# Ma'lumotlarni shifrlash
def encrypt_data(data):
    fernet = Fernet(ENCRYPTION_KEY)
    return fernet.encrypt(data.encode()).decode()

# Ma'lumotlarni deshifrlash
def decrypt_data(encrypted):
    fernet = Fernet(ENCRYPTION_KEY)
    return fernet.decrypt(encrypted.encode()).decode()

# Kechikishni tekshirish
def check_late_coming(login_time):
    expected_time = time(9, 0)
    return login_time.time() > expected_time

# Adminlarga xabar yuborish
def notify_admins(context: CallbackContext, message, photo_path=None):
    if photo_path:
        with open(photo_path, 'rb') as photo:
            context.bot.send_photo(chat_id=admin_chat_id, photo=photo, caption=message)
    else:
        context.bot.send_message(chat_id=admin_chat_id, text=message)

# Database funksiyalari
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Xodimlar jadvali
    c.execute('''CREATE TABLE IF NOT EXISTS employees
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                 username TEXT UNIQUE,
                 password TEXT,
                 firstname TEXT,
                 lastname TEXT,
                 chat_id TEXT,
                 role TEXT DEFAULT 'user',
                 is_active INTEGER DEFAULT 1)''')
    
    # Davomat jadvali
    c.execute('''CREATE TABLE IF NOT EXISTS attendance
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                 username TEXT,
                 firstname TEXT,
                 lastname TEXT,
                 login_time TEXT,
                 logout_time TEXT,
                 selfie_path TEXT,
                 location TEXT,
                 is_late INTEGER DEFAULT 0,
                 FOREIGN KEY(username) REFERENCES employees(username))''')
    
    conn.commit()
    conn.close()

# Login funksiyasi (yangi versiya)
def log_login(username, photo_path=None, location=None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    now = get_current_time()
    
    c.execute("SELECT firstname, lastname FROM employees WHERE username = ?", (username,))
    row = c.fetchone()
    
    if row:
        firstname, lastname = row
        is_late = 1 if check_late_coming(now) else 0
        
        c.execute('''INSERT INTO attendance 
                     (username, firstname, lastname, login_time, selfie_path, location, is_late) 
                     VALUES (?, ?, ?, ?, ?, ?, ?)''',
                  (username, firstname, lastname, format_time(now), photo_path, str(location), is_late))
        conn.commit()
    
    conn.close()
    return firstname, lastname, now, is_late

# Logout funksiyasi (yangi versiya)
def log_logout(username, photo_path=None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    now = get_current_time()
    
    c.execute("SELECT firstname, lastname FROM employees WHERE username = ?", (username,))
    row = c.fetchone()
    
    if row:
        firstname, lastname = row
        c.execute('''UPDATE attendance SET logout_time = ?, selfie_path = ?
                     WHERE username = ? AND logout_time IS NULL
                     ORDER BY login_time DESC LIMIT 1''',
                  (format_time(now), photo_path, username))
        conn.commit()
    
    conn.close()
    return firstname, lastname, now

# Hisobotlar
def generate_report(period='daily'):
    conn = sqlite3.connect(DB_PATH)
    
    query = """SELECT firstname, lastname, login_time, logout_time, is_late 
               FROM attendance"""
    
    if period == 'daily':
        query += " WHERE date(login_time) = date('now')"
    elif period == 'weekly':
        query += " WHERE date(login_time) >= date('now', 'weekday 0', '-7 days')"
    elif period == 'monthly':
        query += " WHERE strftime('%Y-%m', login_time) = strftime('%Y-%m', 'now')"
    
    df = pd.read_sql(query, conn)
    conn.close()
    
    # PDF hisobot yaratish
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    title = f"{period.capitalize()} Report".replace('ly', 'l')
    pdf.cell(200, 10, txt=title, ln=1, align='C')
    
    # Jadval uchun sarlavha
    pdf.cell(40, 10, 'Name', 1)
    pdf.cell(30, 10, 'Login', 1)
    pdf.cell(30, 10, 'Logout', 1)
    pdf.cell(20, 10, 'Late', 1)
    pdf.ln()
    
    for _, row in df.iterrows():
        pdf.cell(40, 10, f"{row['firstname']} {row['lastname']}", 1)
        pdf.cell(30, 10, row['login_time'][11:19], 1)
        pdf.cell(30, 10, row['logout_time'][11:19] if row['logout_time'] else '-', 1)
        pdf.cell(20, 10, 'Yes' if row['is_late'] else 'No', 1)
        pdf.ln()
    
    report_path = f"reports/{period}_report.pdf"
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    pdf.output(report_path)
    
    return report_path

# Kunlik hisobotni avtomatik yuborish
def send_daily_report(context: CallbackContext):
    report_path = generate_report('daily')
    with open(report_path, 'rb') as report:
        context.bot.send_document(chat_id=admin_chat_id, document=report, caption="📊 Kunlik hisobot")

# Bot handlers
def start(update: Update, context: CallbackContext):
    keyboard = [
        [KeyboardButton('✅ Kirish', request_location=True)],
        [KeyboardButton('❌ Chiqish', request_location=True)],
        ['📊 Hisobot', 'ℹ️ Yordam']
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    update.message.reply_text("Salom! Quyidagi menyudan tanlang:", reply_markup=reply_markup)

def handle_message(update: Update, context: CallbackContext):
    msg = update.message.text
    chat_id = update.message.chat_id
    username = update.message.from_user.username

    if not username:
        update.message.reply_text("❗ Iltimos, Telegram username sozlang! (Settings → Username)")
        return

    if msg == '✅ Kirish':
        update.message.reply_text("Iltimos, joylashuvingizni yuboring yoki 'Kirish' tugmasini bosing", 
                                reply_markup=ReplyKeyboardMarkup([[KeyboardButton('Joylashuvni yuborish', request_location=True)]], resize_keyboard=True))
        context.user_data['action'] = 'login'

    elif msg == '❌ Chiqish':
        update.message.reply_text("Iltimos, selfi yuboring", 
                                reply_markup=ReplyKeyboardMarkup([[KeyboardButton('Selfi yuborish')]], resize_keyboard=True))
        context.user_data['action'] = 'logout'

    elif msg == '📊 Hisobot':
        report = get_today_report()
        update.message.reply_text(report)

    elif msg == 'ℹ️ Yordam':
        update.message.reply_text("ℹ️ Buyruqlar:\n✅ Kirish – Ishga kirish\n❌ Chiqish – Ishdan chiqish\n📊 Hisobot – Bugungi hisobot\n📍 Joylashuv – Geolokatsiya")

def handle_location(update: Update, context: CallbackContext):
    user = update.message.from_user
    location = update.message.location
    action = context.user_data.get('action')
    
    if action == 'login':
        # Selfie so'raymiz
        update.message.reply_text("Endi selfie yuboring")
        context.user_data['location'] = (location.latitude, location.longitude)
    else:
        update.message.reply_text("Noma'lum amal")

def handle_photo(update: Update, context: CallbackContext):
    user = update.message.from_user
    photo = update.message.photo[-1]
    action = context.user_data.get('action')
    
    # Rasmni saqlash
    photo_file = photo.get_file()
    photo_path = f"photos/{user.id}_{get_current_time().strftime('%Y%m%d_%H%M%S')}.jpg"
    os.makedirs(os.path.dirname(photo_path), exist_ok=True)
    photo_file.download(photo_path)
    
    if action == 'login':
        location = context.user_data.get('location')
        firstname, lastname, time, is_late = log_login(user.username, photo_path, location)
        
        msg = f"✅ {firstname} {lastname} ishga kirdi\n🕒 {format_time(time)}"
        if is_late:
            msg += "\n⚠️ Kechikish qayd etildi!"
        
        update.message.reply_text(msg)
        notify_admins(context, f"🔔 {firstname} {lastname} ishga kirdi.\n🕒 {format_time(time)}", photo_path)
    
    elif action == 'logout':
        firstname, lastname, time = log_logout(user.username, photo_path)
        update.message.reply_text(f"❌ {firstname} {lastname} ishdan chiqdi\n🕒 {format_time(time)}")
        notify_admins(context, f"📤 {firstname} {lastname} ishdan chiqdi.\n🕒 {format_time(time)}", photo_path)
    
    # Foydalanuvchi holatini tozalash
    context.user_data.clear()

def main():
    # Ma'lumotlar bazasini ishga tushirish
    init_db()
    
    # Avtomatik hisobot jo'natish
    scheduler = BackgroundScheduler()
    scheduler.add_job(send_daily_report, 'cron', hour=17, minute=0, args=[Updater.dispatcher])
    scheduler.start()
    
    # Botni ishga tushurish
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
    dp.add_handler(MessageHandler(Filters.location, handle_location))
    dp.add_handler(MessageHandler(Filters.photo, handle_photo))

    print("🤖 Bot ishga tushdi...")
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
