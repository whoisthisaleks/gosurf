def score_spot(spot, level):
    score = 0

    h = spot["wave_height"]
    p = spot["period"]
    w = spot["wind_speed"]

    if level == "beginner":
        if 0.8 <= h <= 1.5:
            score += 3
        if p >= 8:
            score += 2
        if w < 6:
            score += 2

    elif level == "intermediate":
        if 1.2 <= h <= 2.5:
            score += 3
        if p >= 10:
            score += 2
        if w < 8:
            score += 2

    else:  # advanced
        if h >= 1.5:
            score += 3
        if p >= 12:
            score += 3
        if w < 10:
            score += 1

    return score


def pick_best_spot(spots, level):
    scored = [(spot, score_spot(spot, level)) for spot in spots]
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[0][0] if scored else None