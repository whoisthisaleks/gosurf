import json
import os
from datetime import datetime, timedelta


# ======================
# PATH (LOCAL / RENDER)
# ======================

if os.path.exists("/data"):
    FILE_PATH = "/data/pro_users.json"
else:
    FILE_PATH = "pro_users.json"


# чтобы не спамить уведомлением
notified_users = set()


# ======================
# LOAD / SAVE
# ======================

def _load():
    if not os.path.exists(FILE_PATH):
        return {}

    try:
        with open(FILE_PATH, "r") as f:
            data = json.load(f)
            return {
                int(k): datetime.fromisoformat(v)
                for k, v in data.items()
            }
    except:
        return {}


def _save(data):
    # создаём папку если её нет
    os.makedirs(os.path.dirname(FILE_PATH) or ".", exist_ok=True)

    with open(FILE_PATH, "w") as f:
        json.dump(
            {str(k): v.isoformat() for k, v in data.items()},
            f
        )


# ======================
# START TRIAL (7 days)
# ======================

def start_trial(user_id):
    data = _load()

    if user_id not in data:
        data[user_id] = datetime.utcnow() + timedelta(days=7)
        _save(data)


# ======================
# IS PRO
# ======================

def is_pro(user_id):
    data = _load()

    expire = data.get(user_id)
    if not expire:
        return False

    return expire > datetime.utcnow()


# ======================
# ADD PRO (31 days)
# ======================

def add_pro_user(user_id):
    data = _load()

    data[user_id] = datetime.utcnow() + timedelta(days=31)

    _save(data)

    # сбрасываем флаг уведомления
    if user_id in notified_users:
        notified_users.remove(user_id)


# ======================
# DAYS LEFT
# ======================

def days_left(user_id):
    data = _load()

    expire = data.get(user_id)
    if not expire:
        return 0

    delta = expire - datetime.utcnow()
    return max(delta.days, 0)


# ======================
# NOTIFY EXPIRED
# ======================

def should_notify_expired(user_id):
    data = _load()

    expire = data.get(user_id)

    if not expire:
        return False

    # уже уведомляли
    if user_id in notified_users:
        return False

    # истёк
    if expire <= datetime.utcnow():
        notified_users.add(user_id)
        return True

    return False