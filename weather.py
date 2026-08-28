import os
import json
import time
import logging
import requests

from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from dotenv import load_dotenv

from spots import SPOTS


logging.basicConfig(
    level=logging.INFO
)

logger = logging.getLogger(__name__)


load_dotenv()


API_KEY = os.getenv("STORMGLASS_API_KEY")


CACHE_FILE = "stormglass_cache.json"

CACHE_TIME = 60 * 60  # 1 hour

LOCAL_TIMEZONE = ZoneInfo("Asia/Makassar")



# -------------------------
# Helpers
# -------------------------


def deg_to_direction(deg):

    if deg is None:
        return "unknown"


    directions = [
        "N",
        "NE",
        "E",
        "SE",
        "S",
        "SW",
        "W",
        "NW"
    ]


    index = round(deg / 45) % 8

    return directions[index]


def format_local_time(timestamp):

    try:
        forecast_time = datetime.fromisoformat(
            timestamp.replace("Z", "+00:00")
        )

        if forecast_time.tzinfo is None:
            forecast_time = forecast_time.replace(tzinfo=timezone.utc)

        return forecast_time.astimezone(LOCAL_TIMEZONE).strftime("%H:%M")

    except (AttributeError, TypeError, ValueError):
        return None


def get_hour_value(hour, parameter):

    values = hour.get(parameter)

    if not isinstance(values, dict):
        return None

    return values.get("sg")


def build_hour_conditions(hour):

    if not isinstance(hour, dict):
        return None

    local_time = format_local_time(hour.get("time"))
    height = get_hour_value(hour, "waveHeight")
    period = get_hour_value(hour, "wavePeriod")
    direction = get_hour_value(hour, "waveDirection")
    wind_speed = get_hour_value(hour, "windSpeed")
    wind_direction = get_hour_value(hour, "windDirection")

    if (
            local_time is None
            or height is None
            or period is None
            or direction is None
            or wind_speed is None
            or wind_direction is None
    ):
        return None

    return {
        "time": local_time,
        "wave_height": round(height, 1) if height else 0,
        "period": round(period, 1) if period else 0,
        "swell_direction": deg_to_direction(direction),
        "wind_speed": float(round(wind_speed, 1)),
        "wind_direction": deg_to_direction(wind_direction),
        "source": "stormglass"
    }


def build_fallback_hours():

    start_time = datetime.now(LOCAL_TIMEZONE).replace(
        minute=0,
        second=0,
        microsecond=0
    )

    return [
        {
            "time": (start_time + timedelta(hours=offset)).strftime("%H:%M"),
            "wave_height": 1.0,
            "period": 12,
            "swell_direction": "SW",
            "wind_speed": 0.0,
            "wind_direction": "unknown",
            "source": "fallback"
        }
        for offset in range(24)
    ]



def load_cache():

    if not os.path.exists(CACHE_FILE):
        return None


    with open(
        CACHE_FILE,
        "r"
    ) as file:

        return json.load(file)



def save_cache(data):

    with open(
        CACHE_FILE,
        "w"
    ) as file:

        json.dump(
            {
                "timestamp": time.time(),
                "data": data
            },
            file,
            indent=2
        )



# -------------------------
# Stormglass
# -------------------------


def get_spot_hourly_forecast(
        spot_name,
        lat,
        lng
):


    url = (
        "https://api.stormglass.io/v2/"
        "weather/point"
    )


    params = {

        "lat": lat,

        "lng": lng,

        "params":
            "waveHeight,"
            "wavePeriod,"
            "waveDirection,"
            "windSpeed,"
            "windDirection"

    }


    headers = {

        "Authorization": API_KEY

    }



    try:

        response = requests.get(
            url,
            params=params,
            headers=headers,
            timeout=10
        )

        if response is None:
            logger.error("Stormglass returned no response for %s", spot_name)
            return None


        data = response.json()


        if not isinstance(data, dict):
            logger.error("Stormglass returned invalid data for %s", spot_name)
            return None


        if "errors" in data:

            logger.error(
                "Stormglass returned errors for %s: %s",
                spot_name,
                data["errors"]
            )

            return None



        hours = data.get("hours")

        if not isinstance(hours, list) or len(hours) < 24:
            logger.warning(
                "Stormglass returned fewer than 24 forecast hours for %s",
                spot_name
            )
            return None


        forecast = []

        for hour in hours[:24]:
            conditions = build_hour_conditions(hour)

            if conditions is None:
                logger.warning(
                    "Stormglass returned incomplete forecast data for %s",
                    spot_name
                )
                return None

            forecast.append(conditions)


        return forecast



    except Exception as error:

        logger.error(
            "Stormglass request failed for %s: %s",
            spot_name,
            error
        )

        return None


def get_spot_forecast(
        spot_name,
        lat,
        lng
):

    hourly_forecast = get_spot_hourly_forecast(
        spot_name,
        lat,
        lng
    )

    if not hourly_forecast:
        return None

    return hourly_forecast[0]



# -------------------------
# Main
# -------------------------


def build_hourly_forecast():


    cache = load_cache()



    if cache:

        age = (
            time.time()
            -
            cache["timestamp"]
        )


        cached_data = cache.get("data")

        has_source = (
            isinstance(cached_data, dict)
            and all(
                isinstance(hours, list)
                and len(hours) >= 24
                and all(
                    isinstance(conditions, dict)
                    and "source" in conditions
                    for conditions in hours[:24]
                )
                for hours in cached_data.values()
            )
        )

        has_wind = (
            isinstance(cached_data, dict)
            and all(
                isinstance(hours, list)
                and len(hours) >= 24
                and all(
                    isinstance(conditions, dict)
                    and "wind_speed" in conditions
                    and "wind_direction" in conditions
                    for conditions in hours[:24]
                )
                for hours in cached_data.values()
            )
        )

        if age < CACHE_TIME and has_source and has_wind:

            logger.info(
                "Cache hit: %s min old",
                int(age / 60)
            )

            return cached_data


        if age < CACHE_TIME:
            logger.warning(
                "Cache has no complete hourly forecast and will be refreshed"
            )



    logger.info("Fetching new Stormglass data")


    forecast = {}



    for spot, data in SPOTS.items():


        result = get_spot_hourly_forecast(
            spot,
            data["lat"],
            data["lng"]
        )



        if result:

            forecast[spot] = result


        else:

            forecast[spot] = build_fallback_hours()



    save_cache(
        forecast
    )


    return forecast


def build_forecast():

    hourly_forecast = build_hourly_forecast()

    return {
        spot: hours[0]
        for spot, hours in hourly_forecast.items()
    }
