# ===== DECISION ENGINE (SURF LOGIC) =====

from typing import List, Dict


# ===== SCORING =====

def score_spot(data: dict, level: str) -> float:
    """
    data = {
        "wave_height": float,
        "period": float,
        "wind_speed": float
    }
    """

    wave = data.get("wave_height") or 0
    period = data.get("period") or 0
    wind = data.get("wind_speed") or 0

    score = 0.0

    # ===== WAVE HEIGHT =====
    if level == "beginner":
        # идеал 0.8–1.5
        if 0.8 <= wave <= 1.5:
            score += 40
        else:
            score += max(0, 40 - abs(wave - 1.1) * 25)

    elif level == "intermediate":
        # идеал 1–2.5
        if 1.0 <= wave <= 2.5:
            score += 40
        else:
            score += max(0, 40 - abs(wave - 1.7) * 20)

    else:  # advanced
        # любят больше волны
        if wave >= 1.5:
            score += min(40, wave * 15)
        else:
            score += wave * 10

    # ===== PERIOD =====
    if period >= 12:
        score += 30
    elif period >= 10:
        score += 20
    elif period >= 8:
        score += 10
    else:
        score += 0

    # ===== WIND =====
    # чем меньше — тем лучше
    if level == "beginner":
        if wind <= 5:
            score += 30
        else:
            score += max(0, 30 - (wind - 5) * 5)

    elif level == "intermediate":
        if wind <= 8:
            score += 30
        else:
            score += max(0, 30 - (wind - 8) * 4)

    else:  # advanced
        if wind <= 12:
            score += 30
        else:
            score += max(0, 30 - (wind - 12) * 3)

    return round(min(score, 100), 1)


# ===== PICK BEST =====

def pick_best_spots(spots_with_data: List[Dict], level: str) -> Dict:
    """
    spots_with_data = [
        {
            "name": "Uluwatu",
            "data": {...}
        }
    ]
    """

    scored = []

    for spot in spots_with_data:
        s = score_spot(spot["data"], level)

        scored.append({
            "name": spot["name"],
            "data": spot["data"],
            "score": s
        })

    # сортировка по убыванию
    scored.sort(key=lambda x: x["score"], reverse=True)

    # гарантируем минимум 2
    if len(scored) == 0:
        return {"best": None, "alternative": None}

    if len(scored) == 1:
        return {"best": scored[0], "alternative": scored[0]}

    return {
        "best": scored[0],
        "alternative": scored[1]
    }