import os
import json
import time
import logging
import requests

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


def get_spot_forecast(
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
            "waveDirection"

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

        if not isinstance(hours, list) or not hours:
            logger.warning(
                "Stormglass returned no forecast hours for %s",
                spot_name
            )
            return None


        hour = hours[0]

        if not isinstance(hour, dict):
            logger.warning(
                "Stormglass returned an invalid forecast hour for %s",
                spot_name
            )
            return None



        height = (
            hour
            .get("waveHeight", {})
            .get("sg")
        )


        period = (
            hour
            .get("wavePeriod", {})
            .get("sg")
        )


        direction = (
            hour
            .get("waveDirection", {})
            .get("sg")
        )


        if height is None or period is None or direction is None:
            logger.warning(
                "Stormglass returned incomplete forecast data for %s",
                spot_name
            )
            return None


        return {

            "wave_height":
                round(height, 1)
                if height
                else 0,


            "period":
                round(period, 1)
                if period
                else 0,


            "swell_direction":
                deg_to_direction(direction),


            "source": "stormglass"

        }



    except Exception as error:

        logger.error(
            "Stormglass request failed for %s: %s",
            spot_name,
            error
        )

        return None



# -------------------------
# Main
# -------------------------


def build_forecast():


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
                isinstance(conditions, dict)
                and "source" in conditions
                for conditions in cached_data.values()
            )
        )

        if age < CACHE_TIME and has_source:

            logger.info(
                "Cache hit: %s min old",
                int(age / 60)
            )

            return cached_data


        if age < CACHE_TIME:
            logger.warning(
                "Cache has no source field and will be refreshed"
            )



    logger.info("Fetching new Stormglass data")


    forecast = {}



    for spot, data in SPOTS.items():


        result = get_spot_forecast(
            spot,
            data["lat"],
            data["lng"]
        )



        if result:

            forecast[spot] = result


        else:

            # fallback
            forecast[spot] = {

                "wave_height": 1.0,

                "period": 12,

                "swell_direction": "SW",

                "source": "fallback"

            }



    save_cache(
        forecast
    )


    return forecast
