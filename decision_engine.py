# ===== SIMPLE DECISION ENGINE (STABLE) =====

def extract_conditions(weather):
    try:
        hour = weather["hours"][0]

        return {
            "wave": hour.get("waveHeight", {}).get("sg"),
            "period": hour.get("wavePeriod", {}).get("sg"),
            "wind": hour.get("windSpeed", {}).get("sg"),
        }
    except Exception:
        return {
            "wave": None,
            "period": None,
            "wind": None,
        }


def format_conditions(c):
    return {
        "wave": f"{c['wave']} m" if c["wave"] else "—",
        "period": f"{c['period']} s" if c["period"] else "—",
        "wind": f"{c['wind']} m/s" if c["wind"] else "—",
    }


def generate_reason(c):
    return f"""
Wave: {c['wave']} m
Period: {c['period']} s
Wind: {c['wind']} m/s
"""


# ===== SPOTS =====

SPOTS = [
    {"name": "Uluwatu", "level": ["advanced"]},
    {"name": "Canggu", "level": ["intermediate", "advanced"]},
    {"name": "Kuta", "level": ["beginner", "intermediate"]},
    {"name": "Medewi", "level": ["intermediate", "advanced"]},
]


# ===== PUBLIC API =====

def get_best_spot(weather, level):
    c = extract_conditions(weather)

    # простая логика MVP
    for spot in SPOTS:
        if level in spot["level"]:
            return {
                "name": spot["name"],
                "reason": generate_reason(c),
                "conditions": format_conditions(c)
            }

    return {
        "name": "Kuta",
        "reason": generate_reason(c),
        "conditions": format_conditions(c)
    }


def get_alternatives(weather, level):
    c = extract_conditions(weather)

    alternatives = []

    for spot in SPOTS:
        if level in spot["level"]:
            alternatives.append({
                "name": spot["name"],
                "reason": generate_reason(c)
            })

    return alternatives[1:3]