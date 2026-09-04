def score_spot(spot, level):
    score = 0

    wave = spot.get("wave_height", 0)
    period = spot.get("wave_period", 0)
    wind = spot.get("wind_speed", 0)

    if level == "beginner":
        if 0.8 <= wave <= 1.5:
            score += 3
        if period >= 10:
            score += 2
        if wind <= 5:
            score += 2

    elif level == "intermediate":
        if 1.2 <= wave <= 2.0:
            score += 3
        if period >= 11:
            score += 2
        if wind <= 7:
            score += 2

    elif level == "advanced":
        if wave >= 1.8:
            score += 3
        if period >= 12:
            score += 2
        if wind <= 10:
            score += 2

    return score


def pick_best_spots(spots, level):
    scored = []

    for spot in spots:
        s = score_spot(spot, level)
        spot["score"] = s
        scored.append(spot)

    scored = sorted(scored, key=lambda x: x["score"], reverse=True)

    best = scored[0] if scored else None
    alternatives = scored[1:3] if len(scored) > 1 else []

    return best, alternatives