def score_spot(cond, level):
    score = 0

    wave = cond["wave_height"]
    period = cond["period"]
    wind = cond["wind_speed"]

    # wave
    if level == "beginner":
        if 0.7 <= wave <= 1.5:
            score += 40
    elif level == "intermediate":
        if 1.0 <= wave <= 2.0:
            score += 40
    else:
        if wave >= 1.5:
            score += 40

    # period
    if period >= 10:
        score += 30

    # wind
    if wind <= 5:
        score += 30

    return score


def get_best_spot(forecast, level):
    scored = []

    for spot, cond in forecast.items():
        s = score_spot(cond, level)
        scored.append((spot, s, cond))

    scored.sort(key=lambda x: x[1], reverse=True)

    best = scored[0]
    alt1 = scored[1][0]
    alt2 = scored[2][0]

    return {
        "spot": best[0],
        "score": best[1],
        "conditions": best[2],
        "alternatives": [alt1, alt2],
        "best_time": "morning",
        "reason": [
            "good wave size",
            "favorable wind"
        ]
    }