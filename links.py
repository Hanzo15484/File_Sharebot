import os
import json
import base64
import asyncio
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler

# Load settings
def load_settings():
    try:
        with open('settings.json', 'r') as f:
            return json.load(f)
    except:
        return {
            "auto_delete_time": 10,
            "protect_content": False
        }

# Load links data
def load_links():
    try:
        with open('links.json', 'r') as f:
            return json.load(f)
    except:
        return {}

# Save links data
def save_links(links):
    with open('links.json', 'w') as f:
        json.dump(links, f)

# Encode file ID to base64
def encode_file_id(file_id):
    encoded = base64.urlsafe_b64encode(file_id.encode()).decode()
    # Remove padding to make URL shorter
    return encoded.rstrip('=')

# Decode base64 to file ID
def decode_file_id(encoded_id):
    # Add padding back if needed
    padding = 4 - (len(encoded_id) % 4)
    if padding != 4:
        encoded_id += '=' * padding
    try:
        return base64.urlsafe_b64decode(encoded_id.encode()).decode()
    except:
        return None

async def genlink_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    admins = load_admins()
    
    # Check if user is admin or owner
    if user_id not in admins and user_id != 5373577888:
        await update.message.reply_text("You are not authorized to use this command!")
        return
    
    if not update.message.reply_to_message:
        await update.message.reply_text("Please reply to a message to generate a link.")
        return
    
    replied_message = update.message.reply_to_message
    message_id = replied_message.message_id
    chat_id = update.effective_chat.id
    
    # Generate unique file ID (using chat_id + message_id)
    file_id = f"{chat_id}:{message_id}"
    encoded_id = encode_file_id(file_id)
    
    # Get bot username
    bot_username = context.bot.username
    link = f"https://t.me/{bot_username}?start={encoded_id}"
    
    # Store message data in links.json
    links = load_links()
    links[encoded_id] = {
        "chat_id": chat_id,
        "message_id": message_id,
        "created_at": datetime.utcnow().isoformat(),
        "created_by": user_id
    }
    save_links(links)
    
    await update.message.reply_text(
        f"✅ Link generated successfully!\n\n{link}",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔗 Copy Link", url=link)]
        ])
    )

async def start_link_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    args = context.args
    
    if not args:
        # Regular start command
        await regular_start_handler(update, context)
        return
    
    encoded_id = args[0]
    file_id = decode_file_id(encoded_id)
    
    if not file_id:
        await update.message.reply_text("❌ Invalid link!")
        return
    
    links = load_links()
    if encoded_id not in links:
        await update.message.reply_text("❌ Link expired or not found!")
        return
    
    link_data = links[encoded_id]
    chat_id = link_data["chat_id"]
    message_id = link_data["message_id"]
    
    try:
        # Forward the original message
        settings = load_settings()
        protect_content = settings.get("protect_content", False)
        
        forwarded_msg = await context.bot.copy_message(
            chat_id=update.effective_chat.id,
            from_chat_id=chat_id,
            message_id=message_id,
            protect_content=protect_content
        )
        
        # Store the forwarded message info for deletion
        auto_delete_time = settings.get("auto_delete_time", 10)
        msg = await update.message.reply_text(f"> *⚠️ ɪᴍᴘᴏʀᴛᴀɴᴛ\\:*\n\n> *ᴛʜɪs ғɪʟᴇ ᴡɪʟʟ ʙᴇ ᴅᴇʟᴇᴛᴇᴅ ɪɴ {auto_delete_time} ᴍɪɴᴜᴛᴇs\\. ᴘʟᴇᴀsᴇ sᴀᴠᴇ ᴏʀ ғᴏʀᴡᴀʀᴅ ɪᴛ ᴛᴏ ʏᴏᴜʀ sᴀᴠᴇᴅ ᴍᴇssᴀɢᴇs ʙᴇғᴏʀᴇ ɪᴛ ɢᴇᴛs ʀᴇᴍᴏᴠᴇᴅ\\.*",
        parse_mode = "MarkdownV2")
    await asyncio.sleep(delay_minutes * 60)
    
    try:
        await msg.delete()
    except Exception as e:
        print(f"Error deleting file message: {e}")
        # Schedule deletion without sending warning message first
        asyncio.create_task(
            delete_and_notify(
                context, 
                update.effective_chat.id, 
                forwarded_msg.message_id,
                auto_delete_time,
                encoded_id
            )
        )
        
    except Exception as e:
        await update.message.reply_text("❌ Error retrieving file. It may have been deleted.")

async def delete_and_notify(context, chat_id, file_msg_id, delay_minutes, encoded_id):
    """Delete file after delay and send retrieval message"""
    
    # Wait for the specified time
    await asyncio.sleep(delay_minutes * 60)
    
    try:
        # Delete the file message
        await context.bot.delete_message(chat_id, file_msg_id)
    except Exception as e:
        print(f"Error deleting file message: {e}")
    
    # Send retrieval message after deletion
    completion_text = (
        "*✅ ʏᴏᴜʀ ғɪʟᴇ/ᴠɪᴅᴇᴏ ʜᴀs ʙᴇᴇɴ sᴜᴄᴄᴇssғᴜʟʟʏ ᴅᴇʟᴇᴛᴇᴅ\\!*\n\n"
        "> *ɪғ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ ʀᴇᴛʀɪᴇᴠᴇ ɪᴛ ᴀɢᴀɪɴ, ᴄʟɪᴄᴋ ᴛʜᴇ \"♻️ ᴄʟɪᴄᴋ ʜᴇʀᴇ\" ʙᴜᴛᴛᴏɴ\\. ɪғ ɴᴏᴛ, sɪᴍᴘʟʏ ᴄʟᴏsᴇ ᴛʜɪs ᴍᴇssᴀɢᴇ\\.*"
    )
    
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("♻️ ᴄʟɪᴄᴋ ʜᴇʀᴇ", url=f"https://t.me/{context.bot.username}?start={encoded_id}"),
            InlineKeyboardButton("ᴄʟᴏsᴇ", callback_data=f"link_close")
        ]
    ])
    
    try:
        retrieval_msg = await context.bot.send_message(
            chat_id=chat_id,
            text=completion_text,
            reply_markup=keyboard,
            parse_mode="MarkdownV2"
        )
        
        # Schedule deletion of retrieval message after 10 minutes
        asyncio.create_task(
            delete_retrieval_message(context, chat_id, retrieval_msg.message_id, 10)
        )
    except Exception as e:
        print(f"Error sending retrieval message: {e}")

async def delete_retrieval_message(context, chat_id, message_id, delay_minutes):
    """Delete retrieval message after delay"""
    await asyncio.sleep(delay_minutes * 60)
    try:
        await context.bot.delete_message(chat_id, message_id)
    except:
        pass

async def link_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data == "link_close":
        await query.message.delete()

# Load admin data
def load_admins():
    try:
        with open('admins.json', 'r') as f:
            return json.load(f)
    except:
        return [5373577888]

# Import regular start handler from start.py
async def regular_start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from start import start_handler
    await start_handler(update, context)
