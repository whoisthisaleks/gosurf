# cache.py

import time

_cache = {}

TTL = 600  # 10 минут


def get_cache(key):
    if key in _cache:
        value, ts = _cache[key]

        if time.time() - ts < TTL:
            return value

    return None


def set_cache(key, value):
    _cache[key] = (value, time.time())