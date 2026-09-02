import aiohttp
import asyncio
import time
from datetime import datetime, timezone

from config import STORMGLASS_API_KEY

# ===== CACHE =====
CACHE = {}
TTL = 600  # 10 минут


def _cache_key(lat, lng):
    return f"{lat}:{lng}"


# ===== MAIN FUNCTION =====
async def get_surf_data(spot: dict) -> dict:
    lat = spot["lat"]
    lng = spot["lng"]

    key = _cache_key(lat, lng)

    # ===== CACHE HIT =====
    if key in CACHE:
        cached = CACHE[key]
        if time.time() - cached["time"] < TTL:
            print(f"[CACHE HIT] {spot['name']}")
            return cached["data"]

    print(f"[API REQUEST] {spot['name']}")

    url = "https://api.stormglass.io/v2/weather/point"

    params = {
        "lat": lat,
        "lng": lng,
        "params": "waveHeight,wavePeriod,windSpeed,windDirection",
        "source": "sg",
    }

    headers = {
        "Authorization": STORMGLASS_API_KEY
    }

    try:
        timeout = aiohttp.ClientTimeout(total=10)

        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url, params=params, headers=headers) as resp:

                if resp.status != 200:
                    print(f"[ERROR] Status: {resp.status}")
                    return None

                data = await resp.json()

                hours = data.get("hours")

                if not hours:
                    print("[ERROR] No hours data")
                    return None

                # ===== ВЫБОР БЛИЖАЙШЕГО ЧАСА =====
                now = datetime.now(timezone.utc)

                closest_hour = min(
                    hours,
                    key=lambda h: abs(
                        datetime.fromisoformat(h["time"].replace("Z", "+00:00")) - now
                    )
                )

                def safe_extract(param):
                    value = closest_hour.get(param, {})
                    if isinstance(value, dict):
                        return value.get("sg")
                    return None

                result = {
                    "wave_height": round(safe_extract("waveHeight") or 0, 2),
                    "period": round(safe_extract("wavePeriod") or 0, 1),
                    "wind_speed": round(safe_extract("windSpeed") or 0, 2),
                    "wind_direction": round(safe_extract("windDirection") or 0, 0),
                }

                # ===== CACHE SAVE =====
                CACHE[key] = {
                    "time": time.time(),
                    "data": result
                }

                return result

    except asyncio.TimeoutError:
        print("[ERROR] Timeout")
        return None

    except Exception as e:
        print(f"[ERROR] {e}")
        return None