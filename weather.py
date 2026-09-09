API_COUNTER_KEY = "stormglass_calls"

import requests
import math
from datetime import datetime, timedelta, timezone
from config import STORMGLASS_API_KEY
from cache import get_cache, set_cache

BASE_URL = "https://api.stormglass.io/v2/weather/point"

CACHE_TTL = 3600

DEFAULT_DATA = {
    "wave": 0.8,
    "period": 8,
    "wind_speed": 5,
    "wind_direction": 0,
}


# ======================
# HELPERS
# ======================

def _get_value(obj, key, default=None):
    try:
        sources = obj.get(key, {})
        if not isinstance(sources, dict):
            return default

        for src in ["sg", "noaa", "meto", "ecmwf"]:
            val = sources.get(src)
            if val is not None:
                return val

        return default
    except:
        return default


def _parse_hour(hour):
    return {
        "wave": _get_value(hour, "waveHeight", DEFAULT_DATA["wave"]),
        "period": _get_value(hour, "wavePeriod", DEFAULT_DATA["period"]),
        "wind_speed": _get_value(hour, "windSpeed", DEFAULT_DATA["wind_speed"]),
        "wind_direction": _get_value(hour, "windDirection", DEFAULT_DATA["wind_direction"]),
        "wave_direction": _get_value(hour, "waveDirection", None),
    }


def _get_wind_type(wind_dir, offshore_dir):
    if wind_dir is None:
        return "unknown"

    diff = abs(wind_dir - offshore_dir)
    diff = min(diff, 360 - diff)

    if diff <= 45:
        return "offshore"
    elif diff >= 135:
        return "onshore"
    else:
        return "cross"


def _fake_tide_by_time():
    now = datetime.utcnow()
    t = now.hour + now.minute / 60

    value = math.sin(2 * math.pi * t / 12.4)

    if value < -0.3:
        return "low"
    elif value > 0.3:
        return "high"
    else:
        return "mid"


# ======================
# MAIN FETCH
# ======================

def fetch_spot_weather(spot):
    cache_key = f"weather:{spot['name']}"

    cached = get_cache(cache_key)

    # игнор старого кэша без best_time
    if cached and "best_time" in cached:
        return cached

    now = datetime.now(timezone.utc)
    later = now + timedelta(hours=12)

    params = {
        "lat": spot["lat"],
        "lng": spot["lng"],
        "params": "waveHeight,wavePeriod,windSpeed,windDirection,waveDirection",
        "start": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "end": later.strftime("%Y-%m-%dT%H:%M:%SZ"),
    }

    headers = {"Authorization": STORMGLASS_API_KEY}

    try:
        response = requests.get(BASE_URL, params=params, headers=headers, timeout=10)
        increment_api_calls()

        print(f"{spot['name']} status:", response.status_code)

        if response.status_code != 200:
            return _fallback(spot)

        data = response.json()
        hours = data.get("hours")

        if not hours:
            return _fallback(spot)

        parsed = _parse_hour(hours[0])

        wave = parsed["wave"] * spot.get("wave_factor", 1)

        best_time = get_best_time(hours, spot)
        print("BEST TIME:", best_time)

        result = {
            "spot": spot["name"],
            "wave": round(wave, 1),
            "period": int(parsed["period"]),
            "best_time": best_time,
            "wind": _get_wind_type(parsed["wind_direction"], spot["offshore"]),
            "wind_speed": parsed["wind_speed"],
            "swell_dir": parsed["wave_direction"],
            "tide": _fake_tide_by_time(),
        }

        set_cache(cache_key, result, ttl=CACHE_TTL)

        return result

    except Exception as e:
        print("Exception:", e)
        return _fallback(spot)


def _fallback(spot):
    return {
        "spot": spot["name"],
        "wave": DEFAULT_DATA["wave"],
        "period": DEFAULT_DATA["period"],
        "wind": "unknown",
        "wind_speed": DEFAULT_DATA["wind_speed"],
        "swell_dir": None,
        "tide": _fake_tide_by_time(),
        "best_time": None,
    }


# ======================
# API COUNTER
# ======================

def increment_api_calls():
    count = get_cache(API_COUNTER_KEY) or 0
    count += 1
    set_cache(API_COUNTER_KEY, count, ttl=86400)


# ======================
# BEST TIME (3h RANGE)
# ======================

def get_best_time(hours, spot):
    scored_hours = []

    for h in hours[:12]:
        time_str = h.get("time")

        if not time_str:
            continue

        try:
            hour = int(time_str[11:13])
        except:
            continue

        # только дневное время
        if hour < 5 or hour > 19:
            continue

        parsed = _parse_hour(h)

        wave = parsed["wave"] * spot.get("wave_factor", 1)
        period = parsed["period"]
        wind = _get_wind_type(parsed["wind_direction"], spot["offshore"])

        score = 0
        score += wave * 2
        score += period * 0.5

        if wind == "offshore":
            score += 3
        elif wind == "cross":
            score += 1
        elif wind == "onshore":
            score -= 3

        scored_hours.append({
            "time": time_str,
            "hour": hour,
            "score": score
        })

    if len(scored_hours) < 3:
        return None

    best_block = None
    best_score = -999

    for i in range(len(scored_hours) - 2):
        h1 = scored_hours[i]
        h2 = scored_hours[i + 1]
        h3 = scored_hours[i + 2]

        # подряд
        if not (
            h2["hour"] == h1["hour"] + 1 and
            h3["hour"] == h2["hour"] + 1
        ):
            continue

        score = h1["score"] + h2["score"] + h3["score"]

        # фильтр мусора
        if score < 6:
            continue

        if score > best_score:
            best_score = score
            best_block = [h1, h2, h3]

    if not best_block:
        return None

    try:
        start = best_block[0]["time"][11:16]
        end = best_block[-1]["time"][11:16]
        return f"{start}–{end}"
    except:
        return None