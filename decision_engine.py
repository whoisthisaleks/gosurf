from spots import SPOTS


def calculate_spot_score(
    spot,
    conditions,
    level
):
    score = 0
    reasons = []

    height = conditions.get("wave_height", 0)
    period = conditions.get("period", 0)
    swell = conditions.get("swell_direction", "")
    wind_speed = conditions.get("wind_speed", 0)
    wind_direction = conditions.get("wind_direction", "")

    spot_rules = SPOTS[spot]

    # --------------------
    # Level
    # --------------------
    if level == "beginner":
        if spot_rules.get("beginner"):
            score += 20
            reasons.append("good for your level")
        else:
            score -= 10
            reasons.append("not ideal for beginners")
    else:
        score += 10

    # --------------------
    # Wave height (с учётом спота)
    # --------------------
    min_wave = spot_rules.get("min_wave", 0.5)
    max_wave = spot_rules.get("max_wave", 3.0)

    if height < min_wave:
        score -= 10
        reasons.append("too small")
    elif min_wave <= height <= max_wave:
        score += 30
        reasons.append("optimal wave size")
    else:
        # слишком большая
        if level == "beginner":
            score -= 20
            reasons.append("too big for beginners")
        else:
            score += 10
            reasons.append("powerful waves")

    # --------------------
    # Period (усилен)
    # --------------------
    if period >= 14:
        score += 30
        reasons.append("long clean swell")
    elif period >= 12:
        score += 25
        reasons.append("strong swell")
    elif period >= 10:
        score += 15
    elif period >= 8:
        score += 5
    else:
        score -= 10
        reasons.append("weak swell")

    # --------------------
    # Swell direction
    # --------------------
    if swell in spot_rules.get("swell", []):
        score += 20 if level != "beginner" else 10
        reasons.append("good swell direction")
    else:
        score -= 5

    # --------------------
    # Wind (сильно улучшено)
    # --------------------
    offshore = spot_rules.get("offshore", [])
    onshore = spot_rules.get("onshore", [])

    if wind_direction in offshore:
        if wind_speed <= 5:
            score += 25
            reasons.append("light offshore wind")
        elif wind_speed <= 10:
            score += 15
            reasons.append("offshore wind")
        else:
            score += 5
            reasons.append("strong offshore wind")

    elif wind_direction in onshore:
        score -= 20
        reasons.append("onshore wind")

    elif wind_direction != "unknown":
        score += 5
        reasons.append("cross wind")

    # штраф за сильный ветер
    if wind_speed >= 12:
        score -= 10
        reasons.append("too windy")

    # --------------------
    # Итог
    # --------------------
    return score, reasons


def build_recommendation(
    forecast,
    level
):
    results = []

    for spot, conditions in forecast.items():
        score, reasons = calculate_spot_score(
            spot,
            conditions,
            level
        )

        results.append({
            "spot": spot,
            "score": score,
            "reasons": reasons
        })

    spot_order = {
        spot: index
        for index, spot in enumerate(SPOTS)
    }

    results.sort(
        key=lambda x: (
            -x["score"],
            -int(
                level == "beginner"
                and SPOTS[x["spot"]].get("beginner")
            ),
            spot_order[x["spot"]]
        )
    )

    best = results[0]

    alternatives = [
        x["spot"]
        for x in results[1:3]
    ]

    if best["score"] >= 80:
        confidence = "high"
    elif best["score"] >= 55:
        confidence = "medium"
    else:
        confidence = "low"

    return {
        "best": best["spot"],
        "score": best["score"],
        "reasons": best["reasons"],
        "conditions": forecast[best["spot"]],
        "confidence": confidence,
        "alternatives": alternatives
    }