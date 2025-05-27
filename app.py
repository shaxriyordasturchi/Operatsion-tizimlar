import streamlit as st
import sqlite3
from datetime import datetime, time
import pytz
from telegram import Bot, InputFile
import os
import pandas as pd
from fpdf import fpdf
from apscheduler.schedulers.background import BackgroundScheduler
import bcrypt
from cryptography.fernet import Fernet
from PIL import Image
import io

# Telegram sozlamalari
TELEGRAM_BOT_TOKEN = "7817066006:AAHRcf_wJO4Kmq5PvOrdq5BPi_eyv5vYqaM"
ADMIN_CHAT_ID = "7750409176"  # Hisobot va maoshlar adminga ketadi
bot = Bot(token=TELEGRAM_BOT_TOKEN)

DB_PATH = "worktime.db"
PHOTOS_DIR = "photos"
REPORTS_DIR = "reports"
os.makedirs(PHOTOS_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)

# Shifrlash uchun kalit
ENCRYPTION_KEY = Fernet.generate_key()

# Vaqt olish (Toshkent bo‘yicha)
def get_current_time():
    tz = pytz.timezone("Asia/Tashkent")
    return datetime.now(tz)

# Telegram xabar jo'natish (rasm bilan)
def send_telegram_message(chat_id, message, photo_path=None):
    try:
        if photo_path:
            with open(photo_path, 'rb') as photo:
                bot.send_photo(chat_id=chat_id, photo=photo, caption=message, parse_mode="HTML")
        else:
            bot.send_message(chat_id=chat_id, text=message, parse_mode="HTML")
    except Exception as e:
        st.error(f"Telegram xatosi: {e}")

# Kechikishni tekshirish
def check_late_coming(login_time):
    expected_time = time(9, 0)
    return login_time.time() > expected_time

# Baza va jadvallarni yaratish (yangi versiya)
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Xodimlar jadvali (yangi)
    c.execute('''
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            firstname TEXT,
            lastname TEXT,
            salary INTEGER DEFAULT 0,
            chat_id TEXT,
            role TEXT DEFAULT 'user',
            is_active INTEGER DEFAULT 1
        )
    ''')
    
    # Davomat jadvali (yangi)
    c.execute('''
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            firstname TEXT,
            lastname TEXT,
            login_time TEXT,
            logout_time TEXT,
            selfie_path TEXT,
            location TEXT,
            is_late INTEGER DEFAULT 0,
            FOREIGN KEY(username) REFERENCES employees(username)
        )
    ''')
    
    # Admin foydalanuvchilarni qo'shamiz
    default_users = [
        ("admin", hash_password("admin123"), "Admin", "Adminov", 0, ADMIN_CHAT_ID, "admin", 1),
        ("user", hash_password("user123"), "User", "Userov", 0, "", "user", 1)
    ]
    
    for user in default_users:
        c.execute('''
            INSERT OR IGNORE INTO employees 
            (username, password, firstname, lastname, salary, chat_id, role, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', user)
    
    conn.commit()
    conn.close()

# Parolni hash qilish
def hash_password(password):
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

# Parolni tekshirish
def verify_password(hashed, password):
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

# Foydalanuvchini tekshirish (yangi versiya)
def check_user(username, password):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT password, firstname, lastname FROM employees WHERE username = ?", (username,))
    row = c.fetchone()
    conn.close()
    
    if row and verify_password(row[0], password):
        return row[1], row[2]  # firstname, lastname
    return None, None

# Loginni yozish (yangi versiya)
def log_login(username, firstname, lastname, photo=None, location=None):
    now = get_current_time()
    is_late = check_late_coming(now)
    
    # Rasmni saqlash
    photo_path = None
    if photo:
        photo_path = os.path.join(PHOTOS_DIR, f"{username}_{now.strftime('%Y%m%d_%H%M%S')}.jpg")
        photo.save(photo_path)
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute('''
        INSERT INTO attendance 
        (username, firstname, lastname, login_time, selfie_path, location, is_late)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (username, firstname, lastname, now.strftime("%Y-%m-%d %H:%M:%S"), 
          photo_path, str(location) if location else None, int(is_late)))
    
    conn.commit()
    conn.close()
    
    # Telegramga xabar
    msg = f"✅ <b>{firstname} {lastname}</b> ishga KIRDI\n🕒 {now.strftime('%Y-%m-%d %H:%M:%S')}"
    if is_late:
        msg += "\n⚠️ <b>KECHIKDI!</b>"
    
    send_telegram_message(ADMIN_CHAT_ID, msg, photo_path)
    return is_late

