def calculate_score(spot, level):
    wave = spot.get("wave") or 0
    period = spot.get("period") or 0
    wind = spot.get("wind") or 0

    score = 0

    # WAVE
    if level == "Beginner":
        if 0.8 <= wave <= 1.5:
            score += 40
    elif level == "Intermediate":
        if 1.2 <= wave <= 2.2:
            score += 40
    elif level == "Advanced":
        if wave >= 1.5:
            score += 40

    # PERIOD
    if period >= 10:
        score += 30
    elif period >= 7:
        score += 15

    # WIND
    if wind <= 5:
        score += 30
    elif wind <= 8:
        score += 15

    return score