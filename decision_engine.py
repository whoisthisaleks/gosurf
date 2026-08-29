# decision_engine.py

def score_spot(cond, level):
    score = 0

    wave = cond.get("wave_height", 0)
    period = cond.get("period", 0)
    wind = cond.get("wind_speed", 0)

    # --- LEVEL RULES ---
    if level == "beginner":
        if 0.5 <= wave <= 1.2:
            score += 40
        if period >= 10:
            score += 20
        if wind < 5:
            score += 20

    elif level == "intermediate":
        if 0.8 <= wave <= 2.0:
            score += 40
        if period >= 11:
            score += 20
        if wind < 7:
            score += 20

    elif level == "advanced":
        if wave >= 1.5:
            score += 40
        if period >= 12:
            score += 20
        if wind < 10:
            score += 20

    return score


def get_best_spot(forecast, level):
    results = []

    for spot, cond in forecast.items():
        score = score_spot(cond, level)

        results.append({
            "spot": spot,
            "score": score,
            "wave_height": cond.get("wave_height"),
            "period": cond.get("period"),
            "swell_direction": cond.get("swell_direction"),
            "wind_speed": cond.get("wind_speed"),
            "wind_direction": cond.get("wind_direction"),
            "tide": cond.get("tide")
        })

    # сортировка
    results = sorted(results, key=lambda x: x["score"], reverse=True)

    best = results[0]
    alternatives = [r["spot"] for r in results[1:3]]

    return best, alternatives