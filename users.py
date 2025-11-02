# users.py
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler

from shared_functions import load_admins, load_users

async def users_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    admins = load_admins()
    
    # Check if user is admin or owner
    if user_id not in admins and user_id != 5373577888:
        await update.message.reply_text("You are not authorized to use this command!")
        return
    
    users = load_users()
    total_users = len(users)
    
    # Get recent users (last 7 days)
    recent_users = 0
    week_ago = datetime.utcnow() - timedelta(days=7)
    
    for user in users:
        joined_at = datetime.fromisoformat(user.get('joined_at', datetime.utcnow().isoformat()))
        if joined_at > week_ago:
            recent_users += 1
    
    message_text = (
        f"📊 **Users Statistics**\n\n"
        f"👥 **Total Users:** `{total_users}`\n"
        f"🆕 **Recent Users (7 days):** `{recent_users}`\n"
        f"📈 **Growth Rate:** `{recent_users/total_users*100:.1f}%`\n\n"
        f"💡 *Note: Users are automatically added when they interact with the bot.*"
    )
    
    await update.message.reply_text(
        message_text,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 Refresh", callback_data="users_refresh")],
            [InlineKeyboardButton("❌ Close", callback_data="users_close")]
        ]),
        parse_mode="Markdown"
    )

async def users_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data == "users_refresh":
        await users_handler(update, context)
        await query.message.delete()
    elif data == "users_close":
        await query.message.delete()
