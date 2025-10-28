# batch_link.py
import asyncio
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters

# Import shared functions
from shared_functions import load_admins, load_settings, load_links, save_links, encode_file_id, decode_file_id

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
    
    # Check if we're in force sub mode first (priority to force sub)
    if context.user_data.get('waiting_for_channel'):
        return  # Let force_sub handle this message
    
    batch_state = context.user_data.get('batch_state')
    
    if not batch_state:
        return  # Not in batch mode
    
    message = update.message
    
    if batch_state == 'waiting_first_message':
        # Get chat ID and message ID from forwarded message or message link
        chat_id, message_id, channel_title = await extract_chat_message_info(update, context)
        
        if not chat_id or not message_id:
            await update.message.reply_text("❌ Could not extract message information. Please forward a message from a channel or send a channel message link.")
            return
        
        # Check if bot is admin in the channel
        is_admin = await check_bot_admin(context, chat_id)
        if not is_admin:
            await update.message.reply_text("❌ Bot is not admin in this channel! Please make bot admin first.")
            return
        
        context.user_data['batch_data'] = {
            'first_chat_id': chat_id,
            'first_message_id': message_id,
            'channel_title': channel_title
        }
        context.user_data['batch_state'] = 'waiting_last_message'
        
        await update.message.reply_text(
            f"📌 ɢʀᴇᴀᴛ! ɴᴏᴡ ғᴏʀᴡᴀʀᴅ ᴛʜᴇ ʟᴀsᴛ ᴍᴇssᴀɢᴇ ғʀᴏᴍ **{channel_title}** (ᴡɪᴛʜ ғᴏʀᴡᴀʀᴅ ᴛᴀɢ)\n"
            "ᴏʀ sʜᴀʀᴇ ᴛʜᴇ ʟɪɴᴋ ᴏғ ᴛʜᴇ ʟᴀsᴛ ᴍᴇssᴀɢᴇ ғʀᴏᴍ ʏᴏᴜʀ ʙᴀᴛᴄʜ ᴄʜᴀɴɴᴇʟ.",
            parse_mode="Markdown"
        )
    
    elif batch_state == 'waiting_last_message':
        # Get chat ID and message ID from forwarded message or message link
        chat_id, message_id, channel_title = await extract_chat_message_info(update, context)
        
        if not chat_id or not message_id:
            await update.message.reply_text("❌ Could not extract message information. Please forward a message from a channel or send a channel message link.")
            return
        
        batch_data = context.user_data.get('batch_data', {})
        first_chat_id = batch_data.get('first_chat_id')
        first_message_id = batch_data.get('first_message_id')
        first_channel_title = batch_data.get('channel_title')
        
        if chat_id != first_chat_id:
            await update.message.reply_text("❌ First and last messages must be from the same channel!")
            return
        
        if message_id < first_message_id:
            await update.message.reply_text("❌ Last message ID should be greater than first message ID!")
            return
        
        # Check if bot is admin in the channel
        is_admin = await check_bot_admin(context, chat_id)
        if not is_admin:
            await update.message.reply_text("❌ Bot is not admin in this channel! Please make bot admin first.")
            return
        
        # Generate batch link
        await generate_batch_links(update, context, first_chat_id, first_message_id, message_id, first_channel_title)
        
        # Clear batch state
        context.user_data.pop('batch_state', None)
        context.user_data.pop('batch_data', None)

