from __future__ import annotations

import datetime
from typing import Optional

import httpx


GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"


async def get_weather(
    destination: str,
    start_date: datetime.date,
    end_date: datetime.date,
) -> Optional[dict]:
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Step 1: Geocoding
            geo_resp = await client.get(
                GEOCODING_URL,
                params={"name": destination, "count": 1, "language": "en", "format": "json"},
            )
            geo_resp.raise_for_status()
            geo_data = geo_resp.json()

            results = geo_data.get("results")
            if not results:
                return None

            location = results[0]
            lat = location["latitude"]
            lon = location["longitude"]
            location_name = location.get("name", destination)
            country = location.get("country", "")

            # Step 2: Forecast
            forecast_resp = await client.get(
                FORECAST_URL,
                params={
                    "latitude": lat,
                    "longitude": lon,
                    "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,weathercode",
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "timezone": "auto",
                    "forecast_days": 16,
                },
            )
            forecast_resp.raise_for_status()
            forecast_data = forecast_resp.json()

            daily = forecast_data.get("daily", {})
            dates = daily.get("time", [])
            temp_max = daily.get("temperature_2m_max", [])
            temp_min = daily.get("temperature_2m_min", [])
            precipitation = daily.get("precipitation_sum", [])
            weathercodes = daily.get("weathercode", [])

            forecasts = []
            for i, date_str in enumerate(dates):
                forecasts.append(
                    {
                        "date": date_str,
                        "temp_max": temp_max[i] if i < len(temp_max) else None,
                        "temp_min": temp_min[i] if i < len(temp_min) else None,
                        "precipitation_sum": precipitation[i] if i < len(precipitation) else None,
                        "weathercode": weathercodes[i] if i < len(weathercodes) else None,
                    }
                )

            return {
                "location": location_name,
                "country": country,
                "latitude": lat,
                "longitude": lon,
                "forecasts": forecasts,
            }

    except Exception:
        return None
