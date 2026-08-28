from spots import SPOTS


def calculate_spot_score(spot, conditions, level):
    score = 0
    reasons = []

    height = conditions.get("wave_height", 0)
    period = conditions.get("period", 0)
    swell = conditions.get("swell_direction", "")
    wind_speed = conditions.get("wind_speed", 0)
    wind_direction = conditions.get("wind_direction", "")
    tide = conditions.get("tide")

    rules = SPOTS[spot]

    # LEVEL
    if level == "beginner":
        if rules["beginner"]:
            score += 20
            reasons.append("good for your level")
    elif level == "intermediate":
        score += 10
    else:
        score += 15

    # HEIGHT
    if level == "beginner":
        if 0.5 <= height <= 1.5:
            score += 30
            reasons.append("safe wave size")
    elif level == "intermediate":
        if 1.0 <= height <= 2.0:
            score += 30
            reasons.append("fun wave size")
    else:
        if height >= 1.5:
            score += 35
            reasons.append("powerful waves")

    # PERIOD
    if period >= 12:
        score += 20
        reasons.append("long period swell")
    elif period >= 8:
        score += 10

    # SWELL
    if swell in rules["swell"]:
        score += 20
        reasons.append("clean swell direction")

    # WIND
    if wind_direction in rules.get("offshore", []):
        score += 20
        reasons.append("offshore wind")
    elif wind_direction in rules.get("onshore", []):
        score -= 10
        reasons.append("onshore wind")

    if wind_speed >= 10:
        score -= 10

    # TIDE
    if tide is not None:
        if tide < 0.8:
            state = "low"
        elif tide < 1.8:
            state = "mid"
        else:
            state = "high"

        if state in rules.get("tide_preference", []):
            score += 10
            reasons.append("good tide")

    return score, reasons


def build_recommendation(forecast, level):
    results = []

    for spot, conditions in forecast.items():
        score, reasons = calculate_spot_score(spot, conditions, level)

        results.append({
            "spot": spot,
            "score": score,
            "reasons": reasons
        })

    results.sort(key=lambda x: -x["score"])

    best = results[0]

    return {
        "best": best["spot"],
        "score": best["score"],
        "reasons": best["reasons"],
        "conditions": forecast[best["spot"]],
        "alternatives": [x["spot"] for x in results[1:3]]
    }