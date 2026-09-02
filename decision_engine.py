import math

# =========================
# SPOT CONFIG (ключ к качеству)
# =========================
SPOT_CONFIG = {
    "Uluwatu": {
        "ideal_swell_dir": (180, 220),   # S–SW
        "offshore_wind": (0, 90),        # E wind
    },
    "Canggu": {
        "ideal_swell_dir": (200, 240),   # SW
        "offshore_wind": (90, 180),      # E-SE
    },
    "Kuta": {
        "ideal_swell_dir": (190, 230),
        "offshore_wind": (90, 180),
    },
    "Medewi": {
        "ideal_swell_dir": (210, 250),
        "offshore_wind": (45, 135),      # NE-E
    },
}


# =========================
# HELPERS
# =========================
def in_range(angle, start, end):
    """Check if angle is within circular range"""
    if start <= end:
        return start <= angle <= end
    return angle >= start or angle <= end


def wind_score(wind_speed, wind_dir, offshore_range):
    """Wind scoring"""
    score = 0

    if in_range(wind_dir, *offshore_range):
        score += 25  # offshore bonus
    else:
        score -= 20  # onshore penalty

    if wind_speed > 8:
        score -= 20
    elif wind_speed > 5:
        score -= 10

    return score


def swell_score(swell_dir, ideal_range):
    """Swell direction scoring"""
    if in_range(swell_dir, *ideal_range):
        return 20
    return -15


def wave_score(height, level):
    """Wave height vs skill"""
    if level == "beginner":
        if 0.8 <= height <= 1.5:
            return 25
        return -20

    if level == "intermediate":
        if 1.0 <= height <= 2.5:
            return 25
        return -10

    if level == "advanced":
        if height >= 1.5:
            return 25
        return -5

    return 0


def period_score(period):
    if period >= 12:
        return 20
    if period >= 10:
        return 10
    return -5


# =========================
# MAIN SCORING
# =========================
def score_spot(data: dict, level: str, spot_name: str) -> float:
    try:
        cfg = SPOT_CONFIG[spot_name]

        height = data.get("wave_height", 0)
        period = data.get("period", 0)
        wind_speed = data.get("wind_speed", 0)
        wind_dir = data.get("wind_direction", 0)
        swell_dir = data.get("swell_direction", 0)

        score = 50  # base

        score += wave_score(height, level)
        score += period_score(period)
        score += wind_score(wind_speed, wind_dir, cfg["offshore_wind"])
        score += swell_score(swell_dir, cfg["ideal_swell_dir"])

        # clamp 0–100
        return max(0, min(100, score))

    except Exception as e:
        print("Score error:", e)
        return 0


# =========================
# PICK BEST
# =========================
def pick_best_spots(spots_with_data, level):
    scored = []

    for item in spots_with_data:
        spot = item["spot"]
        data = item["data"]

        score = score_spot(data, level, spot["name"])

        scored.append({
            "spot": spot,
            "data": data,
            "score": score
        })

    scored.sort(key=lambda x: x["score"], reverse=True)

    return {
        "best": scored[0],
        "alternative": scored[1]
    }