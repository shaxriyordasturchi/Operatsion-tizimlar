import streamlit as st
from db import init_db, log_action
from bot import send_telegram_message

init_db()

st.title("👨‍💼 Xodim Kirish Tizimi")

login = st.text_input("Login")
password = st.text_input("Parol", type="password")

if st.button("Kirish"):
    # Bu yerda haqiqiy tekshiruv bo'lishi kerak
    if login == "test" and password == "1234":
        firstname, lastname = "Ali", "Valiyev"
        timestamp = log_action(login, firstname, lastname, "Kirish", "Qashqadaryo")
        send_telegram_message(
            f"👤 <b>{firstname} {lastname}</b>\n🕒 <b>{timestamp}</b>\n📍 <b>Qashqadaryo</b>\n🔔 <b>Kirish amalga oshdi</b>"
        )
        st.success("Kirish muvaffaqiyatli!")
    else:
        st.error("Login yoki parol noto‘g‘ri!")
