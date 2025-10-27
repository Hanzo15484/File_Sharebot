import os
import json
import base64
import asyncio
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters

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

# Load admin data
def load_admins():
    try:
        with open('admins.json', 'r') as f:
            return json.load(f)
    except:
        return [5373577888]

# Encode file ID to base64
def encode_file_id(file_id):
    encoded = base64.urlsafe_b64encode(file_id.encode()).decode()
    return encoded.rstrip('=')

# Decode base64 to file ID
def decode_file_id(encoded_id):
    padding = 4 - (len(encoded_id) % 4)
    if padding != 4:
        encoded_id += '=' * padding
    try:
        return base64.urlsafe_b64decode(encoded_id.encode()).decode()
    except:
        return None

async def batchlink_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    admins = load_admins()
    
    # Check if user is admin or owner
    if user_id not in admins and user_id != 5373577888:
        await update.message.reply_text("You are not authorized to use this command!")
        return
    
    await update.message.reply_text(
        "📌 ᴘʟᴇᴀsᴇ ғᴏʀᴡᴀʀᴅ ᴛʜᴇ ғɪʀsᴛ ᴍᴇssᴀɢᴇ ғʀᴏᴍ ʏᴏᴜʀ ʙᴀᴛᴄʜ ᴄʜᴀɴɴᴇʟ (ᴡɪᴛʜ ғᴏʀᴡᴀʀᴅ ᴛᴀɢ)\n"
        "ᴏʀ sʜᴀʀᴇ ᴛʜᴇ ʟɪɴᴋ ᴏғ ᴛʜᴇ ғɪʀsᴛ ᴍᴇssᴀɢᴇ ғʀᴏᴍ ʏᴏᴜʀ ʙᴀᴛᴄʜ ᴄʜᴀɴɴᴇʟ."
    )
    
    context.user_data['batch_state'] = 'waiting_first_message'

async def batch_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    admins = load_admins()
    
    # Check if user is admin or owner
    if user_id not in admins and user_id != 5373577888:
        return
    
    batch_state = context.user_data.get('batch_state')
    
    if not batch_state:
        return
    
    message = update.message
    
    if batch_state == 'waiting_first_message':
        # Get chat ID and message ID from forwarded message or message link
        chat_id, message_id = await extract_chat_message_id(update, context)
        
        if not chat_id or not message_id:
            await update.message.reply_text("❌ Could not extract message information. Please forward a message from a channel.")
            return
        
        context.user_data['batch_data'] = {
            'first_chat_id': chat_id,
            'first_message_id': message_id
        }
        context.user_data['batch_state'] = 'waiting_last_message'
        
        await update.message.reply_text(
            "📌 ɢʀᴇᴀᴛ! ɴᴏᴡ ғᴏʀᴡᴀʀᴅ ᴛʜᴇ ʟᴀsᴛ ᴍᴇssᴀɢᴇ ғʀᴏᴍ ʏᴏᴜʀ ʙᴀᴛᴄʜ ᴄʜᴀɴɴᴇʟ (ᴡɪᴛʜ ғᴏʀᴡᴀʀᴅ ᴛᴀɢ)\n"
            "ᴏʀ sʜᴀʀᴇ ᴛʜᴇ ʟɪɴᴋ ᴏғ ᴛʜᴇ ʟᴀsᴛ ᴍᴇssᴀɢᴇ ғʀᴏᴍ ʏᴏᴜʀ ʙᴀᴛᴄʜ ᴄʜᴀɴɴᴇʟ."
        )
    
    elif batch_state == 'waiting_last_message':
        # Get chat ID and message ID from forwarded message or message link
        chat_id, message_id = await extract_chat_message_id(update, context)
        
        if not chat_id or not message_id:
            await update.message.reply_text("❌ Could not extract message information. Please forward a message from a channel.")
            return
        
        batch_data = context.user_data.get('batch_data', {})
        first_chat_id = batch_data.get('first_chat_id')
        first_message_id = batch_data.get('first_message_id')
        
        if chat_id != first_chat_id:
            await update.message.reply_text("❌ First and last messages must be from the same channel!")
            return
        
        if message_id < first_message_id:
            await update.message.reply_text("❌ Last message ID should be greater than first message ID!")
            return
        
        # Generate batch link
        await generate_batch_links(update, context, first_chat_id, first_message_id, message_id)
        
        # Clear batch state
        context.user_data.pop('batch_state', None)
        context.user_data.pop('batch_data', None)

async def extract_chat_message_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    
    # Check if message is forwarded from a channel
    if message.forward_from_chat and message.forward_from_chat.type == 'channel':
        chat_id = message.forward_from_chat.id
        message_id = message.forward_message_id
        return chat_id, message_id
    
    # Check if message contains a text with channel link
    elif message.text and 't.me' in message.text:
        try:
            # Extract from message link format: https://t.me/channel/123
            parts = message.text.split('/')
            if len(parts) >= 2:
                channel_username = parts[-2]
                message_id = int(parts[-1])
                
                # Get channel ID from username
                try:
                    chat = await context.bot.get_chat(f"@{channel_username}")
                    return chat.id, message_id
                except:
                    return None, None
        except:
            return None, None
    
    return None, None

