import aiohttp
import asyncio
import time

from config import STORMGLASS_API_KEY

# ===== CONFIG =====

STORMGLASS_URL = "https://api.stormglass.io/v2/weather/point"
PARAMS = "waveHeight,wavePeriod,windSpeed,windDirection"

CACHE_TTL = 600  # 10 minutes
_cache = {}


# ===== CACHE =====

def _cache_key(lat: float, lng: float) -> str:
    return f"{round(lat, 3)}:{round(lng, 3)}"


def _get_cached(key: str):
    data = _cache.get(key)
    if not data:
        return None

    if time.time() - data["ts"] > CACHE_TTL:
        return None

    return data["value"]


def _set_cache(key: str, value: dict):
    _cache[key] = {
        "ts": time.time(),
        "value": value
    }


# ===== HELPERS =====

def _extract_hour(data: dict) -> dict | None:
    try:
        hours = data.get("hours", [])
        if not hours:
            return None
        return hours[0]
    except Exception:
        return None


def _safe_get(metric: dict | None):
    if not metric:
        return None

    # приоритет Stormglass (sg), fallback на noaa если есть
    return metric.get("sg") or metric.get("noaa")


def _round(val):
    if val is None:
        return None
    return round(val, 2)


# ===== MAIN =====

async def get_surf_data(spot: dict) -> dict:
    """
    spot = {
        "name": "Uluwatu",
        "lat": -8.829,
        "lng": 115.084
    }
    """

    lat = spot["lat"]
    lng = spot["lng"]

    key = _cache_key(lat, lng)

    # ===== CACHE HIT =====
    cached = _get_cached(key)
    if cached:
        print(f"[CACHE HIT] {spot['name']}")
        return cached

    print(f"[API CALL] {spot['name']}")

    headers = {
        "Authorization": STORMGLASS_API_KEY
    }

    params = {
        "lat": lat,
        "lng": lng,
        "params": PARAMS
    }

    try:
        timeout = aiohttp.ClientTimeout(total=10)

        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(STORMGLASS_URL, headers=headers, params=params) as resp:

                # ===== QUOTA / HTTP ERRORS =====
                if resp.status != 200:
                    text = await resp.text()
                    print(f"[ERROR] Stormglass {resp.status}: {text}")

                    # fallback
                    result = {
                        "wave_height": None,
                        "period": None,
                        "wind_speed": None,
                        "wind_direction": None
                    }

                    _set_cache(key, result)
                    return result

                data = await resp.json()

    except asyncio.TimeoutError:
        print("[ERROR] Stormglass timeout")

        result = {
            "wave_height": None,
            "period": None,
            "wind_speed": None,
            "wind_direction": None
        }

        _set_cache(key, result)
        return result

    except Exception as e:
        print(f"[ERROR] Stormglass exception: {e}")

        result = {
            "wave_height": None,
            "period": None,
            "wind_speed": None,
            "wind_direction": None
        }

        _set_cache(key, result)
        return result

    # ===== PARSE =====

    hour = _extract_hour(data)

    if not hour:
        print("[ERROR] No hours data")

        result = {
            "wave_height": None,
            "period": None,
            "wind_speed": None,
            "wind_direction": None
        }

        _set_cache(key, result)
        return result

    result = {
        "wave_height": _round(_safe_get(hour.get("waveHeight"))),
        "period": _round(_safe_get(hour.get("wavePeriod"))),
        "wind_speed": _round(_safe_get(hour.get("windSpeed"))),
        "wind_direction": _round(_safe_get(hour.get("windDirection")))
    }

    # ===== CACHE SAVE =====
    _set_cache(key, result)

    return result