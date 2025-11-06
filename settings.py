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

async def show_updated_auto_delete_menu(query, selected):
    def btn(label, value):
        return f"✅ {label}" if selected == value else label

    keyboard = [
        [
            InlineKeyboardButton(btn("5 ᴍɪɴ", 5), callback_data="auto_delete_5"),
            InlineKeyboardButton(btn("10 ᴍɪɴ", 10), callback_data="auto_delete_10"),
        ],
        [
            InlineKeyboardButton(btn("15 ᴍɪɴ", 15), callback_data="auto_delete_15"),
            InlineKeyboardButton(btn("20 ᴍɪɴ", 20), callback_data="auto_delete_20"),
        ],
        [
            InlineKeyboardButton(btn("30 ᴍɪɴ", 30), callback_data="auto_delete_30"),
            InlineKeyboardButton(btn("45 ᴍɪɴ", 45), callback_data="auto_delete_45"),
        ],
        [
            InlineKeyboardButton(btn("1 ʜʀ", 60), callback_data="auto_delete_60"),
            InlineKeyboardButton(btn("3 ʜʀ", 180), callback_data="auto_delete_180"),
        ],
        [InlineKeyboardButton(btn("ᴅɪsᴀʙʟᴇ", 0), callback_data="auto_delete_0")],
        [InlineKeyboardButton("《 ʙᴀᴄᴋ", callback_data="settings_back")],
    ]

    text = "⏰ **Auto Delete Settings**\n\nSelect time duration:"
    
    # Detect message type
    if query.message.photo:
        await query.edit_message_caption(
            caption=text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="MarkdownV2"
        )
    else:
        await query.edit_message_text(
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="MarkdownV2"
        )

