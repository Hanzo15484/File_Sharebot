# broadcast.py
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler
from datetime import datetime

from shared_functions import load_users, load_admins
from middleware import check_ban_and_register

# Global variable to track broadcast status
broadcast_status = {
    'is_running': False,
    'current_index': 0,
    'total_users': 0,
    'success_count': 0,
    'failed_count': 0,
    'start_time': None,
    'message': None,
    'task': None
}

@check_ban_and_register
async def broadcast_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    # Check if user is owner (only owner can broadcast)
    if user_id != 5373577888:
        await update.message.reply_text("❌ This command is only available for the bot owner!")
        return
    
    # Check if broadcast is already running
    if broadcast_status['is_running']:
        await update.message.reply_text(
            "⚠️ **Broadcast is already in progress!**\n\n"
            "Please wait for the current broadcast to complete or cancel it first.",
            parse_mode="Markdown"
        )
        return
    
    # Check if message is replied
    if not update.message.reply_to_message:
        await update.message.reply_text(
            "❌ **Usage:** /broadcast (reply to a message)\n\n"
            "Please reply to the message you want to broadcast.",
            parse_mode="Markdown"
        )
        return
    
    users = load_users()
    total_users = len(users)
    
    if total_users == 0:
        await update.message.reply_text("❌ No users found in the database!")
        return
    
    # Store the message to broadcast
    broadcast_status.update({
        'is_running': True,
        'current_index': 0,
        'total_users': total_users,
        'success_count': 0,
        'failed_count': 0,
        'start_time': datetime.utcnow(),
        'message': update.message.reply_to_message,
        'task': None
    })
    
    # Send initial broadcast confirmation
    confirmation_msg = await update.message.reply_text(
        f"📢 **Broadcast Started**\n\n"
        f"📊 **Total Users:** `{total_users}`\n"
        f"⏰ **Started:** `{broadcast_status['start_time'].strftime('%Y-%m-%d %H:%M:%S')}`\n\n"
        f"🔄 **Preparing to send...**\n"
        f"📤 **Progress:** `0%` (0/{total_users})\n"
        f"✅ **Successful:** `0`\n"
        f"❌ **Failed:** `0`",
        reply_markup=InlineKeyboardMarkup([
                [
                 InlineKeyboardButton("⚠︎ ᴄᴀɴᴄᴇʟ", callback_data="broadcast_cancel"),
                 InlineKeyboardButton("✖ ᴄʟᴏsᴇ", callback_data="broadcast_close")
                ]
            ]),
        parse_mode="Markdown"
    )
    
    # Start the broadcast task
    broadcast_status['task'] = asyncio.create_task(
        send_broadcast_messages(context, confirmation_msg.message_id, update.effective_chat.id)
    )

async def send_broadcast_messages(context, status_message_id, chat_id):
    """Send broadcast messages to all users with progress updates"""
    users = load_users()
    
    for index, user in enumerate(users):
        # Check if broadcast was cancelled
        if not broadcast_status['is_running']:
            break
        
        user_id = user['id']
        broadcast_status['current_index'] = index + 1
        
        try:
            # Forward the message to user
            await context.bot.copy_message(
                chat_id=user_id,
                from_chat_id=broadcast_status['message'].chat_id,
                message_id=broadcast_status['message'].message_id
            )
            broadcast_status['success_count'] += 1
            
        except Exception as e:
            print(f"Failed to send to user {user_id}: {e}")
            broadcast_status['failed_count'] += 1
        
        # Update progress every 10 messages or for the last message
        if (index + 1) % 10 == 0 or (index + 1) == len(users):
            await update_broadcast_progress(context, status_message_id, chat_id)
        
        # Small delay to avoid hitting rate limits
        await asyncio.sleep(0.1)
    
    # Broadcast completed
    await finalize_broadcast(context, status_message_id, chat_id)

async def update_broadcast_progress(context, status_message_id, chat_id):
    """Update the broadcast progress message"""
    if not broadcast_status['is_running']:
        return
    
    current = broadcast_status['current_index']
    total = broadcast_status['total_users']
    success = broadcast_status['success_count']
    failed = broadcast_status['failed_count']
    percentage = (current / total) * 100 if total > 0 else 0
    
    # Calculate ETA
    if current > 0:
        elapsed_time = (datetime.utcnow() - broadcast_status['start_time']).total_seconds()
        time_per_user = elapsed_time / current
        remaining_users = total - current
        eta_seconds = remaining_users * time_per_user
        eta_str = f"{int(eta_seconds // 60)}m {int(eta_seconds % 60)}s"
    else:
        eta_str = "Calculating..."
    
    # Create progress bar
    progress_bar_length = 20
    filled_length = int(progress_bar_length * current // total)
    progress_bar = "█" * filled_length + "░" * (progress_bar_length - filled_length)
    
    status_text = (
        f"📢 **Broadcast in Progress**\n\n"
        f"📊 **Total Users:** `{total}`\n"
        f"⏰ **Started:** `{broadcast_status['start_time'].strftime('%H:%M:%S')}`\n"
        f"⏱️ **ETA:** `{eta_str}`\n\n"
        f"`[{progress_bar}]`\n"
        f"📤 **Progress:** `{percentage:.1f}%` ({current}/{total})\n"
        f"✅ **Successful:** `{success}`\n"
        f"❌ **Failed:** `{failed}`\n"
        f"⏳ **Remaining:** `{total - current}`"
    )
    
    try:
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=status_message_id,
            text=status_text,
            reply_markup=InlineKeyboardMarkup([
                [
                 InlineKeyboardButton("⚠︎ ᴄᴀɴᴄᴇʟ", callback_data="broadcast_cancel"),
                 InlineKeyboardButton("✖ ᴄʟᴏsᴇ", callback_data="broadcast_close")
                ]
            ]),
            parse_mode="Markdown"
        )
    except Exception as e:
        print(f"Error updating progress: {e}")

