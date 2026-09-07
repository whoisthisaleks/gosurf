import math


def _safe(val, default):
    return val if val is not None else default


def _clamp(v, min_v, max_v):
    return max(min_v, min(v, max_v))


def _angle_diff(a, b):
    if a is None or b is None:
        return 180
    diff = abs(a - b)
    return min(diff, 360 - diff)


# --- SCORING ---

def _wave_score(wave, level):
    wave = _safe(wave, 0)

    if level == "Beginner":
        ideal = (0.6, 1.2)
    elif level == "Intermediate":
        ideal = (1.0, 2.0)
    else:
        ideal = (1.5, 3.0)

    if ideal[0] <= wave <= ideal[1]:
        return 30

    dist = min(abs(wave - ideal[0]), abs(wave - ideal[1]))
    return _clamp(30 - dist * 20, 0, 30)


def _period_score(period):
    period = _safe(period, 0)

    if period >= 12:
        return 20
    elif period >= 9:
        return 15
    elif period >= 6:
        return 10
    return 5


def _wind_score(wind):
    if wind == "offshore":
        return 25
    elif wind == "cross":
        return 15
    elif wind == "onshore":
        return 5
    return 10


def _swell_score(spot, swell_dir):
    if swell_dir is None:
        return 5

    swell_min = spot.get("swell_min")
    swell_max = spot.get("swell_max")

    if swell_min is None or swell_max is None:
        return 5

    if swell_min <= swell_dir <= swell_max:
        return 25

    center = (swell_min + swell_max) / 2
    diff = _angle_diff(swell_dir, center)

    return _clamp(25 - diff / 2, 0, 25)


def _tide_score(level, tide):
    if tide is None:
        return 5

    if level == "Beginner":
        return 15 if tide == "mid" else 8
    elif level == "Intermediate":
        return 15 if tide in ["mid", "high"] else 8
    else:
        return 15 if tide in ["low", "mid"] else 8


# --- LEVEL-AWARE WHY ---

def build_reason(data, spot_config, level):
    reasons = []

    wind = data.get("wind")
    swell = data.get("swell_dir")
    wave = data.get("wave")
    tide = data.get("tide")

    swell_min = spot_config.get("swell_min")
    swell_max = spot_config.get("swell_max")

    swell_good = (
        swell is not None and
        swell_min is not None and
        swell_max is not None and
        swell_min <= swell <= swell_max
    )

    # --- BEGINNER ---
    if level == "Beginner":

        if wind == "offshore":
            reasons.append("clean offshore wind")
        elif wind == "cross":
            reasons.append("manageable wind")

        if wave and wave <= 1.2:
            reasons.append("safe wave size")

        if tide == "mid":
            reasons.append("comfortable tide")

        if swell_good:
            reasons.append("stable swell")

    # --- INTERMEDIATE ---
    elif level == "Intermediate":

        if wind == "offshore":
            reasons.append("offshore wind")
        elif wind == "cross":
            reasons.append("clean conditions")

        if swell_good:
            reasons.append("good swell angle")

        if wave and 1.0 <= wave <= 2.0:
            reasons.append("fun wave size")

        if tide in ["mid", "high"]:
            reasons.append("good tide")

    # --- ADVANCED ---
    else:

        if wind == "offshore":
            reasons.append("offshore wind")

        if swell_good:
            reasons.append("ideal swell angle")

        if wave and wave >= 1.5:
            reasons.append("powerful waves")

        if tide in ["low", "mid"]:
            reasons.append("optimal tide")

    if not reasons:
        return "average conditions"

    return " + ".join(reasons)


# --- MAIN ---

def score_spot(data, spot_config, level):
    score = 0
    score += _wave_score(data.get("wave"), level)
    score += _period_score(data.get("period"))
    score += _wind_score(data.get("wind"))
    score += _swell_score(spot_config, data.get("swell_dir"))
    score += _tide_score(level, data.get("tide"))

    return round(score, 1)


def pick_best_spots(data_list, level):
    from spots import SPOTS

    results = []

    for data in data_list:
        spot_config = next(
            (s for s in SPOTS if s["name"] == data["spot"]),
            {}
        )

        data["score"] = score_spot(data, spot_config, level)
        data["reason"] = build_reason(data, spot_config, level)

        results.append(data)

    results.sort(key=lambda x: x["score"], reverse=True)

    best = results[0]
    alternatives = results[1:3]

    return best, alternatives