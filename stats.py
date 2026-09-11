from datetime import datetime, timedelta
from cache import get_cache, set_cache

# ======================
# KEYS
# ======================

FIRST_SEEN_KEY = "first_seen"

DAU_KEY = "dau_users"
REQ_KEY = "requests_count"

BEST_KEY = "best_requests"
ALL_KEY = "all_requests"
MORNING_KEY = "morning_requests"

# ======================
# HELPERS
# ======================

def _date_key(base, date):
    return f"{base}:{date.strftime('%Y-%m-%d')}"

def _today_key(base):
    return _date_key(base, datetime.utcnow())

# ======================
# USERS (DAU + RETENTION)
# ======================

def track_user(user_id):
    """
    Главная функция:
    - считает DAU
    - используется для retention
    """
    key = _today_key(DAU_KEY)

    users = get_cache(key) or []

    if user_id not in users:
        users.append(user_id)

    # 🔥 храним 7 дней (чтобы считать retention)
    set_cache(key, users, ttl=86400 * 7)


def get_dau():
    users = get_cache(_today_key(DAU_KEY)) or []
    return len(users)

# ======================
# REQUESTS (ALL)
# ======================

def track_request():
    key = _today_key(REQ_KEY)

    count = get_cache(key) or 0
    count += 1

    set_cache(key, count, ttl=86400 * 7)


def get_requests():
    return get_cache(_today_key(REQ_KEY)) or 0

# ======================
# REQUEST TYPES
# ======================

def track_best():
    key = _today_key(BEST_KEY)

    count = get_cache(key) or 0
    count += 1

    set_cache(key, count, ttl=86400 * 7)


def track_all():
    key = _today_key(ALL_KEY)

    count = get_cache(key) or 0
    count += 1

    set_cache(key, count, ttl=86400 * 7)


def track_morning():
    key = _today_key(MORNING_KEY)

    count = get_cache(key) or 0
    count += 1

    set_cache(key, count, ttl=86400 * 7)


def get_best():
    return get_cache(_today_key(BEST_KEY)) or 0


def get_all():
    return get_cache(_today_key(ALL_KEY)) or 0


def get_morning():
    return get_cache(_today_key(MORNING_KEY)) or 0

# ======================
# RETENTION
# ======================

def get_retention(day_offset=1):
    """
    D1 retention по умолчанию
    """
    today = datetime.utcnow()
    today_key = _date_key(DAU_KEY, today)

    past_day = today - timedelta(days=day_offset)
    past_key = _date_key(DAU_KEY, past_day)

    today_users = set(get_cache(today_key) or [])
    past_users = set(get_cache(past_key) or [])

    if not past_users:
        return 0

    retained = today_users.intersection(past_users)

    return int(len(retained) / len(past_users) * 100)

# ======================
# FIRST SEEN
# ======================

def track_first_seen(user_id):
    key = f"{FIRST_SEEN_KEY}:{user_id}"

    if get_cache(key):
        return

    today = datetime.utcnow().strftime("%Y-%m-%d")

    set_cache(key, today, ttl=86400 * 365)