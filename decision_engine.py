from spots import SPOTS
from weather import fetch_weather


def score_spot(data, level):
    score = 0

    wave = data["wave"]
    period = data["period"]
    wind = data["wind"]

    # --- wave scoring
    if level == "beginner":
        if 0.8 <= wave <= 1.5:
            score += 3
    elif level == "intermediate":
        if 1.2 <= wave <= 2.0:
            score += 3
    else:
        if wave >= 1.5:
            score += 3

    # --- period
    if period >= 10:
        score += 2

    # --- wind (lower better)
    if wind < 6:
        score += 2

    return score


async def get_best_spot(level):
    results = []

    for spot in SPOTS:
        data = await fetch_weather(spot["lat"], spot["lng"])
        s = score_spot(data, level)

        results.append({
            "spot": spot["name"],
            "score": s,
            "data": data
        })

    best = sorted(results, key=lambda x: x["score"], reverse=True)[0]

    return format_result(best)


async def get_alternative_spots(level):
    results = []

    for spot in SPOTS:
        data = await fetch_weather(spot["lat"], spot["lng"])
        s = score_spot(data, level)

        results.append({
            "spot": spot["name"],
            "score": s,
            "data": data
        })

    sorted_spots = sorted(results, key=lambda x: x["score"], reverse=True)[1:3]

    return [format_result(s) for s in sorted_spots]


def format_result(item):
    d = item["data"]

    return {
        "spot": item["spot"],
        "wave": round(d["wave"], 1),
        "period": int(d["period"]),
        "wind": round(d["wind"], 1),
        "why": build_why(d)
    }


def build_why(d):
    reasons = []

    if d["wave"] > 1:
        reasons.append("good wave height")

    if d["period"] >= 10:
        reasons.append("long swell period")

    if d["wind"] < 6:
        reasons.append("light wind")

    return ", ".join(reasons)