import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters

# Load admin data
def load_admins():
    try:
        with open('admins.json', 'r') as f:
            return json.load(f)
    except:
        return [5373577888]

# Load force sub channels
def load_force_sub():
    try:
        with open('force_sub.json', 'r') as f:
            return json.load(f)
    except:
        return []

# Save force sub channels
def save_force_sub(channels):
    with open('force_sub.json', 'w') as f:
        json.dump(channels, f, indent=4)

async def force_sub_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    admins = load_admins()
    
    # Check if user is admin or owner
    if user_id not in admins and user_id != 5373577888:
        await update.message.reply_text("You are not authorized to use this command!")
        return
    
    keyboard = [
        [InlineKeyboardButton("➕ Add Channel", callback_data="fsub_add_channel")],
        [InlineKeyboardButton("❌ Close", callback_data="fsub_close")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    channels = load_force_sub()
    if channels:
        channels_text = "\n".join([f"• {channel['title']} (ID: {channel['id']})" for channel in channels])
        text = f"📢 **Force Subscribe Channels**\n\n{channels_text}\n\nChoose an option:"
    else:
        text = "📢 **Force Subscribe Channels**\n\nNo channels added yet.\n\nChoose an option:"
    
    await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")

async def force_sub_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    user_id = query.from_user.id
    admins = load_admins()
    
    # Check if user is admin or owner
    if user_id not in admins and user_id != 5373577888:
        await query.answer("You are not authorized!", show_alert=True)
        return
    
    if data == "fsub_add_channel":
        await query.edit_message_text(
            "📢 **Add Force Subscribe Channel**\n\n"
            "ɴᴏᴡ ғᴏʀᴡᴀʀᴅ ᴀ ᴍᴇssᴀɢᴇ ғʀᴏᴍ ʏᴏᴜʀ ᴄʜᴀɴɴᴇʟ ᴀɴᴅ ᴍᴀᴋᴇ sᴜʀᴇ ᴛʜᴀᴛ ᴛʜᴇ ʙᴏᴛ ɪs ᴀᴅᴍɪɴ ɪɴ ᴛʜᴀᴛ ᴄʜᴀɴɴᴇʟ.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back", callback_data="fsub_back"), InlineKeyboardButton("❌ Close", callback_data="fsub_close")]
            ]),
            parse_mode="Markdown"
        )
        context.user_data['waiting_for_channel'] = True
        
    elif data == "fsub_back":
        await force_sub_handler(update, context)
        
    elif data == "fsub_close":
        await query.message.delete()

async def forwarded_channel_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    admins = load_admins()
    
    # Check if user is admin or owner
    if user_id not in admins and user_id != 5373577888:
        return
    
    if not context.user_data.get('waiting_for_channel'):
        return
    
    message = update.message
    
    if not message or not message.forward_origin:
        await message.reply_text("⚠️ This message is not forwarded from a channel!")
        return

    origin = message.forward_origin

    # If forwarded from a channel
    if origin.type == "channel":
        channel_id = origin.chat.id
        channel_title = origin.chat.title
        
        # Check if bot is admin in the channel
        try:
            chat_member = await context.bot.get_chat_member(channel_id, context.bot.id)
            if chat_member.status not in ['administrator', 'creator']:
                await message.reply_text("❌ Bot is not admin in this channel! Please make bot admin first.")
                return
        except Exception as e:
            await message.reply_text("❌ Cannot verify bot admin status in this channel!")
            return
        
        # Add channel to force sub list
        channels = load_force_sub()
        
        # Check if channel already exists
        if any(channel['id'] == channel_id for channel in channels):
            await message.reply_text("❌ This channel is already in force subscribe list!")
            return
        
        channels.append({
            "id": channel_id,
            "title": channel_title,
            "username": origin.chat.username,
            "added_by": user_id,
            "added_at": json.dumps({"$date": {"$numberLong": str(int(message.date.timestamp() * 1000))}})
        })
        
        save_force_sub(channels)
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("➕ Add Channel", callback_data="fsub_add_channel")],
            [InlineKeyboardButton("🔙 Back", callback_data="fsub_back"), InlineKeyboardButton("❌ Close", callback_data="fsub_close")]
        ])
        
        await message.reply_text(
            f"✅ Successfully added **{channel_title}** as force subscribe channel!",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        
        # Clear waiting state
        context.user_data.pop('waiting_for_channel', None)

    else:
        await message.reply_text("⚠️ This forwarded message is not from a channel.")

# Force subscription check function (to be used in links.py)
async def check_force_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int):
    channels = load_force_sub()
    
    if not channels:
        return True  # No force sub required
    
    unsubscribed_channels = []
    
    for channel in channels:
        channel_id = channel['id']
        try:
            chat_member = await context.bot.get_chat_member(channel_id, user_id)
            if chat_member.status in ['left', 'kicked']:
                unsubscribed_channels.append(channel)
        except Exception as e:
            print(f"Error checking subscription for channel {channel_id}: {e}")
            unsubscribed_channels.append(channel)
    
    if unsubscribed_channels:
        # Send force sub message
        await send_force_sub_message(update, context, unsubscribed_channels)
        return False
    
    return True

