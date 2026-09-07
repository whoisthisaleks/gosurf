import requests
import math
from datetime import datetime, timedelta, timezone
from config import STORMGLASS_API_KEY
from cache import get_cache, set_cache

BASE_URL = "https://api.stormglass.io/v2/weather/point"

CACHE_TTL = 3600  # 1 час

DEFAULT_DATA = {
    "wave": 0.8,
    "period": 8,
    "wind_speed": 5,
    "wind_direction": 0,
}


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


def fetch_spot_weather(spot):
    cache_key = f"weather:{spot['name']}"

    cached = get_cache(cache_key)
    if cached:
        return cached

    now = datetime.now(timezone.utc)
    later = now + timedelta(hours=1)

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

        print(f"{spot['name']} status:", response.status_code)

        if response.status_code != 200:
            return _fallback(spot)

        data = response.json()
        hours = data.get("hours")

        if not hours:
            return _fallback(spot)

        parsed = _parse_hour(hours[0])

        wave = parsed["wave"] * spot.get("wave_factor", 1)

        result = {
            "spot": spot["name"],
            "wave": round(wave, 1),
            "period": int(parsed["period"]),
            "wind": _get_wind_type(parsed["wind_direction"], spot["offshore"]),
            "wind_speed": parsed["wind_speed"],
            "swell_dir": parsed["wave_direction"],
            "tide": _fake_tide_by_time(),
        }

        # 🔥 КЭШ НА 1 ЧАС
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
    }