"""End-to-end propagation tests: edit activity template → active trip updates."""
from __future__ import annotations

import datetime

from .conftest import trip_payload

CUSTOM = {
    "slug": "test_prop_act",
    "name": "Test Propagation",
    "icon_emoji": "🧪",
    "climate_types": [],
    "items": [
        {"name": "Prop item one", "quantity": 1,
         "is_essential": False, "priority": 5, "gender_filter": "all"},
    ],
}


async def _setup(client):
    """Create a custom activity + an active trip using it. Returns (activity, trip, list_id)."""
    activity = (await client.post("/activities", json=CUSTOM)).json()
    far_future = (datetime.date.today() + datetime.timedelta(days=365)).isoformat()
    trip = (await client.post("/trips", json=trip_payload(
        destination="Test City",
        end_date=far_future,
        activities=["test_prop_act"],
    ))).json()
    list_id = trip["packing_lists"][0]["id"]
    return activity, trip, list_id


async def test_propagation_response_has_summary(client):
    activity, _, _ = await _setup(client)
    r = await client.put(f"/activities/{activity['id']}", json={"name": "Updated Name"})
    assert r.status_code == 200
    body = r.json()
    assert "propagation_summary" in body
    summary = body["propagation_summary"]
    for key in ("trips_updated", "items_added", "items_updated", "items_removed", "items_skipped_customised"):
        assert key in summary


async def test_propagation_add_item_to_active_trip(client):
    activity, _, list_id = await _setup(client)
    items_before = (await client.get(f"/lists/{list_id}/items")).json()
    count_before = len(items_before)

    await client.post(f"/activities/{activity['id']}/items", json={
        "name": "New template item",
        "quantity": 1, "is_essential": False, "priority": 3, "gender_filter": "all",
    })

    items_after = (await client.get(f"/lists/{list_id}/items")).json()
    assert len(items_after) == count_before + 1
    assert any(i["name"] == "New template item" for i in items_after)


async def test_propagation_update_item_name_in_active_trip(client):
    activity, _, list_id = await _setup(client)
    item_id = activity["items"][0]["id"]

    await client.put(f"/activities/{activity['id']}/items/{item_id}", json={"name": "Updated prop item"})

    items = (await client.get(f"/lists/{list_id}/items")).json()
    assert any(i["name"] == "Updated prop item" for i in items)


async def test_propagation_remove_item_from_active_trip(client):
    activity, _, list_id = await _setup(client)
    item_id = activity["items"][0]["id"]

    await client.delete(f"/activities/{activity['id']}/items/{item_id}")

    items = (await client.get(f"/lists/{list_id}/items")).json()
    assert not any(i["template_item_id"] == item_id for i in items)


async def test_propagation_skips_customised_item_on_update(client):
    activity, _, list_id = await _setup(client)
    template_item_id = activity["items"][0]["id"]

    # Find the packing item that was seeded from this template item
    packing_items = (await client.get(f"/lists/{list_id}/items")).json()
    packing_item = next(i for i in packing_items if i["template_item_id"] == template_item_id)

    # User customises the packing item → is_customised becomes True
    await client.put(f"/items/{packing_item['id']}", json={"name": "My custom version"})

    # Now update the template item
    await client.put(f"/activities/{activity['id']}/items/{template_item_id}", json={"name": "Template renamed"})

    # The packing item should still have the user's custom name
    packing_items = (await client.get(f"/lists/{list_id}/items")).json()
    same_item = next(i for i in packing_items if i["id"] == packing_item["id"])
    assert same_item["name"] == "My custom version"


async def test_propagation_skips_add_if_name_already_exists(client):
    activity, _, list_id = await _setup(client)

    # Manually add an item with the same name as what we're about to add via template
    await client.post(f"/lists/{list_id}/items", json={
        "name": "Duplicate item",
        "quantity": 1, "is_essential": False,
    })

    items_before = (await client.get(f"/lists/{list_id}/items")).json()
    count_before = len(items_before)

    # Add template item with same name → should NOT create a duplicate
    await client.post(f"/activities/{activity['id']}/items", json={
        "name": "Duplicate item",
        "quantity": 1, "is_essential": False, "priority": 3, "gender_filter": "all",
    })

    items_after = (await client.get(f"/lists/{list_id}/items")).json()
    assert len(items_after) == count_before