async def extract_chat_message_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    
    # Check if message is forwarded from a channel using forward_origin
    if hasattr(message, 'forward_origin') and message.forward_origin:
        origin = message.forward_origin
        if origin.type == "channel":
            chat_id = origin.chat.id
            message_id = message.forward_from_message_id
            channel_title = origin.chat.title
            print(f"📨 Forwarded from channel: {channel_title}, Chat ID: {chat_id}, Message ID: {message_id}")
            return chat_id, message_id, channel_title
    
    # Check if message contains a text with channel link
    elif message.text and 't.me' in message.text:
        try:
            # Extract from message link format: https://t.me/channel/123 or https://t.me/c/1234567890/123
            if '/c/' in message.text:
                # Private channel link format: https://t.me/c/1234567890/123
                parts = message.text.split('/')
                chat_id = int(parts[-2])
                message_id = int(parts[-1])
                # Get channel info
                try:
                    chat = await context.bot.get_chat(chat_id)
                    return chat.id, message_id, chat.title
                except Exception as e:
                    print(f"Error getting chat from ID: {e}")
                    return None, None, None
            else:
                # Public channel link format: https://t.me/channel_username/123
                parts = message.text.split('/')
                if len(parts) >= 2:
                    channel_username = parts[-2]
                    message_id = int(parts[-1])
                    
                    # Get channel ID from username
                    try:
                        chat = await context.bot.get_chat(f"@{channel_username}")
                        return chat.id, message_id, chat.title
                    except Exception as e:
                        print(f"Error getting chat from username: {e}")
                        return None, None, None
        except Exception as e:
            print(f"Error parsing message link: {e}")
            return None, None, None
    
    print("❌ Could not extract chat and message ID")
    return None, None, None

async def check_bot_admin(context, chat_id):
    """Check if bot is admin in the channel"""
    try:
        chat_member = await context.bot.get_chat_member(chat_id, context.bot.id)
        if chat_member.status in ['administrator', 'creator']:
            print(f"✅ Bot is admin in channel {chat_id}")
            return True
        else:
            print(f"❌ Bot is NOT admin in channel {chat_id}")
            return False
    except Exception as e:
        print(f"Error checking bot admin status: {e}")
        return False

async def generate_batch_links(update: Update, context: ContextTypes.DEFAULT_TYPE, chat_id, first_msg_id, last_msg_id, channel_title):
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
            "channel_title": channel_title,
            "created_at": datetime.utcnow().isoformat(),
            "created_by": update.effective_user.id
        }
        save_links(links)
        
        # Generate batch link
        bot_username = context.bot.username
        batch_link = f"https://t.me/{bot_username}?start={encoded_batch_id}"
        
        await update.message.reply_text(
            f"✅ **Batch Link Generated Successfully!**\n\n"
            f"📦 **Channel:** {channel_title}\n"
            f"📊 **Total Messages:** {last_msg_id - first_msg_id + 1}\n"
            f"🔢 **Range:** {first_msg_id} - {last_msg_id}\n"
            f"🔗 **Batch Link:** `{batch_link}`",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔗 Copy Batch Link", url=batch_link)],
                [InlineKeyboardButton("📋 Copy as Text", callback_data=f"copy_batch_{encoded_batch_id}")]
            ]),
            parse_mode="Markdown"
        )
        
    except Exception as e:
        print(f"Error generating batch links: {e}")
        await update.message.reply_text("❌ Error generating batch links!")

async def batch_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data.startswith("copy_batch_"):
        encoded_id = data.split("_")[2]
        links = load_links()
        
        if encoded_id in links:
            bot_username = context.bot.username
            batch_link = f"https://t.me/{bot_username}?start={encoded_id}"
            
            await query.answer("Batch link copied to clipboard!", show_alert=True)
            await query.message.reply_text(f"🔗 **Batch Link:**\n`{batch_link}`", parse_mode="Markdown")

