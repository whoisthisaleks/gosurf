def pick_best_spots(spots_data, level):
    results = []

    for spot in spots_data:
        try:
            score = 0

            wave = spot.get("wave_height", 0)
            period = spot.get("period", 0)
            wind = spot.get("wind", 0)

            # простая логика
            score += wave * 10
            score += period * 5
            score -= wind * 3

            results.append({
                "name": spot.get("name"),
                "score": round(score, 1),
                "wave_height": wave,
                "period": period,
                "wind": wind
            })

        except Exception:
            continue

    # сортировка
    results = sorted(results, key=lambda x: x["score"], reverse=True)

    return results