async def generate_batch_links(update: Update, context: ContextTypes.DEFAULT_TYPE, chat_id, first_msg_id, last_msg_id):
    try:
        settings = load_settings()
        auto_delete_time = settings.get("auto_delete_time", 10)
        
        # Create batch data
        batch_id = f"batch_{chat_id}_{first_msg_id}_{last_msg_id}"
        encoded_batch_id = encode_file_id(batch_id)
        
        # Store batch information
        links = load_links()
        links[encoded_batch_id] = {
            "type": "batch",
            "chat_id": chat_id,
            "first_message_id": first_msg_id,
            "last_message_id": last_msg_id,
            "total_messages": last_msg_id - first_msg_id + 1,
            "created_at": datetime.utcnow().isoformat(),
            "created_by": update.effective_user.id
        }
        save_links(links)
        
        # Generate batch link
        bot_username = context.bot.username
        batch_link = f"https://t.me/{bot_username}?start={encoded_batch_id}"
        
        await update.message.reply_text(
            f"✅ Batch link generated successfully!\n\n"
            f"📦 Total messages: {last_msg_id - first_msg_id + 1}\n"
            f"🔗 Batch Link: {batch_link}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔗 Copy Batch Link", url=batch_link)]
            ])
        )
        
    except Exception as e:
        print(f"Error generating batch links: {e}")
        await update.message.reply_text("❌ Error generating batch links!")

# Update start_link_handler in links.py to handle batch links
async def handle_batch_start(update: Update, context: ContextTypes.DEFAULT_TYPE, encoded_id):
    links = load_links()
    
    if encoded_id not in links:
        await update.message.reply_text("❌ Batch link expired or not found!")
        return
    
    batch_data = links[encoded_id]
    
    if batch_data.get("type") != "batch":
        return False
    
    chat_id = batch_data["chat_id"]
    first_msg_id = batch_data["first_message_id"]
    last_msg_id = batch_data["last_message_id"]
    
    settings = load_settings()
    protect_content = settings.get("protect_content", False)
    auto_delete_time = settings.get("auto_delete_time", 10)
    
    # Send all messages in batch
    warning_msg = None
    for msg_id in range(first_msg_id, last_msg_id + 1):
        try:
            forwarded_msg = await context.bot.copy_message(
                chat_id=update.effective_chat.id,
                from_chat_id=chat_id,
                message_id=msg_id,
                protect_content=protect_content
            )
            
            # Send warning message only once for the first file
            if msg_id == first_msg_id:
                warning_msg = await update.message.reply_text(
                    f"> *⚠️ ɪᴍᴘᴏʀᴛᴀɴᴛ\\:*\n\n> *ᴛʜᴇsᴇ ғɪʟᴇs ᴡɪʟʟ ʙᴇ ᴅᴇʟᴇᴛᴇᴅ ɪɴ {auto_delete_time} ᴍɪɴᴜᴛᴇs\\. ᴘʟᴇᴀsᴇ sᴀᴠᴇ ᴏʀ ғᴏʀᴡᴀʀᴅ ᴛʜᴇᴍ ᴛᴏ ʏᴏᴜʀ sᴀᴠᴇᴅ ᴍᴇssᴀɢᴇs ʙᴇғᴏʀᴇ ᴛʜᴇʏ ɢᴇᴛ ʀᴇᴍᴏᴠᴇᴅ\\.*",
                    parse_mode="MarkdownV2"
                )
                
                # Schedule deletion for all batch messages
                asyncio.create_task(
                    delete_batch_messages(
                        context, 
                        update.effective_chat.id, 
                        first_msg_id, 
                        last_msg_id,
                        warning_msg.message_id if warning_msg else None,
                        auto_delete_time,
                        encoded_id
                    )
                )
                
        except Exception as e:
            print(f"Error copying message {msg_id}: {e}")
            continue
    
    return True

async def delete_batch_messages(context, chat_id, first_msg_id, last_msg_id, warning_msg_id, delay_minutes, encoded_id):
    """Delete all batch messages after delay"""
    await asyncio.sleep(delay_minutes * 60)
    
    # Delete all messages in the range
    for msg_id in range(first_msg_id, last_msg_id + 1):
        try:
            await context.bot.delete_message(chat_id, msg_id)
        except:
            pass
    
    # Delete warning message
    if warning_msg_id:
        try:
            await context.bot.delete_message(chat_id, warning_msg_id)
        except:
            pass
    
    # Send retrieval message
    await send_batch_retrieval_message(context, chat_id, encoded_id)

async def send_batch_retrieval_message(context, chat_id, encoded_id):
    completion_text = (
        "*✅ ʏᴏᴜʀ ʙᴀᴛᴄʜ ғɪʟᴇs ʜᴀᴠᴇ ʙᴇᴇɴ sᴜᴄᴄᴇssғᴜʟʟʏ ᴅᴇʟᴇᴛᴇᴅ\\!*\n\n"
        "> *ɪғ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ ʀᴇᴛʀɪᴇᴠᴇ ᴛʜᴇᴍ ᴀɢᴀɪɴ, ᴄʟɪᴄᴋ ᴛʜᴇ \"♻️ ᴄʟɪᴄᴋ ʜᴇʀᴇ\" ʙᴜᴛᴛᴏɴ\\. ɪғ ɴᴏᴛ, sɪᴍᴘʟʏ ᴄʟᴏsᴇ ᴛʜɪs ᴍᴇssᴀɢᴇ\\.*"
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
        
        asyncio.create_task(
            delete_retrieval_message(context, chat_id, retrieval_msg.message_id, 10)
        )
    except Exception as e:
        print(f"Error sending batch retrieval message: {e}")

async def delete_retrieval_message(context, chat_id, message_id, delay_minutes):
    """Delete retrieval message after delay"""
    await asyncio.sleep(delay_minutes * 60)
    try:
        await context.bot.delete_message(chat_id, message_id)
    except:
        pass