async def show_updated_protect_menu(query, is_enabled):
    on_text  = "✅ ᴏɴ" if is_enabled else "ᴏɴ"
    off_text = "✅ ᴏғғ" if not is_enabled else "ᴏғғ"

    keyboard = [
        [InlineKeyboardButton("ғᴏʀᴡᴀʀᴅ", callback_data="protect_forward")],
        [
            InlineKeyboardButton(on_text, callback_data="protect_on"),
            InlineKeyboardButton(off_text, callback_data="protect_off")
        ],
        [InlineKeyboardButton("《 ʙᴀᴄᴋ", callback_data="settings_back")]
    ]

    text = f"🔒 **Protect Content Settings**\n\nCurrent status: {'✅ Enabled' if is_enabled else '❌ Disabled'}\n\nSelect forwarding option:"

    # Detect if message is photo or text
    if query.message.photo:
        await query.edit_message_caption(
            caption=text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="MarkdownV2"
        )
    else:
        await query.edit_message_text(
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="MarkdownV2"
        )

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
    await query.answer(cache_time=1)

    data = query.data
    user_id = query.from_user.id
    admins = load_admins()

    # Check if user is admin or owner
    if user_id not in admins and user_id != 5373577888:
        await query.answer("You are not authorized!", show_alert=True)
        return

    settings = load_settings()

    # START IMAGE
    if data == "settings_start_img":
        await query.edit_message_caption(
            "*ᴘʟᴇᴀsᴇ ᴡᴀɪᴛ\\.\\.\\.\\.*",
            parse_mode="MarkdownV2"
        )
        await asyncio.sleep(0.3)
        await query.edit_message_caption(
            "🖼️ **Start Image Settings**\n\nɴᴏᴡ sᴇɴᴅ ᴍᴇ ɪᴍᴀɢᴇ ᴛʜᴀᴛ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ sᴇᴛ ɪɴ sᴛᴀʀᴛ ᴍᴏᴅᴜʟᴇ",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("《 ʙᴀᴄᴋ", callback_data="settings_back")]
            ]),
            parse_mode="MarkdownV2"
        )
        context.user_data['waiting_for'] = 'start_image'

    # HELP IMAGE
    elif data == "settings_help_img":
        await query.edit_message_caption(
            "*ᴘʟᴇᴀsᴇ ᴡᴀɪᴛ\\.\\.\\.\\.*",
            parse_mode="MarkdownV2"
        )
        await asyncio.sleep(0.3)
        await query.edit_message_caption(
            "📖 **Help Image Settings**\n\nɴᴏᴡ sᴇɴᴅ ᴍᴇ ɪᴍᴀɢᴇ ᴛʜᴀᴛ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ sᴇᴛ ɪɴ ʜᴇʟᴘ ᴍᴏᴅᴜʟᴇ",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("《 ʙᴀᴄᴋ", callback_data="settings_back")]
            ]),
            parse_mode="MarkdownV2"
        )
        context.user_data['waiting_for'] = 'help_image'

    # SETTINGS IMAGE
    elif data == "settings_settings_image":
        await query.edit_message_caption(
            "*ᴘʟᴇᴀsᴇ ᴡᴀɪᴛ\\.\\.\\.\\.*",
            parse_mode="MarkdownV2"
        )
        await asyncio.sleep(0.3)
        await query.edit_message_caption(
            "🖼️ **Settings Image Configuration**\n\nɴᴏᴡ sᴇɴᴅ ᴍᴇ ᴛʜᴇ ɪᴍᴀɢᴇ ᴛʜᴀᴛ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ sᴇᴛ ғᴏʀ ᴛʜᴇ sᴇᴛᴛɪɴɢs ᴍᴏᴅᴜʟᴇ",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("《 ʙᴀᴄᴋ", callback_data="settings_back")]
            ]),
            parse_mode="MarkdownV2"
        )
        context.user_data['waiting_for'] = 'settings_image'

    # FORCE SUBSCRIBE IMAGE
    elif data == "settings_force_sub_image":
        await query.edit_message_caption(
            "*ᴘʟᴇᴀsᴇ ᴡᴀɪᴛ\\.\\.\\.\\.*",
            parse_mode="MarkdownV2"
        )
        await asyncio.sleep(0.3)
        await query.edit_message_caption(
            "🔒 **Force Subscribe Image Settings**\n\nɴᴏᴡ sᴇɴᴅ ᴍᴇ ɪᴍᴀɢᴇ ᴛʜᴀᴛ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ sᴇᴛ ɪɴ ғᴏʀᴄᴇ sᴜʙsᴄʀɪʙᴇ ᴍᴏᴅᴜʟᴇ",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("《 ʙᴀᴄᴋ", callback_data="settings_back")]
            ]),
            parse_mode="MarkdownV2"
        )
        context.user_data['waiting_for'] = 'force_sub_image'

    # AUTO DELETE
    elif data == "settings_auto_delete":
        auto_delete_time = settings.get("auto_delete_time", 10)

        # Dynamic checkmark system
        def btn(label, value):
            return f"✅ {label}" if auto_delete_time == value else label

        keyboard = [
            [
                InlineKeyboardButton(btn("5 ᴍɪɴ", 5), callback_data="auto_delete_5"),
                InlineKeyboardButton(btn("10 ᴍɪɴ", 10), callback_data="auto_delete_10")
            ],
            [
                InlineKeyboardButton(btn("15 ᴍɪɴ", 15), callback_data="auto_delete_15"),
                InlineKeyboardButton(btn("20 ᴍɪɴ", 20), callback_data="auto_delete_20")
            ],
            [
                InlineKeyboardButton(btn("30 ᴍɪɴ", 30), callback_data="auto_delete_30"),
                InlineKeyboardButton(btn("45 ᴍɪɴ", 45), callback_data="auto_delete_45")
            ],
            [
                InlineKeyboardButton(btn("1 ʜʀ", 60), callback_data="auto_delete_60"),
                InlineKeyboardButton(btn("3 ʜʀ", 180), callback_data="auto_delete_180")
            ],
            [InlineKeyboardButton(btn("ᴅɪsᴀʙʟᴇ", 0), callback_data="auto_delete_0")],
            [InlineKeyboardButton("《 ʙᴀᴄᴋ", callback_data="settings_back")]
        ]

        await query.edit_message_caption(
            "*ᴘʟᴇᴀsᴇ ᴡᴀɪᴛ\\.\\.\\.\\.*",
            parse_mode="MarkdownV2"
        )
        await asyncio.sleep(0.3)
        await query.edit_message_caption(
            "⏰ **Auto Delete Settings**\n\nSelect time duration for auto deletion:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="MarkdownV2"
        )

    # PROTECT CONTENT
    elif data == "settings_protect_content":
        protect_content = settings.get("protect_content", False)

        on_text = "✅ ᴏɴ" if protect_content else "ᴏɴ"
        off_text = "✅ ᴏғғ" if not protect_content else "ᴏғғ"

        keyboard = [
            [InlineKeyboardButton("ғᴏʀᴡᴀʀᴅ", callback_data="protect_forward")],
            [
                InlineKeyboardButton(on_text, callback_data="protect_on"),
                InlineKeyboardButton(off_text, callback_data="protect_off")
            ],
            [InlineKeyboardButton("《 ʙᴀᴄᴋ", callback_data="settings_back")]
        ]

        status = "✅ Enabled" if protect_content else "❌ Disabled"

        await query.edit_message_caption(
            "*ᴘʟᴇᴀsᴇ ᴡᴀɪᴛ\\.\\.\\.\\.*",
            parse_mode="MarkdownV2"
        )
        await asyncio.sleep(0.3)
        await query.edit_message_caption(
            f"🔒 **Protect Content Settings**\n\nCurrent status: {status}\n\nSelect forwarding option:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="MarkdownV2"
        )

    # START TEXT
    elif data == "settings_start_text":
        await query.edit_message_caption(
            "*ᴘʟᴇᴀsᴇ ᴡᴀɪᴛ\\.\\.\\.\\.*",
            parse_mode="MarkdownV2"
        )
        await asyncio.sleep(0.3)
        await query.edit_message_caption(
            "📝 **Start Text Settings**\n\nSend me the new start text. You can use {mention} for user mention.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("《 ʙᴀᴄᴋ", callback_data="settings_back")]
            ]),
            parse_mode="MarkdownV2"
        )
        context.user_data['waiting_for'] = 'start_text'

    # HELP TEXT
    elif data == "settings_help_text":
        await query.edit_message_caption(
            "*ᴘʟᴇᴀsᴇ ᴡᴀɪᴛ\\.\\.\\.\\.*",
            parse_mode="MarkdownV2"
        )
        await asyncio.sleep(0.3)
        await query.edit_message_caption(
            "📋 **Help Text Settings**\n\nSend me the new help text.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("《 ʙᴀᴄᴋ", callback_data="settings_back")]
            ]),
            parse_mode="MarkdownV2"
        )
        context.user_data['waiting_for'] = 'help_text'

    # AUTO DELETE TIME SELECTION
    elif data.startswith("auto_delete_"):
        time_minutes = int(data.split("_")[2])
        settings["auto_delete_time"] = time_minutes
        save_settings(settings)

        status = "Disabled" if time_minutes == 0 else f"{time_minutes} minutes"
        await query.answer(f"Auto delete set to {status}!", show_alert=True)
        await show_updated_auto_delete_menu(query, time_minutes)

    # PROTECT CONTENT TOGGLE
    elif data.startswith("protect_"):
        if data == "protect_on":
            settings["protect_content"] = True
            save_settings(settings)
            await query.answer("Protect content enabled!", show_alert=True)
            await show_updated_protect_menu(query, True)
        elif data == "protect_off":
            settings["protect_content"] = False
            save_settings(settings)
            await query.answer("Protect content disabled!", show_alert=True)
            await show_updated_protect_menu(query, False)

    elif data == "protect_forward":
       await query.answer(
         "ᴘʟᴇᴀsᴇ ᴄʜᴏᴏsᴇ ᴛʜᴇ ᴏᴘᴛɪᴏɴ ʙᴇʟᴏᴡ:",
         show_alert=True
      )
    # BACK BUTTON
    elif data == "settings_back":
        settings = load_settings()
        context.user_data.pop('waiting_for', None)
        await query.edit_message_caption(
            "*ᴘʟᴇᴀsᴇ ᴡᴀɪᴛ\\.\\.\\.\\.*",
            parse_mode="MarkdownV2"
        )
        await asyncio.sleep(0.3)
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
                InlineKeyboardButton("ʜᴇʟᴘ ɪᴍᴀɢᴇ", callback_data="settings_help_img")
            ],
            [
                InlineKeyboardButton("ᴀᴜᴛᴏ ᴅᴇʟᴇᴛᴇ", callback_data="settings_auto_delete"),
                InlineKeyboardButton("ᴘʀᴏᴛᴇᴄᴛ ᴄᴏɴᴛᴇɴᴛ", callback_data="settings_protect_content")
            ],
            [
                InlineKeyboardButton("sᴛᴀʀᴛ ᴛᴇxᴛ", callback_data="settings_start_text"),
                InlineKeyboardButton("ʜᴇʟᴘ ᴛᴇxᴛ", callback_data="settings_help_text")
            ],
            [
                InlineKeyboardButton("ғᴏʀᴄᴇ sᴜʙ ɪᴍᴀɢᴇ", callback_data="settings_force_sub_image"),
                InlineKeyboardButton("sᴇᴛᴛɪɴɢs ɪᴍᴀɢᴇ", callback_data="settings_settings_image")
            ],
            [InlineKeyboardButton("✖ ᴄʟᴏsᴇ", callback_data="settings_close")]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)

        try:
            await query.edit_message_caption(
                caption=settings_text,
                reply_markup=reply_markup,
                parse_mode="MarkdownV2"
            )
        except Exception:
            await query.edit_message_text(
                text=settings_text,
                reply_markup=reply_markup,
                parse_mode="MarkdownV2"
            )

    # CLOSE BUTTON
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
