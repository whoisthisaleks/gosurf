SPOTS = [
    {"name": "Uluwatu", "lat": -8.818, "lon": 115.087, "level": "pro"},
    {"name": "Canggu", "lat": -8.651, "lon": 115.138, "level": "mid"},
    {"name": "Kuta", "lat": -8.717, "lon": 115.168, "level": "beginner"},
    {"name": "Medewi", "lat": -8.426, "lon": 114.793, "level": "mid"},
]


def get_best_spot(spots_data):
    return sorted(spots_data, key=lambda x: x["score"], reverse=True)[0]


def score_spot(weather, level):
    score = 0

    wave = weather["wave"]
    period = weather["period"]
    wind = weather["wind"]

    if level == "beginner":
        if 0.8 <= wave <= 1.5:
            score += 3
    elif level == "mid":
        if 1.2 <= wave <= 2:
            score += 3
    else:
        if wave >= 1.5:
            score += 3

    if period >= 10:
        score += 2

    if wind < 6:
        score += 2

    return score