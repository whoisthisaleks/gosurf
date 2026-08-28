SPOTS = {
    "Uluwatu": {
        "lat": -8.8296,
        "lng": 115.0849,

        # условия
        "swell": ["SW", "S", "SE"],
        "offshore": ["E", "NE"],
        "onshore": ["W", "SW"],

        # уровень
        "beginner": False,

        # приоритет (меньше = лучше)
        "priority": {
            "beginner": 99,
            "intermediate": 2,
            "advanced": 1
        },

        # прилив
        "tide_preference": ["mid", "high"]
    },

    "Canggu": {
        # Batu Bolong (основной учебный пик)
        "lat": -8.6617,
        "lng": 115.1300,

        "swell": ["SW", "S"],
        "offshore": ["E", "NE"],
        "onshore": ["W", "SW"],

        "beginner": True,

        "priority": {
            "beginner": 2,
            "intermediate": 1,
            "advanced": 3
        },

        "tide_preference": ["mid"]
    },

    "Kuta": {
        # центральный пляж
        "lat": -8.7184,
        "lng": 115.1686,

        "swell": ["SW", "S"],
        "offshore": ["E"],
        "onshore": ["W"],

        "beginner": True,

        "priority": {
            "beginner": 1,
            "intermediate": 4,
            "advanced": 5
        },

        "tide_preference": ["mid", "high"]
    },

    "Medewi": {
        # main point
        "lat": -8.4260,
        "lng": 114.7903,

        "swell": ["SW", "S"],
        "offshore": ["E", "NE"],
        "onshore": ["W"],

        "beginner": False,

        "priority": {
            "beginner": 3,
            "intermediate": 3,
            "advanced": 2
        },

        "tide_preference": ["mid", "high"]
    }
}