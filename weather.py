import requests
from datetime import datetime, timezone
from config import STORMGLASS_API_KEY

BASE_URL = "https://api.stormglass.io/v2/weather/point"

PARAMS = ",".join([
    "waveHeight",
    "wavePeriod",
    "waveDirection",
    "windSpeed",
    "windDirection",
    "waterTemperature"
])

HEADERS = {
    "Authorization": STORMGLASS_API_KEY
}


def get_nearest_hour(hours):
    """Берем ближайший час к текущему времени"""
    now = datetime.now(timezone.utc)

    closest = min(
        hours,
        key=lambda h: abs(
            datetime.fromisoformat(h["time"].replace("Z", "+00:00")) - now
        )
    )
    return closest


def fetch_weather(lat, lng):
    try:
        response = requests.get(
            BASE_URL,
            params={
                "lat": lat,
                "lng": lng,
                "params": PARAMS
            },
            headers=HEADERS,
            timeout=10
        )

        data = response.json()

        if "hours" not in data:
            print("⚠️ Stormglass quota or error:", data)
            return None

        hour = get_nearest_hour(data["hours"])

        return {
            "wave_height": hour.get("waveHeight", {}).get("sg", 0),
            "wave_period": hour.get("wavePeriod", {}).get("sg", 0),
            "wave_direction": hour.get("waveDirection", {}).get("sg", 0),
            "wind_speed": hour.get("windSpeed", {}).get("sg", 0),
            "wind_direction": hour.get("windDirection", {}).get("sg", 0),
            "water_temp": hour.get("waterTemperature", {}).get("sg", 0),
            "time": hour.get("time")
        }

    except Exception as e:
        print("❌ Weather fetch error:", e)
        return None


def get_spots_data(spots):
    """
    Возвращает список:
    [
        {
            "spot": {...},
            "conditions": {...}
        }
    ]
    """

    result = []

    for spot in spots:
        weather = fetch_weather(spot["lat"], spot["lng"])

        if not weather:
            continue

        result.append({
            "spot": spot,
            "conditions": weather
        })

    return result