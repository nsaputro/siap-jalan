from __future__ import annotations

import json
from typing import Optional

import anthropic


async def generate_suggestions(
    trip: object,
    weather: Optional[dict],
    existing_item_names: list[str],
    api_key: str,
) -> list[dict]:
    if not api_key:
        return []

    # Build climate context from weather
    climate_context = ""
    if weather and weather.get("forecasts"):
        forecasts = weather["forecasts"]
        temps_max = [f["temp_max"] for f in forecasts if f.get("temp_max") is not None]
        temps_min = [f["temp_min"] for f in forecasts if f.get("temp_min") is not None]
        precips = [f["precipitation_sum"] for f in forecasts if f.get("precipitation_sum") is not None]

        if temps_max and temps_min:
            avg_max = sum(temps_max) / len(temps_max)
            avg_min = sum(temps_min) / len(temps_min)
            climate_context = (
                f"Weather forecast: avg high {avg_max:.1f}°C, avg low {avg_min:.1f}°C"
            )
        if precips:
            total_precip = sum(precips)
            climate_context += f", total precipitation {total_precip:.0f}mm"

    existing_set = {name.lower().strip() for name in existing_item_names}
    existing_list_str = ", ".join(existing_item_names[:50]) if existing_item_names else "none"

    destination = getattr(trip, "destination", "unknown destination")
    trip_type = getattr(trip, "trip_type", None) or "general"
    duration_days = getattr(trip, "duration_days", None) or 7
    activities = getattr(trip, "activities", []) or []
    climate_type = getattr(trip, "climate_type", None) or ""
    traveller_count = getattr(trip, "traveller_count", 1) or 1

    activities_str = ", ".join(activities) if activities else "none specified"

    prompt = f"""You are a travel packing assistant. Suggest additional packing items for a trip.

Trip details:
- Destination: {destination}
- Trip type: {trip_type}
- Duration: {duration_days} days
- Activities: {activities_str}
- Climate: {climate_type}
- Travellers: {traveller_count}
{f"- {climate_context}" if climate_context else ""}

Items already packed (do NOT suggest these again): {existing_list_str}

Return ONLY a JSON array of suggested items. Each item must have:
- "name": string (the item name)
- "quantity": integer
- "is_essential": boolean

Suggest 10-20 relevant items that are NOT already in the packed list. Return only the JSON array, no other text."""

    try:
        client = anthropic.AsyncAnthropic(api_key=api_key)
        response = await client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )

        content = response.content[0].text.strip()

        # Extract JSON array from response
        start = content.find("[")
        end = content.rfind("]") + 1
        if start == -1 or end == 0:
            return []

        json_str = content[start:end]
        suggestions = json.loads(json_str)

        # Filter out items that already exist
        filtered = []
        for item in suggestions:
            if not isinstance(item, dict):
                continue
            name = item.get("name", "")
            if name.lower().strip() not in existing_set:
                filtered.append(
                    {
                        "name": name,
                        "quantity": int(item.get("quantity", 1)),
                        "is_essential": bool(item.get("is_essential", False)),
                    }
                )

        return filtered

    except Exception:
        return []