# Logoutni yozish (yangi versiya)
def log_logout(username, firstname, lastname, photo=None):
    now = get_current_time()
    
    # Rasmni saqlash
    photo_path = None
    if photo:
        photo_path = os.path.join(PHOTOS_DIR, f"{username}_{now.strftime('%Y%m%d_%H%M%S')}.jpg")
        photo.save(photo_path)
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute('''
        UPDATE attendance SET logout_time = ?, selfie_path = ?
        WHERE username = ? AND logout_time IS NULL
        ORDER BY login_time DESC LIMIT 1
    ''', (now.strftime("%Y-%m-%d %H:%M:%S"), photo_path, username))
    
    conn.commit()
    conn.close()
    
    # Telegramga xabar
    msg = f"❌ <b>{firstname} {lastname}</b> ishdan CHIQDI\n🕒 {now.strftime('%Y-%m-%d %H:%M:%S')}"
    send_telegram_message(ADMIN_CHAT_ID, msg, photo_path)

# Hisobot yaratish (PDF)
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
    
    report_path = os.path.join(REPORTS_DIR, f"{period}_report.pdf")
    pdf.output(report_path)
    
    return report_path

# Kunlik hisobotni yuborish
def send_daily_report():
    report_path = generate_report('daily')
    with open(report_path, 'rb') as report:
        bot.send_document(chat_id=ADMIN_CHAT_ID, document=report, caption="📊 Kunlik hisobot")

# Maosh boshqaruvi (yangi versiya)
def manage_salary():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, username, firstname, lastname, salary FROM employees WHERE is_active = 1")
    rows = c.fetchall()

    st.subheader("💰 Maosh boshqaruvi")
    
    # Maoshlarni yangilash
    for row in rows:
        id_, username, firstname, lastname, salary = row
        new_salary = st.number_input(
            f"{firstname} {lastname} ({username})",
            min_value=0, 
            value=salary or 0, 
            step=100000,
            key=f"salary_{id_}"
        )
        if new_salary != salary:
            c.execute("UPDATE employees SET salary = ? WHERE id = ?", (new_salary, id_))
    
    conn.commit()
    
    # Maoshlarni yuborish
    if st.button("📤 Maoshlarni yuborish"):
        c.execute("SELECT firstname, lastname, salary, chat_id FROM employees WHERE is_active = 1")
        for fn, ln, sal, chat_id in c.fetchall():
            if chat_id:
                send_telegram_message(chat_id, f"📢 <b>Hurmatli {fn} {ln}, sizning maoshingiz: 💵 {sal:,} so'm</b>")
        st.success("✅ Barcha maoshlar yuborildi.")
    
    conn.close()

