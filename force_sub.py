import os
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from shared_functions import (
    load_admins,
    load_settings,
    load_force_sub,
    save_force_sub
)

OWNER_ID = 5373577888
COUNTDOWN_SECONDS = 60

# ─────────────────────────────────────────────
# Utility
# ─────────────────────────────────────────────

def is_admin(user_id: int) -> bool:
    return user_id == OWNER_ID or user_id in load_admins()

# ─────────────────────────────────────────────
# UI Renderer
# ─────────────────────────────────────────────

async def render_fsub_menu(message, context):
    channels = load_force_sub()

    keyboard = []
    for ch in channels:
        keyboard.append([
            InlineKeyboardButton(
                f"🗑️ {ch['title']}",
                callback_data=f"fsub_delete_{ch['id']}"
            )
        ])

    keyboard.append([InlineKeyboardButton("➕ Add Channel", callback_data="fsub_add")])
    keyboard.append([InlineKeyboardButton("❌ Close", callback_data="fsub_close")])

    text = "📢 **Force Subscribe Channels**\n\n"
    if channels:
        for ch in channels:
            text += f"• {ch['title']} — `{ch.get('mode','normal')}`\n"
    else:
        text += "No channels added yet."

    await message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

# ─────────────────────────────────────────────
# /fsub Command
# ─────────────────────────────────────────────

async def force_sub_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return await update.message.reply_text("❌ Not authorized")

    msg = await update.message.reply_text("Loading...")
    await render_fsub_menu(msg, context)

# ─────────────────────────────────────────────
# Countdown Timer
# ─────────────────────────────────────────────

async def fsub_countdown(message, context):
    for i in range(COUNTDOWN_SECONDS, 0, -1):
        if not context.user_data.get("waiting_fsub"):
            return
        try:
            await message.edit_text(
                f"📢 **Forward channel message**\n\n⏳ Time left: **{i}s**",
                reply_markup=message.reply_markup,
                parse_mode="Markdown"
            )
        except:
            pass
        await asyncio.sleep(1)

    context.user_data.clear()
    await message.edit_text("❌ Timeout! Please use /fsub again.")

# ─────────────────────────────────────────────
# Button Handler
# ─────────────────────────────────────────────

async def force_sub_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if not is_admin(query.from_user.id):
        return await query.answer("Unauthorized", show_alert=True)

    data = query.data

    if data == "fsub_add":
        context.user_data["waiting_fsub"] = True

        await query.edit_message_text(
            "📢 **Forward channel message**\n\n⏳ Time left: **60s**",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("🔙 Back", callback_data="fsub_back"),
                    InlineKeyboardButton("❌ Close", callback_data="fsub_close")
                ]
            ]),
            parse_mode="Markdown"
        )

        asyncio.create_task(fsub_countdown(query.message, context))

    elif data == "fsub_back":
        context.user_data.clear()
        await render_fsub_menu(query.message, context)

    elif data == "fsub_close":
        await query.message.delete()

    elif data.startswith("fsub_delete_"):
        cid = int(data.split("_")[-1])
        channels = load_force_sub()
        channels = [c for c in channels if c["id"] != cid]
        save_force_sub(channels)
        await render_fsub_menu(query.message, context)

    elif data in ("fsub_mode_normal", "fsub_mode_request"):
        ch = context.user_data.pop("pending_channel")

        is_request_mode = (data == "fsub_mode_request")

        try:
            invite = await context.bot.create_chat_invite_link(
                chat_id=ch["id"],
                name=f"ForceSub_{ch['title']}",
                creates_join_request=is_request_mode
            )
        except Exception:
            return await query.answer(
                "❌ Failed to create invite link.\n"
                "Make sure bot has Invite Users permission.",
                show_alert=True
            )

        ch["invite_link"] = invite.invite_link
        ch["mode"] = "request" if is_request_mode else "normal"

        save_force_sub(load_force_sub() + [ch])
        context.user_data.clear()

        if is_request_mode:
            await query.edit_message_text(
                "🕓 **Request mode enabled**\nAdmin approval required.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Back", callback_data="fsub_back")]
                ]),
                parse_mode="Markdown"
            )
        else:
            await render_fsub_menu(query.message, context)
# ─────────────────────────────────────────────
# Forwarded Channel Handler
# ─────────────────────────────────────────────

