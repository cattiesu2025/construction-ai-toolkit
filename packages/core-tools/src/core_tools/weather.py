import os
import requests
from typing import Any

_BASE_URL = os.getenv("OPEN_METEO_BASE_URL", "https://api.open-meteo.com/v1/forecast")

_CITY_COORDS = {
    "Sydney": (-33.8688, 151.2093),
    "Melbourne": (-37.8136, 144.9631),
    "Brisbane": (-27.4698, 153.0251),
    "Perth": (-31.9505, 115.8605),
    "Gold Coast": (-28.0167, 153.4000),
    "Fremantle": (-32.0569, 115.7439),
}


def check_weather_impact(date_range: str, location: str) -> dict[str, Any]:
    """Fetch 7-day weather forecast and assess construction impact risk.

    Args:
        date_range: ISO date range string e.g. '2024-11-01 to 2024-11-07'
        location: City name matching a known Australian city
    """
    city = _resolve_city(location)
    lat, lon = _CITY_COORDS.get(city, _CITY_COORDS["Sydney"])

    try:
        resp = requests.get(
            _BASE_URL,
            params={
                "latitude": lat,
                "longitude": lon,
                "daily": "precipitation_sum,windspeed_10m_max,temperature_2m_max,temperature_2m_min",
                "forecast_days": 7,
                "timezone": "Australia/Sydney",
            },
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as exc:
        return {"error": f"Weather API unavailable: {exc}", "location": location, "risk": "unknown"}

    daily = data.get("daily", {})
    dates = daily.get("time", [])
    rain = daily.get("precipitation_sum", [])
    wind = daily.get("windspeed_10m_max", [])
    temp_max = daily.get("temperature_2m_max", [])
    temp_min = daily.get("temperature_2m_min", [])

    risk_days = []
    for i, d in enumerate(dates):
        r = rain[i] if i < len(rain) else 0
        w = wind[i] if i < len(wind) else 0
        t_max = temp_max[i] if i < len(temp_max) else 25
        t_min = temp_min[i] if i < len(temp_min) else 10

        risks = []
        if r and r > 20:
            risks.append(f"heavy rain {r:.0f}mm")
        elif r and r > 5:
            risks.append(f"rain {r:.0f}mm")
        if w and w > 60:
            risks.append(f"strong wind {w:.0f}km/h - crane ops suspended")
        elif w and w > 40:
            risks.append(f"elevated wind {w:.0f}km/h")
        if t_max and t_max > 38:
            risks.append(f"extreme heat {t_max:.0f}°C - mandatory rest breaks")
        if t_min and t_min < 2:
            risks.append(f"near-freezing {t_min:.0f}°C - concrete curing risk")

        if risks:
            risk_days.append({"date": d, "risks": risks, "rain_mm": r, "wind_kmh": w})

    overall_risk = "LOW"
    if len(risk_days) >= 4:
        overall_risk = "HIGH"
    elif len(risk_days) >= 2:
        overall_risk = "MEDIUM"

    return {
        "location": city,
        "date_range": date_range,
        "forecast_days": len(dates),
        "risk_days_count": len(risk_days),
        "overall_weather_risk": overall_risk,
        "risk_days": risk_days,
        "summary": f"{len(risk_days)} of {len(dates)} days have weather risk in {city}",
    }


def _resolve_city(location: str) -> str:
    location_lower = location.lower()
    for city in _CITY_COORDS:
        if city.lower() in location_lower:
            return city
    return "Sydney"
