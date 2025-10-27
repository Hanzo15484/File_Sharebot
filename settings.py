import os
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler, MessageHandler, filters

# Load settings
def load_settings():
    try:
        with open('settings.json', 'r') as f:
            return json.load(f)
    except:
        return {
            "start_image": "img.jpg",
            "help_image": "",
            "start_text": "Hi {mention} welcome to File Store Bot",
            "help_text": "Available Commands:\\n\\n/start - Start the bot\\n/help - Show this help message\\n/genlink - Generate link\\n/batchlink - Generate batch links\\n/custombatch - Custom batch processing\\n/fsub - Force subscribe\\n/settings - Bot settings\\n/promote - Promote user to admin\\n/demote - Demote admin\\n/ban - Ban user\\n/unban - Unban user\\n/users - Show users\\n/admins - Show admins\\n/update - Update bot\\n/restart - Restart bot",
            "auto_delete_time": 10,
            "protect_content": False
        }

# Save settings
def save_settings(settings):
    with open('settings.json', 'w') as f:
        json.dump(settings, f, indent=4)

# Load admin data
def load_admins():
    try:
        with open('admins.json', 'r') as f:
            return json.load(f)
    except:
        return [5373577888]

async def settings_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    admins = load_admins()
    
    # Check if user is admin or owner
    if user_id not in admins and user_id != 5373577888:
        await update.message.reply_text("You are not authorized to use this command!")
        return
    
    settings = load_settings()
    auto_delete_time = settings.get("auto_delete_time", 10)
    protect_content = settings.get("protect_content", False)
    
    settings_text = (
        "⚙️ **Bot Settings**\n\n"
        f"🖼️ Start Image: {'✅ Set' if settings.get('start_image') and os.path.exists(settings.get('start_image')) else '❌ Not Set'}\n"
        f"📖 Help Image: {'✅ Set' if settings.get('help_image') and os.path.exists(settings.get('help_image')) else '❌ Not Set'}\n"
        f"⏰ Auto Delete: {auto_delete_time} minutes\n"
        f"🔒 Protect Content: {'✅ ON' if protect_content else '❌ OFF'}\n\n"
        "Select an option to configure:"
    )
    
    keyboard = [
        [InlineKeyboardButton("🖼️ Start Image", callback_data="settings_start_img")],
        [InlineKeyboardButton("📖 Help Image", callback_data="settings_help_img")],
        [InlineKeyboardButton("⏰ Auto Delete", callback_data="settings_auto_delete")],
        [InlineKeyboardButton("🔒 Protect Content", callback_data="settings_protect_content")],
        [InlineKeyboardButton("📝 Start Text", callback_data="settings_start_text")],
        [InlineKeyboardButton("📋 Help Text", callback_data="settings_help_text")],
        [InlineKeyboardButton("🔙 Back", callback_data="settings_back"), InlineKeyboardButton("❌ Close", callback_data="settings_close")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.edit_message_text(settings_text, reply_markup=reply_markup, parse_mode="Markdown")
    else:
        await update.message.reply_text(settings_text, reply_markup=reply_markup, parse_mode="Markdown")

async def settings_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    user_id = query.from_user.id
    admins = load_admins()
    
    # Check if user is admin or owner
    if user_id not in admins and user_id != 5373577888:
        await query.answer("You are not authorized!", show_alert=True)
        return
    
    settings = load_settings()
    
    if data == "settings_start_img":
        await query.edit_message_text(
            "🖼️ **Start Image Settings**\n\nɴᴏᴡ sᴇɴᴅ ᴍᴇ ɪᴍᴀɢᴇ ᴛʜᴀᴛ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ sᴇᴛ ɪɴ sᴛᴀʀᴛ ᴍᴏᴅᴜʟᴇ",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back", callback_data="settings_back")]
            ]),
            parse_mode="Markdown"
        )
        context.user_data['waiting_for'] = 'start_image'
        
    elif data == "settings_help_img":
        await query.edit_message_text(
            "📖 **Help Image Settings**\n\nɴᴏᴡ sᴇɴᴅ ᴍᴇ ɪᴍᴀɢᴇ ᴛʜᴀᴛ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ sᴇᴛ ɪɴ ʜᴇʟᴘ ᴍᴏᴅᴜʟᴇ",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back", callback_data="settings_back")]
            ]),
            parse_mode="Markdown"
        )
        context.user_data['waiting_for'] = 'help_image'
        
    elif data == "settings_auto_delete":
        auto_delete_time = settings.get("auto_delete_time", 10)
        
        # Create buttons with checkmarks for current selection
        buttons_5 = "5 ᴍɪɴ" if auto_delete_time != 5 else "✅ 5 ᴍɪɴ"
        buttons_10 = "10 ᴍɪɴ" if auto_delete_time != 10 else "✅ 10 ᴍɪɴ"
        buttons_15 = "15 ᴍɪɴ" if auto_delete_time != 15 else "✅ 15 ᴍɪɴ"
        buttons_20 = "20 ᴍɪɴ" if auto_delete_time != 20 else "✅ 20 ᴍɪɴ"
        buttons_30 = "30 ᴍɪɴ" if auto_delete_time != 30 else "✅ 30 ᴍɪɴ"
        buttons_45 = "45 ᴍɪɴ" if auto_delete_time != 45 else "✅ 45 ᴍɪɴ"
        buttons_60 = "1 ʜʀ" if auto_delete_time != 60 else "✅ 1 ʜʀ"
        buttons_180 = "3 ʜʀ" if auto_delete_time != 180 else "✅ 3 ʜʀ"
        buttons_0 = "ᴅɪsᴀʙʟᴇ" if auto_delete_time != 0 else "✅ ᴅɪsᴀʙʟᴇ"
        
        keyboard = [
            [InlineKeyboardButton(buttons_5, callback_data="auto_delete_5"), InlineKeyboardButton(buttons_10, callback_data="auto_delete_10")],
            [InlineKeyboardButton(buttons_15, callback_data="auto_delete_15"), InlineKeyboardButton(buttons_20, callback_data="auto_delete_20")],
            [InlineKeyboardButton(buttons_30, callback_data="auto_delete_30"), InlineKeyboardButton(buttons_45, callback_data="auto_delete_45")],
            [InlineKeyboardButton(buttons_60, callback_data="auto_delete_60"), InlineKeyboardButton(buttons_180, callback_data="auto_delete_180")],
            [InlineKeyboardButton(buttons_0, callback_data="auto_delete_0")],
            [InlineKeyboardButton("🔙 Back", callback_data="settings_back")]
        ]
        
        await query.edit_message_text(
            "⏰ **Auto Delete Settings**\n\nSelect time duration for auto deletion:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        
    elif data == "settings_protect_content":
        protect_content = settings.get("protect_content", False)
        
        # Create buttons with checkmarks
        on_text = "✅ ᴏɴ" if protect_content else "ᴏɴ"
        off_text = "✅ ᴏғғ" if not protect_content else "ᴏғғ"
        
        keyboard = [
            [InlineKeyboardButton("ғᴏʀᴡᴀʀᴅ", callback_data="protect_forward")],
            [InlineKeyboardButton(on_text, callback_data="protect_on"), InlineKeyboardButton(off_text, callback_data="protect_off")],
            [InlineKeyboardButton("🔙 Back", callback_data="settings_back")]
        ]
        
        status = "✅ Enabled" if protect_content else "❌ Disabled"
        await query.edit_message_text(
            f"🔒 **Protect Content Settings**\n\nCurrent status: {status}\n\nSelect forwarding option:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        
    elif data == "settings_start_text":
        await query.edit_message_text(
            "📝 **Start Text Settings**\n\nSend me the new start text. You can use {mention} for user mention.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back", callback_data="settings_back")]
            ]),
            parse_mode="Markdown"
        )
        context.user_data['waiting_for'] = 'start_text'
        
    elif data == "settings_help_text":
        await query.edit_message_text(
            "📋 **Help Text Settings**\n\nSend me the new help text.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back", callback_data="settings_back")]
            ]),
            parse_mode="Markdown"
        )
        context.user_data['waiting_for'] = 'help_text'
        
    elif data.startswith("auto_delete_"):
        time_minutes = int(data.split("_")[2])
        settings["auto_delete_time"] = time_minutes
        save_settings(settings)
        
        status = "Disabled" if time_minutes == 0 else f"{time_minutes} minutes"
        await query.answer(f"Auto delete set to {status}!", show_alert=True)
        # Go back to auto delete menu to show updated buttons
        await settings_button_handler(update, context)
        
    elif data.startswith("protect_"):
        if data == "protect_on":
            settings["protect_content"] = True
            save_settings(settings)
            await query.answer("Protect content enabled!", show_alert=True)
        elif data == "protect_off":
            settings["protect_content"] = False
            save_settings(settings)
            await query.answer("Protect content disabled!", show_alert=True)
        # Go back to protect content menu to show updated buttons
        await settings_button_handler(update, context)
        
    elif data == "settings_back":
        await settings_handler(update, context)
        
    elif data == "settings_close":
        await query.message.delete()

