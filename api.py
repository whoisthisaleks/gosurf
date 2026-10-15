"""Read-only HTTP API for the GoSurf iOS client."""

from typing import Literal

from fastapi import FastAPI
from pydantic import BaseModel

from cache import get_cache, set_cache
from decision_engine import pick_best_spots
from spots import SPOTS
from weather import fetch_spot_weather


Level = Literal["Beginner", "Intermediate", "Advanced"]
SCORING_FIELDS = {"wave", "period", "wind_direction", "wave_direction"}
UNAVAILABLE_WEATHER_CACHE_TTL = 600

app = FastAPI(title="GoSurf API", version="1.0.0")


class HealthResponse(BaseModel):
    status: Literal["ok"]


class SpotResponse(BaseModel):
    name: str
    latitude: float
    longitude: float


class ForecastSpotResponse(BaseModel):
    name: str
    wave_height: float | None
    period: int | None
    wind: str | None
    wind_speed: float | None
    swell_direction: float | None
    tide: str | None
    best_time: str | None
    data_source: Literal["stormglass", "unavailable"]


class RecommendationResponse(BaseModel):
    spot: str
    reason: str
    confidence: str
    bad_day: bool


class ForecastResponse(BaseModel):
    level: Level
    status: Literal["live", "partial", "unavailable"]
    spots: list[ForecastSpotResponse]
    recommendation: RecommendationResponse | None
    alternatives: list[str]


def _forecast_spot(spot: dict, weather: dict) -> ForecastSpotResponse:
    """Expose measurements only when they came from an actual provider response."""
    available = set(weather.get("available_fields", []))
    is_live = (
        weather.get("data_source") == "stormglass"
        and bool(available.intersection({"wave", "period", "wind_speed", "wind_direction", "wave_direction"}))
    )
    return ForecastSpotResponse(
        name=spot["name"],
        wave_height=weather.get("wave") if is_live and "wave" in available else None,
        period=weather.get("period") if is_live and "period" in available else None,
        wind=weather.get("wind") if is_live and "wind_direction" in available else None,
        wind_speed=weather.get("wind_speed") if is_live and "wind_speed" in available else None,
        swell_direction=weather.get("swell_dir") if is_live and "wave_direction" in available else None,
        # The current tide value is synthetic; no tide provider is integrated yet.
        tide=None,
        best_time=weather.get("api_best_time") if is_live else None,
        data_source="stormglass" if is_live else "unavailable",
    )


def _fetch_api_weather(spot: dict) -> dict:
    """Cache unavailable provider results briefly for API callers only."""
    cache_key = f"api:unavailable-weather:{spot['name']}"
    cached = get_cache(cache_key)
    if cached is not None:
        return cached

    try:
        weather = fetch_spot_weather(spot)
    except Exception:
        weather = {"data_source": "fallback"}

    if weather.get("data_source") != "stormglass":
        set_cache(cache_key, weather, ttl=UNAVAILABLE_WEATHER_CACHE_TTL)

    return weather


@app.get("/v1/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok")


@app.get("/v1/spots", response_model=list[SpotResponse])
def list_spots() -> list[SpotResponse]:
    return [
        SpotResponse(name=spot["name"], latitude=spot["lat"], longitude=spot["lng"])
        for spot in SPOTS
    ]


@app.get("/v1/forecast", response_model=ForecastResponse)
def forecast(level: Level = "Intermediate") -> ForecastResponse:
    forecasts = []
    scoring_results = []

    for spot in SPOTS:
        weather = _fetch_api_weather(spot)
        forecast_spot = _forecast_spot(spot, weather)
        forecasts.append(forecast_spot)
        # Old cache entries lack source metadata and are conservatively excluded.
        if forecast_spot.data_source == "stormglass":
            trusted = dict(weather)
            available = set(weather.get("available_fields", []))
            # The legacy tide estimate is synthetic, and missing measurements are defaults.
            trusted["tide"] = None
            if "wind_direction" not in available:
                trusted["wind"] = None
            if "wave_direction" not in available:
                trusted["swell_dir"] = None
            if "wave" not in available:
                trusted["wave"] = None
            if "period" not in available:
                trusted["period"] = None
            # Wind speed alone cannot support a spot recommendation.
            if available.intersection(SCORING_FIELDS):
                scoring_results.append(trusted)

    recommendation = None
    alternatives: list[str] = []
    if scoring_results:
        best, other_spots = pick_best_spots(scoring_results, level)
        recommendation = RecommendationResponse(
            spot=best["spot"],
            reason=best["reason"],
            confidence=best["confidence"],
            bad_day=best["bad_day"],
        )
        alternatives = [item["spot"] for item in other_spots]

    live_count = sum(item.data_source == "stormglass" for item in forecasts)
    status = "unavailable" if live_count == 0 else (
        "live" if live_count == len(SPOTS) else "partial"
    )
    return ForecastResponse(
        level=level,
        status=status,
        spots=forecasts,
        recommendation=recommendation,
        alternatives=alternatives,
    )
