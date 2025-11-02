import os
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# ----------------------- DATA HANDLING -----------------------

DATA_FILE = "users.json"

async def load_data():
    if not os.path.exists(DATA_FILE):
        return {"users": {}, "admins": [], "banned_users": []}
    with open(DATA_FILE, "r") as f:
        return json.load(f)

async def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

# ----------------------- PERMISSIONS -----------------------

def is_admin(user_id: int) -> bool:
    try:
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
        return user_id in data.get("admins", [])
    except:
        return False

# ----------------------- AUTO USER ADD SYSTEM -----------------------

async def auto_add_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Automatically adds new users when they send any message."""
    user = update.effective_user
    if not user:
        return

    user_id = str(user.id)
    username = user.username or "Unknown"

    data = await load_data()
    users = data.get("users", {})

    # Add only if new user
    if user_id not in users:
        users[user_id] = {
            "id": user.id,
            "username": username,
            "first_name": user.first_name,
        }
        data["users"] = users
        await save_data(data)
        print(f"✅ New user added: {username} ({user_id})")

# ----------------------- USERS COMMAND -----------------------

async def users_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user statistics."""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.message.reply_text("You are not authorized to use this bot.")
        return
    
    data = await load_data()
    users_count = len(data.get("users", {}))
    admins_count = len(data.get("admins", []))
    banned_count = len(data.get("banned_users", []))
    
    message = f"""📊 **User Statistics:**

• Total Users: {users_count}
• Admins: {admins_count}
• Banned Users: {banned_count}"""

    keyboard = [[InlineKeyboardButton("ᴄʟᴏsᴇ", callback_data="close")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(message, reply_markup=reply_markup)
