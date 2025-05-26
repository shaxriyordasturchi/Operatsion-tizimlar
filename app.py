import streamlit as st
from datetime import datetime, timedelta
import sqlite3
from bot import send_telegram_message

DB_PATH = "worktime.db"

# Foydalanuvchilar lug'ati: username: (password, firstname, lastname)
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

def check_user(username, password):
    if username in users and users[username][0] == password:
        return users[username][1], users[username][2]
    return None, None

def log_login(username, firstname, lastname):
    now = datetime.now()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO attendance (username, firstname, lastname, login_time) VALUES (?, ?, ?, ?)",
              (username, firstname, lastname, now.strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()
    send_telegram_message(f"✅ <b>{firstname} {lastname}</b> foydalanuvchisi <b>KIRDI</b>.\nVaqt: <i>{now.strftime('%Y-%m-%d %H:%M:%S')}</i>")

def log_logout(username, firstname, lastname):
    now = datetime.now()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # So‘nggi login qilingan yozuvga logout vaqtini qo‘yish (agar logout bo‘lmagan yozuv mavjud bo‘lsa)
    c.execute('''
        UPDATE attendance 
        SET logout_time = ? 
        WHERE username = ? AND logout_time IS NULL
        ORDER BY login_time DESC LIMIT 1
    ''', (now.strftime("%Y-%m-%d %H:%M:%S"), username))
    conn.commit()
    conn.close()
    send_telegram_message(f"❌ <b>{firstname} {lastname}</b> foydalanuvchisi <b>CHIQQAN</b>.\nVaqt: <i>{now.strftime('%Y-%m-%d %H:%M:%S')}</i>")

def send_failed_login_alert(username):
    now = datetime.now()
    send_telegram_message(f"⚠️ Noto‘g‘ri login urinishi: <b>{username}</b>\nVaqt: {now.strftime('%Y-%m-%d %H:%M:%S')}")

def get_attendance_summary():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        SELECT firstname, lastname, login_time, logout_time FROM attendance
        WHERE login_time >= date('now','-1 day')
    ''')
    rows = c.fetchall()
    conn.close()
    return rows

def send_daily_report():
    rows = get_attendance_summary()
    if not rows:
        send_telegram_message("📅 Bugungi ish faoliyati haqida ma'lumot yo'q.")
        return
    msg = "📅 Bugungi ish faoliyati:\n"
    for row in rows:
        firstname, lastname, login_time, logout_time = row
        logout_time = logout_time if logout_time else "Hozircha chiqmagan"
        msg += f"- {firstname} {lastname}: Kirish: {login_time}, Chiqish: {logout_time}\n"
    send_telegram_message(msg)

def main():
    st.title("Xodimlar Kirish/Chiqish Tizimi")

    init_db()

    menu = ["Kirish", "Chiqish", "Kunlik hisobot yuborish (admin)"]
    choice = st.selectbox("Amalni tanlang", menu)

    login = st.text_input("Login")
    password = st.text_input("Parol", type="password")

    if st.button(choice):
        if choice == "Kunlik hisobot yuborish (admin)":
            send_daily_report()
            st.success("Kunlik hisobot Telegramga yuborildi.")
            return

        firstname, lastname = check_user(login, password)
        if firstname and lastname:
            if choice == "Kirish":
                log_login(login, firstname, lastname)
                st.success(f"{firstname} {lastname}, tizimga muvaffaqiyatli kirdingiz.")
            else:
                log_logout(login, firstname, lastname)
                st.success(f"{firstname} {lastname}, tizimdan muvaffaqiyatli chiqdiz.")
        else:
            send_failed_login_alert(login)
            st.error("Login yoki parol noto‘g‘ri.")

    # Ish vaqti jadvali
    st.subheader("Bugungi ish vaqti (kirish/chiqish)")
    rows = get_attendance_summary()
    if rows:
        for row in rows:
            firstname, lastname, login_time, logout_time = row
            logout_time = logout_time if logout_time else "Hozircha chiqmagan"
            st.write(f"{firstname} {lastname}: Kirish: {login_time}, Chiqish: {logout_time}")
    else:
        st.write("Bugungi yozuvlar mavjud emas.")

if __name__ == "__main__":
    main()
