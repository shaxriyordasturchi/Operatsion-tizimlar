import streamlit as st
from datetime import datetime
import sqlite3
from telegram import Bot
import pytz
import time  # real-time uchun

# Telegram sozlamalari
TELEGRAM_BOT_TOKEN = "7817066006:AAHRcf_wJO4Kmq5PvOrdq5BPi_eyv5vYqaM"
CHAT_ID = 7750409176
bot = Bot(token=TELEGRAM_BOT_TOKEN)

def send_telegram_message(message: str):
    try:
        bot.send_message(chat_id=CHAT_ID, text=message, parse_mode="HTML")
    except Exception as e:
        st.error(f"❌ Telegram xabari yuborilmadi: {e}")

DB_PATH = "worktime.db"

# Foydalanuvchilar
users = {
    "ali": ("1234", "Ali", "Valiyev"),
    "john": ("abcd", "John", "Doe"),
    "jane": ("pass", "Jane", "Doe"),
}

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
    conn.commit()
    conn.close()

def get_current_time():
    tz = pytz.timezone('Asia/Tashkent')
    return datetime.now(tz)

def check_user(username, password):
    if username in users and users[username][0] == password:
        return users[username][1], users[username][2]
    return None, None

def log_login(username, firstname, lastname):
    now = get_current_time()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO attendance (username, firstname, lastname, login_time) VALUES (?, ?, ?, ?)",
              (username, firstname, lastname, now.strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()
    send_telegram_message(f"✅ <b>{firstname} {lastname}</b> KIRDI.\n🕒 {now.strftime('%Y-%m-%d %H:%M:%S')}")

def log_logout(username, firstname, lastname):
    now = get_current_time()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        UPDATE attendance 
        SET logout_time = ? 
        WHERE username = ? AND logout_time IS NULL
        ORDER BY login_time DESC LIMIT 1
    ''', (now.strftime("%Y-%m-%d %H:%M:%S"), username))
    conn.commit()
    conn.close()
    send_telegram_message(f"❌ <b>{firstname} {lastname}</b> CHIQDI.\n🕒 {now.strftime('%Y-%m-%d %H:%M:%S')}")

def send_failed_login_alert(username):
    now = get_current_time()
    send_telegram_message(f"⚠️ Noto‘g‘ri login: <b>{username}</b>\n🕒 {now.strftime('%Y-%m-%d %H:%M:%S')}")

def get_attendance_summary():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        SELECT firstname, lastname, login_time, logout_time FROM attendance
        WHERE login_time >= date('now','start of day')
    ''')
    rows = c.fetchall()
    conn.close()
    return rows

def send_daily_report():
    rows = get_attendance_summary()
    if not rows:
        send_telegram_message("📅 Bugungi ish faoliyati haqida ma'lumot yo'q.")
        return
    msg = "📅 <b>Bugungi ish faoliyati:</b>\n"
    for row in rows:
        firstname, lastname, login_time, logout_time = row
        logout_time = logout_time if logout_time else "🚪 Chiqmagan"
        msg += f"👤 {firstname} {lastname}\n  Kirish: {login_time}\n  Chiqish: {logout_time}\n"
    send_telegram_message(msg)

def show_realtime_clock():
    clock_placeholder = st.empty()
    now = get_current_time().strftime("%Y-%m-%d  ⏰ %H:%M:%S")
    clock_placeholder.markdown(f"### 📆 Bugungi sana va vaqt: `{now}`")

def main():
    st.set_page_config(page_title="Xodimlar Monitoring", page_icon="🧑‍💼", layout="centered")
    st.title("🧑‍💼 Xodimlar Kirish/Chiqish Paneli")

    show_realtime_clock()
    init_db()

    menu = ["Kirish", "Chiqish", "Kunlik hisobot yuborish (admin)"]
    choice = st.selectbox("Amalni tanlang", menu)

    login = st.text_input("Login")
    password = st.text_input("Parol", type="password")

    if st.button("Tasdiqlash"):
        if choice == "Kunlik hisobot yuborish (admin)":
            send_daily_report()
            st.success("✅ Hisobot Telegramga yuborildi.")
            return

        firstname, lastname = check_user(login, password)
        if firstname:
            if choice == "Kirish":
                log_login(login, firstname, lastname)
                st.success(f"Xush kelibsiz, {firstname} {lastname}!")
            else:
                log_logout(login, firstname, lastname)
                st.success(f"Xayr, {firstname} {lastname}!")
        else:
            send_failed_login_alert(login)
            st.error("❌ Login yoki parol noto‘g‘ri!")

    st.subheader("📊 Bugungi qatnashuv:")
    rows = get_attendance_summary()
    if rows:
        for row in rows:
            fn, ln, li, lo = row
            st.write(f"👤 {fn} {ln}: 🟢 {li} | 🔴 {lo or 'Hali chiqmagan'}")
    else:
        st.info("Bugun uchun hech qanday yozuv yo‘q.")

if __name__ == "__main__":
    main()
