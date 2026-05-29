"""Integration tests for /export and /import (transfer) endpoints."""
from __future__ import annotations

import datetime


def _future_trip(**overrides: object) -> dict:
    """A trip whose end_date is in the future, so /export includes it."""
    start = datetime.date.today() + datetime.timedelta(days=30)
    end = start + datetime.timedelta(days=6)
    return {
        "destination": "Tokyo",
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        "traveller_count": 1,
        **overrides,
    }


def _past_trip(**overrides: object) -> dict:
    start = datetime.date.today() - datetime.timedelta(days=30)
    end = start + datetime.timedelta(days=6)
    return {
        "destination": "Yesterland",
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        "traveller_count": 1,
        **overrides,
    }


# ── Export ──────────────────────────────────────────────────────────────────

async def test_export_empty(client):
    r = await client.get("/export")
    assert r.status_code == 200
    body = r.json()
    assert body["version"] == "1"
    assert body["trips"] == []
    # only built-in activities are seeded; none belong to the user
    assert body["activities"] == []


async def test_export_includes_active_trip_with_items(client):
    await client.post("/trips", json=_future_trip(activities=["hiking"]))
    body = (await client.get("/export")).json()
    assert len(body["trips"]) == 1
    trip = body["trips"][0]
    assert trip["destination"] == "Tokyo"
    assert trip["activities"] == ["hiking"]
    assert len(trip["packing_lists"]) == 1
    assert len(trip["packing_lists"][0]["items"]) > 0


async def test_export_excludes_past_trips(client):
    await client.post("/trips", json=_past_trip())
    await client.post("/trips", json=_future_trip())
    body = (await client.get("/export")).json()
    destinations = [t["destination"] for t in body["trips"]]
    assert destinations == ["Tokyo"]


async def test_export_excludes_builtin_activities(client):
    # The DB is seeded with built-in templates; none should be exported.
    body = (await client.get("/export")).json()
    assert body["activities"] == []


async def test_export_includes_custom_activity(client):
    await client.post("/activities", json={
        "slug": "my_thing",
        "name": "My Thing",
        "icon_emoji": "🎯",
        "items": [{"name": "Gizmo", "is_essential": True}],
    })
    body = (await client.get("/export")).json()
    slugs = [a["slug"] for a in body["activities"]]
    assert "my_thing" in slugs
    custom = next(a for a in body["activities"] if a["slug"] == "my_thing")
    assert custom["items"][0]["name"] == "Gizmo"
    assert custom["items"][0]["is_essential"] is True


async def test_export_selective_trips_only(client):
    await client.post("/trips", json=_future_trip())
    await client.post("/activities", json={"name": "Solo", "items": []})
    body = (await client.get("/export?trips=true&activities=false")).json()
    assert len(body["trips"]) == 1
    assert body["activities"] == []


async def test_export_selective_activities_only(client):
    await client.post("/trips", json=_future_trip())
    await client.post("/activities", json={"name": "Solo", "items": []})
    body = (await client.get("/export?trips=false&activities=true")).json()
    assert body["trips"] == []
    assert len(body["activities"]) == 1


# ── Import ──────────────────────────────────────────────────────────────────

async def test_import_roundtrip(client):
    await client.post("/trips", json=_future_trip(activities=["hiking"]))
    await client.post("/activities", json={
        "slug": "custom_one",
        "name": "Custom One",
        "items": [{"name": "Widget"}],
    })
    exported = (await client.get("/export")).json()

    # Import into a fresh client (separate in-memory DB) would be ideal, but we
    # re-import here: trips duplicate, the activity slug collides and is renamed.
    result = (await client.post("/import", json=exported)).json()
    assert result["trips_imported"] == 1
    assert result["activities_imported"] == 1


async def test_import_creates_trip_and_activity(client):
    payload = {
        "version": "1",
        "trips": [_future_trip(destination="Imported", activities=["brand_new"])],
        "activities": [
            {"slug": "brand_new", "name": "Brand New", "items": [{"name": "Thing"}]}
        ],
    }
    result = (await client.post("/import", json=payload)).json()
    assert result["trips_imported"] == 1
    assert result["activities_imported"] == 1
    assert result["warnings"] == []

    trips = (await client.get("/trips")).json()
    imported = next(t for t in trips if t["destination"] == "Imported")
    assert imported["activities"] == ["brand_new"]


async def test_import_slug_conflict_renames_and_remaps(client):
    # Pre-existing custom activity occupies the slug.
    await client.post("/activities", json={"slug": "hiking_custom", "name": "Hiking Custom", "items": []})

    payload = {
        "version": "1",
        "trips": [_future_trip(destination="Remap", activities=["hiking_custom"])],
        "activities": [
            {"slug": "hiking_custom", "name": "Hiking Custom (copy)", "items": [{"name": "Boots"}]}
        ],
    }
    result = (await client.post("/import", json=payload)).json()
    assert result["activities_imported"] == 1
    assert len(result["warnings"]) == 1
    assert "hiking_custom_2" in result["warnings"][0]

    # The trip's activity reference must point at the renamed slug.
    trips = (await client.get("/trips")).json()
    remapped = next(t for t in trips if t["destination"] == "Remap")
    assert remapped["activities"] == ["hiking_custom_2"]


async def test_import_only_activities(client):
    payload = {
        "version": "1",
        "trips": [],
        "activities": [{"slug": "acts_only", "name": "Acts Only", "items": []}],
    }
    result = (await client.post("/import", json=payload)).json()
    assert result["trips_imported"] == 0
    assert result["activities_imported"] == 1
    assert (await client.get("/trips")).json() == []


async def test_import_tolerates_partial_payload(client):
    """Minimal records (missing optional fields) should import via schema defaults."""
    payload = {
        "trips": [
            {
                "destination": "Minimal",
                "start_date": _future_trip()["start_date"],
                "end_date": _future_trip()["end_date"],
                "packing_lists": [{"name": "Main", "items": [{"name": "Toothbrush"}]}],
            }
        ],
        "activities": [{"slug": "bare", "name": "Bare"}],
    }
    result = (await client.post("/import", json=payload)).json()
    assert result["trips_imported"] == 1
    assert result["activities_imported"] == 1
