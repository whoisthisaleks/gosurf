# ===== MULTI-SPOT ENGINE (SMART MVP) =====

def extract_base(weather):
    try:
        h = weather["hours"][0]

        return {
            "wave": h.get("waveHeight", {}).get("sg"),
            "period": h.get("wavePeriod", {}).get("sg"),
            "wind": h.get("windSpeed", {}).get("sg"),
        }
    except:
        return {
            "wave": None,
            "period": None,
            "wind": None,
        }


# ===== SPOT PROFILES =====
# оффсеты имитируют реальные различия

SPOTS = [
    {
        "name": "Kuta",
        "level": ["beginner", "intermediate"],
        "wave_offset": -0.5,
        "wind_multiplier": 0.9,
    },
    {
        "name": "Canggu",
        "level": ["intermediate", "advanced"],
        "wave_offset": 0,
        "wind_multiplier": 1.0,
    },
    {
        "name": "Uluwatu",
        "level": ["advanced"],
        "wave_offset": +0.7,
        "wind_multiplier": 1.1,
    },
    {
        "name": "Medewi",
        "level": ["intermediate", "advanced"],
        "wave_offset": -0.2,
        "wind_multiplier": 0.8,
    },
]


# ===== APPLY PROFILE =====

def apply_spot(base, spot):
    return {
        "wave": round((base["wave"] or 0) + spot["wave_offset"], 2),
        "period": base["period"],
        "wind": round((base["wind"] or 0) * spot["wind_multiplier"], 2),
    }


# ===== SCORING =====

def score(conditions, level):
    wave = conditions["wave"] or 0
    wind = conditions["wind"] or 0
    period = conditions["period"] or 0

    # базовый скоринг
    score = 0

    # wave
    if level == "beginner":
        score += max(0, 1 - abs(wave - 1.0))
    elif level == "intermediate":
        score += max(0, 1 - abs(wave - 1.5))
    else:
        score += min(1, wave / 3)

    # wind (меньше лучше)
    score += max(0, 1 - wind / 15)

    # period
    score += min(1, period / 12)

    return round(score * 100 / 3, 1)


# ===== FORMAT =====

def format_conditions(c):
    return {
        "wave": f"{c['wave']} m",
        "period": f"{c['period']} s",
        "wind": f"{c['wind']} m/s",
    }


# ===== PUBLIC =====

def get_best_spot(weather, level):
    base = extract_base(weather)

    scored = []

    for spot in SPOTS:
        if level not in spot["level"]:
            continue

        c = apply_spot(base, spot)
        s = score(c, level)

        scored.append((spot, c, s))

    scored.sort(key=lambda x: x[2], reverse=True)

    best = scored[0]

    return {
        "name": best[0]["name"],
        "conditions": format_conditions(best[1]),
    }


def get_alternatives(weather, level):
    base = extract_base(weather)

    scored = []

    for spot in SPOTS:
        if level not in spot["level"]:
            continue

        c = apply_spot(base, spot)
        s = score(c, level)

        scored.append((spot, c, s))

    scored.sort(key=lambda x: x[2], reverse=True)

    result = []

    for spot, cond, _ in scored[1:3]:
        result.append({
            "name": spot["name"],
            "conditions": format_conditions(cond)
        })

    return result