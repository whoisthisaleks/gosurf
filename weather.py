import requests
from datetime import datetime
from config import STORMGLASS_API_KEY
from spots import SPOTS

STORM_URL = "https://api.stormglass.io/v2/weather/point"

PARAMS = ",".join([
    "waveHeight",
    "wavePeriod",
    "windSpeed",
])

HEADERS = {
    "Authorization": STORMGLASS_API_KEY
}


def get_spots_data():
    results = []

    for spot in SPOTS:
        try:
            response = requests.get(
                STORM_URL,
                params={
                    "lat": spot["lat"],
                    "lng": spot["lng"],
                    "params": PARAMS,
                },
                headers=HEADERS,
                timeout=10
            )

            data = response.json()

            # защита от пустого ответа
            if "hours" not in data or not data["hours"]:
                continue

            current = data["hours"][0]

            # безопасное извлечение значений
            wave = _extract(current, "waveHeight")
            period = _extract(current, "wavePeriod")
            wind = _extract(current, "windSpeed")

            spot_data = {
                "name": spot["name"],
                "wave": round(wave, 1) if wave else 0,
                "period": round(period, 1) if period else 0,
                "wind": round(wind, 1) if wind else 0,
            }

            results.append(spot_data)

        except Exception as e:
            print(f"Weather error for {spot['name']}: {e}")
            continue

    return results


def _extract(hour_data, key):
    """
    Stormglass возвращает значения из разных источников.
    Берём первый доступный.
    """
    if key not in hour_data:
        return None

    sources = hour_data[key]

    # приоритет источников (можешь поменять позже)
    priority = ["sg", "noaa", "dwd", "icon"]

    for src in priority:
        if src in sources and sources[src] is not None:
            return sources[src]

    # fallback — любое значение
    for val in sources.values():
        if val is not None:
            return val

    return None