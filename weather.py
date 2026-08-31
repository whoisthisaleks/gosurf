import aiohttp
import os
import logging
from cache import get_cache, set_cache

API_KEY = os.getenv("STORMGLASS_API_KEY")

BASE_URL = "https://api.stormglass.io/v2/weather/point"
PARAMS = "waveHeight,wavePeriod,waveDirection,windSpeed"


async def fetch_weather(lat, lng):
    cache_key = f"{lat}_{lng}"
    cached = get_cache(cache_key)

    if cached:
        return cached

    if not API_KEY:
        logging.warning("No Stormglass API key, using fallback")
        return fallback()

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                BASE_URL,
                params={
                    "lat": lat,
                    "lng": lng,
                    "params": PARAMS
                },
                headers={"Authorization": API_KEY},
                timeout=aiohttp.ClientTimeout(total=8)
            ) as resp:

                if resp.status != 200:
                    logging.warning(f"Stormglass error: {resp.status}")
                    return fallback()

                data = await resp.json()

                if "hours" not in data or not data["hours"]:
                    return fallback()

                h = data["hours"][0]

                result = {
                    "wave": h.get("waveHeight", {}).get("sg", 0),
                    "period": h.get("wavePeriod", {}).get("sg", 0),
                    "direction": h.get("waveDirection", {}).get("sg", 0),
                    "wind": h.get("windSpeed", {}).get("sg", 0),
                }

                set_cache(cache_key, result)
                return result

    except Exception:
        logging.exception("WEATHER_ERROR")
        return fallback()


def fallback():
    return {
        "wave": 1.2,
        "period": 10,
        "direction": 180,
        "wind": 5
    }