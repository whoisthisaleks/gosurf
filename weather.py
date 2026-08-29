import aiohttp
import asyncio
import time
import logging
from config import STORMGLASS_API_KEY

logger = logging.getLogger(__name__)

# ===== CONFIG =====
CACHE_TTL = 900  # 15 минут
LAT = -8.65   # Bali
LNG = 115.13

# ===== CACHE =====
_cache = {
    "data": None,
    "timestamp": 0
}


# ===== HELPERS =====

def is_cache_valid():
    return time.time() - _cache["timestamp"] < CACHE_TTL


def save_cache(data):
    _cache["data"] = data
    _cache["timestamp"] = time.time()


# ===== API =====

async def fetch_weather():
    url = "https://api.stormglass.io/v2/weather/point"

    params = {
        "lat": LAT,
        "lng": LNG,
        "params": "waveHeight,wavePeriod,windSpeed,windDirection",
        "hours": 12
    }

    headers = {
        "Authorization": STORMGLASS_API_KEY
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, headers=headers) as resp:

                if resp.status != 200:
                    text = await resp.text()
                    logger.error(f"Stormglass error {resp.status}: {text}")
                    return None

                data = await resp.json()
                return data

    except Exception as e:
        logger.exception("Stormglass request failed")
        return None


# ===== PUBLIC =====

async def get_weather():
    # 1. если кеш жив — возвращаем
    if _cache["data"] and is_cache_valid():
        logger.info("Weather: cache hit")
        return _cache["data"]

    logger.info("Weather: fetching new data")

    # 2. пробуем получить новые данные
    fresh = await fetch_weather()

    if fresh:
        save_cache(fresh)
        return fresh

    # 3. fallback — отдаем старые данные
    if _cache["data"]:
        logger.warning("Using stale cache (Stormglass failed)")
        return _cache["data"]

    # 4. полный фейл
    logger.error("No weather data available")
    return None