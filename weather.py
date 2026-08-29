import os
import time
import logging
import requests
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

API_KEY = os.getenv("STORMGLASS_API_KEY")

CACHE = {
    "time": 0,
    "data": None
}

CACHE_TTL = 60 * 20  # 20 минут

SPOTS = {
    "Uluwatu": {"lat": -8.829, "lng": 115.084},
    "Canggu": {"lat": -8.648, "lng": 115.138},
    "Kuta": {"lat": -8.717, "lng": 115.168},
    "Medewi": {"lat": -8.426, "lng": 114.787},
}


# -------------------------
# HELPERS
# -------------------------
def deg_to_direction(deg):
    if deg is None:
        return "unknown"
    directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
    return directions[round(deg / 45) % 8]


def safe_val(data, key):
    return data.get(key, {}).get("sg")


# -------------------------
# API (ОДИН ЗАПРОС)
# -------------------------
def fetch_all_spots():
    url = "https://api.stormglass.io/v2/weather/point"

    # Берём центральную точку Бали (чтобы покрыть все споты)
    lat = -8.65
    lng = 115.10

    params = {
        "lat": lat,
        "lng": lng,
        "params": "waveHeight,wavePeriod,waveDirection,windSpeed,windDirection,waterLevel"
    }

    headers = {"Authorization": API_KEY}

    try:
        logger.info("🌊 Stormglass API request")

        r = requests.get(url, params=params, headers=headers, timeout=10)

        if r.status_code != 200:
            logger.error(f"Stormglass error: {r.status_code}")
            return None

        data = r.json()
        hour = data["hours"][0]

        base = {
            "wave_height": round(safe_val(hour, "waveHeight") or 0, 1),
            "period": round(safe_val(hour, "wavePeriod") or 0, 1),
            "swell_direction": deg_to_direction(safe_val(hour, "waveDirection")),
            "wind_speed": round(safe_val(hour, "windSpeed") or 0, 1),
            "wind_direction": deg_to_direction(safe_val(hour, "windDirection")),
            "tide": round(safe_val(hour, "waterLevel"), 2) if safe_val(hour, "waterLevel") else None,
            "source": "stormglass"
        }

        return base

    except Exception as e:
        logger.error(f"Stormglass failed: {e}")
        return None


# -------------------------
# FALLBACK
# -------------------------
def fallback():
    return {
        "wave_height": 1.0,
        "period": 10,
        "swell_direction": "SW",
        "wind_speed": 3,
        "wind_direction": "E",
        "tide": None,
        "source": "fallback"
    }


# -------------------------
# MAIN
# -------------------------
def build_forecast():
    now = time.time()

    # CACHE HIT
    if CACHE["data"] and now - CACHE["time"] < CACHE_TTL:
        logger.info("⚡ Cache hit")
        return CACHE["data"]

    logger.info("🚀 Fetching new data")

    base = fetch_all_spots()

    forecast = {}

    for spot in SPOTS.keys():
        forecast[spot] = base if base else fallback()

    CACHE["time"] = now
    CACHE["data"] = forecast

    return forecast