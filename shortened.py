import requests
import json
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters

from shared_functions import load_admins, load_settings
from middleware import check_ban_and_register
from datetime import datetime

# Load shortener settings
def load_shortener():
    try:
        with open('shortener.json', 'r') as f:
            return json.load(f)
    except:
        return {
            "enabled": False,
            "api_key": "",
            "website": "",
            "website_name": ""
        }

# Save shortener settings
def save_shortener(settings):
    with open('shortener.json', 'w') as f:
        json.dump(settings, f, indent=4)

@check_ban_and_register
async def shortener_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    admins = load_admins()
    
    # Check if user is admin or owner
    if user_id not in admins and user_id != 5373577888:
        await update.message.reply_text("You are not authorized to use this command!")
        return
    
    shortener_settings = load_shortener()
    
    if shortener_settings['enabled']:
        # Shortener is already set up
        website_name = shortener_settings.get('website_name', 'Unknown')
        await update.message.reply_text(
            f"🔗 **Shortener Settings**\n\n"
            f"✅ **Status:** Enabled\n"
            f"🌐 **Website:** {website_name}\n\n"
            f"📝 **Usage:** Reply to any message with /shortlink to generate a shortened link\n"
            f"🔄 **To change shortener:** Use /shortener again to reset",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Change Shortener", callback_data="shortener_change")],
                [InlineKeyboardButton("❌ Disable", callback_data="shortener_disable")],
                [InlineKeyboardButton("❌ Close", callback_data="shortener_close")]
            ]),
            parse_mode="Markdown"
        )
    else:
        # No shortener set up
        await update.message.reply_text(
            "🔗 **Shortener Settings**\n\n"
            "📢 Please add the shortener API first to enable link shortening.\n\n"
            "Supported shorteners:\n"
            "• GPLinks\n• ShortConnect\n• Dalink\n• And more...",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("➕ Add Shortener", callback_data="shortener_add")],
                [InlineKeyboardButton("❌ Close", callback_data="shortener_close")]
            ]),
            parse_mode="Markdown"
        )

async def shortener_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    user_id = query.from_user.id
    admins = load_admins()
    
    # Check if user is admin or owner
    if user_id not in admins and user_id != 5373577888:
        await query.answer("You are not authorized!", show_alert=True)
        return
    
    if data == "shortener_add":
        await query.edit_message_text(
            "🔗 **Add Shortener API**\n\n"
            "Please send me your API token from any shortener website within 60 seconds.\n\n"
            "📋 **Format:** `API_TOKEN`\n"
            "💡 **Example:** `30c51949bc643988e66bfcf171cae91987b6446a`\n\n"
            "⏰ **Time Limit:** 60 seconds",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("❌ Cancel", callback_data="shortener_cancel")]
            ]),
            parse_mode="Markdown"
        )
        
        # Set waiting state for API input
        context.user_data['waiting_for_api'] = True
        context.user_data['original_message_id'] = query.message.message_id
        context.user_data['original_chat_id'] = query.message.chat.id
        
        # Set timeout task
        asyncio.create_task(shortener_timeout(context, 60))
        
    elif data == "shortener_change":
        await query.edit_message_text(
            "🔄 **Change Shortener**\n\n"
            "Please send me your new API token within 60 seconds.\n\n"
            "📋 **Format:** `API_TOKEN`\n"
            "⏰ **Time Limit:** 60 seconds",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("❌ Cancel", callback_data="shortener_cancel")]
            ]),
            parse_mode="Markdown"
        )
        
        context.user_data['waiting_for_api'] = True
        context.user_data['original_message_id'] = query.message.message_id
        context.user_data['original_chat_id'] = query.message.chat.id
        
        asyncio.create_task(shortener_timeout(context, 60))
        
    elif data == "shortener_disable":
        shortener_settings = load_shortener()
        shortener_settings['enabled'] = False
        shortener_settings['api_key'] = ""
        shortener_settings['website'] = ""
        shortener_settings['website_name'] = ""
        save_shortener(shortener_settings)
        
        await query.edit_message_text(
            "❌ **Shortener Disabled**\n\n"
            "Link shortening has been disabled successfully.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("➕ Enable Again", callback_data="shortener_add")],
                [InlineKeyboardButton("❌ Close", callback_data="shortener_close")]
            ]),
            parse_mode="Markdown"
        )
        
    elif data == "shortener_cancel":
        context.user_data.pop('waiting_for_api', None)
        await shortener_handler(update, context)
        
    elif data == "shortener_close":
        await query.message.delete()

