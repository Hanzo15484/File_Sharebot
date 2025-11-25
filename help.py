import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

# Load admin data
def load_admins():
    try:
        with open('admins.json', 'r') as f:
            return json.load(f)
    except:
        return []

# Load settings
def load_settings():
    try:
        with open('settings.json', 'r') as f:
            return json.load(f)
    except:
        return {
            "help_image": "",
            "help_text": "Available Commands:\\n\\n/start - Start the bot\\n/help - Show this help message\\n/genlink - Generate link\\n/batchlink - Generate batch links\\n/custombatch - Custom batch processing\\n/fsub - Force subscribe\\n/settings - Bot settings\\n/promote - Promote user to admin\\n/demote - Demote admin\\n/ban - Ban user\\n/unban - Unban user\\n/users - Show users\\n/admins - Show admins\\n/update - Update bot\\n/restart - Restart bot"
        }
@CheckBotAdmin()
async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    admins = load_admins()
    
    # Check if user is admin or owner
    if user_id not in admins and user_id != 5373577888:  # Owner ID
        await update.message.reply_text("You are not authorized to use this command!")
        return
    
    settings = load_settings()
    help_text = settings.get("help_text", 
        "Available Commands:\\n\\n/start - Start the bot\\n/help - Show this help message\\n/genlink - Generate link\\n/batchlink - Generate batch links\\n/custombatch - Custom batch processing\\n/fsub - Force subscribe\\n/settings - Bot settings\\n/promote - Promote user to admin\\n/demote - Demote admin\\n/ban - Ban user\\n/unban - Unban user\\n/users - Show users\\n/admins - Show admins\\n/update - Update bot\\n/restart - Restart bot"
    )
    
    help_image = settings.get("help_image", "")
    
    keyboard = [
    [
        InlineKeyboardButton("《 ʙᴀᴄᴋ", callback_data="start_back"),
        InlineKeyboardButton("✖ ᴄʟᴏsᴇ", callback_data="start_close")
    ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Send message with image if available
    if help_image:
        try:
            with open(help_image, 'rb') as photo:
                await context.bot.send_photo(
                    chat_id=update.effective_chat.id,
                    photo=photo,
                    caption=help_text,
                    reply_markup=reply_markup
                )
        except FileNotFoundError:
            # If image not found, send text only
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=help_text,
                reply_markup=reply_markup
            )
    else:
        # Send text only if no help image is set
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=help_text,
            reply_markup=reply_markup
        )

@CheckBotAdmin()
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    user_id = query.from_user.id
    
    if data == "help_back":
        # Go back to start menu
        user = query.from_user
        mention = user.mention_html()
        
        settings = load_settings()
        start_text = settings.get("start_text", "Hi {mention} welcome to File Store Bot").format(mention=mention)
        start_image = settings.get("start_image", "img.jpg")
        
        keyboard = [
        [
          InlineKeyboardButton("ᴀʙᴏᴜᴛ", callback_data="start_about"),
          InlineKeyboardButton("ʜᴇʟᴘ", callback_data="start_help")
        ],
        [
          InlineKeyboardButton("✖ ᴄʟᴏsᴇ", callback_data="start_close")
        ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Check if current message has photo or is text
        if query.message.photo:
            # Current message has photo, so we need to send new start message
            try:
                with open(start_image, 'rb') as photo:
                    await context.bot.send_photo(
                        chat_id=update.effective_chat.id,
                        photo=photo,
                        caption=start_text,
                        reply_markup=reply_markup,
                        parse_mode='HTML'
                    )
                await query.message.delete()
            except FileNotFoundError:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=start_text,
                    reply_markup=reply_markup,
                    parse_mode='HTML'
                )
                await query.message.delete()
        else:
            # Current message is text, edit it to show start menu
            try:
                # Try to send photo if start image exists
                with open(start_image, 'rb') as photo:
                    await context.bot.send_photo(
                        chat_id=update.effective_chat.id,
                        photo=photo,
                        caption=start_text,
                        reply_markup=reply_markup,
                        parse_mode='HTML'
                    )
                    await query.message.delete()
            except FileNotFoundError:
                # If no image, edit current text message
                await query.edit_message_text(
                    text=start_text,
                    reply_markup=reply_markup,
                    parse_mode='HTML'
                )
    
    elif data == "help_close":
        await query.message.delete()
