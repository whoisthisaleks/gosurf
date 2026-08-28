from spots import SPOTS


# --------------------
# HELPERS
# --------------------
def get_time_bucket(hour_str):
    try:
        hour = int(hour_str.split(":")[0])
    except:
        return "other"

    if 6 <= hour <= 11:
        return "morning"
    elif 12 <= hour <= 18:
        return "afternoon"
    return "other"


# --------------------
# SCORE
# --------------------
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

    else:  # advanced
        score += 15

    # WAVE HEIGHT
    if level == "beginner":
        if 0.5 <= height <= 1.5:
            score += 30
            reasons.append("safe wave size")
        elif height < 0.5:
            score += 10
        else:
            score += 5

    elif level == "intermediate":
        if 1.0 <= height <= 2.0:
            score += 30
            reasons.append("fun wave size")
        elif height < 1.0:
            score += 15
        else:
            score += 20

    else:  # advanced
        if height >= 1.5:
            score += 35
            reasons.append("powerful waves")
        elif height >= 1.0:
            score += 25
        else:
            score += 10

    # PERIOD
    if period >= 12:
        score += 20
        reasons.append("strong swell")
    elif period >= 8:
        score += 10

    # SWELL
    if swell in rules["swell"]:
        score += 20
        reasons.append("good swell direction")

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
            tide_state = "low"
        elif tide < 1.8:
            tide_state = "mid"
        else:
            tide_state = "high"

        if tide_state in rules.get("tide_preference", []):
            score += 10
            reasons.append("good tide")

    return score, reasons


# --------------------
# BEST TIME
# --------------------
def calculate_best_time(hourly_forecast, level):
    buckets = {"morning": [], "afternoon": []}

    for spot, hours in hourly_forecast.items():
        for h in hours:
            bucket = get_time_bucket(h.get("time"))
            if bucket not in buckets:
                continue

            score, _ = calculate_spot_score(spot, h, level)
            buckets[bucket].append(score)

    avg = {
        k: (sum(v) / len(v)) if v else 0
        for k, v in buckets.items()
    }

    return "morning" if avg["morning"] >= avg["afternoon"] else "afternoon"


# --------------------
# MAIN
# --------------------
def build_recommendation(forecast, level, hourly_forecast=None):
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

    alternatives = [x["spot"] for x in results[1:3]]

    if best["score"] >= 75:
        confidence = "high"
    elif best["score"] >= 50:
        confidence = "medium"
    else:
        confidence = "low"

    best_time = (
        calculate_best_time(hourly_forecast, level)
        if hourly_forecast else None
    )

    return {
        "best": best["spot"],
        "score": best["score"],
        "reasons": best["reasons"],
        "conditions": forecast[best["spot"]],
        "confidence": confidence,
        "alternatives": alternatives,
        "best_time": best_time
    }