SPOTS = {
    "Uluwatu": {
        "lat": -8.829,
        "lng": 115.084,

        # уровень
        "beginner": False,

        # волна
        "min_wave": 1.2,
        "max_wave": 3.5,

        # период
        "optimal_period": 12,

        # направление свелла
        "swell": ["SW", "S"],

        # ветер
        "offshore": ["E", "NE"],
        "onshore": ["W", "SW"],

        # новое
        "type": "reef",
        "tide_preference": ["mid", "high"],
        "danger_level": 3,
    },

    "Canggu": {
        "lat": -8.651,
        "lng": 115.138,

        "beginner": True,

        "min_wave": 0.8,
        "max_wave": 2.5,

        "optimal_period": 10,

        "swell": ["SW", "W"],

        "offshore": ["E", "NE"],
        "onshore": ["W"],

        "type": "beach",
        "tide_preference": ["low", "mid"],
        "danger_level": 1,
    },

    "Kuta": {
        "lat": -8.717,
        "lng": 115.168,

        "beginner": True,

        "min_wave": 0.5,
        "max_wave": 2.0,

        "optimal_period": 9,

        "swell": ["SW", "W"],

        "offshore": ["E"],
        "onshore": ["W"],

        "type": "beach",
        "tide_preference": ["low", "mid"],
        "danger_level": 1,
    },

    "Medewi": {
        "lat": -8.419,
        "lng": 114.802,

        "beginner": False,

        "min_wave": 1.0,
        "max_wave": 3.0,

        "optimal_period": 11,

        "swell": ["SW"],

        "offshore": ["SE", "E"],
        "onshore": ["W"],

        "type": "point",
        "tide_preference": ["mid", "high"],
        "danger_level": 2,
    }
}