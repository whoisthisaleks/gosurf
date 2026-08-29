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

CACHE_TIME = 60 * 30  # 30 мин оптимально
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
def get_best_source(values: dict):
    """Берем первый доступный источник"""
    if not isinstance(values, dict):
        return None

    for source in ["sg", "noaa", "icon", "meteo"]:
        if source in values and values[source] is not None:
            return values[source]

    return None


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


def build_hour_conditions(hour):
    if not isinstance(hour, dict):
        return None

    time_local = format_local_time(hour.get("time"))

    if time_local is None:
        return None

    height = get_best_source(hour.get("waveHeight"))
    period = get_best_source(hour.get("wavePeriod"))
    direction = get_best_source(hour.get("waveDirection"))
    wind_speed = get_best_source(hour.get("windSpeed"))
    wind_direction = get_best_source(hour.get("windDirection"))
    tide = get_best_source(hour.get("waterLevel"))

    # ❗ НЕ ломаем если часть данных отсутствует
    return {
        "time": time_local,
        "wave_height": round(height, 1) if height else None,
        "period": round(period, 1) if period else None,
        "swell_direction": deg_to_direction(direction) if direction else "unknown",
        "wind_speed": round(wind_speed, 1) if wind_speed else None,
        "wind_direction": deg_to_direction(wind_direction) if wind_direction else "unknown",
        "tide": round(tide, 2) if tide else None,
        "is_partial": any(v is None for v in [height, period, wind_speed])
    }


def build_fallback_hours():
    logger.warning("Using FULL fallback data")

    start = datetime.now(LOCAL_TIMEZONE).replace(minute=0, second=0, microsecond=0)

    return [
        {
            "time": (start + timedelta(hours=i)).strftime("%H:%M"),
            "wave_height": 1.0,
            "period": 12,
            "swell_direction": "SW",
            "wind_speed": None,
            "wind_direction": "unknown",
            "tide": None,
            "is_partial": True,
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
            logger.error(f"{spot}: Stormglass error {response.status_code}")
            return None

        data = response.json()
        hours = data.get("hours")

        if not isinstance(hours, list) or len(hours) < 24:
            logger.warning(f"{spot}: not enough data")
            return None

        result = []

        for hour in hours[:24]:
            cond = build_hour_conditions(hour)

            if cond is None:
                continue  # ❗ пропускаем, но не ломаем

            result.append(cond)

        if len(result) < 12:
            logger.warning(f"{spot}: too many missing hours")
            return None

        return result

    except Exception as e:
        logger.error(f"{spot}: request failed {e}")
        return None


# -------------------------
# MAIN
# -------------------------
def build_hourly_forecast():
    global MEM_CACHE

    now = time.time()

    if MEM_CACHE["data"] and now - MEM_CACHE["timestamp"] < CACHE_TIME:
        logger.info("Cache hit (memory)")
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