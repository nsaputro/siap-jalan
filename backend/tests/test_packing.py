"""Integration tests for packing lists and items."""
from __future__ import annotations

from .conftest import trip_payload


async def _create_trip(client, **kwargs):
    r = await client.post("/trips", json=trip_payload(**kwargs))
    assert r.status_code == 201
    trip = r.json()
    return trip["id"], trip["packing_lists"][0]["id"]


async def test_add_item_to_list(client):
    _, list_id = await _create_trip(client)
    r = await client.post(f"/lists/{list_id}/items", json={"name": "Passport", "quantity": 1, "is_essential": True})
    assert r.status_code == 201
    item = r.json()
    assert item["name"] == "Passport"
    assert item["added_by"] == "user"
    assert item["source_activities"] == []


async def test_add_adhoc_item_with_source_activity(client):
    _, list_id = await _create_trip(client)
    r = await client.post(f"/lists/{list_id}/items", json={
        "name": "Blister kit", "quantity": 1,
        "is_essential": False, "source_activity": "hiking",
    })
    assert r.status_code == 201
    item = r.json()
    assert item["added_by"] == "adhoc"
    assert "hiking" in item["source_activities"]


async def test_toggle_item_unpacked_to_packed(client):
    _, list_id = await _create_trip(client)
    item = (await client.post(f"/lists/{list_id}/items", json={"name": "Sunscreen", "quantity": 1, "is_essential": False})).json()
    assert item["is_packed"] is False
    toggled = (await client.post(f"/items/{item['id']}/toggle")).json()
    assert toggled["is_packed"] is True


async def test_toggle_item_packed_to_unpacked(client):
    _, list_id = await _create_trip(client)
    item = (await client.post(f"/lists/{list_id}/items", json={"name": "Hat", "quantity": 1, "is_essential": False})).json()
    await client.post(f"/items/{item['id']}/toggle")
    toggled = (await client.post(f"/items/{item['id']}/toggle")).json()
    assert toggled["is_packed"] is False


async def test_update_item_fields(client):
    _, list_id = await _create_trip(client)
    item = (await client.post(f"/lists/{list_id}/items", json={"name": "Old name", "quantity": 1, "is_essential": False})).json()
    r = await client.put(f"/items/{item['id']}", json={"name": "New name", "quantity": 3})
    assert r.status_code == 200
    assert r.json()["name"] == "New name"
    assert r.json()["quantity"] == 3


async def test_update_template_linked_item_sets_customised(client):
    _, list_id = await _create_trip(client, activities=["hiking"])
    items_r = await client.get(f"/lists/{list_id}/items")
    linked = next((i for i in items_r.json() if i["template_item_id"] is not None), None)
    assert linked is not None, "Expected at least one template-linked item from hiking"
    r = await client.put(f"/items/{linked['id']}", json={"name": "Custom name"})
    assert r.status_code == 200
    assert r.json()["is_customised"] is True


async def test_update_is_packed_does_not_set_customised(client):
    _, list_id = await _create_trip(client, activities=["hiking"])
    items_r = await client.get(f"/lists/{list_id}/items")
    linked = next((i for i in items_r.json() if i["template_item_id"] is not None), None)
    assert linked is not None
    r = await client.put(f"/items/{linked['id']}", json={"is_packed": True})
    assert r.status_code == 200
    assert r.json()["is_customised"] is False


async def test_delete_item(client):
    _, list_id = await _create_trip(client)
    item = (await client.post(f"/lists/{list_id}/items", json={"name": "Toothbrush", "quantity": 1, "is_essential": False})).json()
    r = await client.delete(f"/items/{item['id']}")
    assert r.status_code == 204
    items = (await client.get(f"/lists/{list_id}/items")).json()
    assert not any(i["id"] == item["id"] for i in items)


async def test_bulk_create_items(client):
    _, list_id = await _create_trip(client)
    payload = [
        {"list_id": list_id, "name": "Item A", "quantity": 1, "is_essential": False, "added_by": "user", "source_activities": []},
        {"list_id": list_id, "name": "Item B", "quantity": 2, "is_essential": True,  "added_by": "user", "source_activities": []},
        {"list_id": list_id, "name": "Item C", "quantity": 1, "is_essential": True,  "added_by": "user", "source_activities": []},
    ]
    r = await client.post("/items/bulk", json=payload)
    assert r.status_code == 201
    assert len(r.json()) == 3


async def test_get_packing_lists_for_trip(client):
    trip_id, _ = await _create_trip(client)
    r = await client.get(f"/trips/{trip_id}/lists")
    assert r.status_code == 200
    lists = r.json()
    assert len(lists) == 1
    assert lists[0]["is_default"] is True
