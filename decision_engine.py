from spots import SPOTS


def calculate_spot_score(
        spot,
        conditions,
        level
):

    score = 0
    reasons = []


    height = conditions.get(
        "wave_height",
        0
    )

    period = conditions.get(
        "period",
        0
    )

    swell = conditions.get(
        "swell_direction",
        ""
    )


    spot_rules = SPOTS[spot]



    # --------------------
    # Level
    # --------------------

    if level == "beginner":

        if spot_rules["beginner"]:
            score += 20
            reasons.append(
                "good for your level"
            )


    else:

        score += 10



    # --------------------
    # Wave height
    # --------------------

    if 1.0 <= height <= 2.0:

        score += 25

        reasons.append(
            "good wave size"
        )


    elif height < 1:

        score += 10

        reasons.append(
            "small waves"
        )


    else:

        score += 15



    # --------------------
    # Period
    # --------------------

    if period >= 12:

        score += 25

        reasons.append(
            "strong swell period"
        )

    elif period >= 8:

        score += 15



    # --------------------
    # Swell direction
    # --------------------

    if swell in spot_rules["swell"]:

        score += 30

        reasons.append(
            "good swell direction"
        )



    return score, reasons



def build_recommendation(
        forecast,
        level
):


    results = []



    for spot, conditions in forecast.items():


        score, reasons = calculate_spot_score(
            spot,
            conditions,
            level
        )


        results.append(

            {
                "spot": spot,
                "score": score,
                "reasons": reasons
            }

        )



    spot_order = {
        spot: index
        for index, spot in enumerate(SPOTS)
    }


    results.sort(
        key=lambda x: (
            -x["score"],
            -int(
                level == "beginner"
                and SPOTS[x["spot"]]["beginner"]
            ),
            spot_order[x["spot"]]
        )
    )



    best = results[0]


    alternatives = [
        x["spot"]
        for x in results[1:3]
    ]


    if best["score"] >= 75:
        confidence = "high"

    elif best["score"] >= 50:
        confidence = "medium"

    else:
        confidence = "low"



    return {

        "best": best["spot"],

        "score": best["score"],

        "reasons": best["reasons"],

        "conditions": forecast[best["spot"]],

        "confidence": confidence,

        "alternatives":
            alternatives

    }
