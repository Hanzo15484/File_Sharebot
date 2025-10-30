import json, asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackQueryHandler, ContextTypes

BROADCAST_CANCELLED = False


def load_admins():
    """Load admin IDs from admins.json"""
    try:
        with open('admins.json', 'r') as f:
            return json.load(f)
    except:
        return [5373577888]  # fallback default admin ID


async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /broadcast <reply to message> command."""
    global BROADCAST_CANCELLED
    user_id = update.effective_user.id

    admins = load_admins()
    if user_id not in admins:
        await update.message.reply_text("🚫 You are not authorized to use this command.")
        return

    if not update.message.reply_to_message:
        await update.message.reply_text("⚠️ Please reply to a message to broadcast it.")
        return

    message_obj = await update.message.reply_text("📢 Starting broadcast...")
    text = update.message.reply_to_message.text or update.message.reply_to_message.caption

    if not text:
        await message_obj.edit_text("⚠️ The replied message doesn't contain text or caption.")
        return

    await broadcast_to_users_with_progress(context, text, message_obj)


async def broadcast_to_users_with_progress(context: ContextTypes.DEFAULT_TYPE, text: str, message_obj):
    """Broadcast message to all active users with progress bar and cancel support."""
    global BROADCAST_CANCELLED
    BROADCAST_CANCELLED = False

    # Load users (replace with your own storage logic)
    data = await load_data()  # must return dict with key "users"
    users = list(data.get("users", {}))
    total_users = len(users)
    success_count = 0
    failed_count = 0

    keyboard = [[InlineKeyboardButton("❌ Cancel", callback_data="broadcast_cancel")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    for idx, user_id in enumerate(users, start=1):
        if BROADCAST_CANCELLED:
            await message_obj.edit_text("❌ Broadcasting cancelled by owner.")
            return

        try:
            await context.bot.send_message(chat_id=int(user_id), text=text)
            success_count += 1
        except Exception:
            failed_count += 1

        remaining_count = total_users - idx
        percent = int((idx / total_users) * 100)
        bar_length = 20
        filled_length = int(bar_length * percent // 100)
        bar = "█" * filled_length + "░" * (bar_length - filled_length)

        status_text = (
            f"📢 Broadcasting message...\n\n"
            f"{bar} {percent}%\n"
            f"✅ Success: {success_count}\n"
            f"❌ Failed: {failed_count}\n"
            f"⏳ Remaining: {remaining_count}\n"
        )

        await message_obj.edit_text(status_text, reply_markup=reply_markup)
        await asyncio.sleep(0.05)  # delay to avoid Telegram rate limits

    await message_obj.edit_text(
        f"✅ Broadcasting completed!\n\n"
        f"✅ Sent: {success_count}\n"
        f"❌ Failed: {failed_count}\n"
        f"👥 Total Users: {total_users}"
    )


async def cancel_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle broadcast cancel button."""
    global BROADCAST_CANCELLED
    query = update.callback_query
    await query.answer("❌ Broadcast cancelled")
    BROADCAST_CANCELLED = True
