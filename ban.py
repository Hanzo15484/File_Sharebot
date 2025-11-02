import os
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

# ==========================
# ⚙️ CONFIG
# ==========================

DATA_FILE = "users.json"   # Same file used to store users, admins, and banned users
OWNER_ID = 5373577888
ADMIN_IDS = []


# ==========================
# 📦 DATA HANDLERS
# ==========================

def load_data():
    """Load JSON data from file."""
    if not os.path.exists(DATA_FILE):
        return {"users": {}, "admins": [], "banned_users": []}
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def save_data(data):
    """Save updated data to JSON."""
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)


def is_owner(user_id: int) -> bool:
    """Check if user is the bot owner."""
    return user_id == OWNER_ID


# ==========================
# 🔒 BAN CHECK (Middleware)
# ==========================

async def is_banned(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check if a user is banned before processing commands."""
    user_id = update.effective_user.id
    data = load_data()

    if "banned_users" in data and user_id in data["banned_users"]:
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
    """Ban a user from using the bot."""
    if not is_owner(update.effective_user.id):
        await update.message.reply_text("You are not authorized to use this command.")
        return
    
    if not context.args:
        await update.message.reply_text("Usage: /ban <user_id>")
        return
    
    try:
        user_id = int(context.args[0])
        data = load_data()

        # Initialize banned list
        if "banned_users" not in data:
            data["banned_users"] = []

        if user_id not in data["banned_users"]:
            data["banned_users"].append(user_id)

            # Remove user from admins/users if present
            if user_id in ADMIN_IDS and user_id != OWNER_ID:
                ADMIN_IDS.remove(user_id)
            if "admins" in data and user_id in data["admins"]:
                data["admins"].remove(user_id)
            if "users" in data and str(user_id) in data["users"]:
                del data["users"][str(user_id)]

            save_data(data)
            await update.message.reply_text(
                f"✅ User `{user_id}` has been *banned* from using the bot.",
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text(
                f"⚠️ User `{user_id}` is already banned.",
                parse_mode="Markdown"
            )

    except ValueError:
        await update.message.reply_text("Invalid user ID format. Please use a number.")


# ==========================
# 🔓 /UNBAN COMMAND
# ==========================

async def unban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Unban a user."""
    if not is_owner(update.effective_user.id):
        await update.message.reply_text("You are not authorized to use this command.")
        return
    
    if not context.args:
        await update.message.reply_text("Usage: /unban <user_id>")
        return
    
    try:
        user_id = int(context.args[0])
        data = load_data()

        if "banned_users" in data and user_id in data["banned_users"]:
            data["banned_users"].remove(user_id)
            save_data(data)
            await update.message.reply_text(
                f"✅ User `{user_id}` has been *unbanned*.",
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text(
                f"⚠️ User `{user_id}` is not banned.",
                parse_mode="Markdown"
            )

    except ValueError:
        await update.message.reply_text("Invalid user ID format. Please use a number.")
