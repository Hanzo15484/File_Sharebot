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
    
    message = f"""User Statistics:

• Total Users: {users_count}
• Admins: {admins_count}
• Banned Users: {banned_count}"""

    keyboard = [
        [InlineKeyboardButton("ᴄʟᴏsᴇ", callback_data="close")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(message, reply_markup=reply_markup)
