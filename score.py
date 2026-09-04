def calculate_score(spot, user_level):
    score = 0

    wave = spot["wave_height"]
    period = spot["period"]
    wind = spot["wind_dir"]

    # 🌊 размер волн под уровень
    if user_level == "beginner":
        if 0.7 <= wave <= 1.5:
            score += 30
        else:
            score -= 20

    elif user_level == "intermediate":
        if 1.0 <= wave <= 2.0:
            score += 30
        else:
            score -= 10

    else:  # advanced
        if wave >= 1.5:
            score += 30

    # ⏱ период
    if period > 12:
        score += 20
    elif period < 8:
        score -= 10

    # 🌬 ветер (упрощенно)
    if 200 <= wind <= 320:
        score += 40  # offshore-ish
    else:
        score -= 20

    return score