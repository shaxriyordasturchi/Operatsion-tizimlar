import logging
from telegram import Update, Bot
from telegram.ext import Updater, CommandHandler, CallbackContext, Filters, MessageHandler
from datetime import datetime

# Bot token va admin ID ni kiriting
TELEGRAM_BOT_TOKEN = "7817066006:AAHRcf_wJO4Kmq5PvOrdq5BPi_eyv5vYqaM"
ADMIN_ID = 7750409176

# Log sozlamalari
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Xodimlar ma'lumotlari: username -> info dict
employees = {
    "ali": {"firstname": "Ali", "lastname": "Valiyev", "salary": 0, "logins": [], "logouts": []},
    "john": {"firstname": "John", "lastname": "Doe", "salary": 0, "logins": [], "logouts": []},
    "jane": {"firstname": "Jane", "lastname": "Doe", "salary": 0, "logins": [], "logouts": []},
    # Shu yerga 10 taga to'ldiring...
}

def is_admin(user_id):
    return user_id == ADMIN_ID

def start(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if is_admin(user_id):
        update.message.reply_text("Salom, admin! Buyruqlar uchun /help yozing.")
    else:
        update.message.reply_text("Salom, xodim! /login yoki /logout buyruqlaridan foydalaning.")

def help_command(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        update.message.reply_text("Faqat admin uchun buyruqlar.")
        return
    help_text = (
        "/employee_count - Xodimlar sonini ko‘rish\n"
        "/activity - Xodimlarning login/chiqish tarixini ko‘rish\n"
        "/pay <username> <amount> - Maosh berish\n"
        "/list - Xodimlar ro‘yxatini ko‘rish\n"
    )
    update.message.reply_text(help_text)

def employee_count(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        update.message.reply_text("Faqat admin uchun.")
        return
    count = len(employees)
    update.message.reply_text(f"Tizimda jami {count} ta xodim mavjud.")

def activity(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        update.message.reply_text("Faqat admin uchun.")
        return
    msg = "Xodimlar faoliyati:\n"
    for username, info in employees.items():
        logins = ', '.join(dt.strftime("%Y-%m-%d %H:%M:%S") for dt in info["logins"]) or "Yo'q"
        logouts = ', '.join(dt.strftime("%Y-%m-%d %H:%M:%S") for dt in info["logouts"]) or "Yo'q"
        msg += f"{info['firstname']} {info['lastname']}:\n  Kirishlar: {logins}\n  Chiqishlar: {logouts}\n"
    update.message.reply_text(msg)

def pay(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        update.message.reply_text("Faqat admin uchun.")
        return
    args = context.args
    if len(args) != 2:
        update.message.reply_text("Foydalanish: /pay <username> <amount>")
        return
    username, amount_str = args
    if username not in employees:
        update.message.reply_text("Bunday xodim topilmadi.")
        return
    try:
        amount = float(amount_str)
    except ValueError:
        update.message.reply_text("Iltimos, to‘g‘ri raqam kiriting.")
        return
    employees[username]["salary"] += amount
    update.message.reply_text(f"{employees[username]['firstname']} {employees[username]['lastname']} ga {amount} so‘m maosh qo‘shildi. Jami: {employees[username]['salary']} so‘m.")

def list_employees(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        update.message.reply_text("Faqat admin uchun.")
        return
    names = [f"{info['firstname']} ({username})" for username, info in employees.items()]
    update.message.reply_text("Xodimlar ro'yxati:\n" + "\n".join(names))

def login(update: Update, context: CallbackContext):
    user = update.effective_user
    username = user.username
    if not username:
        update.message.reply_text("Iltimos, Telegram username o‘rnating va qaytadan urinib ko‘ring.")
        return
    if username not in employees:
        update.message.reply_text("Siz ro‘yxatda yo‘qsiz. Admin bilan bog‘laning.")
        return
    now = datetime.now()
    employees[username]["logins"].append(now)
    update.message.reply_text(f"{employees[username]['firstname']}, siz tizimga {now.strftime('%Y-%m-%d %H:%M:%S')} da kirdingiz.")
    # Adminga xabar
    bot.send_message(chat_id=ADMIN_ID, text=f"{employees[username]['firstname']} {employees[username]['lastname']} tizimga kirdi: {now.strftime('%Y-%m-%d %H:%M:%S')}")

def logout(update: Update, context: CallbackContext):
    user = update.effective_user
    username = user.username
    if not username:
        update.message.reply_text("Iltimos, Telegram username o‘rnating va qaytadan urinib ko‘ring.")
        return
    if username not in employees:
        update.message.reply_text("Siz ro‘yxatda yo‘qsiz. Admin bilan bog‘laning.")
        return
    now = datetime.now()
    employees[username]["logouts"].append(now)
    update.message.reply_text(f"{employees[username]['firstname']}, siz tizimdan {now.strftime('%Y-%m-%d %H:%M:%S')} da chiqdingiz.")
    # Adminga xabar
    bot.send_message(chat_id=ADMIN_ID, text=f"{employees[username]['firstname']} {employees[username]['lastname']} tizimdan chiqdi: {now.strftime('%Y-%m-%d %H:%M:%S')}")

def main():
    updater = Updater(token=TELEGRAM_BOT_TOKEN, use_context=True)
    global bot
    bot = updater.bot

    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help_command))
    dp.add_handler(CommandHandler("employee_count", employee_count))
    dp.add_handler(CommandHandler("activity", activity))
    dp.add_handler(CommandHandler("pay", pay))
    dp.add_handler(CommandHandler("list", list_employees))
    dp.add_handler(CommandHandler("login", login))
    dp.add_handler(CommandHandler("logout", logout))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
