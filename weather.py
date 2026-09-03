import requests
from spots import SPOTS
from config import STORMGLASS_API_KEY

URL = "https://api.stormglass.io/v2/weather/point"

def get_spots_data():
    results = []

    for spot in SPOTS:
        params = {
            "lat": spot["lat"],
            "lng": spot["lng"],
            "params": "waveHeight,wavePeriod,windSpeed,windDirection"
        }

        headers = {
            "Authorization": STORMGLASS_API_KEY
        }

        try:
            res = requests.get(URL, params=params, headers=headers)
            data = res.json()

            hour = data["hours"][0]

            results.append({
                "name": spot["name"],
                "lat": spot["lat"],
                "lng": spot["lng"],

                "wave": hour["waveHeight"]["sg"],
                "period": hour["wavePeriod"]["sg"],
                "wind": hour["windSpeed"]["sg"],
                "wind_dir": hour["windDirection"]["sg"],
            })

        except Exception as e:
            print("Weather error:", e)

    return results