async def forwarded_channel_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not is_admin(user_id):
        return

    if not context.user_data.get("waiting_fsub"):
        return

    message = update.message
    if not message or not message.forward_origin:
        return await message.reply_text("⚠️ Forward a channel message.")

    origin = message.forward_origin
    if origin.type != "channel":
        return await message.reply_text("⚠️ This is not a channel message.")

    chat = origin.chat
    channel_id = chat.id
    channel_title = chat.title

    # ✅ BOT MUST BE ADMIN
    try:
        member = await context.bot.get_chat_member(channel_id, context.bot.id)
        if member.status not in ("administrator", "creator"):
            return await message.reply_text(
                "❌ Bot must be admin in this channel."
            )
    except Exception as e:
        return await message.reply_text("❌ Cannot verify bot permissions.")

    channels = load_force_sub()
    if any(c["id"] == channel_id for c in channels):
        return await message.reply_text("❌ Channel already added.")


    # SAVE CHANNEL
    context.user_data["pending_channel"] = {
        "id": channel_id,
        "title": channel_title,
        "username": chat.username,
        "added_by": user_id
    }

    await message.reply_text(
        "⚙️ **Choose Force Subscribe Mode**",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✅ Normal Mode", callback_data="fsub_mode_normal"),
                InlineKeyboardButton("🕓 Request Mode", callback_data="fsub_mode_request")
            ],
            [
                InlineKeyboardButton("🔙 Back", callback_data="fsub_back"),
                InlineKeyboardButton("❌ Close", callback_data="fsub_close")
            ]
        ]),
        parse_mode="Markdown"
        )
    
# Force subscription check function
async def check_force_subscription(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    user_id: int
):
    channels = load_force_sub()

    if not channels:
        return True

    temp_msg = await update.message.reply_text(
        "ᴄʜᴇᴄᴋɪɴɢ sᴜʙsᴄʀɪᴘᴛɪᴏɴ...."
    )

    unsubscribed_channels = []

    for channel in channels:
        channel_id = channel["id"]
        mode = channel.get("mode", "normal")

        try:
            member = await context.bot.get_chat_member(channel_id, user_id)
            status = member.status

            # 🚫 Always fail if left or kicked
            if status in ("left", "kicked"):
                unsubscribed_channels.append(channel)
                continue

            # ✅ NORMAL MODE → must be member
            if mode == "normal":
                if status == "member":
                    continue
                else:
                    unsubscribed_channels.append(channel)
                    continue

            # ✅ REQUEST MODE → member OR restricted is OK
            if mode == "request":
                if status in ("member", "restricted"):
                    continue
                else:
                    unsubscribed_channels.append(channel)
                    continue

        except Exception as e:
            print(f"Error checking subscription for {channel_id}: {e}")
            unsubscribed_channels.append(channel)

    # ❌ Not verified
    if unsubscribed_channels:
        await asyncio.sleep(0.5)
        await temp_msg.edit_text(
            "❌ ɴᴏᴛ ᴠᴇʀɪғɪᴇᴅ!\n"
            "ᴘʟᴇᴀsᴇ ᴊᴏɪɴ ᴀʟʟ ᴄʜᴀɴɴᴇʟs ᴛᴏ ᴄᴏɴᴛɪɴᴜᴇ"
        )
        await asyncio.sleep(0.6)
        await temp_msg.delete()
        await send_force_sub_message(update, context, unsubscribed_channels)
        return False

    # ✅ Verified
    try:
        await asyncio.sleep(0.3)
        await temp_msg.edit_text("ᴠᴇʀɪғɪᴇᴅ ✅")
        await asyncio.sleep(0.4)
        await temp_msg.edit_text("ᴘ

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
    
    # ✅ Everything below is indented INSIDE the async function
    buttons = []
    row = []

    for index, channel in enumerate(channels[:6], start=1):
        channel_url = (
            channel.get("invite_link")
            or (f"https://t.me/{channel['username']}" if channel.get("username") else f"https://t.me/c/{str(channel['id'])[4:]}")
        )

        row.append(InlineKeyboardButton(f"{channel['title']}", url=channel_url))

        if index % 2 == 0:
            buttons.append(row)
            row = []

    if row:
        buttons.append(row)
    encoded_link = context.user_data.get("original_encoded_id", "home")
    
    buttons.append([InlineKeyboardButton("🔄 ᴛʀʏ ᴀɢᴀɪɴ", url=f"https://t.me/Rimuru_filebot?start={encoded_link}")])

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
            return
        except Exception as e:
            print(f"Error sending photo: {e}")
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=text,
                reply_markup=keyboard,
                parse_mode="Markdown"
        )
