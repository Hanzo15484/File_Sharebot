# shared_functions.py
import json
import base64
import os
from datetime import datetime, timedelta
# Load admin data
def load_admins():
    try:
        with open('admins.json', 'r') as f:
            return json.load(f)
    except:
        return [5373577888]

# Load settings
def load_settings():
    try:
        with open('settings.json', 'r') as f:
            return json.load(f)
    except:
        return {
            "start_image": "img.jpg",
            "help_image": "",
            "force_sub_image": "",
            "start_text": "Hi {mention} welcome to File Store Bot",
            "help_text": "Available Commands:\n\n/start - Start the bot\n/help - Show this help message\n/genlink - Generate link\n/batchlink - Generate batch links\n/custombatch - Custom batch processing\n/fsub - Force subscribe\n/settings - Bot settings\n/promote - Promote user to admin\n/demote - Demote admin\n/ban - Ban user\n/unban - Unban user\n/users - Show users\n/admins - Show admins\n/update - Update bot\n/restart - Restart bot",
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

# Add these functions to shared_functions.py

# Load users data
def load_users():
    try:
        with open('users.json', 'r') as f:
            return json.load(f)
    except:
        return []

# Save users data
def save_users(users):
    with open('users.json', 'w') as f:
        json.dump(users, f, indent=4)

# Load banned users
def load_banned_users():
    try:
        with open('banned_users.json', 'r') as f:
            return json.load(f)
    except:
        return []

# Save banned users
def save_banned_users(banned_users):
    with open('banned_users.json', 'w') as f:
        json.dump(banned_users, f, indent=4)

# Auto-add user to users.json
def auto_add_user(user_id, username, first_name, last_name=None):
    users = load_users()
    
    # Check if user already exists
    user_exists = any(user['id'] == user_id for user in users)
    
    if not user_exists:
        user_data = {
            "id": user_id,
            "username": username,
            "first_name": first_name,
            "last_name": last_name,
            "joined_at": datetime.utcnow().isoformat()
        }
        users.append(user_data)
        save_users(users)
        print(f"✅ Added new user: {first_name} (ID: {user_id})")

# Check if user is banned
def is_user_banned(user_id):
    banned_users = load_banned_users()
    return any(user['id'] == user_id for user in banned_users)

ADMINS_FILE = "admins.json"
NOTIFIED_FILE = "expiry_notified.json"


def read_json(path, default):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return default


def write_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


def ensure_admin_system():
    if not os.path.exists(ADMINS_FILE):
        write_json(ADMINS_FILE, {"admins": [5373577888], "expiry": {}})

    if not os.path.exists(NOTIFIED_FILE):
        write_json(NOTIFIED_FILE, {})


def load_admins_full():
    data = read_json(ADMINS_FILE, {"admins": [5373577888], "expiry": {}})

    if "admins" not in data:
        data["admins"] = [5373577888]

    if "expiry" not in data:
        data["expiry"] = {}

    return data


def save_admins_full(data):
    write_json(ADMINS_FILE, data)


def load_notified():
    return read_json(NOTIFIED_FILE, {})


def save_notified(data):
    write_json(NOTIFIED_FILE, data)


def is_admin(user_id):
    data = load_admins_full()
    return user_id in data["admins"]


def add_admin(user_id, duration):
    data = load_admins_full()

    if user_id not in data["admins"]:
        data["admins"].append(user_id)

    if duration:
        expiry_time = (datetime.utcnow() + duration).isoformat()
        data["expiry"][str(user_id)] = expiry_time
    else:
        if str(user_id) in data["expiry"]:
            data["expiry"].pop(str(user_id))

    save_admins_full(data)
    return True


def remove_admin(user_id):
    data = load_admins_full()

    if user_id in data["admins"]:
        data["admins"].remove(user_id)

    if str(user_id) in data["expiry"]:
        data["expiry"].pop(str(user_id))

    save_admins_full(data)
    return True


def cleanup_expired_admins():
    data = load_admins_full()
    expiry = data["expiry"]
    notified = load_notified()

    now = datetime.utcnow()
    expired = []

    for uid, timestamp in list(expiry.items()):
        exp_time = datetime.fromisoformat(timestamp)

        if now >= exp_time:
            expired.append(int(uid))

            if int(uid) in data["admins"]:
                data["admins"].remove(int(uid))

            expiry.pop(uid, None)
            notified.pop(uid, None)

    data["expiry"] = expiry
    save_admins_full(data)
    save_notified(notified)

    return expired


def parse_duration(duration_str):
    if not duration_str:
        return None

    duration_str = duration_str.lower()

    try:
        if duration_str.endswith("d"):
            return timedelta(days=int(duration_str[:-1]))

        if duration_str.endswith("m"):
            return timedelta(days=int(duration_str[:-1]) * 30)

        if duration_str.endswith("y"):
            return timedelta(days=int(duration_str[:-1]) * 365)

        if duration_str.endswith("h"):
            return timedelta(hours=int(duration_str[:-1]))

        if duration_str.endswith("min"):
            return timedelta(minutes=int(duration_str[:-3]))

        return None
    except:
        return None


def get_expiry(user_id):
    data = load_admins_full()
    expiry_map = data["expiry"]

    timestamp = expiry_map.get(str(user_id))
    if not timestamp:
        return None

    return datetime.fromisoformat(timestamp)


def get_remaining(user_id):
    expiry = get_expiry(user_id)
    if not expiry:
        return None

    return expiry - datetime.utcnow()


def get_notification_stage(user_id):
    notified = load_notified()
    return notified.get(str(user_id))


def set_notification_stage(user_id, stage):
    notified = load_notified()
    notified[str(user_id)] = stage
    save_notified(notified)


def clear_notification(user_id):
    notified = load_notified()
    if str(user_id) in notified:
        notified.pop(str(user_id))
        save_notified(notified)
# Ensure admin-related JSON files exist (needed by main.py)
def ensure_admin_files_exist():
    if not os.path.exists("admins.json"):
        with open("admins.json", "w") as f:
            json.dump([5373577888], f)

    if not os.path.exists("expiry_notified.json"):
        with open("expiry_notified.json", "w") as f:
            json.dump({}, f)
