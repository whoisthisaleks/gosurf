import aiohttp
import asyncio
import time

from config import STORMGLASS_API_KEY


CACHE = {}
CACHE_TTL = 600  # 10 минут


def _cache_key(lat, lng):
    return f"{lat}:{lng}"


async def get_surf_data(spot: dict) -> dict:
    lat = spot["lat"]
    lng = spot["lng"]

    key = _cache_key(lat, lng)

    # ===== CACHE HIT =====
    if key in CACHE:
        cached = CACHE[key]
        if time.time() - cached["time"] < CACHE_TTL:
            print(f"[CACHE HIT] {spot['name']}")
            return cached["data"]

    url = "https://api.stormglass.io/v2/weather/point"

    params = {
        "lat": lat,
        "lng": lng,
        "params": "waveHeight,wavePeriod,windSpeed,windDirection"
    }

    headers = {
        "Authorization": STORMGLASS_API_KEY
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, headers=headers, timeout=10) as response:

                if response.status != 200:
                    print(f"[ERROR] Stormglass status: {response.status}")
                    return empty_data()

                data = await response.json()

    except asyncio.TimeoutError:
        print("[ERROR] Timeout from Stormglass")
        return empty_data()

    except Exception as e:
        print(f"[ERROR] Request failed: {e}")
        return empty_data()

    # ===== PARSE =====

    hours = data.get("hours")

    if not hours:
        print("[ERROR] No hours in response")
        return empty_data()

    hour = hours[0]

    def safe_get(param):
        try:
            return round(hour[param]["sg"], 2)
        except:
            return None

    result = {
        "wave_height": safe_get("waveHeight"),
        "period": safe_get("wavePeriod"),
        "wind_speed": safe_get("windSpeed"),
        "wind_direction": safe_get("windDirection"),
    }

    # ===== CACHE SAVE =====
    CACHE[key] = {
        "time": time.time(),
        "data": result
    }

    print(f"[API] {spot['name']} -> {result}")

    return result


def empty_data():
    return {
        "wave_height": None,
        "period": None,
        "wind_speed": None,
        "wind_direction": None
    }