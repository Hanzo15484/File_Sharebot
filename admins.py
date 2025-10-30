async def admins_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List all bot admins."""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.message.reply_text("You are not authorized to use this bot.")
        return
    
    data = await load_data()
    admins = data.get("admins", [])
    
    message = "Bot Admins:\n\n"
    for i, admin_id in enumerate(admins, 1):
        try:
            user = await context.bot.get_chat(admin_id)
            message += f"{i}. {user.first_name} ({user.id})\n"
        except:
            message += f"{i}. Unknown User ({admin_id})\n"
    
    keyboard = [
        [InlineKeyboardButton("ᴄʟᴏsᴇ", callback_data="close")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(message, reply_markup=reply_markup)
  