async def handle_batch_start(update: Update, context: ContextTypes.DEFAULT_TYPE, encoded_id):
    links = load_links()
    
    if encoded_id not in links:
        await update.message.reply_text("❌ Batch link expired or not found!")
        return False
    
    batch_data = links[encoded_id]
    
    if batch_data.get("type") != "batch":
        return False
    
    chat_id = batch_data["chat_id"]
    first_msg_id = batch_data["first_message_id"]
    last_msg_id = batch_data["last_message_id"]
    channel_title = batch_data.get("channel_title", "Unknown Channel")
    
    settings = load_settings()
    protect_content = settings.get("protect_content", False)
    auto_delete_time = settings.get("auto_delete_time", 10)
    
    # Send all messages in batch
    warning_msg = None
    sent_messages = []  # Store message IDs of sent files
    success_count = 0
    
    await update.message.reply_text(f"📦 **Processing Batch Files...**\n\n🔄 Sending {last_msg_id - first_msg_id + 1} files from {channel_title}")

    for msg_id in range(first_msg_id, last_msg_id + 1):
        try:
            forwarded_msg = await context.bot.copy_message(
                chat_id=update.effective_chat.id,
                from_chat_id=chat_id,
                message_id=msg_id,
                protect_content=protect_content
            )
            sent_messages.append(forwarded_msg.message_id)
            success_count += 1
            
            # Send warning message only once for the first file
            if msg_id == first_msg_id and not warning_msg:
                warning_msg = await update.message.reply_text(
                    f"> *⚠️ ɪᴍᴘᴏʀᴛᴀɴᴛ\\:*\n\n> *ᴛʜᴇsᴇ ғɪʟᴇs ᴡɪʟʟ ʙᴇ ᴅᴇʟᴇᴛᴇᴅ ɪɴ {auto_delete_time} ᴍɪɴᴜᴛᴇs\\. ᴘʟᴇᴀsᴇ sᴀᴠᴇ ᴏʀ ғᴏʀᴡᴀʀᴅ ᴛʜᴇᴍ ᴛᴏ ʏᴏᴜʀ sᴀᴠᴇᴅ ᴍᴇssᴀɢᴇs ʙᴇғᴏʀᴇ ᴛʜᴇʏ ɢᴇᴛ ʀᴇᴍᴏᴠᴇᴅ\\.*",
                    parse_mode="MarkdownV2"
                )
                
                # Schedule deletion for all batch messages
                asyncio.create_task(
                    delete_batch_messages(
                        context, 
                        update.effective_chat.id, 
                        sent_messages,
                        warning_msg.message_id if warning_msg else None,
                        auto_delete_time,
                        encoded_id
                    )
                )
                
        except Exception as e:
            print(f"Error copying message {msg_id}: {e}")
            continue
    
    # Send completion summary
    if success_count > 0:
        await update.message.reply_text(f"✅ **Batch Complete!**\n\n📊 Successfully sent {success_count} files out of {last_msg_id - first_msg_id + 1} total files.")
    else:
        await update.message.reply_text("❌ No files could be sent from this batch!")
    
    return True

async def delete_batch_messages(context, chat_id, sent_message_ids, warning_msg_id, delay_minutes, encoded_id):
    """Delete all batch messages after delay"""
    print(f"🕒 Batch deletion scheduled for {delay_minutes} minutes from now")
    
    # Wait for the specified time
    await asyncio.sleep(delay_minutes * 60)
    
    print(f"🗑️ Deleting {len(sent_message_ids)} batch messages...")
    
    # Delete all sent file messages
    deleted_count = 0
    for msg_id in sent_message_ids:
        try:
            await context.bot.delete_message(chat_id, msg_id)
            deleted_count += 1
            print(f"✅ Deleted file message {msg_id}")
        except Exception as e:
            print(f"❌ Error deleting file message {msg_id}: {e}")
    
    # Delete warning message
    if warning_msg_id:
        try:
            await context.bot.delete_message(chat_id, warning_msg_id)
            print(f"✅ Deleted warning message {warning_msg_id}")
        except Exception as e:
            print(f"❌ Error deleting warning message {warning_msg_id}: {e}")
    
    print(f"✅ Batch deletion completed. Deleted {deleted_count} files.")
    
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

async def batch_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data.startswith("copy_batch_"):
        encoded_id = data.split("_")[2]
        links = load_links()
        
        if encoded_id in links:
            bot_username = context.bot.username
            batch_link = f"https://t.me/{bot_username}?start={encoded_id}"
            
            await query.answer("Batch link copied to clipboard!", show_alert=True)
            # You can also send the link as a message
            await query.message.reply_text(f"🔗 **Batch Link:**\n`{batch_link}`", parse_mode="Markdown")
