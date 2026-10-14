import weather


def test_old_cache_entry_is_refreshed_with_provenance(monkeypatch):
    spot = {
        "name": "Example Spot",
        "lat": -8.0,
        "lng": 115.0,
        "offshore": 90,
    }
    calls = {"weather": 0, "cache": 0}

    monkeypatch.setattr(
        weather,
        "get_cache",
        lambda key: {"spot": spot["name"], "best_time": "09:00–12:00"},
    )
    monkeypatch.setattr(weather, "increment_api_calls", lambda: None)
    monkeypatch.setattr(weather, "_fake_tide_by_time", lambda: "mid")

    class Response:
        status_code = 200

        @staticmethod
        def json():
            return {
                "hours": [
                    {
                        "time": "2026-10-14T10:00:00+00:00",
                        "waveHeight": {"sg": 1.1},
                        "wavePeriod": {"sg": 12},
                        "windSpeed": {"sg": 4},
                        "windDirection": {"sg": 90},
                        "waveDirection": {"sg": 220},
                    }
                ]
            }

    def fake_get(*args, **kwargs):
        calls["weather"] += 1
        return Response()

    def fake_set_cache(*args, **kwargs):
        calls["cache"] += 1

    monkeypatch.setattr(weather.requests, "get", fake_get)
    monkeypatch.setattr(weather, "set_cache", fake_set_cache)

    result = weather.fetch_spot_weather(spot)

    assert calls == {"weather": 1, "cache": 1}
    assert result["data_source"] == "stormglass"
    assert result["available_fields"] == [
        "wave",
        "period",
        "wind_speed",
        "wind_direction",
        "wave_direction",
    ]
