# ban.py
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler

from shared_functions import load_admins, load_users, save_users, load_banned_users, save_banned_users, auto_add_user, is_user_banned

from middleware import check_ban_and_register

async def is_banned(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Check if user is banned and send message if banned
    Returns True if user is banned, False otherwise
    """
    user_id = update.effective_user.id
    
    if is_user_banned(user_id):
        await update.message.reply_text(
            "🚫 **You have been banned from using this bot!**\n\n"
            "If you think this is a mistake, please contact the administrator.",
            parse_mode="Markdown"
        )
        return True  # User is banned
    return False  # User is not banned

@check_ban_and_register
async def ban_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    admins = load_admins()
    
    # Check if user is admin or owner
    if user_id not in admins and user_id != 5373577888:
        await update.message.reply_text("You are not authorized to use this command!")
        return
    
    if not context.args:
        await update.message.reply_text(
            "❌ Usage: /ban <user_id>\n\nExample: /ban 123456789",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("❌ Close", callback_data="ban_close")]
            ])
        )
        return
    
    try:
        target_user_id = int(context.args[0])
        
        # Check if trying to ban self
        if target_user_id == user_id:
            await update.message.reply_text("❌ You cannot ban yourself!")
            return
        
        # Check if trying to ban owner
        if target_user_id == 5373577888:
            await update.message.reply_text("❌ You cannot ban the bot owner!")
            return
        
        # Check if target is admin
        if target_user_id in admins:
            await update.message.reply_text("❌ You cannot ban an admin!")
            return
        
        banned_users = load_banned_users()
        users = load_users()
        
        # Check if user already banned
        if any(user['id'] == target_user_id for user in banned_users):
            await update.message.reply_text("❌ User is already banned!")
            return
        
        # Find user info
        user_info = None
        for user in users:
            if user['id'] == target_user_id:
                user_info = user
                break
        
        if user_info:
            username = user_info.get('username', 'N/A')
            first_name = user_info.get('first_name', 'Unknown')
        else:
            # If user not in users.json, try to get info from Telegram
            try:
                target_user = await context.bot.get_chat(target_user_id)
                username = target_user.username if target_user.username else 'N/A'
                first_name = target_user.first_name
                user_info = {"username": username, "first_name": first_name}
            except:
                username = 'N/A'
                first_name = 'Unknown User'
        
        # Add to banned users
        banned_users.append({
            "id": target_user_id,
            "username": username,
            "first_name": first_name,
            "banned_by": user_id,
            "banned_at": datetime.utcnow().isoformat()
        })
        save_banned_users(banned_users)
        
        await update.message.reply_text(
            f"✅ User banned successfully!\n\n"
            f"👤 User: {first_name}\n"
            f"🆔 ID: `{target_user_id}`\n"
            f"📛 Username: @{username}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("❌ Close", callback_data="ban_close")]
            ]),
            parse_mode="Markdown"
        )
        
    except ValueError:
        await update.message.reply_text(
            "❌ Invalid user ID! Please provide a numeric user ID.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("❌ Close", callback_data="ban_close")]
            ])
        )

@check_ban_and_register
async def unban_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    admins = load_admins()
    
    # Check if user is admin or owner
    if user_id not in admins and user_id != 5373577888:
        await update.message.reply_text("You are not authorized to use this command!")
        return
    
    if not context.args:
        await update.message.reply_text(
            "❌ Usage: /unban <user_id>\n\nExample: /unban 123456789",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("❌ Close", callback_data="ban_close")]
            ])
        )
        return
    
    try:
        target_user_id = int(context.args[0])
        
        banned_users = load_banned_users()
        
        # Check if user is banned
        user_found = None
        for user in banned_users:
            if user['id'] == target_user_id:
                user_found = user
                break
        
        if not user_found:
            await update.message.reply_text("❌ User is not banned!")
            return
        
        # Remove from banned users
        banned_users = [user for user in banned_users if user['id'] != target_user_id]
        save_banned_users(banned_users)
        
        await update.message.reply_text(
            f"✅ User unbanned successfully!\n\n"
            f"👤 User: {user_found.get('first_name', 'Unknown')}\n"
            f"🆔 ID: `{target_user_id}`\n"
            f"📛 Username: @{user_found.get('username', 'N/A')}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("❌ Close", callback_data="ban_close")]
            ]),
            parse_mode="Markdown"
        )
        
    except ValueError:
        await update.message.reply_text(
            "❌ Invalid user ID! Please provide a numeric user ID.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("❌ Close", callback_data="ban_close")]
            ])
        )

async def ban_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data == "ban_close":
        await query.message.delete()
