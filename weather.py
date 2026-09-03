import requests
import os

API_KEY = os.getenv("STORMGLASS_API_KEY")

def get_spots_data():
    results = []

    for spot in SPOTS:
        try:
            url = "https://api.stormglass.io/v2/weather/point"

            params = {
                "lat": spot["lat"],
                "lng": spot["lng"],
                "params": "waveHeight,wavePeriod,windSpeed,windDirection,swellDirection",
                "source": "sg"
            }

            headers = {"Authorization": API_KEY}

            res = requests.get(url, params=params, headers=headers)
            data = res.json()

            hour = data["hours"][0]

            results.append({
                "spot": spot["name"],
                "lat": spot["lat"],
                "lng": spot["lng"],
                "wave": hour["waveHeight"]["sg"],
                "period": hour["wavePeriod"]["sg"],
                "wind": hour["windSpeed"]["sg"],
                "wind_dir": hour["windDirection"]["sg"],
                "swell_dir": hour["swellDirection"]["sg"]
            })

        except Exception:
            continue

    return results