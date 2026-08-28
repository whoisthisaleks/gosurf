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

    wind_speed = conditions.get(
        "wind_speed",
        0
    )

    wind_direction = conditions.get(
        "wind_direction",
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

    if level == "beginner":

        if 0.5 <= height <= 1.5:

            score += 30

            reasons.append(
                "safe for beginners"
            )


        elif height < 0.5:

            score += 10

            reasons.append(
                "small waves"
            )


        else:

            score += 5

            reasons.append(
                "big waves (challenging)"
            )


    else:

        if 1.2 <= height <= 2.5:

            score += 30

            reasons.append(
                "fun wave size"
            )


        elif height < 1.2:

            score += 15

            reasons.append(
                "smaller waves"
            )


        else:

            score += 20

            reasons.append(
                "powerful waves"
            )



    # --------------------
    # Period
    # --------------------

    if level == "beginner":

        if period >= 12:

            score += 15

            reasons.append(
                "strong swell period"
            )

        elif period >= 8:

            score += 10


    else:

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

        if level == "beginner":
            score += 15

        else:
            score += 30

        reasons.append(
            "good swell direction"
        )


    # --------------------
    # Wind
    # --------------------

    if wind_direction in spot_rules.get("offshore", []):
        score += 20
        reasons.append("offshore wind")

    elif (
            wind_direction != "unknown"
            and wind_direction in spot_rules.get("onshore", [])
    ):
        score -= 10
        reasons.append("onshore wind")


    if wind_speed >= 10:
        score -= 10
        reasons.append("strong wind")



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
