def angle_diff(a, b):
    diff = abs(a - b) % 360
    return min(diff, 360 - diff)


def wind_score(wind_dir, spot_orientation):
    diff = angle_diff(wind_dir, spot_orientation)

    # offshore (ветер в лицо волне)
    if diff > 150:
        return 3

    # cross
    if 60 < diff <= 150:
        return 1

    # onshore
    return -3


def swell_score(swell_dir, spot_orientation):
    diff = angle_diff(swell_dir, spot_orientation)

    if diff < 40:
        return 3
    elif diff < 80:
        return 2
    else:
        return 0


def size_score(height, level):
    if level == "beginner":
        if 0.8 <= height <= 1.5:
            return 3
        return -2

    if level == "intermediate":
        if 1.2 <= height <= 2.5:
            return 3
        return 0

    if level == "advanced":
        if height >= 1.5:
            return 3
        return 1


def period_score(period):
    if period >= 12:
        return 3
    if period >= 9:
        return 2
    return 0


def pick_best_spot(spots, level):
    best = None
    best_score = -999

    for s in spots:
        score = 0

        score += size_score(s["wave_height"], level)
        score += period_score(s["period"])
        score += wind_score(s["wind_dir"], s["orientation"])
        score += swell_score(s["swell_dir"], s["orientation"])

        if score > best_score:
            best_score = score
            best = s

    return best