from spots import SPOTS
from weather import fetch_weather
from ai_explainer import generate_explanation


# =========================
# HELPERS
# =========================

def get_direction(deg):
    dirs = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
    return dirs[int((deg + 22.5) // 45) % 8]


def wind_text(speed):
    if speed < 3:
        return "light"
    elif speed < 6:
        return "light/variable"
    elif speed < 10:
        return "moderate"
    return "strong"


# =========================
# SCORING
# =========================

def score_spot(spot, data, level):
    score = 0

    wave = data["wave"]
    period = data["period"]
    wind = data["wind"]

    # wave
    if level == "beginner" and 0.8 <= wave <= 1.4:
        score += 30
    elif level == "intermediate" and 1.0 <= wave <= 1.8:
        score += 30
    elif level == "advanced" and wave >= 1.5:
        score += 30

    # period
    if period >= 12:
        score += 25
    elif period >= 10:
        score += 18

    # wind
    if wind < 6:
        score += 20

    # swell direction
    swell = get_direction(data["direction"])
    if swell in spot["optimal_swell"]:
        score += 15

    # offshore wind
    wind_dir = get_direction(data["wind_dir"])
    if wind_dir in spot["offshore_wind"]:
        score += 20

    return min(score, 100)


# =========================
# CORE
# =========================

async def get_best_spot(level):
    results = []

    for spot in SPOTS:
        data = await fetch_weather(spot["lat"], spot["lng"])
        score = score_spot(spot, data, level)

        results.append({
            "spot": spot,
            "score": score,
            "data": data
        })

    results = sorted(results, key=lambda x: x["score"], reverse=True)

    best = results[0]
    alt1 = results[1]
    alt2 = results[2]

    reasons = await generate_explanation(level, best["spot"]["name"], best["data"])

    return format_result(best, reasons, [alt1["spot"]["name"], alt2["spot"]["name"]])


async def get_alternative_spots(level):
    results = []

    for spot in SPOTS:
        data = await fetch_weather(spot["lat"], spot["lng"])
        score = score_spot(spot, data, level)

        results.append({
            "spot": spot,
            "score": score,
            "data": data
        })

    results = sorted(results, key=lambda x: x["score"], reverse=True)[1:3]

    output = []

    for r in results:
        reasons = await generate_explanation(level, r["spot"]["name"], r["data"])
        output.append(format_result(r, reasons, []))

    return output


# =========================
# FORMAT
# =========================

def format_result(item, reasons, alts):
    d = item["data"]

    return {
        "spot": item["spot"]["name"],
        "lat": item["spot"]["lat"],
        "lng": item["spot"]["lng"],
        "score": item["score"],
        "wave": round(d["wave"], 1),
        "period": int(d["period"]),
        "swell": get_direction(d["direction"]),
        "wind_text": wind_text(d["wind"]),
        "reasons": reasons,
        "alts": alts
    }