async def finalize_broadcast(context, status_message_id, chat_id):
    """Send final broadcast summary"""
    total = broadcast_status['total_users']
    success = broadcast_status['success_count']
    failed = broadcast_status['failed_count']
    percentage = (success / total) * 100 if total > 0 else 0
    
    end_time = datetime.utcnow()
    duration = end_time - broadcast_status['start_time']
    duration_str = f"{int(duration.total_seconds() // 60)}m {int(duration.total_seconds() % 60)}s"
    
    if broadcast_status['is_running']:
        status = "✅ **Broadcast Completed**"
    else:
        status = "🚫 **Broadcast Cancelled**"
    
    summary_text = (
        f"{status}\n\n"
        f"📊 **Total Users:** `{total}`\n"
        f"⏰ **Duration:** `{duration_str}`\n"
        f"📈 **Success Rate:** `{percentage:.1f}%`\n\n"
        f"✅ **Successful:** `{success}`\n"
        f"❌ **Failed:** `{failed}`\n"
        f"📤 **Sent:** `{broadcast_status['current_index']}`\n"
        f"⏳ **Skipped:** `{total - broadcast_status['current_index']}`"
    )
    
    try:
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=status_message_id,
            text=summary_text,
            reply_markup=InlineKeyboardMarkup([
                [
                  InlineKeyboardButton("▪︎ ɴᴇᴡ", callback_data="broadcast_new"),
                  InlineKeyboardButton("✖ ᴄʟᴏsᴇ", callback_data="broadcast_close")
                ]
            ]),
            parse_mode="Markdown"
        )
    except Exception as e:
        print(f"Error sending final summary: {e}")
    
    # Reset broadcast status
    broadcast_status.update({
        'is_running': False,
        'current_index': 0,
        'total_users': 0,
        'success_count': 0,
        'failed_count': 0,
        'start_time': None,
        'message': None,
        'task': None
    })

async def broadcast_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle broadcast button clicks"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data == "broadcast_cancel":
        if broadcast_status['is_running']:
            # Cancel the broadcast
            broadcast_status['is_running'] = False
            if broadcast_status['task']:
                broadcast_status['task'].cancel()
            
            await query.edit_message_text(
                "🚫 **Broadcast Cancelled**\n\n"
                "The broadcast has been stopped. Some users may have already received the message.",
                reply_markup=InlineKeyboardMarkup([
                [
                  InlineKeyboardButton("▪︎ ɴᴇᴡ", callback_data="broadcast_new"),
                  InlineKeyboardButton("✖ ᴄʟᴏsᴇ", callback_data="broadcast_close")
                ]
            ]),
                parse_mode="Markdown"
            )
        else:
            await query.answer("No broadcast is currently running!", show_alert=True)
    
    elif data == "broadcast_new":
        await query.edit_message_text(
            "📢 **New Broadcast**\n\n"
            "Reply to a message with /broadcast to start a new broadcast.",
            parse_mode="Markdown"
        )
    
    elif data == "broadcast_close":
        await query.message.delete()

# Command to check broadcast status
@check_ban_and_register
async def broadcast_status_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if user_id != 5373577888:
        await update.message.reply_text("❌ This command is only available for the bot owner!")
        return
    
    if broadcast_status['is_running']:
        current = broadcast_status['current_index']
        total = broadcast_status['total_users']
        success = broadcast_status['success_count']
        failed = broadcast_status['failed_count']
        percentage = (current / total) * 100
        
        status_text = (
            f"📢 **Broadcast Running**\n\n"
            f"📊 **Progress:** `{percentage:.1f}%` ({current}/{total})\n"
            f"✅ **Successful:** `{success}`\n"
            f"❌ **Failed:** `{failed}`\n"
            f"⏳ **Remaining:** `{total - current}`\n\n"
            f"⏰ **Started:** `{broadcast_status['start_time'].strftime('%H:%M:%S')}`"
        )
        
        await update.message.reply_text(
            status_text,
            reply_markup=InlineKeyboardMarkup([
                [
                 InlineKeyboardButton("⚠︎ ᴄᴀɴᴄᴇʟ", callback_data="broadcast_cancel"),
                 InlineKeyboardButton("✖ ᴄʟᴏsᴇ", callback_data="broadcast_close")
                ]
            ]),
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            "📢 **No active broadcast**\n\n"
            "There is no broadcast currently running.",
            parse_mode="Markdown"
    )
