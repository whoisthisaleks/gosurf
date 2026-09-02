def is_offshore(spot_name: str, wind_dir: float) -> bool:
    """
    Простая модель направлений для Бали
    """

    # нормализуем угол
    wd = wind_dir % 360

    if spot_name in ["Canggu", "Kuta", "Medewi"]:
        # offshore: 60–140 (E-SE)
        return 60 <= wd <= 140

    if spot_name == "Uluwatu":
        # offshore: 30–120 (NE-E)
        return 30 <= wd <= 120

    return False


def score_wave_height(height: float, level: str) -> float:
    if level == "beginner":
        if 0.8 <= height <= 1.5:
            return 30
        elif height < 0.8:
            return 10
        else:
            return -20

    if level == "intermediate":
        if 1.0 <= height <= 2.5:
            return 30
        elif height < 1.0:
            return 10
        else:
            return 5

    if level == "advanced":
        if height >= 1.5:
            return 30
        else:
            return 10

    return 0


def score_period(period: float) -> float:
    if period >= 12:
        return 30
    elif period >= 10:
        return 20
    elif period >= 8:
        return 10
    else:
        return -10


def score_wind(speed: float, offshore: bool) -> float:
    score = 0

    # ветер по силе
    if speed < 3:
        score += 15
    elif speed < 6:
        score += 5
    else:
        score -= 10

    # направление
    if offshore:
        score += 25
    else:
        score -= 20

    return score


def score_spot(data: dict, level: str, spot_name: str) -> float:
    if not data:
        return -999

    wave = data.get("wave_height", 0)
    period = data.get("period", 0)
    wind = data.get("wind_speed", 0)
    wind_dir = data.get("wind_direction", 0)

    offshore = is_offshore(spot_name, wind_dir)

    score = 0

    score += score_wave_height(wave, level)
    score += score_period(period)
    score += score_wind(wind, offshore)

    return score


def build_reason(data: dict, level: str, spot_name: str) -> str:
    wave = data.get("wave_height", 0)
    period = data.get("period", 0)
    wind = data.get("wind_speed", 0)
    wind_dir = data.get("wind_direction", 0)

    offshore = is_offshore(spot_name, wind_dir)

    reasons = []

    # волна
    if level == "beginner" and 0.8 <= wave <= 1.5:
        reasons.append("Safe wave size")
    elif level == "intermediate" and 1 <= wave <= 2.5:
        reasons.append("Good wave size")
    elif level == "advanced" and wave >= 1.5:
        reasons.append("Powerful waves")

    # период
    if period >= 10:
        reasons.append("Long clean swell")

    # ветер
    if offshore:
        reasons.append("Offshore wind")
    else:
        reasons.append("Onshore wind")

    return "\n".join(reasons)


def pick_best_spots(spots_with_data, level: str):
    scored = []

    for item in spots_with_data:
        spot = item["spot"]
        data = item["data"]

        s = score_spot(data, level, spot["name"])

        scored.append({
            "spot": spot,
            "data": data,
            "score": s
        })

    scored.sort(key=lambda x: x["score"], reverse=True)

    best = scored[0]
    alt = scored[1] if len(scored) > 1 else scored[0]

    return {
        "best": best,
        "alternative": alt
    }