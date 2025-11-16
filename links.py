import os
import json
import base64
import asyncio
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler
from batch_link import handle_batch_start
from force_sub import check_force_subscription
from middleware import check_ban_and_register
from shortened import load_shortener, shorten_url
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
        
@check_ban_and_register
async def genlink_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    admins = load_admins()

    # Only admin can use command
    if user_id not in admins and user_id != 5373577888:
        await update.message.reply_text("You are not authorized!")
        return

    # Set waiting mode
    context.user_data["waiting_for_genlink"] = True
    context.user_data["stop_timer"] = False

    # Send initial message
    sent = await update.message.reply_text(
         f"> ᴘʟᴇᴀsᴇ sᴇɴᴅ ᴏʀ ғᴏʀᴡᴀʀᴅ ᴀ ᴍᴇssᴀɢᴇ ᴛᴏ ɢᴇɴᴇʀᴀᴛᴇ ᴀ ʟɪɴᴋ\\.\n"
         f"ᴛɪᴍᴇᴏᴜᴛ\\: 60s ʀᴇᴍᴀɪɴɪɴɢ",
        parse_mode="MarkdownV2"
     )

    # Save message for editing
    context.user_data["genlink_wait_msg"] = sent

    # Start countdown
    context.user_data["timer_task"] = asyncio.create_task(
        genlink_countdown(context)
        )

async def genlink_countdown(context):
    msg = context.user_data.get("genlink_wait_msg")

    for seconds in range(60, 0, -1):

        # Stop instantly if user sends message
        if context.user_data.get("stop_timer"):
            return

        text = (
            f"> ᴘʟᴇᴀsᴇ sᴇɴᴅ ᴏʀ ғᴏʀᴡᴀʀᴅ ᴀ ᴍᴇssᴀɢᴇ ᴛᴏ ɢᴇɴᴇʀᴀᴛᴇ ᴀ ʟɪɴᴋ\\.\n"
            f"ᴛɪᴍᴇᴏᴜᴛ\\: {seconds}s ʀᴇᴍᴀɪɴɪɴɢ"
        )

        try:
            await msg.edit_text(text, parse_mode="MarkdownV2")
        except:
            pass

        await asyncio.sleep(1)

    # Timer finished → timeout
    context.user_data["waiting_for_genlink"] = False

    timeout_text = (
        "ᴛɪᴍᴇᴏᴜᴛ ❌"
        "ᴘʟᴇᴀsᴇ ᴜsᴇ /genlink ᴀɢᴀɪɴ\\."
    )

    try:
        await msg.edit_text(timeout_text, parse_mode="MarkdownV2")
    except:
        pass

@check_ban_and_register
async def genlink_next_message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    # If not in genlink waiting mode → ignore
    if not context.user_data.get("waiting_for_genlink"):
        return

    # Stop waiting + stop countdown
    context.user_data["waiting_for_genlink"] = False
    context.user_data["stop_timer"] = True

    timer = context.user_data.get("timer_task")
    if timer:
        timer.cancel()

    # Update waiting message to show progress
    wait_msg = context.user_data.get("genlink_wait_msg")
    try:
        await wait_msg.edit_text("✅ Generating your link…")
    except:
        pass

    msg = update.message
    user_id = update.effective_user.id

    # Create encoded ID
    file_id = f"{msg.chat_id}:{msg.message_id}"
    encoded_id = encode_file_id(file_id)
    bot_username = context.bot.username
    link = f"https://t.me/{bot_username}?start={encoded_id}"

    # Save link
    links = load_links()
    links[encoded_id] = {
        "chat_id": msg.chat_id,
        "message_id": msg.message_id,
        "created_at": datetime.utcnow().isoformat(),
        "created_by": user_id
    }
    save_links(links)

    # Show generated link
    share_url = f"https://telegram.me/share/url?url={link}"

    await wait_msg.edit_text(
     f"🔗 *ʏᴏᴜʀ ᴜʀʟ*\n`{link}`",
     parse_mode="Markdown",
     reply_markup=InlineKeyboardMarkup([

        # Row 1 → Your URL + Share URL
        [
            InlineKeyboardButton("🔗 ʏᴏᴜʀ ᴜʀʟ", url=link),
            InlineKeyboardButton("🔁 sʜᴀʀᴇ ᴜʀʟ", url=share_url),
        ],

        # Row 2 → Copy button
        [
            InlineKeyboardButton("⎙ Copy", callback_data=f"copy_original_{encoded_id}")
        ]
    ])
)
    
