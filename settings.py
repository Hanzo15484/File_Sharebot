import os
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler, MessageHandler, filters
import asyncio
# Load settings
def load_settings():
    try:
        with open('settings.json', 'r') as f:
            return json.load(f)
    except:
        return {
            "start_image": "img.jpg",
            "help_image": "",
            "force_sub_image": "",
            "start_text": "Hi {mention} welcome to File Store Bot",
            "help_text": "Available Commands:\\n\\n/start - Start the bot\\n/help - Show this help message\\n/genlink - Generate link\\n/batchlink - Generate batch links\\n/custombatch - Custom batch processing\\n/fsub - Force subscribe\\n/settings - Bot settings\\n/promote - Promote user to admin\\n/demote - Demote admin\\n/ban - Ban user\\n/unban - Unban user\\n/users - Show users\\n/admins - Show admins\\n/update - Update bot\\n/restart - Restart bot",
            "auto_delete_time": 10,
            "protect_content": False,
            "settings_image": ""
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
        f"sᴛᴀʀᴛ ɪᴍᴀɢᴇ: {'✅ Set' if settings.get('start_image') and os.path.exists(settings.get('start_image')) else '❌ Not Set'}\n"
        f"ʜᴇʟᴘ ɪᴍᴀɢᴇ: {'✅ Set' if settings.get('help_image') and os.path.exists(settings.get('help_image')) else '❌ Not Set'}\n"
        f"ᴀᴜᴛᴏ ᴅᴇʟᴇᴛᴇ: {auto_delete_time} minutes\n"
        f"ᴘʀᴏᴛᴇᴄᴛ ᴄᴏɴᴛᴇɴᴛ: {'✅ ON' if protect_content else '❌ OFF'}\n\n"
        f"ғᴏʀᴄᴇ sᴜʙ ɪᴍᴀɢᴇ: {'✅ Set' if settings.get('force_sub_image') and os.path.exists(settings.get('force_sub_image')) else '❌ Not Set'}\n"
        f"sᴇᴛᴛɪɴɢs ɪᴍᴀɢᴇ: {'✅ Set' if settings.get('settings_image') and os.path.exists(settings.get('settings_image')) else '❌ Not Set'}\n"
        "sᴇʟᴇᴄᴛ ᴀɴ ᴏᴘᴛɪᴏɴ ᴛᴏ ᴄᴏɴғɪɢᴜʀᴇ:"
    )

    keyboard = [
        [
            InlineKeyboardButton("sᴛᴀʀᴛ ɪᴍᴀɢᴇ", callback_data="settings_start_img"),
            InlineKeyboardButton("ʜᴇʟᴘ ɪᴍᴀɢᴇ", callback_data="settings_help_img"),
        ],
        [
            InlineKeyboardButton("ᴀᴜᴛᴏ ᴅᴇʟᴇᴛᴇ", callback_data="settings_auto_delete"),
            InlineKeyboardButton("ᴘʀᴏᴛᴇᴄᴛ ᴄᴏɴᴛᴇɴᴛ", callback_data="settings_protect_content"),
        ],
        [
            InlineKeyboardButton("sᴛᴀʀᴛ ᴛᴇxᴛ", callback_data="settings_start_text"),
            InlineKeyboardButton("ʜᴇʟᴘ ᴛᴇxᴛ", callback_data="settings_help_text"),
        ],
        [
            InlineKeyboardButton("ғᴏʀᴄᴇ sᴜʙ ɪᴍᴀɢᴇ", callback_data="settings_force_sub_image"),
            InlineKeyboardButton("sᴇᴛᴛɪɴɢs ɪᴍᴀɢᴇ", callback_data="settings_settings_image"),
        ],
        [InlineKeyboardButton("✖ ᴄʟᴏsᴇ", callback_data="settings_close")],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    settings_image = settings.get("settings_image")

    # Try sending with image if available
    if settings_image and os.path.exists(settings_image):
        try:
            if update.callback_query:
                await update.callback_query.message.reply_photo(
                    photo=open(settings_image, "rb"),
                    caption=settings_text,
                    reply_markup=reply_markup,
                    parse_mode="Markdown",
                )
            else:
                await update.message.reply_photo(
                    photo=open(settings_image, "rb"),
                    caption=settings_text,
                    reply_markup=reply_markup,
                    parse_mode="Markdown",
                )
            return  # ✅ Prevent sending text again
        except Exception as e:
            print(f"Error sending settings image: {e}")

    # Fallback if image not found
    if update.callback_query:
        await update.callback_query.edit_message_text(
            settings_text, reply_markup=reply_markup, parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            settings_text, reply_markup=reply_markup, parse_mode="Markdown"
        )
        
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
        await query.edit_message_caption("*ᴘʟᴇᴀsᴇ ᴡᴀɪᴛ\\.\\.\\.\\.*",
        parse_mode="MarkdownV2")
        await asyncio.sleep(0.3)
        await query.edit_message_caption(
            "🖼️ **Start Image Settings**\n\nɴᴏᴡ sᴇɴᴅ ᴍᴇ ɪᴍᴀɢᴇ ᴛʜᴀᴛ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ sᴇᴛ ɪɴ sᴛᴀʀᴛ ᴍᴏᴅᴜʟᴇ",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("《 ʙᴀᴄᴋ", callback_data="settings_back")]
            ]),
            parse_mode="Markdownv2"
        )
        context.user_data['waiting_for'] = 'start_image'
        
    elif data == "settings_help_img":
        await query.edit_message_caption("*ᴘʟᴇᴀsᴇ ᴡᴀɪᴛ\\.\\.\\.\\.*",
        parse_mode="MarkdownV2")
        await asyncio.sleep(0.3)
        await query.edit_message_caption(
            "📖 **Help Image Settings**\n\nɴᴏᴡ sᴇɴᴅ ᴍᴇ ɪᴍᴀɢᴇ ᴛʜᴀᴛ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ sᴇᴛ ɪɴ ʜᴇʟᴘ ᴍᴏᴅᴜʟᴇ",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("《 ʙᴀᴄᴋ", callback_data="settings_back")]
            ]),
            parse_mode="Markdown"
        )
        context.user_data['waiting_for'] = 'help_image'
        
    elif data == "settings_settings_image":
        await query.edit_message_caption("*ᴘʟᴇᴀsᴇ ᴡᴀɪᴛ\\.\\.\\.\\.*",
        parse_mode="MarkdownV2")
        await asyncio.sleep(0.3)
        await query.edit_message_caption(
           "🖼️ **Settings Image Configuration**\n\nɴᴏᴡ sᴇɴᴅ ᴍᴇ ᴛʜᴇ ɪᴍᴀɢᴇ ᴛʜᴀᴛ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ sᴇᴛ ғᴏʀ ᴛʜᴇ sᴇᴛᴛɪɴɢs ᴍᴏᴅᴜʟᴇ.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("《 ʙᴀᴄᴋ", callback_data="settings_back")]
            ]),
            parse_mode="Markdown"
        )
        context.user_data['waiting_for'] = 'settings_image'
        
    elif data == "settings_force_sub_image":
        await query.edit_message_caption("*ᴘʟᴇᴀsᴇ ᴡᴀɪᴛ\\.\\.\\.\\.*",
        parse_mode="MarkdownV2")
        await asyncio.sleep(0.3)
        await query.edit_message_caption(
           "🔒 **Force Subscribe Image Settings**\n\nɴᴏᴡ sᴇɴᴅ ᴍᴇ ɪᴍᴀɢᴇ ᴛʜᴀᴛ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ sᴇᴛ ɪɴ ғᴏʀᴄᴇ sᴜʙsᴄʀɪʙᴇ ᴍᴏᴅᴜʟᴇ",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("《 ʙᴀᴄᴋ", callback_data="settings_back")]
            ]),
            parse_mode="Markdown"
        )
        context.user_data['waiting_for'] = 'force_sub_image'
    
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
            [InlineKeyboardButton("《 ʙᴀᴄᴋ", callback_data="settings_back")]
        ]
        
        await query.edit_message_caption("*ᴘʟᴇᴀsᴇ ᴡᴀɪᴛ\\.\\.\\.\\.*",
        parse_mode="MarkdownV2")
        await asyncio.sleep(0.3)
        await query.edit_message_caption(
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
            [InlineKeyboardButton("《 ʙᴀᴄᴋ", callback_data="settings_back")]
        ]
        
        status = "✅ Enabled" if protect_content else "❌ Disabled"
        await query.edit_message_caption("*ᴘʟᴇᴀsᴇ ᴡᴀɪᴛ\\.\\.\\.\\.*",
        parse_mode="MarkdownV2")
        await asyncio.sleep(0.3)
        await query.edit_message_caption(
            f"🔒 **Protect Content Settings**\n\nCurrent status: {status}\n\nSelect forwarding option:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        
    elif data == "settings_start_text":
        await query.edit_message_caption("*ᴘʟᴇᴀsᴇ ᴡᴀɪᴛ\\.\\.\\.\\.*",
        parse_mode="MarkdownV2")
        await asyncio.sleep(0.3)
        await query.edit_message_caption(
            "📝 **Start Text Settings**\n\nSend me the new start text. You can use {mention} for user mention.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("《 ʙᴀᴄᴋ", callback_data="settings_back")]
            ]),
            parse_mode="Markdown"
        )
        context.user_data['waiting_for'] = 'start_text'
        
    elif data == "settings_help_text":
        await query.edit_message_caption("*ᴘʟᴇᴀsᴇ ᴡᴀɪᴛ\\.\\.\\.\\.*",
        parse_mode="MarkdownV2")
        await asyncio.sleep(0.3)
        await query.edit_message_caption(
            "📋 **Help Text Settings**\n\nSend me the new help text.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("《 ʙᴀᴄᴋ", callback_data="settings_back")]
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
    # Edit the same message instead of sending a new one
    query = update.callback_query
    settings = load_settings()

    auto_delete_time = settings.get("auto_delete_time", 10)
    protect_content = settings.get("protect_content", False)

    settings_text = (
        "⚙️ **Bot Settings**\n\n"
        f"sᴛᴀʀᴛ ɪᴍᴀɢᴇ: {'✅ Set' if settings.get('start_image') and os.path.exists(settings.get('start_image')) else '❌ Not Set'}\n"
        f"ʜᴇʟᴘ ɪᴍᴀɢᴇ: {'✅ Set' if settings.get('help_image') and os.path.exists(settings.get('help_image')) else '❌ Not Set'}\n"
        f"ᴀᴜᴛᴏ ᴅᴇʟᴇᴛᴇ: {auto_delete_time} minutes\n"
        f"ᴘʀᴏᴛᴇᴄᴛ ᴄᴏɴᴛᴇɴᴛ: {'✅ ON' if protect_content else '❌ OFF'}\n\n"
        f"ғᴏʀᴄᴇ sᴜʙ ɪᴍᴀɢᴇ: {'✅ Set' if settings.get('force_sub_image') and os.path.exists(settings.get('force_sub_image')) else '❌ Not Set'}\n"
        f"sᴇᴛᴛɪɴɢs ɪᴍᴀɢᴇ: {'✅ Set' if settings.get('settings_image') and os.path.exists(settings.get('settings_image')) else '❌ Not Set'}\n"
        "sᴇʟᴇᴄᴛ ᴀɴ ᴏᴘᴛɪᴏɴ ᴛᴏ ᴄᴏɴғɪɢᴜʀᴇ:"
    )

    keyboard = [
        [
            InlineKeyboardButton("sᴛᴀʀᴛ ɪᴍᴀɢᴇ", callback_data="settings_start_img"),
            InlineKeyboardButton("ʜᴇʟᴘ ɪᴍᴀɢᴇ", callback_data="settings_help_img"),
        ],
        [
            InlineKeyboardButton("ᴀᴜᴛᴏ ᴅᴇʟᴇᴛᴇ", callback_data="settings_auto_delete"),
            InlineKeyboardButton("ᴘʀᴏᴛᴇᴄᴛ ᴄᴏɴᴛᴇɴᴛ", callback_data="settings_protect_content"),
        ],
        [
            InlineKeyboardButton("sᴛᴀʀᴛ ᴛᴇxᴛ", callback_data="settings_start_text"),
            InlineKeyboardButton("ʜᴇʟᴘ ᴛᴇxᴛ", callback_data="settings_help_text"),
        ],
        [
            InlineKeyboardButton("ғᴏʀᴄᴇ sᴜʙ ɪᴍᴀɢᴇ", callback_data="settings_force_sub_image"),
            InlineKeyboardButton("sᴇᴛᴛɪɴɢs ɪᴍᴀɢᴇ", callback_data="settings_settings_image"),
        ],
        [InlineKeyboardButton("✖ ᴄʟᴏsᴇ", callback_data="settings_close")],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    # Edit the existing message
    try:
        await query.edit_message_caption(
            caption=settings_text,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    except Exception:
        # If no caption (for text-only), fallback to edit_message_text
        await query.edit_message_text(
            text=settings_text,
            reply_markup=reply_markup,
            parse_mode="Markdown"
    )
        
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
    
    if waiting_for in ['start_image', 'help_image', 'settings_image']:
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

       await update.message.reply_text(
        f"✅ {waiting_for.replace('_', ' ').title()} has been updated successfully!"
       )
    # Clear waiting state
       context.user_data.pop('waiting_for', None)
    # Return to settings menu
       await settings_handler(update, context)
    
    elif waiting_for == 'force_sub_image':
        if update.message.photo:
            # Get the largest photo
            photo = update.message.photo[-1]
            photo_file = await photo.get_file()
            filename = "force_sub_image.jpg"
            await photo_file.download_to_drive(filename)
            
            settings[waiting_for] = filename
            save_settings(settings)
            
            await update.message.reply_text("✅ Force Subscribe image has been set successfully!")
            # Clear waiting state and go back to settings
            context.user_data.pop('waiting_for', None)
            await settings_handler(update, context)
        else:
            await update.message.reply_text("❌ Please send a valid image!")
        # Clear waiting state and go back to settings
        context.user_data.pop('waiting_for', None)
        await settings_handler(update, context)
