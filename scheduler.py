import schedule
import time
from bot import send_telegram_message

def schedule_reminders():
    schedule.every().day.at("09:00").do(lambda: send_telegram_message("⏰ Ish boshlash vaqti!"))
    schedule.every().day.at("18:00").do(lambda: send_telegram_message("✅ Ish tugadi. Yaxshi dam oling!"))

def run_scheduler():
    schedule_reminders()
    while True:
        schedule.run_pending()
        time.sleep(1)
