import os
import time
import requests
from datetime import datetime

API_KEY = os.getenv("STORMGLASS_API_KEY")

CACHE = {
    "time": 0,
    "data": None
}

CACHE_TTL = 60 * 30  # 30 min


SPOTS = {
    "Uluwatu": {"lat": -8.829, "lng": 115.084},
    "Canggu": {"lat": -8.648, "lng": 115.138},
    "Kuta": {"lat": -8.717, "lng": 115.168},
    "Medewi": {"lat": -8.426, "lng": 114.787},
}


def fetch_spot(lat, lng):
    url = "https://api.stormglass.io/v2/weather/point"

    params = {
        "lat": lat,
        "lng": lng,
        "params": "waveHeight,wavePeriod,waveDirection,windSpeed,windDirection,waterLevel"
    }

    headers = {
        "Authorization": API_KEY
    }

    try:
        r = requests.get(url, params=params, headers=headers, timeout=10)

        if r.status_code != 200:
            return None

        data = r.json()["hours"][0]

        def val(p):
            return data.get(p, {}).get("sg")

        return {
            "wave_height": round(val("waveHeight") or 0, 1),
            "period": round(val("wavePeriod") or 0, 1),
            "swell_direction": "SW",
            "wind_speed": round(val("windSpeed") or 0, 1),
            "wind_direction": "E",
            "tide": round(val("waterLevel"), 2) if val("waterLevel") else None,
            "source": "stormglass"
        }

    except:
        return None


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


def build_forecast():
    now = time.time()

    if CACHE["data"] and now - CACHE["time"] < CACHE_TTL:
        return CACHE["data"]

    forecast = {}

    for spot, coords in SPOTS.items():
        data = fetch_spot(coords["lat"], coords["lng"])
        forecast[spot] = data if data else fallback()

    CACHE["time"] = now
    CACHE["data"] = forecast

    return forecast