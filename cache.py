import time

CACHE = {}
CACHE_TTL = 900  # 15 минут

def get_cache(key):
    if key in CACHE:
        data, ts = CACHE[key]
        if time.time() - ts < CACHE_TTL:
            return data
    return None

def set_cache(key, value):
    CACHE[key] = (value, time.time())