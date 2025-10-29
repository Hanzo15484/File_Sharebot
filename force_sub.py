# force_sub.py
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters

# Import shared functions
from shared_functions import load_admins, load_settings, load_force_sub, save_force_sub

async def force_sub_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    admins = load_admins()
    
    # Check if user is admin or owner
    if user_id not in admins and user_id != 5373577888:
        await update.message.reply_text("You are not authorized to use this command!")
        return
    
    channels = load_force_sub()
    
    keyboard = []
    if channels:
        # Add delete buttons for each channel
        for channel in channels:
            keyboard.append([
                InlineKeyboardButton(f"🗑️ {channel['title']}", callback_data=f"fsub_delete_{channel['id']}")
            ])
    
    # Always show Add Channel and Close buttons
    keyboard.append([InlineKeyboardButton("➕ Add Channel", callback_data="fsub_add_channel")])
    keyboard.append([InlineKeyboardButton("❌ Close", callback_data="fsub_close")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if channels:
        channels_text = "\n".join([f"• {channel['title']} (ID: {channel['id']})" for channel in channels])
        text = f"📢 **Force Subscribe Channels**\n\n{channels_text}\n\nSelect a channel to delete or add new:"
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
        
    elif data.startswith("fsub_delete_"):
        channel_id = int(data.split("_")[2])
        channels = load_force_sub()
        
        # Find and remove the channel
        channel_to_delete = None
        for channel in channels:
            if channel['id'] == channel_id:
                channel_to_delete = channel
                break
        
        if channel_to_delete:
            channels = [ch for ch in channels if ch['id'] != channel_id]
            save_force_sub(channels)
            await query.answer(f"✅ {channel_to_delete['title']} removed from force subscribe!", show_alert=True)
            await force_sub_handler(update, context)
        else:
            await query.answer("❌ Channel not found!", show_alert=True)
        
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
    
    # Only process if we're specifically waiting for channel in force sub
    if not context.user_data.get('waiting_for_channel'):
        return  # Let batch handler process this forwarded message
    
    message = update.message
    
    if not message or not message.forward_origin:
        await message.reply_text("⚠️ This message is not forwarded from a channel!")
        return

    origin = message.forward_origin

    # If forwarded from a channel
    if origin.type == "channel":
        channel_id = origin.chat.id
        channel_title = origin.chat.title

        try:
            chat = await context.bot.get_chat(channel_id)
            invite_link = getattr(chat, "invite_link", None)
            if not invite_link:
                try:
                    new_invite = await context.bot.create_chat_invite_link(
                        chat_id=channel_id,
                        name=f"Permanet link_{channel_title}",
                        creates_join_request=False
                    )
                    invite_link=new_invite.invite_link
                except Exception as e:
                  print(f"error fetching invite link {channel_title}, {e}:")
        except Except as e:
            print(f"error in creating new link {e}:")
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
            "invite_link": invite_link,
            "username": origin.chat.username,
            "added_by": user_id
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

# Force subscription check function
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
row = []

for index, channel in enumerate(channels[:4], start=1):
    channel_url = (
        channel.get("invite_link")
        or (f"https://t.me/{channel['username']}" if channel.get("username") else f"https://t.me/c/{str(channel['id'])[4:]}")
    )

    # ✅ Add button to current row
    row.append(InlineKeyboardButton(f"📢 {channel['title']}", url=channel_url))

    # ✅ Every 2 buttons → start a new row
    if index % 2 == 0:
        buttons.append(row)
        row = []

# ✅ Add last row if odd number of channels
if row:
    buttons.append(row)

# ✅ Add Try Again button
buttons.append([InlineKeyboardButton("🔄 ᴛʀʏ ᴀɢᴀɪɴ", callback_data="fsub_try_again")])

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
        return  # prevent duplicate message sending
    except Exception as e:
        print(f"Error sending force_sub image: {e}")
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
        await send_force_sub_message(update, context, unsubscribed_channels)
        await query.message.delete()
    else:
        await query.answer("✅ All channels joined! Processing your request...", show_alert=False)
        await query.message.delete()
        
        # Get the original start link and process it
        if 'original_encoded_id' in context.user_data:
            encoded_id = context.user_data['original_encoded_id']
            # Import and call the function to process the link
            from links import process_link_after_force_sub
            await process_link_after_force_sub(update, context, encoded_id)
