import requests
from spots import SPOTS
from config import STORMGLASS_API_KEY

URL = "https://api.stormglass.io/v2/weather/point"

PARAMS = "waveHeight,wavePeriod,windSpeed,windDirection"

def get_spots_data():
    results = []

    for spot in SPOTS:
        try:
            response = requests.get(
                URL,
                params={
                    "lat": spot["lat"],
                    "lng": spot["lng"],
                    "params": PARAMS
                },
                headers={"Authorization": STORMGLASS_API_KEY}
            )

            data = response.json()

            if "hours" not in data:
                raise Exception("No data from API")

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
            print("API ERROR:", e)

            # fallback (чтобы бот НЕ умирал)
            results.append({
                "name": spot["name"],
                "lat": spot["lat"],
                "lng": spot["lng"],
                "wave": 1.2,
                "period": 10,
                "wind": 5,
                "wind_dir": 180,
            })

    return results