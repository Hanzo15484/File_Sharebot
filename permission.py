# permissions.py

from functools import wraps
from admin_system import load_admins_full, cleanup_expired_admins
from telegram import Update
from telegram.ext import ContextTypes

def CheckBotAdmin():
    def decorator(func):
        @wraps(func)
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):

            cleanup_expired_admins()  # auto remove expired admins

            data = load_admins_full()
            admins = data["admins"]

            user_id = update.effective_user.id

            if user_id not in admins and user_id != 5373577888:
                await update.message.reply_text("You are not authorized to use this command!")
                return

            return await func(update, context)

        return wrapper
    return decorator