async def shortener_timeout(context: ContextTypes.DEFAULT_TYPE, timeout: int):
    """Handle shortener setup timeout"""
    await asyncio.sleep(timeout)
    
    if context.user_data.get('waiting_for_api'):
        context.user_data.pop('waiting_for_api', None)
        
        original_chat_id = context.user_data.get('original_chat_id')
        original_message_id = context.user_data.get('original_message_id')
        
        if original_chat_id and original_message_id:
            try:
                await context.bot.edit_message_text(
                    chat_id=original_chat_id,
                    message_id=original_message_id,
                    text="⏰ **Time Expired**\n\n"
                         "The 60-second time limit has expired. Please use /shortener again to retry.",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔄 Try Again", callback_data="shortener_add")],
                        [InlineKeyboardButton("❌ Close", callback_data="shortener_close")]
                    ]),
                    parse_mode="Markdown"
                )
            except:
                pass

async def shortener_api_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle API token input"""
    user_id = update.effective_user.id
    admins = load_admins()
    
    # Check if user is admin or owner
    if user_id not in admins and user_id != 5373577888:
        return
    
    if not context.user_data.get('waiting_for_api'):
        return
    
    api_token = update.message.text.strip()
    
    # Validate API token format (basic validation)
    if not api_token or len(api_token) < 10:
        await update.message.reply_text(
            "❌ **Invalid API Token**\n\n"
            "Please provide a valid API token. It should be at least 10 characters long.\n\n"
            "Use /shortener to try again.",
            parse_mode="Markdown"
        )
        context.user_data.pop('waiting_for_api', None)
        return
    
    # Detect shortener service and verify API
    website_name, website_url = await detect_shortener_service(api_token)
    
    if website_name:
        # API is valid, save settings
        shortener_settings = {
            "enabled": True,
            "api_key": api_token,
            "website": website_url,
            "website_name": website_name
        }
        save_shortener(shortener_settings)
        
        original_chat_id = context.user_data.get('original_chat_id')
        original_message_id = context.user_data.get('original_message_id')
        
        if original_chat_id and original_message_id:
            await context.bot.edit_message_text(
                chat_id=original_chat_id,
                message_id=original_message_id,
                text=f"✅ **Shortener Set Successfully**\n\n"
                     f"🌐 **Website:** {website_name}\n"
                     f"🔗 **API Status:** Verified\n\n"
                     f"📝 **Usage:** Reply to any message with /shortlink to generate shortened links",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔗 Test Shortlink", callback_data="shortener_test")],
                    [InlineKeyboardButton("❌ Close", callback_data="shortener_close")]
                ]),
                parse_mode="Markdown"
            )
        
        await update.message.reply_text(
            f"✅ Successfully set {website_name}!\n\n"
            f"You can now create shortened links directly by replying to messages with /shortlink",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            "❌ **API Verification Failed**\n\n"
            "The provided API token could not be verified. Please check:\n"
            "• API token is correct\n"
            "• Supported shortener service\n"
            "• Internet connection\n\n"
            "Use /shortener to try again.",
            parse_mode="Markdown"
        )
    
    context.user_data.pop('waiting_for_api', None)

async def detect_shortener_service(api_token: str):
    """Detect which shortener service the API token belongs to"""
    test_url = "https://google.com"
    
    services = {
        "GPLinks": {
            "url": "https://api.gplinks.com/api",
            "method": "GET",  # GPLinks uses GET
            "params": {"api": api_token, "url": test_url},
        },
        "ShortConnect": {
            "url": "https://api.shortconnect.com/shorten",
            "method": "GET",
            "params": {"api": api_token, "url": test_url}
        },
        "Dalink": {
            "url": "https://dalink.in/api",
            "method": "GET", 
            "params": {"api": api_token, "url": test_url}
        }
    }
    
    for name, config in services.items():
        try:
            print(f"Testing {name} API...")
            
            if config['method'] == 'POST':
                response = requests.post(config['url'], data=config['data'], headers=config.get('headers', {}), timeout=10)
            else:
                response = requests.get(config['url'], params=config.get('params', {}), timeout=10)
                
            print(f"{name} Response Status: {response.status_code}")
            print(f"{name} Response Text: {response.text}")
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success' or 'shortenedUrl' in data or 'short_url' in data:
                    print(f"✅ {name} API verified successfully!")
                    return name, config['url'].replace('/api', '').replace('/shorten', '')
        except Exception as e:
            print(f"❌ {name} test failed: {e}")
            continue
    
    # If no specific service detected, assume generic
    print("⚠️ No specific service detected, using generic")
    return "Custom Shortener", "https://example.com"

#shortlink handler
@check_ban_and_register
async def shortlink_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    admins = load_admins()

    if user_id not in admins and user_id != 5373577888:
        await update.message.reply_text("You are not authorized!")
        return

    short_set = load_shortener()
    if not short_set["enabled"]:
        await update.message.reply_text("❌ Shortener not set. Use /shortener", parse_mode="Markdown")
        return

    # Set waiting state
    context.user_data["waiting_for_shortlink"] = True
    context.user_data["stop_shortlink_timer"] = False

    msg = await update.message.reply_text(
        "> ᴘʟᴇᴀsᴇ sᴇɴᴅ ᴏʀ ғᴏʀᴡᴀʀᴅ ᴀ ᴍᴇssᴀɢᴇ ᴛᴏ ɢᴇɴᴇʀᴀᴛᴇ ᴀ ʟɪɴᴋ\\.\n"
        "ᴛɪᴍᴇᴏᴜᴛ\\: 60s ʀᴇᴍᴀɪɴɪɴɢ",
        parse_mode="MarkdownV2"
    )

    context.user_data["shortlink_wait_msg"] = msg

    context.user_data["sl_timer"] = asyncio.create_task(
        shortlink_countdown(context)
    )

#countdown shortener
@check_ban_and_register
async def shortlink_countdown(context):
    msg = context.user_data.get("shortlink_wait_msg")

    for sec in range(60, 0, -1):
        if context.user_data.get("stop_shortlink_timer"):
            return

        try:
            await msg.edit_text(
                f"> ᴘʟᴇᴀsᴇ sᴇɴᴅ ᴏʀ ғᴏʀᴡᴀʀᴅ ᴀ ᴍᴇssᴀɢᴇ ᴛᴏ ɢᴇɴᴇʀᴀᴛᴇ ᴀ ʟɪɴᴋ\\.\n"
                f"ᴛɪᴍᴇᴏᴜᴛ\\: {sec}s ʀᴇᴍᴀɪɴɪɴɢ",
                parse_mode="MarkdownV2"
            )
        except:
            pass

        await asyncio.sleep(1)

    context.user_data["waiting_for_shortlink"] = False

    try:
        await msg.edit_text("⏰ *Time expired!*", parse_mode="Markdown")
    except:
        pass

    return

#main function   
async def shortlink_wait_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("waiting_for_shortlink"):
        return

    # Stop countdown
    context.user_data["waiting_for_shortlink"] = False
    context.user_data["stop_shortlink_timer"] = True

    timer = context.user_data.get("sl_timer")
    if timer:
        timer.cancel()

    wait_msg = context.user_data.get("shortlink_wait_msg")

    try:
        await wait_msg.edit_text("⏳ Generating shortlink…")
    except:
        pass

    # Build encoded link
    msg = update.message
    from links import encode_file_id, load_links, save_links
    encoded = encode_file_id(f"{msg.chat_id}:{msg.message_id}")

    # Save link
    links = load_links()
    links[encoded] = {
        "chat_id": msg.chat_id,
        "message_id": msg.message_id,
        "created_at": datetime.utcnow().isoformat(),
        "created_by": update.effective_user.id
    }
    save_links(links)

    # Shorten
    settings = load_shortener()
    shortened_url = await shorten_url(
        settings["api_key"],
        f"https://t.me/{context.bot.username}?start={encoded}",
        settings["website"]
    )

    await wait_msg.edit_text(
        f"🔗 **Shortened Link Generated**\n\n"
        f"🌐 Service: {settings['website_name']}\n"
        f"🔗 Short URL: {shortened_url}\n\n"
        f"📎 Original URL:\n`https://t.me/{context.bot.username}?start={encoded}`",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔗 Open Short Link", url=shortened_url)],
            [InlineKeyboardButton("📋 Copy", callback_data=f"shortlink_copy_{shortened_url}")]
        ])
    )

async def shorten_url(api_key: str, url: str, website: str) -> str:
    """Shorten URL using the configured shortener service"""
    try:

        # ✅ GPLinks (official developer API)
        if "gplinks" in website.lower():
            api_url = "https://api.gplinks.com/api"
            params = {
                "api": api_key,
                "url": url
            }

            print(f"[GPLinks] Request → {params}")

            try:
                response = requests.get(api_url, params=params, timeout=10)
            except Exception as e:
                raise Exception(f"GPLinks request failed: {str(e)}")

            print(f"[GPLinks] Response ({response.status_code}) → {response.text}")

            if response.status_code != 200:
                raise Exception(f"GPLinks HTTP error {response.status_code}")

            try:
                data = response.json()
            except:
                raise Exception(f"GPLinks returned non-JSON: {response.text}")

            if data.get("status") == "success":
                return data.get("shortenedUrl", url)
            else:
                raise Exception(f"GPLinks API error: {data}")

        # ✅ ShortConnect
        elif "shortconnect" in website.lower():
            api_url = "https://api.shortconnect.com/shorten"
            params = {"api": api_key, "url": url}

            response = requests.get(api_url, params=params, timeout=10)

            try:
                data = response.json()
            except:
                raise Exception(f"ShortConnect returned non-JSON: {response.text}")

            if data.get("status") == "success":
                return data.get("short_url", url)
            else:
                msg = data.get("message", "Unknown error from ShortConnect")
                raise Exception(f"ShortConnect API error: {msg}")

        # ✅ Dalink (if reachable)
        elif "dalink" in website.lower():
            api_url = "https://dalink.in/api"
            params = {"api": api_key, "url": url}

            response = requests.get(api_url, params=params, timeout=10)

            try:
                data = response.json()
            except:
                raise Exception(f"Dalink returned non-JSON: {response.text}")

            if data.get("status") == "success":
                return data.get("shortenedUrl", url)
            else:
                msg = data.get("msg", "Unknown error from Dalink")
                raise Exception(f"Dalink API error: {msg}")

        # ✅ Generic API-compatible shorteners
        else:
            api_url = f"{website}/api"
            params = {"api": api_key, "url": url}

            response = requests.get(api_url, params=params, timeout=10)

            try:
                data = response.json()
            except:
                raise Exception(f"Shortener returned non-JSON: {response.text}")

            # Universal JSON patterns
            if data.get("status") == "success":
                return data.get("shortenedUrl", data.get("short_url", url))

            if "shortenedUrl" in data:
                return data["shortenedUrl"]

            if "short_url" in data:
                return data["short_url"]

            raise Exception(f"Unknown API format: {data}")

    except requests.exceptions.RequestException as e:
        raise Exception(f"Network error: {str(e)}")

    except Exception as e:
        raise Exception(f"Shortening failed: {str(e)}")
        
async def shortlink_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle shortlink button clicks"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data.startswith("shortlink_copy_"):
        url = data.replace("shortlink_copy_", "")
        await query.answer(f"Copied: {url}", show_alert=True)
    
    elif data == "shortener_test":
        # Test the shortener with a sample URL
        shortener_settings = load_shortener()
        try:
            test_url = await shorten_url(
                shortener_settings['api_key'],
                "https://google.com",
                shortener_settings['website']
            )
            
            await query.edit_message_text(
                f"✅ **Shortener Test Successful**\n\n"
                f"🌐 **Service:** {shortener_settings['website_name']}\n"
                f"🔗 **Test URL:** {test_url}\n\n"
                f"Your shortener is working correctly!",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔗 Open Test Link", url=test_url)],
                    [InlineKeyboardButton("❌ Close", callback_data="shortener_close")]
                ]),
                parse_mode="Markdown"
            )
        except Exception as e:
            await query.edit_message_text(
                f"❌ **Shortener Test Failed**\n\n"
                f"Error: {str(e)}\n\n"
                f"Please check your API settings.",
                parse_mode="Markdown"
             )
