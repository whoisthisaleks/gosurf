def score_spot(data: dict, level: str) -> float:
    if not data:
        return 0

    wave = data.get("wave_height") or 0
    period = data.get("period") or 0
    wind = data.get("wind_speed") or 0

    score = 0

    # ===== WAVE =====
    if level == "beginner":
        if 0.8 <= wave <= 1.5:
            score += 40
        elif wave < 0.8:
            score += 20
        else:
            score -= 20

    elif level == "intermediate":
        if 1.0 <= wave <= 2.5:
            score += 40
        else:
            score += 20

    elif level == "advanced":
        if wave >= 1.5:
            score += 40
        else:
            score += 10

    # ===== PERIOD =====
    if period >= 10:
        score += 30
    elif period >= 7:
        score += 15

    # ===== WIND =====
    if wind < 5:
        score += 20
    elif wind < 8:
        score += 10
    else:
        score -= 20

    return score


def pick_best_spots(spots_with_data, level):
    scored = []

    for spot in spots_with_data:
        s = score_spot(spot["data"], level)

        scored.append({
            "name": spot["name"],
            "data": spot["data"],
            "score": s
        })

    scored.sort(key=lambda x: x["score"], reverse=True)

    best = scored[0] if len(scored) > 0 else None
    alternative = scored[1] if len(scored) > 1 else None

    return {
        "best": best,
        "alternative": alternative
    }