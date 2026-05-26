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

# Activity without explicit slug — tests auto-slug generation
NAMELESS_SLUG_ACTIVITY = {
    "name": "My Custom Hike",
    "icon_emoji": "⛰️",
    "items": [],
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


# ---------------------------------------------------------------------------
# Auto-slug generation
# ---------------------------------------------------------------------------

async def test_create_activity_without_slug_auto_generates(client):
    r = await client.post("/activities", json=NAMELESS_SLUG_ACTIVITY)
    assert r.status_code == 201
    body = r.json()
    assert body["slug"] == "my_custom_hike"
    assert body["is_builtin"] is False


async def test_create_activity_duplicate_slug_auto_increments(client):
    await client.post("/activities", json=NAMELESS_SLUG_ACTIVITY)
    r2 = await client.post("/activities", json=NAMELESS_SLUG_ACTIVITY)
    assert r2.status_code == 201
    assert r2.json()["slug"] == "my_custom_hike_2"


# ---------------------------------------------------------------------------
# Authorization — built-in templates are immutable
# ---------------------------------------------------------------------------

async def test_cannot_update_builtin_activity(client, as_user):
    hiking = (await client.get("/activities/hiking")).json()
    with as_user("any_user"):
        r = await client.put(f"/activities/{hiking['id']}", json={"name": "Hacked"})
    assert r.status_code == 403


async def test_cannot_delete_builtin_activity_returns_403(client, as_user):
    hiking = (await client.get("/activities/hiking")).json()
    with as_user("any_user"):
        r = await client.delete(f"/activities/{hiking['id']}")
    assert r.status_code == 403


async def test_cannot_add_item_to_builtin_activity(client, as_user):
    hiking = (await client.get("/activities/hiking")).json()
    with as_user("any_user"):
        r = await client.post(
            f"/activities/{hiking['id']}/items",
            json={"name": "Hacked item", "quantity": 1},
        )
    assert r.status_code == 403


async def test_cannot_update_item_in_builtin_activity(client, as_user):
    hiking = (await client.get("/activities/hiking")).json()
    item_id = hiking["items"][0]["id"]
    with as_user("any_user"):
        r = await client.put(
            f"/activities/{hiking['id']}/items/{item_id}",
            json={"name": "Hacked"},
        )
    assert r.status_code == 403


async def test_cannot_delete_item_from_builtin_activity(client, as_user):
    hiking = (await client.get("/activities/hiking")).json()
    item_id = hiking["items"][0]["id"]
    with as_user("any_user"):
        r = await client.delete(f"/activities/{hiking['id']}/items/{item_id}")
    assert r.status_code == 403


# ---------------------------------------------------------------------------
# Authorization — cross-user ownership enforcement
# ---------------------------------------------------------------------------

async def test_cannot_update_other_users_template(client, as_user):
    with as_user("user_a"):
        activity = (await client.post("/activities", json=CUSTOM_ACTIVITY)).json()
    with as_user("user_b"):
        r = await client.put(f"/activities/{activity['id']}", json={"name": "Stolen"})
    assert r.status_code == 403


async def test_cannot_delete_other_users_template(client, as_user):
    with as_user("user_a"):
        activity = (await client.post("/activities", json=CUSTOM_ACTIVITY)).json()
    with as_user("user_b"):
        r = await client.delete(f"/activities/{activity['id']}")
    assert r.status_code == 403


async def test_cannot_add_item_to_other_users_template(client, as_user):
    with as_user("user_a"):
        activity = (await client.post("/activities", json=CUSTOM_ACTIVITY)).json()
    with as_user("user_b"):
        r = await client.post(
            f"/activities/{activity['id']}/items",
            json={"name": "Injected", "quantity": 1},
        )
    assert r.status_code == 403


# ---------------------------------------------------------------------------
# Clone endpoint
# ---------------------------------------------------------------------------

async def test_clone_builtin_activity(client, as_user):
    """Cloning a built-in creates a user-owned copy."""
    with as_user("user_a"):
        r = await client.post("/activities/hiking/clone", json={"name": "My Hiking"})
    assert r.status_code == 201
    body = r.json()
    assert body["name"] == "My Hiking"
    assert body["is_builtin"] is False
    assert body["ha_user_id"] == "user_a"
    assert body["slug"] == "my_hiking"


async def test_clone_preserves_all_items(client, as_user):
    """Cloned template has the same number of items as the source."""
    hiking = (await client.get("/activities/hiking")).json()
    original_count = len(hiking["items"])
    with as_user("user_a"):
        r = await client.post("/activities/hiking/clone", json={"name": "My Hiking"})
    assert len(r.json()["items"]) == original_count


async def test_clone_uses_provided_emoji(client, as_user):
    with as_user("user_a"):
        r = await client.post(
            "/activities/hiking/clone",
            json={"name": "My Hiking", "icon_emoji": "🏕️"},
        )
    assert r.json()["icon_emoji"] == "🏕️"


async def test_clone_inherits_emoji_when_omitted(client, as_user):
    hiking = (await client.get("/activities/hiking")).json()
    with as_user("user_a"):
        r = await client.post("/activities/hiking/clone", json={"name": "My Hiking"})
    assert r.json()["icon_emoji"] == hiking["icon_emoji"]


async def test_clone_generates_unique_slug_on_collision(client, as_user):
    """Cloning twice with the same name produces distinct slugs."""
    with as_user("user_a"):
        r1 = await client.post("/activities/hiking/clone", json={"name": "My Hiking"})
        r2 = await client.post("/activities/hiking/clone", json={"name": "My Hiking"})
    assert r1.json()["slug"] != r2.json()["slug"]


async def test_clone_nonexistent_slug_returns_404(client, as_user):
    with as_user("user_a"):
        r = await client.post("/activities/nonexistent_xyz/clone", json={"name": "Copy"})
    assert r.status_code == 404


async def test_clone_custom_activity(client, as_user):
    """A user can also clone their own custom template."""
    with as_user("user_a"):
        original = (await client.post("/activities", json=CUSTOM_ACTIVITY)).json()
        r = await client.post(
            f"/activities/{original['slug']}/clone",
            json={"name": "Yoga Copy"},
        )
    assert r.status_code == 201
    body = r.json()
    assert body["name"] == "Yoga Copy"
    assert body["is_builtin"] is False
    assert len(body["items"]) == len(original["items"])


async def test_owner_can_update_own_template(client, as_user):
    """The owner can freely edit their custom template."""
    with as_user("user_a"):
        activity = (await client.post("/activities", json=CUSTOM_ACTIVITY)).json()
        r = await client.put(f"/activities/{activity['id']}", json={"name": "Updated Yoga"})
    assert r.status_code == 200
    assert r.json()["template"]["name"] == "Updated Yoga"


async def test_owner_can_delete_own_template(client, as_user):
    """The owner can delete their custom template."""
    with as_user("user_a"):
        activity = (await client.post("/activities", json=CUSTOM_ACTIVITY)).json()
        r = await client.delete(f"/activities/{activity['id']}")
    assert r.status_code == 204
