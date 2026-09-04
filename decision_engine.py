def _angle_diff(a, b):
    diff = abs(a - b)
    return min(diff, 360 - diff)


def _swell_score(spot, swell_dir):
    if swell_dir is None:
        return 0

    if spot["swell_min"] <= swell_dir <= spot["swell_max"]:
        return 2

    mid = (spot["swell_min"] + spot["swell_max"]) / 2
    if _angle_diff(swell_dir, mid) <= 40:
        return 1

    return -2


def _wind_score(wind):
    if wind == "offshore":
        return 2
    if wind == "cross":
        return 1
    if wind == "onshore":
        return -2
    return 0


def _tide_score(spot, tide):
    if tide == "unknown":
        return 0

    if tide == spot["tide"]:
        return 2

    if spot["tide"] == "mid" and tide in ["low", "high"]:
        return 1

    return -1


def _wave_score(level, wave):
    if level == "beginner":
        return 2 if 0.5 <= wave <= 1.2 else -2

    if level == "intermediate":
        return 2 if 0.8 <= wave <= 2.0 else 0

    if level == "advanced":
        return 2 if wave >= 1.5 else 0

    return 0


def score_spot(data, spot_config, level):
    score = 0

    score += _wave_score(level, data["wave"])
    score += _wind_score(data["wind"])
    score += _swell_score(spot_config, data.get("swell_dir"))
    score += _tide_score(spot_config, data.get("tide"))

    return score


def pick_best_spots(weather_data, level):
    from spots import SPOTS

    scored = []

    for data in weather_data:
        config = next(s for s in SPOTS if s["name"] == data["spot"])
        s = score_spot(data, config, level)

        data["score"] = s
        scored.append(data)

    scored.sort(key=lambda x: x["score"], reverse=True)

    return scored[0], scored[1:3]