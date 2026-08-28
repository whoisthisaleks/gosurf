import unittest

from decision_engine import build_recommendation
from weather import build_forecast


class ForecastContractTests(unittest.TestCase):
    def test_forecast_contains_tide_data_for_every_spot(self):
        forecast = build_forecast()

        self.assertEqual(set(forecast), {"Uluwatu", "Canggu", "Kuta", "Medewi"})
        for conditions in forecast.values():
            self.assertIsInstance(conditions["tide_level"], float)
            self.assertIn(conditions["tide_state"], {"rising", "falling"})


class RecommendationTests(unittest.TestCase):
    def test_recommendation_prioritizes_beginner_safe_conditions_and_tide(self):
        forecast = {
            "Uluwatu": {
                "wave_height": 1.4,
                "period": 13.0,
                "swell_direction": "SW",
                "wind_speed": 4.0,
                "wind_direction": "E",
                "tide_level": 1.3,
                "tide_state": "rising",
            },
            "Canggu": {
                "wave_height": 2.1,
                "period": 12.0,
                "swell_direction": "SW",
                "wind_speed": 5.0,
                "wind_direction": "W",
                "tide_level": 1.2,
                "tide_state": "falling",
            },
            "Kuta": {
                "wave_height": 0.6,
                "period": 8.0,
                "swell_direction": "W",
                "wind_speed": 7.0,
                "wind_direction": "N",
                "tide_level": 0.4,
                "tide_state": "rising",
            },
            "Medewi": {
                "wave_height": 1.8,
                "period": 10.0,
                "swell_direction": "SW",
                "wind_speed": 5.0,
                "wind_direction": "W",
                "tide_level": 2.3,
                "tide_state": "falling",
            },
        }

        recommendation = build_recommendation(forecast, "beginner")

        self.assertEqual(recommendation["best"], "Uluwatu")
        self.assertEqual(recommendation["score"], 100)
        self.assertEqual(recommendation["alternatives"], ["Canggu", "Medewi"])
        self.assertIn("favorable tide", recommendation["reasons"])


if __name__ == "__main__":
    unittest.main()
