import asyncio

import httpx

import api


def get(path):
    async def request():
        transport = httpx.ASGITransport(app=api.app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            return await client.get(path)

    return asyncio.run(request())


def test_health_and_spots_responses():
    assert get("/v1/health").json() == {"status": "ok"}

    response = get("/v1/spots")
    assert response.status_code == 200
    assert response.json()[0] == {
        "name": "Uluwatu Suluban",
        "latitude": -8.818,
        "longitude": 115.089,
    }


def test_forecast_uses_live_results_and_explicit_level(monkeypatch):
    calls = []

    def live_weather(spot):
        calls.append(spot["name"])
        return {
            "spot": spot["name"],
            "wave": 1.4,
            "period": 12,
            "wind": "offshore",
            "wind_speed": 5,
            "swell_dir": 220,
            "tide": "mid",
            "best_time": "09:00–12:00",
            "api_best_time": "09:00–12:00",
            "data_source": "stormglass",
            "available_fields": ["wave", "period", "wind_speed", "wind_direction", "wave_direction"],
        }

    monkeypatch.setattr(api, "fetch_spot_weather", live_weather)

    response = get("/v1/forecast?level=Advanced")
    body = response.json()
    assert response.status_code == 200
    assert body["level"] == "Advanced"
    assert body["status"] == "live"
    assert len(calls) == len(api.SPOTS)
    assert body["spots"][0]["wave_height"] == 1.4
    assert body["spots"][0]["data_source"] == "stormglass"
    assert body["spots"][0]["tide"] is None
    assert body["spots"][0]["best_time"] == "09:00–12:00"
    assert body["recommendation"] is not None


def test_forecast_never_exposes_fallback_defaults_or_recommends_them(monkeypatch):
    monkeypatch.setattr(
        api,
        "fetch_spot_weather",
        lambda spot: {
            "spot": spot["name"],
            "wave": 0.8,
            "period": 8,
            "wind_speed": 5,
            "data_source": "fallback",
        },
    )

    body = get("/v1/forecast").json()
    assert body["status"] == "unavailable"
    assert body["recommendation"] is None
    assert all(item["data_source"] == "unavailable" for item in body["spots"])
    assert all(item["wave_height"] is None for item in body["spots"])
    assert all(item["period"] is None for item in body["spots"])


def test_forecast_marks_mixed_provider_results_partial(monkeypatch):
    monkeypatch.setattr(
        api,
        "fetch_spot_weather",
        lambda spot: {
            "spot": spot["name"],
            "wave": 1.2,
            "period": 10,
            "wind": "cross",
            "wind_speed": 4,
            "swell_dir": 220,
            "tide": "mid",
            "best_time": None,
            "data_source": "stormglass" if spot is api.SPOTS[0] else "fallback",
            "available_fields": ["wave", "period", "wind_speed", "wind_direction", "wave_direction"] if spot is api.SPOTS[0] else [],
        },
    )

    body = get("/v1/forecast").json()
    assert body["status"] == "partial"
    assert body["spots"][0]["wave_height"] == 1.2
    assert body["spots"][1]["wave_height"] is None
    assert body["recommendation"]["spot"] == api.SPOTS[0]["name"]


def test_forecast_hides_defaulted_fields_and_excludes_synthetic_tide_from_scoring(monkeypatch):
    def partial_weather(spot):
        return {
            "spot": spot["name"],
            "wave": 0.8,
            "period": 12,
            "wind": "offshore",
            "wind_speed": 5,
            "swell_dir": None,
            "tide": "mid",
            "data_source": "stormglass",
            "available_fields": ["period"],
        }

    seen = {}

    def pick_best_spots(data, level):
        seen["data"] = data
        return (
            {"spot": data[0]["spot"], "reason": "clean period", "confidence": "👍 Good", "bad_day": False},
            [],
        )

    monkeypatch.setattr(api, "fetch_spot_weather", partial_weather)
    monkeypatch.setattr(api, "pick_best_spots", pick_best_spots)

    body = get("/v1/forecast").json()
    assert body["spots"][0]["wave_height"] is None
    assert body["spots"][0]["period"] == 12
    assert body["spots"][0]["wind"] is None
    assert body["spots"][0]["tide"] is None
    assert seen["data"][0]["wave"] is None
    assert seen["data"][0]["wind"] is None
    assert seen["data"][0]["tide"] is None


def test_wind_speed_alone_does_not_create_a_recommendation(monkeypatch):
    monkeypatch.setattr(
        api,
        "fetch_spot_weather",
        lambda spot: {
            "spot": spot["name"],
            "wave": 0.8,
            "period": 8,
            "wind_speed": 5,
            "data_source": "stormglass",
            "available_fields": ["wind_speed"],
        },
    )

    body = get("/v1/forecast").json()
    assert body["status"] == "live"
    assert body["spots"][0]["wind_speed"] == 5
    assert body["recommendation"] is None


def test_forecast_rejects_unknown_level():
    assert get("/v1/forecast?level=Expert").status_code == 422
