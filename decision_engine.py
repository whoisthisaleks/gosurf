from spots import SPOTS


def calculate_spot_score(spot, conditions, level):
    score = 0
    reasons = []

    height = conditions.get("wave_height", 0)
    period = conditions.get("period", 0)
    swell = conditions.get("swell_direction", "")
    wind_speed = conditions.get("wind_speed", 0)
    wind_direction = conditions.get("wind_direction", "")
    tide = conditions.get("tide")

    spot_rules = SPOTS[spot]

    # Level
    if level == "beginner":
        if spot_rules.get("beginner"):
            score += 20
            reasons.append("good for your level")
    else:
        score += 10

    # Wave
    if level == "beginner":
        if 0.5 <= height <= 1.5:
            score += 30
            reasons.append("safe wave size")
        elif height < 0.5:
            score += 10
        else:
            score += 5
    else:
        if 1.2 <= height <= 2.5:
            score += 30
            reasons.append("good wave size")
        elif height < 1.2:
            score += 15
        else:
            score += 20

    # Period
    if period >= 12:
        score += 20
        reasons.append("strong swell")
    elif period >= 8:
        score += 10

    # Swell
    if swell in spot_rules.get("swell", []):
        score += 20
        reasons.append("good swell direction")

    # Wind
    if wind_direction == "unknown":
        score -= 15
    elif wind_direction in spot_rules.get("offshore", []):
        score += 20
        reasons.append("offshore wind")
    elif wind_direction in spot_rules.get("onshore", []):
        score -= 10
        reasons.append("onshore wind")

    if wind_speed >= 10:
        score -= 10

    # Tide
    if tide is not None:
        tide_pref = spot_rules.get("tide_preference", [])

        if tide < 0.8:
            tide_state = "low"
        elif tide < 1.8:
            tide_state = "mid"
        else:
            tide_state = "high"

        if tide_state in tide_pref:
            score += 10
            reasons.append("good tide")
        else:
            score -= 5

    return score, reasons


# --------------------
# BEST TIME
# --------------------
def find_best_time(hourly_forecast, best_spot, level):
    hours = hourly_forecast.get(best_spot, [])

    best_score = -999
    best_hour = None

    for hour in hours:
        score, _ = calculate_spot_score(best_spot, hour, level)

        if score > best_score:
            best_score = score
            best_hour = hour

    if not best_hour:
        return None

    start = best_hour.get("time")

    try:
        h = int(start.split(":")[0])
        end = f"{(h + 1) % 24:02d}:00"
    except:
        end = start

    return f"{start}–{end}"


# --------------------
# MORNING vs AFTERNOON
# --------------------
def analyze_day_parts(hourly_forecast, spot, level):
    hours = hourly_forecast.get(spot, [])

    morning_scores = []
    afternoon_scores = []

    for hour in hours:
        time = hour.get("time")
        if not time:
            continue

        try:
            h = int(time.split(":")[0])
        except:
            continue

        score, _ = calculate_spot_score(spot, hour, level)

        if 5 <= h < 11:
            morning_scores.append(score)
        elif 11 <= h < 18:
            afternoon_scores.append(score)

    def avg(arr):
        return sum(arr) / len(arr) if arr else 0

    morning_avg = avg(morning_scores)
    afternoon_avg = avg(afternoon_scores)

    if morning_avg > afternoon_avg:
        return "morning"
    elif afternoon_avg > morning_avg:
        return "afternoon"
    else:
        return None


def build_recommendation(forecast, level, hourly_forecast=None):
    results = []

    for spot, conditions in forecast.items():
        score, reasons = calculate_spot_score(spot, conditions, level)

        results.append(
            {
                "spot": spot,
                "score": score,
                "reasons": reasons,
            }
        )

    results.sort(key=lambda x: -x["score"])

    best = results[0]
    alternatives = [x["spot"] for x in results[1:3]]

    best_time = None
    best_part = None

    if hourly_forecast:
        best_time = find_best_time(hourly_forecast, best["spot"], level)
        best_part = analyze_day_parts(hourly_forecast, best["spot"], level)

    return {
        "best": best["spot"],
        "score": best["score"],
        "reasons": best["reasons"],
        "conditions": forecast[best["spot"]],
        "alternatives": alternatives,
        "best_time": best_time,
        "best_part": best_part,
    }