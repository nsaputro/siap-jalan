"""Integration tests for activity template endpoints."""
from __future__ import annotations


CUSTOM_ACTIVITY = {
    "slug": "test_yoga",
    "name": "Yoga",
    "icon_emoji": "🧘",
    "description": "Yoga retreat",
    "climate_types": ["tropical"],
    "items": [
        {"name": "Yoga mat", "quantity": 1, "is_essential": True, "priority": 8, "gender_filter": "all"},
        {"name": "Yoga pants", "quantity": 2, "is_essential": False, "priority": 5, "gender_filter": "all"},
    ],
}


async def test_list_activities_returns_seeded(client):
    r = await client.get("/activities")
    assert r.status_code == 200
    assert len(r.json()) >= 16, "Expected at least 16 built-in activity templates"


async def test_get_activity_by_slug(client):
    r = await client.get("/activities/hiking")
    assert r.status_code == 200
    body = r.json()
    assert body["slug"] == "hiking"
    assert len(body["items"]) > 0


async def test_get_activity_not_found(client):
    r = await client.get("/activities/nonexistent_xyz")
    assert r.status_code == 404


async def test_merge_single_activity(client):
    r = await client.post("/activities/merge", json={"activity_slugs": ["hiking"]})
    assert r.status_code == 200
    items = r.json()
    assert len(items) > 0
    for item in items:
        assert "hiking" in item["source_activities"]


async def test_merge_two_activities_no_duplicates(client):
    r = await client.post("/activities/merge", json={"activity_slugs": ["beach", "swimming"]})
    assert r.status_code == 200
    items = r.json()
    names_lower = [i["name"].lower() for i in items]
    assert len(names_lower) == len(set(names_lower)), "Duplicate names found in merged result"


async def test_merge_empty_slugs(client):
    r = await client.post("/activities/merge", json={"activity_slugs": []})
    assert r.status_code == 200
    assert r.json() == []


async def test_create_custom_activity(client):
    r = await client.post("/activities", json=CUSTOM_ACTIVITY)
    assert r.status_code == 201
    body = r.json()
    assert body["slug"] == "test_yoga"
    assert body["is_builtin"] is False
    assert len(body["items"]) == 2


async def test_get_custom_activity_after_create(client):
    await client.post("/activities", json=CUSTOM_ACTIVITY)
    r = await client.get("/activities/test_yoga")
    assert r.status_code == 200
    assert r.json()["name"] == "Yoga"


async def test_delete_custom_activity(client):
    created = (await client.post("/activities", json=CUSTOM_ACTIVITY)).json()
    r = await client.delete(f"/activities/{created['id']}")
    assert r.status_code == 204


async def test_cannot_delete_builtin_activity(client):
    r = await client.get("/activities/hiking")
    hiking_id = r.json()["id"]
    r = await client.delete(f"/activities/{hiking_id}")
    assert r.status_code in (400, 403)


async def test_add_item_to_custom_activity(client):
    activity = (await client.post("/activities", json=CUSTOM_ACTIVITY)).json()
    r = await client.post(f"/activities/{activity['id']}/items", json={
        "name": "Foam roller", "quantity": 1,
        "is_essential": False, "priority": 3, "gender_filter": "all",
    })
    assert r.status_code == 201
    assert r.json()["name"] == "Foam roller"


async def test_update_item_in_activity(client):
    activity = (await client.post("/activities", json=CUSTOM_ACTIVITY)).json()
    item_id = activity["items"][0]["id"]
    r = await client.put(f"/activities/{activity['id']}/items/{item_id}", json={"name": "Meditation mat"})
    assert r.status_code == 200
    assert r.json()["name"] == "Meditation mat"


async def test_delete_item_from_activity(client):
    activity = (await client.post("/activities", json=CUSTOM_ACTIVITY)).json()
    item_id = activity["items"][0]["id"]
    r = await client.delete(f"/activities/{activity['id']}/items/{item_id}")
    assert r.status_code == 204
    updated = (await client.get(f"/activities/{activity['slug']}")).json()
    assert not any(i["id"] == item_id for i in updated["items"])
