def get_condition_label(score):
    if score >= 13:
        return "EPIC"
    elif score >= 9:
        return "GOOD"
    elif score >= 5:
        return "OKAY"
    else:
        return "BAD"


def is_offshore(spot, wind_dir):
    offshore_map = {
        "Uluwatu": ["E", "NE", "SE"],
        "Canggu": ["E", "SE"],
        "Kuta": ["E", "SE"],
        "Medewi": ["E", "SE"]
    }
    return wind_dir in offshore_map.get(spot, [])


def swell_good_for_spot(spot, swell_dir):
    swell_map = {
        "Uluwatu": ["SW", "S", "WSW"],
        "Canggu": ["W", "NW", "SW"],
        "Kuta": ["W", "SW"],
        "Medewi": ["SW", "S"]
    }
    return swell_dir in swell_map.get(spot, [])


def score_hour(hour, spot_name, level):
    score = 0

    wave = hour["wave"]
    period = hour["period"]
    wind = hour["wind"]

    # wave
    if level == "beginner":
        if 0.5 <= wave <= 1.5:
            score += 3
    elif level == "intermediate":
        if 1 <= wave <= 2.5:
            score += 3
    else:
        if wave >= 1.5:
            score += 3

    # period
    if period >= 12:
        score += 3
    elif period >= 9:
        score += 2

    # wind
    if wind < 5:
        score += 3
    elif wind < 8:
        score += 1
    else:
        score -= 2

    # offshore
    if is_offshore(spot_name, hour["wind_dir"]):
        score += 4
    else:
        score -= 2

    # swell
    if swell_good_for_spot(spot_name, hour["swell_dir"]):
        score += 3

    return score


def find_best_window(hours, spot_name, level):
    scored = []

    for h in hours:
        try:
            s = score_hour(h, spot_name, level)
            scored.append({**h, "score": s})
        except Exception:
            continue

    scored = sorted(scored, key=lambda x: x["score"], reverse=True)

    if not scored:
        return None, None, None

    best = scored[0]

    # ищем окно ±2 часа
    best_index = hours.index(next(h for h in hours if h["time"] == best["time"]))

    start = max(0, best_index - 1)
    end = min(len(hours) - 1, best_index + 1)

    window = f"{hours[start]['time']}–{hours[end]['time']}"

    return best, window, best["score"]


def analyze_reasons(hour, spot_name):
    reasons = []

    if is_offshore(spot_name, hour["wind_dir"]):
        reasons.append("Offshore wind")
    else:
        reasons.append("Onshore wind")

    if hour["period"] >= 12:
        reasons.append("Long period")

    if hour["wind"] < 5:
        reasons.append("Light wind")

    if swell_good_for_spot(spot_name, hour["swell_dir"]):
        reasons.append("Good swell direction")

    return reasons


def pick_best_spots(spots_data, level):
    results = []

    for spot in spots_data:
        try:
            best_hour, window, score = find_best_window(
                spot["hours"], spot["name"], level
            )

            if not best_hour:
                continue

            result = {
                "name": spot["name"],
                "wave": best_hour["wave"],
                "period": best_hour["period"],
                "wind": best_hour["wind"],
                "time": best_hour["time"],
                "window": window,
                "score": score,
                "label": get_condition_label(score),
                "reasons": analyze_reasons(best_hour, spot["name"])
            }

            results.append(result)

        except Exception:
            continue

    results = sorted(results, key=lambda x: x["score"], reverse=True)

    best = results[0] if len(results) > 0 else None
    second = results[1] if len(results) > 1 else None

    return best, second