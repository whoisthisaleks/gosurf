def pick_best(spots, level):
    ranked = []

    for spot in spots:
        score = calculate_score(spot, level)
        spot["score"] = score
        ranked.append(spot)

    ranked.sort(key=lambda x: x["score"], reverse=True)

    best = ranked[0]
    alternatives = ranked[1:3]

    return best, alternatives


from score import calculate_score