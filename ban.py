import os
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

DATA_FILE = "users.json"
OWNER_ID = 5373577888

# ==========================
# 📦 DATA HANDLERS
# ==========================

def load_data():
    if not os.path.exists(DATA_FILE):
        default = {"users": {}, "admins": [OWNER_ID], "banned_users": []}
        with open(DATA_FILE, "w") as f:
            json.dump(default, f, indent=4)
        return default
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

def is_owner(user_id: int) -> bool:
    return user_id == OWNER_ID

# ==========================
# 🔒 BAN CHECK
# ==========================

async def is_banned(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    data = load_data()

    if user_id in data.get("banned_users", []):
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📩 Contact Owner", url="https://t.me/Quarel7")]
        ])

        await update.message.reply_text(
            "🚫 Sorry, you have been *banned* from using this bot.\n\n"
            "If you believe this is a mistake, please contact the owner.",
            parse_mode="Markdown",
            reply_markup=keyboard
        )
        return True
    return False

# ==========================
# 🚫 /BAN COMMAND
# ==========================

async def ban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        await update.message.reply_text("You are not authorized to use this command.")
        return
    
    if not context.args:
        await update.message.reply_text("Usage: /ban <user_id>")
        return
    
    try:
        user_id = int(context.args[0])
        data = load_data()

        if user_id not in data.get("banned_users", []):
            data["banned_users"].append(user_id)
            data["admins"] = [a for a in data.get("admins", []) if a != user_id]
            data["users"].pop(str(user_id), None)
            save_data(data)
            await update.message.reply_text(f"✅ User `{user_id}` has been *banned*.", parse_mode="Markdown")
        else:
            await update.message.reply_text(f"⚠️ User `{user_id}` is already banned.", parse_mode="Markdown")
    except ValueError:
        await update.message.reply_text("Invalid user ID format. Please use a number.")

# ==========================
# 🔓 /UNBAN COMMAND
# ==========================

async def unban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        await update.message.reply_text("You are not authorized to use this command.")
        return
    
    if not context.args:
        await update.message.reply_text("Usage: /unban <user_id>")
        return
    
    try:
        user_id = int(context.args[0])
        data = load_data()

        if user_id in data.get("banned_users", []):
            data["banned_users"].remove(user_id)
            save_data(data)
            await update.message.reply_text(f"✅ User `{user_id}` has been *unbanned*.", parse_mode="Markdown")
        else:
            await update.message.reply_text(f"⚠️ User `{user_id}` is not banned.", parse_mode="Markdown")
    except ValueError:
        await update.message.reply_text("Invalid user ID format. Please use a number.")
