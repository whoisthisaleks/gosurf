import requests
from datetime import datetime, timedelta
from config import STORMGLASS_API_KEY
from cache import get_cache, set_cache

BASE_URL = "https://api.stormglass.io/v2/weather/point"

DEFAULT_DATA = {
    "wave": 0.8,
    "period": 8,
    "wind_speed": 5,
    "wind_direction": 0,
}


# ======================
# SAFE HELPERS
# ======================

def _safe_get(d, path, default=None):
    try:
        for p in path:
            d = d[p]
        return d
    except (KeyError, TypeError, IndexError):
        return default


def _parse_hour(hour):
    return {
        "wave": _safe_get(hour, ["waveHeight", "sg"], DEFAULT_DATA["wave"]),
        "period": _safe_get(hour, ["wavePeriod", "sg"], DEFAULT_DATA["period"]),
        "wind_speed": _safe_get(hour, ["windSpeed", "sg"], DEFAULT_DATA["wind_speed"]),
        "wind_direction": _safe_get(hour, ["windDirection", "sg"], DEFAULT_DATA["wind_direction"]),
        "wave_direction": _safe_get(hour, ["waveDirection", "sg"], None),
    }


# ======================
# WIND (PER SPOT)
# ======================

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


# ======================
# MAIN
# ======================

def fetch_spot_weather(spot):
    cache_key = f"weather:{spot['name']}"
    cached = get_cache(cache_key)

    if cached:
        return cached

    now = datetime.utcnow()
    later = now + timedelta(hours=1)

    params = {
        "lat": spot["lat"],
        "lng": spot["lng"],
        "params": "waveHeight,wavePeriod,windSpeed,windDirection,waveDirection",
        "start": now.isoformat(),
        "end": later.isoformat(),
    }

    headers = {
        "Authorization": STORMGLASS_API_KEY
    }

    try:
        response = requests.get(BASE_URL, params=params, headers=headers, timeout=10)

        print(f"{spot['name']} status:", response.status_code)

        if response.status_code != 200:
            print("Bad response:", response.text[:200])
            return _fallback(spot)

        data = response.json()

        # API errors
        if "errors" in data:
            print("Stormglass ERROR:", data["errors"])
            return _fallback(spot)

        hours = data.get("hours")

        if not hours:
            print("No hours data")
            return _fallback(spot)

        parsed = _parse_hour(hours[0])

        result = {
            "spot": spot["name"],
            "wave": round(parsed["wave"], 1),
            "period": int(parsed["period"]),
            "wind": _get_wind_type(
                parsed["wind_direction"],
                spot["offshore"]
            ),
            "wind_speed": parsed["wind_speed"],
            "swell_dir": parsed["wave_direction"],
        }

        print(f"{spot['name']} -> {result}")

        # cache (без ttl)
        set_cache(cache_key, result)

        return result

    except Exception as e:
        print("Exception:", e)
        return _fallback(spot)


# ======================
# FALLBACK
# ======================

def _fallback(spot):
    print(f"{spot['name']} -> FALLBACK")

    return {
        "spot": spot["name"],
        "wave": DEFAULT_DATA["wave"],
        "period": DEFAULT_DATA["period"],
        "wind": "unknown",
        "wind_speed": DEFAULT_DATA["wind_speed"],
        "swell_dir": None,
    }