@check_ban_and_register
async def start_link_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    args = context.args
    
    if not args:
        # Regular start command
        await regular_start_handler(update, context)
        return
    
    encoded_id = args[0]

    context.user_data['original_encoded_id'] = encoded_id
    # Check force subscription first
    is_subscribed = await check_force_subscription(update, context, user_id)
    
    if not is_subscribed:
        return  # Force sub message already sent

    await process_link_after_force_sub(update, context, encoded_id)
    
async def process_link_after_force_sub(update: Update, context: ContextTypes.DEFAULT_TYPE, encoded_id):
    """Process the link after user passes force subscription check"""
    user_id = update.effective_user.id
    
    # Check if it's a batch link
    is_batch = await handle_batch_start(update, context, encoded_id)
    
    if is_batch:
        return  # Batch link handled
        
    file_id = decode_file_id(encoded_id)
    
    if not file_id:
        await update.message.reply_text("❌ Invalid link!")
        return

        # Check if it's a batch link
    is_batch = await handle_batch_start(update, context, encoded_id)
    
    if is_batch:
        return  # Batch link handled
    
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
        warning_msg = await update.message.reply_text(f"> *⚠️ ɪᴍᴘᴏʀᴛᴀɴᴛ\\:*\n\n> *ᴛʜɪs ғɪʟᴇ ᴡɪʟʟ ʙᴇ ᴅᴇʟᴇᴛᴇᴅ ɪɴ {auto_delete_time} ᴍɪɴᴜᴛᴇs\\. ᴘʟᴇᴀsᴇ sᴀᴠᴇ ᴏʀ ғᴏʀᴡᴀʀᴅ ɪᴛ ᴛᴏ ʏᴏᴜʀ sᴀᴠᴇᴅ ᴍᴇssᴀɢᴇs ʙᴇғᴏʀᴇ ɪᴛ ɢᴇᴛs ʀᴇᴍᴏᴠᴇᴅ\\.*",
        parse_mode = "MarkdownV2")
        # Schedule deletion without sending warning message first
        asyncio.create_task(
            delete_and_notify(
                context, 
                update.effective_chat.id, 
                forwarded_msg.message_id,
                warning_msg.message_id,
                auto_delete_time,
                encoded_id
            )
        )
        
    except Exception as e:
        await update.message.reply_text("❌ Error retrieving file. It may have been deleted.")

async def delete_and_notify(context, chat_id, file_msg_id, warning_msg_id, delay_minutes, encoded_id):
    """Delete file after delay and send retrieval message"""
    
    # Wait for the specified time
    await asyncio.sleep(delay_minutes * 60)
    
    try:
        # Delete the file message
        await context.bot.delete_message(chat_id, file_msg_id)
    except Exception as e:
        print(f"Error deleting file message: {e}")
        
    try:
        await context.bot.delete_message(chat_id, warning_msg_id)
    except Exception as e:
        print(f"Error deleting warning message: {e}")
        
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
        
    except Exception as e:
        print(f"Error sending retrieval message: {e}")
        
async def link_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data == "link_close":
        await query.message.delete()
    
    # Add this new condition for copying original links
    elif data.startswith("copy_original_"):
      encoded_id = data.replace("copy_original_", "")
      bot_username = context.bot.username
      original_link = f"https://t.me/{bot_username}?start={encoded_id}"
      await query.answer("Link copied to clipboard!", show_alert=False)
      await query.message.reply_text(
        f"🔗 **Your Link:**\n`{original_link}`",
        parse_mode="Markdown"
    )

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
