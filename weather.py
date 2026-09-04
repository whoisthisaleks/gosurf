import requests
from config import STORMGLASS_API_KEY
from spots import SPOTS

URL = "https://api.stormglass.io/v2/weather/point"

def get_spots_data():
    result = []

    for spot in SPOTS:
        params = {
            "lat": spot["lat"],
            "lng": spot["lng"],
            "params": "waveHeight,wavePeriod,windDirection,swellDirection",
        }

        headers = {
            "Authorization": STORMGLASS_API_KEY
        }

        try:
            response = requests.get(URL, params=params, headers=headers, timeout=5)
            data = response.json()

            hours = data.get("hours", [])
            if not hours:
                raise Exception("No data")

            current = hours[0]

            spot_data = {
                "name": spot["name"],
                "level": spot["level"],
                "wave_height": current["waveHeight"]["sg"],
                "period": current["wavePeriod"]["sg"],
                "wind_dir": current["windDirection"]["sg"],
                "swell_dir": current["swellDirection"]["sg"],
            }

        except Exception as e:
            print("API ERROR:", e)

            # fallback
            spot_data = {
                "name": spot["name"],
                "level": spot["level"],
                "wave_height": 1.2,
                "period": 10,
                "wind_dir": 90,
                "swell_dir": 220,
            }

        result.append(spot_data)

    return result