import math


# ======================
# HELPERS
# ======================

def _in_range(value, min_v, max_v):
    if value is None:
        return False
    return min_v <= value <= max_v


def _swell_score(spot, swell_dir):
    if swell_dir is None:
        return 0

    if _in_range(swell_dir, spot["swell_min"], spot["swell_max"]):
        return 3
    return 0


def _wind_score(wind):
    if wind is None:
        return 0

    if wind == "offshore":
        return 3
    elif wind == "cross":
        return 1
    elif wind == "onshore":
        return -2

    return 0


def _wave_score(level, wave):
    if wave is None:
        return 0

    if level == "Beginner":
        if 0.5 <= wave <= 1.2:
            return 2
        elif wave > 1.5:
            return -2

    elif level == "Intermediate":
        if 1.0 <= wave <= 2.0:
            return 2

    elif level == "Advanced":
        if wave >= 1.5:
            return 2

    return 0


def _period_score(period):
    if period is None:
        return 0

    if period >= 10:
        return 2
    elif period >= 7:
        return 1

    return 0


def _tide_score(tide):
    if tide is None:
        return 0

    if tide in ["mid", "incoming"]:
        return 1

    return 0


# ======================
# CONFIDENCE
# ======================

def get_confidence(score):
    if score >= 7:
        return "🔥 Epic"
    elif score >= 4:
        return "👍 Good"
    else:
        return "⚠️ Poor"


def is_bad_day(score):
    return score < 4    


# ======================
# REASON
# ======================

def build_reason(data, level):
    reasons = []

    if data.get("wind") == "offshore":
        reasons.append("offshore wind")
    elif data.get("wind") == "cross":
        reasons.append("light cross wind")

    if data.get("swell_dir"):
        reasons.append("good swell angle")

    if data.get("period") and data["period"] >= 8:
        reasons.append("clean period")

    if level == "Beginner":
        if data.get("wave") and data["wave"] <= 1.2:
            reasons.append("safe size")

    if level == "Advanced":
        if data.get("wave") and data["wave"] >= 1.8:
            reasons.append("powerful waves")

    return " + ".join(reasons) if reasons else "average conditions"


# ======================
# SCORING
# ======================

def score_spot(data, spot_config, level):
    score = 0

    score += _swell_score(spot_config, data.get("swell_dir"))
    score += _wind_score(data.get("wind"))
    score += _wave_score(level, data.get("wave"))
    score += _period_score(data.get("period"))
    score += _tide_score(data.get("tide"))

    return score


# ======================
# MAIN
# ======================

def pick_best_spots(all_data, level):
    scored = []

    from spots import SPOTS

    # 🔒 делаем безопасный индекс
    spot_map = {s["name"]: s for s in SPOTS if isinstance(s, dict)}

    for data in all_data:
        try:
            spot_name = data.get("spot")

            if spot_name not in spot_map:
                print("UNKNOWN SPOT:", spot_name)
                continue

            spot_config = spot_map[spot_name]

            s = score_spot(data, spot_config, level)
            scored.append((s, data))

        except Exception as e:
            print("SCORING ERROR:", e)
            continue

    if not scored:
        raise Exception("No valid spots to score")

    scored.sort(key=lambda x: x[0], reverse=True)

    best_score, best = scored[0]
    alternatives = [x[1] for x in scored[1:3]]

    # добавляем умные поля
    best["reason"] = build_reason(best, level)
    best["confidence"] = get_confidence(best_score)
    best["bad_day"] = is_bad_day(best_score)

    return best, alternatives