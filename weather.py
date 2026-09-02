import requests
from datetime import datetime, timezone
from config import STORMGLASS_API_KEY

SPOTS = {
    "Uluwatu": {"lat": -8.829, "lng": 115.084},
    "Canggu": {"lat": -8.65, "lng": 115.13},
    "Kuta": {"lat": -8.72, "lng": 115.17},
    "Medewi": {"lat": -8.42, "lng": 114.78},
}


def get_spots_data():
    result = []

    for name, coords in SPOTS.items():
        url = f"https://api.stormglass.io/v2/weather/point?lat={coords['lat']}&lng={coords['lng']}&params=waveHeight,wavePeriod,windSpeed,windDirection"

        headers = {"Authorization": STORMGLASS_API_KEY}

        try:
            res = requests.get(url, headers=headers)
            data = res.json()

            hours = data.get("hours", [])
            if not hours:
                continue

            now = datetime.now(timezone.utc)

            closest = min(
                hours,
                key=lambda h: abs(
                    datetime.fromisoformat(h["time"].replace("Z", "+00:00")) - now
                ),
            )

            result.append({
                "name": name,
                "wave_height": closest["waveHeight"]["sg"],
                "period": closest["wavePeriod"]["sg"],
                "wind_speed": closest["windSpeed"]["sg"],
                "wind_dir": closest["windDirection"]["sg"],
            })

        except Exception as e:
            print("Weather error:", e)

    return result