# Foydalanuvchi qo'shish/o'chirish
def manage_users():
    st.subheader("👥 Foydalanuvchi boshqaruvi")
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Yangi foydalanuvchi qo'shish
    with st.expander("➕ Yangi foydalanuvchi qo'shish"):
        with st.form("new_user_form"):
            username = st.text_input("Login")
            password = st.text_input("Parol", type="password")
            firstname = st.text_input("Ism")
            lastname = st.text_input("Familiya")
            role = st.selectbox("Rol", ["user", "admin"])
            salary = st.number_input("Maosh", min_value=0, value=0, step=100000)
            
            if st.form_submit_button("Qo'shish"):
                try:
                    c.execute('''
                        INSERT INTO employees 
                        (username, password, firstname, lastname, role, salary)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (username, hash_password(password), firstname, lastname, role, salary))
                    conn.commit()
                    st.success("✅ Foydalanuvchi qo'shildi!")
                except sqlite3.IntegrityError:
                    st.error("❌ Bu login band!")
    
    # Mavjud foydalanuvchilar
    st.subheader("📝 Foydalanuvchilar ro'yxati")
    c.execute("SELECT id, username, firstname, lastname, role, is_active FROM employees")
    users = c.fetchall()
    
    for user in users:
        id_, username, firstname, lastname, role, is_active = user
        col1, col2, col3 = st.columns([3, 2, 1])
        
        with col1:
            st.write(f"👤 {firstname} {lastname} ({username}) - {role}")
        
        with col2:
            new_status = st.selectbox(
                "Holat",
                ["Aktiv", "Noaktiv"],
                index=0 if is_active else 1,
                key=f"status_{id_}"
            )
            if (new_status == "Aktiv" and not is_active) or (new_status == "Noaktiv" and is_active):
                c.execute("UPDATE employees SET is_active = ? WHERE id = ?", (1 if new_status == "Aktiv" else 0, id_))
                conn.commit()
        
        with col3:
            if st.button("🗑️", key=f"delete_{id_}"):
                c.execute("DELETE FROM employees WHERE id = ?", (id_,))
                conn.commit()
                st.experimental_rerun()
    
    conn.close()

# Asosiy funksiya (yangi versiya)
def main():
    st.set_page_config(
        page_title="Xodimlar Monitoring Tizimi", 
        layout="wide",
        page_icon="🧑‍💼"
    )
    
    init_db()
    
    # Avtomatik hisobot jo'natish
    scheduler = BackgroundScheduler()
    scheduler.add_job(send_daily_report, 'cron', hour=17, minute=0)
    scheduler.start()
    
    st.title("🧑‍💼 Xodimlar Monitoring Tizimi")
    
    menu = ["Kirish/Chiqish", "Hisobotlar", "Maosh boshqaruvi", "Foydalanuvchi boshqaruvi"]
    choice = st.sidebar.selectbox("Menyu", menu)
    
    if choice == "Kirish/Chiqish":
        st.header("🔑 Kirish/Chiqish")
        
        login = st.text_input("Login")
        password = st.text_input("Parol", type="password")
        action = st.radio("Amalni tanlang", ["Kirish", "Chiqish"])
        
        if action in ["Kirish", "Chiqish"]:
            if action == "Kirish":
                st.info("Iltimos, kirish uchun selfie yuboring")
                photo = st.camera_input("Selfie olish")
                location = st.text_input("Joylashuv (kenglik, uzunlik)", help="Masalan: 41.311081, 69.240562")
            else:
                st.info("Iltimos, chiqish uchun selfie yuboring")
                photo = st.camera_input("Selfie olish")
                location = None
            
            if st.button(action):
                firstname, lastname = check_user(login, password)
                if firstname:
                    if action == "Kirish":
                        # Rasmni olish
                        img = None
                        if photo:
                            img = Image.open(io.BytesIO(photo.getvalue()))
                        
                        # Joylashuvni ajratib olish
                        loc = None
                        if location:
                            try:
                                lat, lon = map(float, location.split(','))
                                loc = (lat, lon)
                            except:
                                st.warning("Joylashuv noto'g'ri kiritildi")
                        
                        is_late = log_login(login, firstname, lastname, img, loc)
                        msg = f"✅ Xush kelibsiz, {firstname} {lastname}"
                        if is_late:
                            msg += "\n⚠️ Siz kechikdingiz!"
                        st.success(msg)
                    else:
                        # Rasmni olish
                        img = None
                        if photo:
                            img = Image.open(io.BytesIO(photo.getvalue()))
                        
                        log_logout(login, firstname, lastname, img)
                        st.success(f"✅ Xayr, {firstname} {lastname}")
                else:
                    st.error("❌ Login yoki parol noto‘g‘ri!")
    
    elif choice == "Hisobotlar":
        st.header("📊 Hisobotlar")
        
        report_type = st.selectbox("Hisobot turi", ["Kunlik", "Haftalik", "Oylik"])
        
        if st.button("Hisobot yaratish"):
            period = report_type.lower().replace('lik', 'ly')
            report_path = generate_report(period)
            
            with open(report_path, "rb") as f:
                st.download_button(
                    label="📥 Hisobotni yuklab olish",
                    data=f,
                    file_name=f"{period}_report.pdf",
                    mime="application/pdf"
                )
            
            if st.button("Telegramga yuborish"):
                with open(report_path, "rb") as f:
                    bot.send_document(chat_id=ADMIN_CHAT_ID, document=f, caption=f"{report_type} hisobot")
                st.success("✅ Hisobot yuborildi!")
        
        # Bugungi qatnashuv jadvali
        st.subheader("📅 Bugungi qatnashuv")
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql("""
            SELECT firstname || ' ' || lastname as name, 
                   login_time as kirish, 
                   logout_time as chiqish,
                   CASE WHEN is_late THEN 'Ha' ELSE 'Yo\'q' END as kechikdi
            FROM attendance 
            WHERE date(login_time) = date('now')
            ORDER BY login_time
        """, conn)
        conn.close()
        
        if not df.empty:
            st.dataframe(df.style.applymap(
                lambda x: 'color: red' if x == 'Ha' else 'color: green', 
                subset=['kechikdi']
            ))
        else:
            st.warning("Bugun hech qanday yozuv yo'q")
    
    elif choice == "Maosh boshqaruvi":
        st.header("💰 Maosh boshqaruvi")
        manage_salary()
    
    elif choice == "Foydalanuvchi boshqaruvi":
        st.header("👥 Foydalanuvchi boshqaruvi")
        manage_users()

if __name__ == "__main__":
    main()
