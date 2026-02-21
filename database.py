import json
import os
import asyncio
from datetime import datetime
from threading import Lock

DB_FILE = "users.json"
ALERTS_FILE = "alerts.json"
_db_lock = Lock()

def load_users():
    """Load users from database"""
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def load_alerts():
    """Load alerts from database"""
    if os.path.exists(ALERTS_FILE):
        try:
            with open(ALERTS_FILE, 'r') as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
        except:
            return []
    return []

def save_users(users):
    """Save users to database"""
    try:
        with open(DB_FILE, 'w') as f:
            json.dump(users, f, indent=2)
    except Exception as e:
        print(f"Error saving users: {e}")

def save_alerts(alerts):
    """Save alerts to database"""
    try:
        with open(ALERTS_FILE, 'w') as f:
            json.dump(alerts, f, indent=2)
    except Exception as e:
        print(f"Error saving alerts: {e}")

def add_user(user_id, username=None, first_name=None):
    """Add or update user in database with thread-safe locking"""
    with _db_lock:
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
    """Get user statistics with thread-safe locking"""
    with _db_lock:
        users = load_users()
        total_users = len(users)
        total_commands = sum(user.get("command_count", 0) for user in users.values())
        
        return {
            "total_users": total_users,
            "total_commands": total_commands,
            "users": users
        }

def create_alert(user_id, chat_id, coin_symbol, target_price, direction, created_price):
    """Create a new price alert"""
    with _db_lock:
        alerts = load_alerts()
        next_id = max((a.get("id", 0) for a in alerts), default=0) + 1
        now = datetime.now().isoformat()

        new_alert = {
            "id": next_id,
            "user_id": int(user_id),
            "chat_id": int(chat_id),
            "coin_symbol": coin_symbol.lower(),
            "target_price": float(target_price),
            "direction": direction,
            "created_price": float(created_price),
            "created_at": now,
            "triggered_at": None,
            "triggered_price": None,
            "is_active": True,
            "last_checked_price": float(created_price),
        }
        alerts.append(new_alert)
        save_alerts(alerts)
        return new_alert

def list_user_alerts(user_id, only_active=True):
    """List alerts for a user"""
    with _db_lock:
        alerts = load_alerts()
        user_alerts = [a for a in alerts if a.get("user_id") == int(user_id)]
        if only_active:
            user_alerts = [a for a in user_alerts if a.get("is_active", True)]
        user_alerts.sort(key=lambda a: a.get("id", 0))
        return user_alerts

def delete_user_alert(user_id, alert_id):
    """Delete a specific alert belonging to a user"""
    with _db_lock:
        alerts = load_alerts()
        new_alerts = []
        deleted = False
        for alert in alerts:
            if alert.get("id") == int(alert_id) and alert.get("user_id") == int(user_id):
                deleted = True
                continue
            new_alerts.append(alert)

        if deleted:
            save_alerts(new_alerts)
        return deleted

def clear_user_alerts(user_id, only_active=True):
    """Delete all alerts for a user. Returns number of deleted alerts."""
    with _db_lock:
        alerts = load_alerts()
        kept = []
        deleted_count = 0
        for alert in alerts:
            is_user = alert.get("user_id") == int(user_id)
            is_active = alert.get("is_active", True)

            if is_user and (not only_active or is_active):
                deleted_count += 1
                continue
            kept.append(alert)

        if deleted_count > 0:
            save_alerts(kept)
        return deleted_count

def get_active_alerts():
    """Return all active alerts"""
    with _db_lock:
        alerts = load_alerts()
        return [a for a in alerts if a.get("is_active", True)]

def update_alert_last_price(alert_id, price):
    """Update latest checked price for an alert"""
    with _db_lock:
        alerts = load_alerts()
        updated = False
        for alert in alerts:
            if alert.get("id") == int(alert_id):
                alert["last_checked_price"] = float(price)
                updated = True
                break
        if updated:
            save_alerts(alerts)
        return updated

def mark_alert_triggered(alert_id, trigger_price):
    """Mark alert as triggered and inactive"""
    with _db_lock:
        alerts = load_alerts()
        updated = False
        for alert in alerts:
            if alert.get("id") == int(alert_id):
                alert["is_active"] = False
                alert["triggered_at"] = datetime.now().isoformat()
                alert["triggered_price"] = float(trigger_price)
                alert["last_checked_price"] = float(trigger_price)
                updated = True
                break
        if updated:
            save_alerts(alerts)
        return updated
