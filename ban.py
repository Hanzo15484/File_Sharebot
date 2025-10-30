from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

# Replace with your actual owner ID
OWNER_ID = 5373577888  
ADMIN_IDS = []  # Example admin list

# Helper check for owner
def is_owner(user_id: int) -> bool:
    return user_id == OWNER_ID

# ==========================
# 🔒 BAN SYSTEM CORE
# ==========================

async def is_banned(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check if a user is banned and stop execution if yes."""
    user_id = update.effective_user.id
    data = await load_data()

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
        data = await load_data()

        # Initialize banned list
        if "banned_users" not in data:
            data["banned_users"] = []

        # Check if already banned
        if user_id not in data["banned_users"]:
            data["banned_users"].append(user_id)

            # Clean from admin/user lists
            if user_id in ADMIN_IDS and user_id != OWNER_ID:
                ADMIN_IDS.remove(user_id)
            if "admins" in data and user_id in data["admins"]:
                data["admins"].remove(user_id)
            if "users" in data and str(user_id) in data["users"]:
                del data["users"][str(user_id)]

            await save_data(data)
            await update.message.reply_text(f"✅ User `{user_id}` has been *banned* from using the bot.", parse_mode="Markdown")
        else:
            await update.message.reply_text(f"⚠️ User `{user_id}` is already banned.", parse_mode="Markdown")

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
        data = await load_data()

        if "banned_users" in data and user_id in data["banned_users"]:
            data["banned_users"].remove(user_id)
            await save_data(data)
            await update.message.reply_text(f"✅ User `{user_id}` has been *unbanned*.", parse_mode="Markdown")
        else:
            await update.message.reply_text(f"⚠️ User `{user_id}` is not banned.", parse_mode="Markdown")

    except ValueError:
        await update.message.reply_text("Invalid user ID format. Please use a number.")
