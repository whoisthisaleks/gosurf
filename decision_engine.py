def get_condition_label(score):
    if score >= 13:
        return "🚀 EPIC"
    elif score >= 9:
        return "🔥 GOOD"
    elif score >= 5:
        return "👍 OKAY"
    else:
        return "❌ BAD"


def analyze_conditions(data, level):
    reasons = []

    if data["period"] >= 12:
        reasons.append("Long period")
    elif data["period"] >= 9:
        reasons.append("Decent period")

    if data["wind"] < 5:
        reasons.append("Light wind")

    if data["offshore"]:
        reasons.append("Offshore wind")
    else:
        reasons.append("Onshore wind")

    if data["swell_good"]:
        reasons.append("Good swell direction")

    return reasons


def enrich_spot(data, level):
    from math import floor

    score = score_spot(data, level)

    data["score"] = score
    data["label"] = get_condition_label(score)

    # 👉 добавляем computed поля
    data["offshore"] = is_offshore(data["name"], data["wind_dir"])
    data["swell_good"] = swell_good_for_spot(data["name"], data["swell_dir"])

    data["reasons"] = analyze_conditions(data, level)

    return data


def pick_best_spots(spots_data, level):
    enriched = []

    for spot in spots_data:
        try:
            enriched.append(enrich_spot(spot, level))
        except Exception:
            continue

    enriched = sorted(enriched, key=lambda x: x["score"], reverse=True)

    best = enriched[0] if len(enriched) > 0 else None
    second = enriched[1] if len(enriched) > 1 else None

    return best, second