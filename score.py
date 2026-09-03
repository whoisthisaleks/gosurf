def calculate_score(spot, level):
    wave = spot["wave"]
    period = spot["period"]
    wind = spot["wind"]

    score = 0

    # 🌊 wave
    if level == "beginner":
        if 0.8 <= wave <= 1.5:
            score += 30
    elif level == "intermediate":
        if 1.2 <= wave <= 2.0:
            score += 30
    else:
        if wave >= 1.8:
            score += 30

    # ⏱ period
    if period >= 10:
        score += 25

    # 💨 wind (меньше лучше)
    if wind <= 5:
        score += 25
    elif wind <= 8:
        score += 15

    # бонус
    score += 20

    return min(score, 100)