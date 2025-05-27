import streamlit as st
import sqlite3
from datetime import datetime
import pytz
from telegram import Bot

# Telegram sozlamalari
TELEGRAM_BOT_TOKEN = "7817066006:AAHRcf_wJO4Kmq5PvOrdq5BPi_eyv5vYqaM"
ADMIN_CHAT_ID = "7750409176"  # Hisobot va maoshlar adminga ketadi
bot = Bot(token=TELEGRAM_BOT_TOKEN)

DB_PATH = "worktime.db"

# Foydalanuvchilar (Login, Parol, Ism, Familiya)
users = {
    "ali": ("1234", "Ali", "Valiyev"),
    "john": ("abcd", "John", "Doe"),
    "jane": ("pass", "Jane", "Doe"),
}

# Vaqt olish (Toshkent bo‘yicha)
def get_current_time():
    tz = pytz.timezone("Asia/Tashkent")
    return datetime.now(tz)

# Telegram xabar jo‘natish
def send_telegram_message(chat_id, message):
    try:
        bot.send_message(chat_id=chat_id, text=message, parse_mode="HTML")
    except Exception as e:
        st.error(f"Telegram xatosi: {e}")

# Baza va jadvallarni yaratish
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            firstname TEXT,
            lastname TEXT,
            login_time TEXT,
            logout_time TEXT
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS employees (
            username TEXT PRIMARY KEY,
            firstname TEXT,
            lastname TEXT,
            salary INTEGER,
            chat_id TEXT
        )
    ''')

    # Namuna foydalanuvchilarni qo‘shish
    for k, v in users.items():
        c.execute('''
            INSERT OR IGNORE INTO employees (username, firstname, lastname, salary, chat_id)
            VALUES (?, ?, ?, ?, ?)
        ''', (k, v[1], v[2], 0, ADMIN_CHAT_ID))  # Admin chat IDni vaqtincha ularga biriktiramiz

    conn.commit()
    conn.close()

# Foydalanuvchini tekshirish
def check_user(username, password):
    if username in users and users[username][0] == password:
        return users[username][1], users[username][2]
    return None, None

# Loginni yozish
def log_login(username, firstname, lastname):
    now = get_current_time()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO attendance (username, firstname, lastname, login_time) VALUES (?, ?, ?, ?)",
              (username, firstname, lastname, now.strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()

    chat_id = get_chat_id(username)
    if chat_id:
        send_telegram_message(chat_id, f"✅ <b>{firstname} {lastname}</b> ishga KIRDI.\n🕒 {now.strftime('%Y-%m-%d %H:%M:%S')}")

# Logoutni yozish
def log_logout(username, firstname, lastname):
    now = get_current_time()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        UPDATE attendance SET logout_time = ? 
        WHERE username = ? AND logout_time IS NULL
        ORDER BY login_time DESC LIMIT 1
    ''', (now.strftime("%Y-%m-%d %H:%M:%S"), username))
    conn.commit()
    conn.close()

    chat_id = get_chat_id(username)
    if chat_id:
        send_telegram_message(chat_id, f"❌ <b>{firstname} {lastname}</b> ishdan CHIQDI.\n🕒 {now.strftime('%Y-%m-%d %H:%M:%S')}")

# Telegram chat ID olish
def get_chat_id(username):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT chat_id FROM employees WHERE username = ?", (username,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else None

# Bugungi qatnashuvlarni olish
def get_attendance_summary():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT firstname, lastname, login_time, logout_time FROM attendance WHERE login_time >= date('now','start of day')")
    data = c.fetchall()
    conn.close()
    return data

# Kunlik hisobot yuborish
def send_daily_report():
    rows = get_attendance_summary()
    msg = "📅 <b>Bugungi ish faoliyati:</b>\n"
    for row in rows:
        fn, ln, li, lo = row
        msg += f"👤 {fn} {ln}\n🔓 Kirish: {li}\n🔒 Chiqish: {lo or '🚪 Chiqmagan'}\n\n"
    send_telegram_message(ADMIN_CHAT_ID, msg)

# Maosh boshqaruvi
def manage_salary():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT username, firstname, lastname, salary FROM employees")
    rows = c.fetchall()

    st.subheader("💰 Maosh belgilash:")
    for row in rows:
        username, firstname, lastname, salary = row
        new_salary = st.number_input(f"{firstname} {lastname}", min_value=0, value=salary or 0, step=100000)
        if new_salary != salary:
            c.execute("UPDATE employees SET salary = ? WHERE username = ?", (new_salary, username))

    conn.commit()

    if st.button("📤 Maoshlarni Telegramga yuborish"):
        c.execute("SELECT firstname, lastname, salary, chat_id FROM employees")
        for fn, ln, sal, chat_id in c.fetchall():
            if chat_id:
                send_telegram_message(chat_id, f"📢 <b>Hurmatli {fn} {ln}, sizning maoshingiz: 💵 {sal} so'm</b>")
        st.success("✅ Barcha maoshlar yuborildi.")
    conn.close()

# Asosiy funksiya
def main():
    st.set_page_config(page_title="Xodimlar Monitoring", layout="centered")
    st.title("🧑‍💼 Xodimlar Kirish/Chiqish Paneli")
    init_db()

    menu = ["Kirish", "Chiqish", "Kunlik hisobot yuborish", "Maosh belgilash va yuborish"]
    choice = st.selectbox("Amalni tanlang", menu)

    if choice in ["Kirish", "Chiqish"]:
        login = st.text_input("Login")
        password = st.text_input("Parol", type="password")
        if st.button("Tasdiqlash"):
            firstname, lastname = check_user(login, password)
            if firstname:
                if choice == "Kirish":
                    log_login(login, firstname, lastname)
                    st.success(f"Xush kelibsiz, {firstname} {lastname}")
                else:
                    log_logout(login, firstname, lastname)
                    st.success(f"Xayr, {firstname} {lastname}")
            else:
                st.error("❌ Login yoki parol noto‘g‘ri!")

    elif choice == "Kunlik hisobot yuborish":
        send_daily_report()
        st.success("✅ Hisobot Telegramga yuborildi.")

    elif choice == "Maosh belgilash va yuborish":
        manage_salary()

    # Bugungi qatnashuvni ko‘rsatish
    st.subheader("📊 Bugungi qatnashuv:")
    for row in get_attendance_summary():
        fn, ln, li, lo = row
        st.write(f"👤 {fn} {ln}: ⏰ {li} | 🔚 {lo or 'Hali chiqmagan'}")

if __name__ == "__main__":
    main()
