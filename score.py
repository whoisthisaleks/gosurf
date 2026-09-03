def calculate_score(spot, level):
    wave = spot["wave"]
    period = spot["period"]
    wind = spot["wind"]
    wind_dir = spot["wind_dir"]
    swell_dir = spot["swell_dir"]

    score = 0

    if level == "Beginner":
        if 0.8 <= wave <= 1.5:
            score += 40
    elif level == "Intermediate":
        if 1.2 <= wave <= 2.2:
            score += 40
    elif level == "Advanced":
        if wave >= 1.8:
            score += 40

    score += min(period * 2, 20)

    if wind < 3:
        score += 20
    elif wind < 6:
        score += 10

    angle_diff = abs(wind_dir - swell_dir)
    if angle_diff > 180:
        angle_diff = 360 - angle_diff

    if angle_diff > 120:
        score += 20
    elif angle_diff > 60:
        score += 10

    return round(min(score, 100))