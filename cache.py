import time
import json
import os


CACHE_FILE = "weather_cache.json"

CACHE_TIME = 3600  # 1 час



def save_cache(data):

    cache = {
        "timestamp": time.time(),
        "data": data
    }


    with open(
        CACHE_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            cache,
            f,
            ensure_ascii=False,
            indent=2
        )



def load_cache():

    if not os.path.exists(CACHE_FILE):
        return None


    with open(
        CACHE_FILE,
        "r",
        encoding="utf-8"
    ) as f:

        cache = json.load(f)



    age = time.time() - cache["timestamp"]


    if age < CACHE_TIME:

        print(
            f"CACHE HIT: {round(age/60)} min old"
        )

        return cache["data"]



    print("CACHE EXPIRED")

    return None