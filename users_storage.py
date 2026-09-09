import json
import os

# ======================
# PATH
# ======================

FILE_PATH = os.getenv("USERS_FILE", "./users.json")

# если Render disk доступен — используем его
if os.path.exists("/data"):
    FILE_PATH = "/data/users.json"


# ======================
# LOAD / SAVE
# ======================

def _load():
    if not os.path.exists(FILE_PATH):
        return {}

    try:
        with open(FILE_PATH, "r") as f:
            return json.load(f)
    except:
        return {}


def _save(data):
    os.makedirs(os.path.dirname(FILE_PATH), exist_ok=True)

    with open(FILE_PATH, "w") as f:
        json.dump(data, f)


# ======================
# PUBLIC API
# ======================

def register_user(chat_id, level):
    data = _load()
    data[str(chat_id)] = level
    _save(data)


def get_users():
    data = _load()
    return {int(k): v for k, v in data.items()}