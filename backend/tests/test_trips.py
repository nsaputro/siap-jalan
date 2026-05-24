"""Integration tests for /trips endpoints."""
from __future__ import annotations

from .conftest import trip_payload


async def test_create_trip_no_activities(client):
    r = await client.post("/trips", json=trip_payload())
    assert r.status_code == 201
    body = r.json()
    assert body["destination"] == "Bali"
    assert len(body["packing_lists"]) == 1
    assert body["packing_lists"][0]["items"] == []


async def test_create_trip_with_activities_populates_items(client):
    r = await client.post("/trips", json=trip_payload(activities=["hiking"]))
    assert r.status_code == 201
    items = r.json()["packing_lists"][0]["items"]
    assert len(items) > 0
    assert all(i["added_by"] == "activity" for i in items)
    assert all(i["source_activities"] == ["hiking"] for i in items)


async def test_create_trip_merged_activities_deduplicates(client):
    # beach and swimming both have swimwear — should appear only once
    r = await client.post("/trips", json=trip_payload(activities=["beach", "swimming"]))
    assert r.status_code == 201
    items = r.json()["packing_lists"][0]["items"]
    names = [i["name"].lower() for i in items]
    assert len(names) == len(set(names)), "Duplicate item names found after merge"


async def test_list_trips_returns_all(client):
    await client.post("/trips", json=trip_payload(destination="Bali"))
    await client.post("/trips", json=trip_payload(destination="Lombok"))
    r = await client.get("/trips")
    assert r.status_code == 200
    destinations = [t["destination"] for t in r.json()]
    assert "Bali" in destinations
    assert "Lombok" in destinations


async def test_get_trip(client):
    created = (await client.post("/trips", json=trip_payload())).json()
    r = await client.get(f"/trips/{created['id']}")
    assert r.status_code == 200
    assert r.json()["id"] == created["id"]


async def test_get_trip_not_found(client):
    r = await client.get("/trips/99999")
    assert r.status_code == 404


async def test_update_trip(client):
    trip = (await client.post("/trips", json=trip_payload())).json()
    r = await client.put(f"/trips/{trip['id']}", json={"destination": "Lombok"})
    assert r.status_code == 200
    assert r.json()["destination"] == "Lombok"


async def test_delete_trip(client):
    trip = (await client.post("/trips", json=trip_payload())).json()
    r = await client.delete(f"/trips/{trip['id']}")
    assert r.status_code == 204
    assert (await client.get(f"/trips/{trip['id']}")).status_code == 404


async def test_delete_trip_cascades_packing_list(client):
    trip = (await client.post("/trips", json=trip_payload(activities=["hiking"]))).json()
    list_id = trip["packing_lists"][0]["id"]
    await client.delete(f"/trips/{trip['id']}")
    r = await client.get(f"/lists/{list_id}/items")
    # Either 404 (list gone) or empty list — cascade should have cleaned up
    assert r.status_code in (200, 404)
    if r.status_code == 200:
        assert r.json() == []
