import os
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

DATA_FILE = "admins.json"

def load_data():
    if not os.path.exists(DATA_FILE):
        default = {"users": {}, "admins": [5373577888], "banned_users": []}
        with open(DATA_FILE, "w") as f:
            json.dump(default, f, indent=4)
        return default
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

def is_admin(user_id: int) -> bool:
    data = load_data()
    return user_id in data.get("admins", [])

# ---------- Main Command ----------
async def admins_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List all bot admins."""
    user_id = update.effective_user.id

    if not is_admin(user_id):
        await update.message.reply_text("You are not authorized to use this bot.")
        return

    data = load_data()
    admins = data.get("admins", [])

    message = "👑 **Bot Admins:**\n\n"
    for i, admin_id in enumerate(admins, 1):
        try:
            user = await context.bot.get_chat(admin_id)
            message += f"{i}. {user.first_name} (`{user.id}`)\n"
        except Exception:
            message += f"{i}. Unknown User (`{admin_id}`)\n"

    keyboard = [[InlineKeyboardButton("ᴄʟᴏsᴇ", callback_data="close")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(message, reply_markup=reply_markup, parse_mode="Markdown")
