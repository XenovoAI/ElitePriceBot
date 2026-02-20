import json
import os
from datetime import datetime

DB_FILE = "users.json"

def load_users():
    """Load users from database"""
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_users(users):
    """Save users to database"""
    try:
        with open(DB_FILE, 'w') as f:
            json.dump(users, f, indent=2)
    except Exception as e:
        print(f"Error saving users: {e}")

def add_user(user_id, username=None, first_name=None):
    """Add or update user in database"""
    users = load_users()
    user_id_str = str(user_id)
    
    if user_id_str not in users:
        users[user_id_str] = {
            "user_id": user_id,
            "username": username,
            "first_name": first_name,
            "joined_at": datetime.now().isoformat(),
            "last_seen": datetime.now().isoformat(),
            "command_count": 1
        }
    else:
        users[user_id_str]["last_seen"] = datetime.now().isoformat()
        users[user_id_str]["command_count"] += 1
        if username:
            users[user_id_str]["username"] = username
        if first_name:
            users[user_id_str]["first_name"] = first_name
    
    save_users(users)
    return users[user_id_str]

def get_stats():
    """Get user statistics"""
    users = load_users()
    total_users = len(users)
    total_commands = sum(user.get("command_count", 0) for user in users.values())
    
    return {
        "total_users": total_users,
        "total_commands": total_commands,
        "users": users
    }
