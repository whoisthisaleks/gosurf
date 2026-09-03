from score import calculate_score

def pick_best(spots, level):
    scored = []

    for spot in spots:
        score = calculate_score(spot, level)
        spot["score"] = score
        scored.append(spot)

    scored = sorted(scored, key=lambda x: x["score"], reverse=True)

    best = scored[0]
    alternatives = scored[1:3]

    return best, alternatives