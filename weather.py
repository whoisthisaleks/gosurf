import os
import time
import logging
import requests
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from dotenv import load_dotenv

from spots import SPOTS

# -------------------------
# CONFIG
# -------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

API_KEY = os.getenv("STORMGLASS_API_KEY")

CACHE_TIME = 60 * 60
LOCAL_TIMEZONE = ZoneInfo("Asia/Makassar")

MEM_CACHE = {
    "timestamp": 0,
    "data": None
}

API_USAGE = {
    "count": 0,
    "day": datetime.now().date()
}


def track_api_usage():
    global API_USAGE

    today = datetime.now().date()

    if API_USAGE["day"] != today:
        API_USAGE = {
            "count": 0,
            "day": today
        }

    API_USAGE["count"] += 1
    logger.info(f"API calls today: {API_USAGE['count']}")


# -------------------------
# HELPERS
# -------------------------
def deg_to_direction(deg):
    if deg is None:
        return "unknown"

    directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
    return directions[round(deg / 45) % 8]


def format_local_time(timestamp):
    try:
        dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(LOCAL_TIMEZONE).strftime("%H:%M")
    except Exception:
        return None


def get_hour_value(hour, param):
    values = hour.get(param)
    if not isinstance(values, dict):
        return None
    return values.get("sg")


def build_hour_conditions(hour):
    if not isinstance(hour, dict):
        return None

    time_local = format_local_time(hour.get("time"))

    height = get_hour_value(hour, "waveHeight")
    period = get_hour_value(hour, "wavePeriod")
    direction = get_hour_value(hour, "waveDirection")
    wind_speed = get_hour_value(hour, "windSpeed")
    wind_direction = get_hour_value(hour, "windDirection")
    tide = get_hour_value(hour, "waterLevel")

    if None in (time_local, height, period, direction, wind_speed, wind_direction):
        return None

    return {
        "time": time_local,
        "wave_height": round(height, 1),
        "period": round(period, 1),
        "swell_direction": deg_to_direction(direction),
        "wind_speed": round(wind_speed, 1),
        "wind_direction": deg_to_direction(wind_direction),
        "tide": round(tide, 2) if tide is not None else None,
        "source": "stormglass"
    }


def build_fallback_hours():
    start = datetime.now(LOCAL_TIMEZONE).replace(minute=0, second=0, microsecond=0)

    return [
        {
            "time": (start + timedelta(hours=i)).strftime("%H:%M"),
            "wave_height": 1.0,
            "period": 12,
            "swell_direction": "SW",
            "wind_speed": 0.0,
            "wind_direction": "unknown",
            "tide": None,
            "source": "fallback"
        }
        for i in range(24)
    ]


# -------------------------
# API
# -------------------------
def get_spot_hourly_forecast(spot, lat, lng):
    url = "https://api.stormglass.io/v2/weather/point"

    params = {
        "lat": lat,
        "lng": lng,
        "params": ",".join([
            "waveHeight",
            "wavePeriod",
            "waveDirection",
            "windSpeed",
            "windDirection",
            "waterLevel"
        ])
    }

    headers = {
        "Authorization": API_KEY
    }

    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)

        track_api_usage()

        if response.status_code != 200:
            logger.error("Stormglass error %s for %s", response.status_code, spot)
            return None

        data = response.json()
        hours = data.get("hours")

        if not isinstance(hours, list) or len(hours) < 24:
            return None

        result = []

        for hour in hours[:24]:
            cond = build_hour_conditions(hour)
            if cond is None:
                return None
            result.append(cond)

        return result

    except Exception as e:
        logger.error("Stormglass failed for %s: %s", spot, e)
        return None


# -------------------------
# MAIN
# -------------------------
def build_hourly_forecast():
    global MEM_CACHE

    now = time.time()

    if MEM_CACHE["data"] and now - MEM_CACHE["timestamp"] < CACHE_TIME:
        logger.info("Memory cache hit")
        return MEM_CACHE["data"]

    logger.info("Fetching Stormglass data")

    forecast = {}

    for spot, data in SPOTS.items():
        result = get_spot_hourly_forecast(spot, data["lat"], data["lng"])

        if result:
            forecast[spot] = result
        else:
            forecast[spot] = build_fallback_hours()

    MEM_CACHE = {
        "timestamp": now,
        "data": forecast
    }

    return forecast


def build_forecast():
    hourly = build_hourly_forecast()

    return {
        spot: hours[0]
        for spot, hours in hourly.items()
    }