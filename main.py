import os
import json
import logging
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from dotenv import load_dotenv
# Import handlers from all modules
from start import start_handler, button_handler as start_button_handler
from help import help_handler, button_handler as help_button_handler
from links import genlink_handler, start_link_handler, link_button_handler
from settings import settings_handler, settings_button_handler, settings_message_handler
from batch_link import batchlink_handler, batch_message_handler, batch_button_handler
from force_sub import force_sub_handler, force_sub_button_handler, forwarded_channel_handler, force_sub_try_again_handler, check_force_subscription
# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Load admin data for verification
def load_admins():
    try:
        with open('admins.json', 'r') as f:
            return json.load(f)
    except:
        return [5373577888]

# Load or create JSON files
def load_json_files():
    json_files = ['links.json', 'files.json', 'admins.json', 'users.json', 'settings.json']
    
    for file in json_files:
        if not os.path.exists(file):
            with open(file, 'w') as f:
                if file == 'admins.json':
                    # Add the provided admin ID
                    json.dump([5373577888], f)
                    print(f"Created {file} with admin ID: 5373577888")
                
                elif file == 'users.json':
                    json.dump([], f)  # Empty list for users
                    print(f"Created {file}")
                
                elif file == 'settings.json':
                    default_settings = {
                        "start_image": "img.jpg",
                        "help_image": "",
                        "start_text": "Hi {mention} welcome to File Store Bot",
                        "help_text": "Available Commands:\n\n/start - Start the bot\n/help - Show this help message\n/genlink - Generate link\n/batchlink - Generate batch links\n/custombatch - Custom batch processing\n/fsub - Force subscribe\n/settings - Bot settings\n/promote - Promote user to admin\n/demote - Demote admin\n/ban - Ban user\n/unban - Unban user\n/users - Show users\n/admins - Show admins\n/update - Update bot\n/restart - Restart bot",
                        "auto_delete_time": 10,
                        "protect_content": False
                    }
                    json.dump(default_settings, f, indent=4)
                    print(f"Created {file} with default settings")
                
                else:
                    json.dump({}, f)  # Empty dict for links and files
                    print(f"Created {file}")

def main():
    # Load JSON files
    print("Initializing JSON files...")
    load_json_files()
    
    # Get bot token from environment variable
    load_dotenv("Bot_Token.env")
    TOKEN = os.getenv('BOT_TOKEN')
    if not TOKEN:
        print("❌ ERROR: Please set BOT_TOKEN environment variable")
        print("Example: export BOT_TOKEN='your_bot_token_here'")
        return
    
    # Verify token format
    if ':' not in TOKEN:
        print("❌ ERROR: Invalid bot token format")
        return
    
    # Create application
    print("🤖 Creating bot application...")
    application = Application.builder().token(TOKEN).build()
    
    # Add command handlers
    print("📝 Adding command handlers...")
    
    # Command handlers
    application.add_handler(CommandHandler("start", start_link_handler))  # Override start handler for link support
    application.add_handler(CommandHandler("help", help_handler))
    application.add_handler(CommandHandler("genlink", genlink_handler))
    application.add_handler(CommandHandler("settings", settings_handler))
    application.add_handler(CommandHandler("batchlink", batchlink_handler))
    application.add_handler(CommandHandler("fsub", force_sub_handler))
    # Callback query handlers with specific patterns
    print("🔘 Adding callback query handlers...")
    
    # Start module callbacks
    application.add_handler(CallbackQueryHandler(start_button_handler, pattern="^start_"))

    # Batch_Link module callbacks
    # Message handlers - order matters!
    application.add_handler(MessageHandler(filters.FORWARDED, forwarded_channel_handler))  # Force sub first
    application.add_handler(MessageHandler(filters.TEXT | filters.FORWARDED, batch_message_handler))  # Batch second
    application.add_handler(CallbackQueryHandler(batch_button_handler, pattern="^copy_batch_"))
    application.add_handler(CallbackQueryHandler(force_sub_button_handler, pattern="^fsub_"))
    # Help module callbacks  
    application.add_handler(CallbackQueryHandler(help_button_handler, pattern="^help_"))
    
    # Links module callbacks
    application.add_handler(CallbackQueryHandler(link_button_handler, pattern="^link_"))
    
    # Settings module callbacks - multiple patterns
    application.add_handler(CallbackQueryHandler(settings_button_handler, pattern="^settings_"))
    application.add_handler(CallbackQueryHandler(settings_button_handler, pattern="^auto_delete_"))
    application.add_handler(CallbackQueryHandler(settings_button_handler, pattern="^protect_"))

    
    # Message handlers for settings (image and text input)
    print("📨 Adding message handlers...")
    application.add_handler(MessageHandler(
        filters.PHOTO | (filters.TEXT & ~filters.COMMAND), 
        settings_message_handler
    ))
    
    # Error handler
    async def error_handler(update: object, context):
        logging.error(f"Exception while handling an update: {context.error}")
    
    application.add_error_handler(error_handler)
    
    # Display loaded modules and commands
    print("\n✅ Bot initialized successfully!")
    print("📦 Loaded modules:")
    print("   - start.py (Start command with buttons)")
    print("   - help.py (Help command with admin check)")
    print("   - links.py (Link generation with auto-delete)")
    print("   - settings.py (Bot configuration)")
    print("\n🔧 Available commands:")
    print("   /start - Start the bot or access files via links")
    print("   /help - Show help (admin only)")
    print("   /genlink - Generate file links (admin only)")
    print("   /settings - Bot settings (admin only)")
    print("\n⚙️ Features:")
    print("   - Auto-delete files after configured time")
    print("   - Customizable start/help messages and images")
    print("   - Protect content (forwarding restrictions)")
    print("   - Permanent links with base64 encoding")
    print("   - JSON-based data storage")
    print("   - Batch_Link checked ✅")
    print("   - Force_Sub checked ✅")
    # Get bot info
    try:
        bot_info = application.bot.get_me()
        print(f"\n🤖 Bot Info:")
        print(f"   Name: {bot_info.first_name}")
        print(f"   Username: @{bot_info.username}")
        print(f"   ID: {bot_info.id}")
    except Exception as e:
        print(f"   Could not fetch bot info: {e}")
    
    # Check for required files
    print(f"\n📁 File check:")
    if os.path.exists('img.jpg'):
        print("   ✅ img.jpg found")
    else:
        print("   ⚠️  img.jpg not found (bot will use text-only messages)")
    
    # Start the bot
    print(f"\n🚀 Starting bot...")
    print("Press Ctrl+C to stop the bot")
    
    try:
        application.run_polling()
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user")
    except Exception as e:
        print(f"\n❌ Error running bot: {e}")

if __name__ == '__main__':
    main()
