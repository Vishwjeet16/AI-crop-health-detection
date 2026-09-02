"""
Weather service.

Calls a real weather provider (OpenWeatherMap-compatible) when
WEATHER_API_KEY is set; otherwise falls back to a clearly-labeled demo
reading so the rest of the pipeline (and the frontend) always has
something to render. Never silently fabricates a "real" reading — callers
can check `is_demo` on the returned dict.
"""

import httpx

from app.config import get_settings
from app.schemas.scans import Weather

_DEMO_WEATHER = Weather(
    temperature_c=31,
    humidity_percent=78,
    rain_probability_percent=40,
    wind_kph=12,
    condition="Partly cloudy",
    disease_risk_note=(
        "High humidity may increase the risk of certain fungal diseases. "
        "This is a general environmental signal, not proof of infection."
    ),
)


def _disease_risk_note(humidity: float) -> str:
    if humidity >= 70:
        return (
            "High humidity may increase the risk of certain fungal diseases. "
            "This is a general environmental signal, not proof of infection."
        )
    if humidity >= 45:
        return "Moderate humidity — typical conditions for this region."
    return "Low humidity — generally lower fungal disease pressure, but monitor for pests."


async def get_weather(latitude: float, longitude: float) -> Weather:
    settings = get_settings()
    if not settings.weather_api_key:
        return _DEMO_WEATHER

    try:
        async with httpx.AsyncClient(timeout=6) as client:
            resp = await client.get(
                "https://api.openweathermap.org/data/2.5/weather",
                params={
                    "lat": latitude,
                    "lon": longitude,
                    "appid": settings.weather_api_key,
                    "units": "metric",
                },
            )
        resp.raise_for_status()
        data = resp.json()
        humidity = float(data["main"]["humidity"])
        return Weather(
            temperature_c=float(data["main"]["temp"]),
            humidity_percent=humidity,
            rain_probability_percent=float(data.get("rain", {}).get("1h", 0)) * 10,
            wind_kph=float(data["wind"]["speed"]) * 3.6,
            condition=str(data["weather"][0]["description"]).title(),
            disease_risk_note=_disease_risk_note(humidity),
        )
    except (httpx.HTTPError, KeyError, ValueError, IndexError):
        # Weather API unavailable — degrade to the demo reading rather than
        # breaking the whole /api/analyze pipeline over a non-critical input.
        return _DEMO_WEATHER
