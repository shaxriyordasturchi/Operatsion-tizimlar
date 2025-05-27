import streamlit as st
import sqlite3
import datetime
import telebot

# --- Telegram bot sozlamalari ---
TELEGRAM_TOKEN = "7817066006:AAHRcf_wJO4Kmq5PvOrdq5BPi_eyv5vYqaM"
ADMIN_CHAT_ID = 7750409176

bot = telebot.TeleBot(TELEGRAM_TOKEN)

DB_PATH = "users_logins.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            firstname TEXT,
            lastname TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS logins (
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

def add_user(username, password, firstname, lastname):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (username, password, firstname, lastname) VALUES (?, ?, ?, ?)",
                  (username, password, firstname, lastname))
        conn.commit()
    except sqlite3.IntegrityError:
        pass
    conn.close()

def check_user(username, password):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
    user = c.fetchone()
    conn.close()
    return user

def log_login(user):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    now = datetime.datetime.now().isoformat(timespec='seconds')
    c.execute("INSERT INTO logins (username, firstname, lastname, login_time) VALUES (?, ?, ?, ?)",
              (user[1], user[2], user[3], now))
    conn.commit()
    conn.close()
    return now

def log_logout(username):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    now = datetime.datetime.now().isoformat(timespec='seconds')
    # SQLite da ORDER BY LIMIT 1 bilan UPDATE ishlamaydi,
    # shuning uchun avval oxirgi login yozuvining id sini olamiz:
    c.execute("""
        SELECT id FROM logins WHERE username=? AND logout_time IS NULL ORDER BY login_time DESC LIMIT 1
    """, (username,))
    last_login = c.fetchone()
    if last_login:
        c.execute("UPDATE logins SET logout_time=? WHERE id=?", (now, last_login[0]))
        conn.commit()
    conn.close()
    return now

def send_telegram_login(user, login_time):
    msg = f"✅ Foydalanuvchi {user[2]} {user[3]} ({user[1]}) tizimga kirdi.\nVaqti: {login_time}"
    bot.send_message(chat_id=ADMIN_CHAT_ID, text=msg)

def send_telegram_logout(user, logout_time):
    msg = f"❌ Foydalanuvchi {user[2]} {user[3]} ({user[1]}) tizimdan chiqdi.\nVaqti: {logout_time}"
    bot.send_message(chat_id=ADMIN_CHAT_ID, text=msg)

def generate_report(period):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    if period == 'daily':
        c.execute("SELECT date(login_time), username, firstname, lastname FROM logins WHERE date(login_time) = date('now')")
    elif period == 'weekly':
        c.execute("SELECT date(login_time), username, firstname, lastname FROM logins WHERE login_time >= date('now', '-7 days')")
    elif period == 'monthly':
        c.execute("SELECT date(login_time), username, firstname, lastname FROM logins WHERE login_time >= date('now', '-30 days')")
    rows = c.fetchall()
    conn.close()

    if not rows:
        return None

    report_text = f"{period.capitalize()} hisobot:\n\n"
    for row in rows:
        date_, username, firstname, lastname = row
        report_text += f"{date_}: {firstname} {lastname} ({username}) kirgan\n"

    return report_text

def send_report_to_telegram(report):
    if report:
        bot.send_message(chat_id=ADMIN_CHAT_ID, text=report)

def main():
    st.title("Login tizimi (Telegram integratsiya bilan)")
    init_db()

    menu = ["Kirish", "Ro'yxatdan o'tish", "Admin panel"]
    choice = st.sidebar.selectbox("Menu", menu)

    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.user = None

    if choice == "Ro'yxatdan o'tish":
        st.subheader("Yangi foydalanuvchi ro'yxatdan o'tishi")
        username = st.text_input("Login")
        password = st.text_input("Parol", type="password")
        firstname = st.text_input("Ism")
        lastname = st.text_input("Familiya")
        if st.button("Ro'yxatdan o'tish"):
            if username and password and firstname and lastname:
                add_user(username, password, firstname, lastname)
                st.success("Foydalanuvchi muvaffaqiyatli qo'shildi!")
            else:
                st.warning("Iltimos, barcha maydonlarni to'ldiring.")

    elif choice == "Kirish":
        if not st.session_state.logged_in:
            st.subheader("Foydalanuvchi kirishi")
            username = st.text_input("Login", key="login_username")
            password = st.text_input("Parol", type="password", key="login_password")
            if st.button("Kirish"):
                user = check_user(username, password)
                if user:
                    st.session_state.logged_in = True
                    st.session_state.user = user
                    login_time = log_login(user)
                    send_telegram_login(user, login_time)
                    st.success(f"Xush kelibsiz, {user[2]}!")
                else:
                    st.error("Login yoki parol noto‘g‘ri!")
        else:
            user = st.session_state.user
            st.write(f"Salom, {user[2]}! Siz tizimdasiz.")
            if st.button("Chiqish"):
                logout_time = log_logout(user[1])
                send_telegram_logout(user, logout_time)
                st.session_state.logged_in = False
                st.session_state.user = None
                st.success("Tizimdan chiqdingiz.")

    elif choice == "Admin panel":
        st.subheader("Hisobotlar")
        period = st.selectbox("Hisobot davrini tanlang:", ["daily", "weekly", "monthly"])
        if st.button("Hisobotni Telegramga yuborish"):
            report = generate_report(period)
            if report:
                send_report_to_telegram(report)
                st.success(f"{period.capitalize()} hisobot Telegramga yuborildi.")
            else:
                st.warning("Hisobot uchun ma'lumotlar mavjud emas.")

if __name__ == "__main__":
    main()