async def settings_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    admins = load_admins()
    
    # Check if user is admin or owner
    if user_id not in admins and user_id != 5373577888:
        return
    
    waiting_for = context.user_data.get('waiting_for')
    
    if not waiting_for:
        return
    
    settings = load_settings()
    
    if waiting_for in ['start_image', 'help_image']:
        if update.message.photo:
            # Get the largest photo
            photo = update.message.photo[-1]
            photo_file = await photo.get_file()
            filename = f"{waiting_for}.jpg"
            await photo_file.download_to_drive(filename)
            
            settings[waiting_for] = filename
            save_settings(settings)
            
            await update.message.reply_text(f"✅ {waiting_for.replace('_', ' ').title()} has been set successfully!")
            # Clear waiting state and go back to settings
            context.user_data.pop('waiting_for', None)
            await settings_handler(update, context)
        else:
            await update.message.reply_text("❌ Please send a valid image!")
            
    elif waiting_for in ['start_text', 'help_text']:
        new_text = update.message.text
        settings[waiting_for] = new_text
        save_settings(settings)
        
        await update.message.reply_text(f"✅ {waiting_for.replace('_', ' ').title()} has been updated successfully!")
        # Clear waiting state and go back to settings
        context.user_data.pop('waiting_for', None)
        await settings_handler(update, context)
