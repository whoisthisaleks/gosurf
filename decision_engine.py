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

    spot_rules = SPOTS[spot]

    # --------------------
    # Level
    # --------------------
    if level == "beginner":
        if spot_rules.get("beginner"):
            score += 20
            reasons.append("good for your level")
    else:
        score += 10

    # --------------------
    # Wave height
    # --------------------
    if level == "beginner":
        if 0.5 <= height <= 1.5:
            score += 30
            reasons.append("safe wave size")
        elif height < 0.5:
            score += 10
            reasons.append("small waves")
        else:
            score += 5
            reasons.append("too big")
    else:
        if 1.2 <= height <= 2.5:
            score += 30
            reasons.append("good wave size")
        elif height < 1.2:
            score += 15
            reasons.append("smaller waves")
        else:
            score += 20
            reasons.append("powerful waves")

    # --------------------
    # Period
    # --------------------
    if period >= 12:
        score += 20
        reasons.append("strong swell")
    elif period >= 8:
        score += 10

    # --------------------
    # Swell direction
    # --------------------
    if swell in spot_rules.get("swell", []):
        score += 20
        reasons.append("good swell direction")

    # --------------------
    # Wind
    # --------------------
    if wind_direction == "unknown":
        score -= 15
        reasons.append("no wind data")

    elif wind_direction in spot_rules.get("offshore", []):
        score += 20
        reasons.append("offshore wind")

    elif wind_direction in spot_rules.get("onshore", []):
        score -= 10
        reasons.append("onshore wind")

    if wind_speed >= 10:
        score -= 10
        reasons.append("strong wind")

    # --------------------
    # Tide (NEW)
    # --------------------
    if tide is not None:
        tide_pref = spot_rules.get("tide_preference", [])

        if tide < 0.8:
            tide_state = "low"
        elif tide < 1.8:
            tide_state = "mid"
        else:
            tide_state = "high"

        if tide_state in tide_pref:
            score += 10
            reasons.append("good tide")
        else:
            score -= 5
            reasons.append("less optimal tide")

    return score, reasons


def build_recommendation(forecast, level):
    results = []

    for spot, conditions in forecast.items():
        score, reasons = calculate_spot_score(spot, conditions, level)

        results.append(
            {
                "spot": spot,
                "score": score,
                "reasons": reasons,
            }
        )

    spot_order = {spot: i for i, spot in enumerate(SPOTS)}

    results.sort(
        key=lambda x: (
            -x["score"],
            -int(level == "beginner" and SPOTS[x["spot"]].get("beginner")),
            spot_order[x["spot"]],
        )
    )

    best = results[0]

    alternatives = [x["spot"] for x in results[1:3]]

    if best["score"] >= 75:
        confidence = "high"
    elif best["score"] >= 50:
        confidence = "medium"
    else:
        confidence = "low"

    return {
        "best": best["spot"],
        "score": best["score"],
        "reasons": best["reasons"],
        "conditions": forecast[best["spot"]],
        "confidence": confidence,
        "alternatives": alternatives,
    }