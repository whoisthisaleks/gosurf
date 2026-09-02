import requests
from datetime import datetime, timezone
from config import STORMGLASS_API_KEY

SPOTS = {
    "Uluwatu": {"lat": -8.829, "lng": 115.084, "orientation": 210},
    "Canggu": {"lat": -8.65, "lng": 115.13, "orientation": 220},
    "Kuta": {"lat": -8.72, "lng": 115.17, "orientation": 215},
    "Medewi": {"lat": -8.42, "lng": 114.78, "orientation": 240},
}


def get_spots_data():
    result = []

    for name, spot in SPOTS.items():
        url = (
            f"https://api.stormglass.io/v2/weather/point?"
            f"lat={spot['lat']}&lng={spot['lng']}"
            f"&params=waveHeight,wavePeriod,windSpeed,windDirection,waveDirection"
        )

        tide_url = (
            f"https://api.stormglass.io/v2/tide/sea-level/point?"
            f"lat={spot['lat']}&lng={spot['lng']}"
        )

        headers = {"Authorization": STORMGLASS_API_KEY}

        try:
            # weather
            res = requests.get(url, headers=headers)
            data = res.json()
            hours = data.get("hours", [])

            # tide
            tide_res = requests.get(tide_url, headers=headers)
            tide_data = tide_res.json()
            tide_hours = tide_data.get("data", [])

            if not hours:
                continue

            now = datetime.now(timezone.utc)

            closest = min(
                hours,
                key=lambda h: abs(
                    datetime.fromisoformat(h["time"].replace("Z", "+00:00")) - now
                ),
            )

            tide_level = None
            if tide_hours:
                tide_closest = min(
                    tide_hours,
                    key=lambda h: abs(
                        datetime.fromisoformat(h["time"].replace("Z", "+00:00")) - now
                    ),
                )
                tide_level = tide_closest["sg"]

            result.append({
                "name": name,
                "orientation": spot["orientation"],
                "wave_height": closest["waveHeight"]["sg"],
                "period": closest["wavePeriod"]["sg"],
                "wind_speed": closest["windSpeed"]["sg"],
                "wind_dir": closest["windDirection"]["sg"],
                "swell_dir": closest["waveDirection"]["sg"],
                "tide": tide_level,
            })

        except Exception as e:
            print("Weather error:", e)

    return result