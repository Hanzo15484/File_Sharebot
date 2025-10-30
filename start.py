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
            "start_image": "img.jpg",
            "start_text": "Hi {mention} welcome to File Store Bot",
            "help_text": "Available Commands:\\n\\n/start - Start the bot\\n/help - Show this help message\\n/genlink - Generate link\\n/batchlink - Generate batch links\\n/custombatch - Custom batch processing\\n/fsub - Force subscribe\\n/settings - Bot settings\\n/promote - Promote user to admin\\n/demote - Demote admin\\n/ban - Ban user\\n/unban - Unban user\\n/users - Show users\\n/admins - Show admins\\n/update - Update bot\\n/restart - Restart bot"
        }

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    mention = user.mention_html()
    
    settings = load_settings()
    start_text = settings.get("start_text", "Hi {mention} welcome to File Store Bot").format(mention=mention)
    start_image = settings.get("start_image", "img.jpg")
    
    # Create keyboard
    keyboard = [
        [InlineKeyboardButton("About", callback_data="start_about")],
        [InlineKeyboardButton("Help", callback_data="start_help")],
        [InlineKeyboardButton("Close", callback_data="start_close")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Send message with image
    try:
        with open(start_image, 'rb') as photo:
            await context.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=photo,
                caption=start_text,
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
    except FileNotFoundError:
        # If image not found, send text only
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=start_text,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    user_id = query.from_user.id
    
    if data == "start_about":
        about_text = (
            "\*ʙᴏᴛ ɴᴀᴍᴇ\* \- Rɪᴍᴜʀᴜ Tᴇᴍᴘᴇsᴛ"
            "\*ʙᴏᴛ ᴜsᴇʀɴᴀᴍᴇ\* \- @Rimuru_filebot"
            "\*ᴘʏᴛʜᴏɴ ᴠᴇʀsɪᴏɴ\* \- 3.8\+"
            "\*ᴅᴀᴛᴀʙᴀsᴇ\* \- ᴊsᴏɴ"
            "\*ᴏᴡɴᴇʀ\* \- \[ʜᴀɴᴢᴏ𒆜\]\(url\-https\://t\.me/quarel7\)"
            "\*ᴛʜɪs ʙᴏᴛ ɪs ᴏɴʟʏ ғᴏʀ ᴀɴɪᴍᴇ ғᴀʙʟᴇ\*"
        )
        
        keyboard = [
            [InlineKeyboardButton("Back", callback_data="start_back")],
            [InlineKeyboardButton("Close", callback_data="start_close")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Check if message has photo (caption) or is text message
        if query.message.photo:
            await query.edit_message_caption(
                caption=about_text,
                reply_markup=reply_markup,
                parse_mode="MarkdownV2",
            )
        else:
            await query.edit_message_text(
                text=about_text,
                reply_markup=reply_markup
            )
    
    elif data == "start_help":
        admins = load_admins()
        if user_id not in admins and user_id != 5373577888:  # Owner ID
            await query.answer("You are not my senpai!", show_alert=True)
            return
        
        # If user is admin/owner, show help menu
        settings = load_settings()
        help_text = settings.get("help_text", 
            "Available Commands:\\n\\n/start - Start the bot\\n/help - Show this help message\\n/genlink - Generate link\\n/batchlink - Generate batch links\\n/custombatch - Custom batch processing\\n/fsub - Force subscribe\\n/settings - Bot settings\\n/promote - Promote user to admin\\n/demote - Demote admin\\n/ban - Ban user\\n/unban - Unban user\\n/users - Show users\\n/admins - Show admins\\n/update - Update bot\\n/restart - Restart bot"
        )
        
        keyboard = [
            [InlineKeyboardButton("Back", callback_data="start_back")],
            [InlineKeyboardButton("Close", callback_data="start_close")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Check if message has photo (caption) or is text message
        if query.message.photo:
            await query.edit_message_caption(
                caption=help_text,
                reply_markup=reply_markup
            )
        else:
            await query.edit_message_text(
                text=help_text,
                reply_markup=reply_markup
            )
    
    elif data == "start_back":
        user = query.from_user
        mention = user.mention_html()
        
        settings = load_settings()
        start_text = settings.get("start_text", "Hi {mention} welcome to File Store Bot").format(mention=mention)
        
        keyboard = [
            [InlineKeyboardButton("About", callback_data="start_about")],
            [InlineKeyboardButton("Help", callback_data="start_help")],
            [InlineKeyboardButton("Close", callback_data="start_close")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Check if message has photo (caption) or is text message
        if query.message.photo:
            await query.edit_message_caption(
                caption=start_text,
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
        else:
            await query.edit_message_text(
                text=start_text,
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
    
    elif data == "start_close":
        await query.message.delete()
