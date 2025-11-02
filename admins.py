import os
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

DATA_FILE = "admins.json"


# ---------- Helper Functions ----------
def load_data():
    """Load data from JSON file (sync — no need for async here)."""
    if not os.path.exists(DATA_FILE):
        return {"users": {}, "admins": [], "banned_users": []}
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def save_data(data):
    """Save updated data to JSON file."""
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)


def is_admin(user_id: int) -> bool:
    """Check if a user is an admin."""
    data = load_data()
    return user_id in data.get("admins", [])


# ---------- Main Command ----------
async def admins_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List all bot admins."""
    user_id = update.effective_user.id

    # Access control
    if not is_admin(user_id):
        await update.message.reply_text("You are not authorized to use this bot.")
        return

    data = load_data()
    admins = data.get("admins", [])

    # Build message
    message = "👑 **Bot Admins:**\n\n"
    for i, admin_id in enumerate(admins, 1):
        try:
            user = await context.bot.get_chat(admin_id)
            message += f"{i}. {user.first_name} (`{user.id}`)\n"
        except Exception:
            message += f"{i}. Unknown User (`{admin_id}`)\n"

    # Inline button
    keyboard = [
        [InlineKeyboardButton("ᴄʟᴏsᴇ", callback_data="close")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        message,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
