import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from middleware import check_ban_and_register
import asyncio
from permission import CheckBotAdmin

OWNER_ID = 5373577888
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
@check_ban_and_register
async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    mention = user.mention_html()
    
    settings = load_settings()
    start_text = settings.get("start_text", "Hi {mention} welcome to File Store Bot").format(mention=mention)
    start_image = settings.get("start_image", "img.jpg")
    
    # Create keyboard
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
    
    data = query.data
    user_id = query.from_user.id
    
    if data == "start_about":
        loading_text = ("*ᴘʟᴇᴀsᴇ ᴡᴀɪᴛ\\.\\.\\.\\.*")
        about_text = (
            "*ʙᴏᴛ ɴᴀᴍᴇ* \\- *Rɪᴍᴜʀᴜ Tᴇᴍᴘᴇsᴛ*\n"
            "*ʙᴏᴛ ᴜsᴇʀɴᴀᴍᴇ* \\- *@Rimuru\\_filebot*\n"
            "*ᴘʏᴛʜᴏɴ ᴠᴇʀsɪᴏɴ* \\- *3\\.8\\+*\n"
            "*ᴅᴀᴛᴀʙᴀsᴇ* \\- *ᴊsᴏɴ*\n"
            "*ᴏᴡɴᴇʀ* \\- [ʜᴀɴᴢᴏ𒆜](https://t\\.me/quarel7)\n"
            "ᴛʜɪs ʙᴏᴛ ɪs ᴏɴʟʏ ғᴏʀ [*ᴀɴɪᴍᴇ ғᴀʙʟᴇ*](https://t\\.me/Anime\\_Fable)"
        )
        
        keyboard = [
      [
        InlineKeyboardButton("《 ʙᴀᴄᴋ", callback_data="start_back"),
        InlineKeyboardButton("✖ ᴄʟᴏsᴇ", callback_data="start_close")
      ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        if query.message.photo:
            await query.edit_message_caption(
                caption=loading_text,
                reply_markup=reply_markup,
                parse_mode="MarkdownV2",
            )
        else:
            await query.edit_message_text(
                text=loading_text,
                reply_markup=reply_markup
            )

        await asyncio.sleep(0.3)
        
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
        if user_id not in admins and user_id != OWNER_ID:
            await query.answer("You are not authorized to use this bot", show_alert=True)
            return
        
        # If user is admin/owner, show help menu
        settings = load_settings()
        help_loading = ("*ᴘʟᴇᴀsᴇ ᴡᴀɪᴛ\\.\\.\\.\\.*")
        help_text = settings.get("help_text", 
            "Available Commands:\\n\\n/start - Start the bot\\n/help - Show this help message\\n/genlink - Generate link\\n/batchlink - Generate batch links\\n/custombatch - Custom batch processing\\n/fsub - Force subscribe\\n/settings - Bot settings\\n/promote - Promote user to admin\\n/demote - Demote admin\\n/ban - Ban user\\n/unban - Unban user\\n/users - Show users\\n/admins - Show admins\\n/update - Update bot\\n/restart - Restart bot"
        )
        
        keyboard = [
      [
        InlineKeyboardButton("《 ʙᴀᴄᴋ", callback_data="start_back"),
        InlineKeyboardButton("✖ ᴄʟᴏsᴇ", callback_data="start_close")
      ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        if query.message.photo:
            await query.edit_message_caption(
                caption=help_loading,
                reply_markup=reply_markup,
                parse_mode="MarkdownV2",
            )
        else:
            await query.edit_message_text(
                text=help_loading,
                reply_markup=reply_markup
            )
        await asyncio.sleep(0.3)
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
        back_text = ("*ᴘʟᴇᴀsᴇ ᴡᴀɪᴛ\\.\\.\\.\\.*")
        start_text = settings.get("start_text", "Hi {mention} welcome to File Store Bot").format(mention=mention)
        
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

        if query.message.photo:
            await query.edit_message_caption(
                caption=back_text,
                reply_markup=reply_markup,
                parse_mode="MarkdownV2",
            )
        else:
            await query.edit_message_text(
                text=back_text,
                reply_markup=reply_markup
        )
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
