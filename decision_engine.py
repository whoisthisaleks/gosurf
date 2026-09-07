def _safe_get(d, key, default=None):
    return d.get(key, default)


# ======================
# SCORING
# ======================

def _wave_score(level, wave):
    if wave is None:
        return 0

    if level == "Beginner":
        if 0.5 <= wave <= 1.2:
            return 3
        elif wave < 1.5:
            return 1
        return -2

    if level == "Intermediate":
        if 1 <= wave <= 2:
            return 3
        return 1

    if level == "Advanced":
        if wave >= 1.5:
            return 3
        return 1

    return 0


def _wind_score(wind):
    if wind == "offshore":
        return 3
    if wind == "cross":
        return 1
    if wind == "onshore":
        return -2
    return 0


def _period_score(period):
    if period is None:
        return 0

    if period >= 10:
        return 2
    elif period >= 7:
        return 1
    return 0


def _swell_score(spot, swell_dir):
    if swell_dir is None:
        return 0

    swell_min = spot.get("swell_min")
    swell_max = spot.get("swell_max")

    # 👉 КЛЮЧЕВОЙ FIX (никаких KeyError)
    if swell_min is None or swell_max is None:
        return 0

    if swell_min <= swell_dir <= swell_max:
        return 2

    return 0


# ======================
# TOTAL SCORE
# ======================

def score_spot(data, spot_config, level):
    score = 0

    score += _wave_score(level, data.get("wave"))
    score += _wind_score(data.get("wind"))
    score += _period_score(data.get("period"))
    score += _swell_score(spot_config, data.get("swell_dir"))

    return score


# ======================
# PICK BEST
# ======================

def pick_best_spots(spots_data, level):
    scored = []

    for data in spots_data:
        # ищем конфиг по имени
        spot_config = next(
            (s for s in spots_data if s["spot"] == data["spot"]),
            {}
        )

        s = score_spot(data, spot_config, level)
        scored.append((data, s))

    scored.sort(key=lambda x: x[1], reverse=True)

    best = scored[0][0]
    alternatives = [x[0] for x in scored[1:3]]

    return best, alternatives