async def send_force_sub_message(update: Update, context: ContextTypes.DEFAULT_TYPE, channels):
    settings = load_settings()
    force_sub_image = settings.get("force_sub_image", "")
    
    channels_text = "\n".join([f"• {channel['title']}" for channel in channels])
    
    text = (
        "🔒 **Join Required Channels**\n\n"
        "ʏᴏᴜ ᴍᴜsᴛ ᴊᴏɪɴ ᴛʜᴇ ғᴏʟʟᴏᴡɪɴɢ ᴄʜᴀɴɴᴇʟ(s) ᴛᴏ ᴀᴄᴄᴇss ᴛʜᴇ ғɪʟᴇs:\n\n"
        f"{channels_text}\n\n"
        "ᴀғᴛᴇʀ ᴊᴏɪɴɪɴɢ, ᴄʟɪᴄᴋ ᴛʜᴇ \"🔄 ᴛʀʏ ᴀɢᴀɪɴ\" ʙᴜᴛᴛᴏɴ."
    )
    
    buttons = []
    for channel in channels:
        if channel.get('username'):
            channel_url = f"https://t.me/{channel['username']}"
        else:
            channel_url = f"https://t.me/c/{str(channel['id'])[4:]}"
        
        buttons.append([InlineKeyboardButton(f"📢 {channel['title']}", url=channel_url)])
    
    buttons.append([InlineKeyboardButton("🔄 Try Again", callback_data="fsub_try_again")])
    
    keyboard = InlineKeyboardMarkup(buttons)
    
    if force_sub_image and os.path.exists(force_sub_image):
        try:
            with open(force_sub_image, 'rb') as photo:
                await context.bot.send_photo(
                    chat_id=update.effective_chat.id,
                    photo=photo,
                    caption=text,
                    reply_markup=keyboard,
                    parse_mode="Markdown"
                )
        except:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=text,
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
    else:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=text,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )

async def force_sub_try_again_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    # Check subscription again
    channels = load_force_sub()
    unsubscribed_channels = []
    
    for channel in channels:
        channel_id = channel['id']
        try:
            chat_member = await context.bot.get_chat_member(channel_id, user_id)
            if chat_member.status in ['left', 'kicked']:
                unsubscribed_channels.append(channel)
        except:
            unsubscribed_channels.append(channel)
    
    if unsubscribed_channels:
        await query.answer("❌ You haven't joined all channels yet!", show_alert=True)
        # Update the message to show remaining channels
        await send_force_sub_message(update, context, unsubscribed_channels)
        await query.message.delete()
    else:
        await query.answer("✅ All channels joined! Processing your request...", show_alert=True)
        await query.message.delete()
        # Continue with the original file sending process
        # This will be handled in the main start_link_handler
