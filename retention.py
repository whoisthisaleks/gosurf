from datetime import datetime, timedelta
from cache import get_cache, set_cache

RETENTION_KEY = "retention_users"


def _day_key(date):
    return date.strftime("%Y-%m-%d")


# ======================
# TRACK USER BY DAY
# ======================

def track_user_day(user_id):
    today = datetime.utcnow()
    key = f"{RETENTION_KEY}:{_day_key(today)}"

    users = get_cache(key) or []

    if user_id not in users:
        users.append(user_id)

    set_cache(key, users, ttl=86400 * 7)  # храним 7 дней


# ======================
# GET USERS BY DAY
# ======================

def get_users_by_day(date):
    key = f"{RETENTION_KEY}:{_day_key(date)}"
    return get_cache(key) or []


# ======================
# D1 RETENTION
# ======================

def get_d1_retention():
    today = datetime.utcnow()
    yesterday = today - timedelta(days=1)

    users_today = set(get_users_by_day(today))
    users_yesterday = set(get_users_by_day(yesterday))

    if not users_yesterday:
        return 0, 0, 0

    returned = users_today.intersection(users_yesterday)

    retention = int(len(returned) / len(users_yesterday) * 100)

    return len(users_yesterday), len(returned), retention