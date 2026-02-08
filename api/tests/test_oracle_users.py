"""Tests for Oracle user management CRUD endpoints."""

import pytest

USERS_URL = "/api/oracle/users"

VALID_USER = {
    "name": "John Doe",
    "birthday": "1990-05-15",
    "mother_name": "Jane Doe",
}

FULL_USER = {
    "name": "Ali Karimi",
    "name_persian": "\u0639\u0644\u06cc \u06a9\u0631\u06cc\u0645\u06cc",
    "birthday": "1985-12-01",
    "mother_name": "Maryam",
    "mother_name_persian": "\u0645\u0631\u06cc\u0645",
    "country": "Iran",
    "city": "Tehran",
}


# ─── CREATE ──────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_user(client):
    resp = await client.post(USERS_URL, json=VALID_USER)
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "John Doe"
    assert data["birthday"] == "1990-05-15"
    assert data["mother_name"] == "Jane Doe"
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data


@pytest.mark.asyncio
async def test_create_user_all_fields(client):
    resp = await client.post(USERS_URL, json=FULL_USER)
    assert resp.status_code == 201
    data = resp.json()
    assert data["name_persian"] == "\u0639\u0644\u06cc \u06a9\u0631\u06cc\u0645\u06cc"
    assert data["country"] == "Iran"
    assert data["city"] == "Tehran"


@pytest.mark.asyncio
async def test_create_user_duplicate_409(client):
    await client.post(USERS_URL, json=VALID_USER)
    resp = await client.post(USERS_URL, json=VALID_USER)
    assert resp.status_code == 409
    assert "already exists" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_create_user_future_birthday_422(client):
    user = {**VALID_USER, "birthday": "2099-01-01"}
    resp = await client.post(USERS_URL, json=user)
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_create_user_short_name_422(client):
    user = {**VALID_USER, "name": "A"}
    resp = await client.post(USERS_URL, json=user)
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_create_user_missing_field_422(client):
    resp = await client.post(USERS_URL, json={"name": "Test"})
    assert resp.status_code == 422


# ─── LIST ────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_list_users_empty(client):
    resp = await client.get(USERS_URL)
    assert resp.status_code == 200
    data = resp.json()
    assert data["users"] == []
    assert data["total"] == 0


@pytest.mark.asyncio
async def test_list_users_pagination(client):
    for i in range(5):
        await client.post(
            USERS_URL,
            json={
                "name": f"User {i:02d}",
                "birthday": f"1990-01-{i+1:02d}",
                "mother_name": "Mom",
            },
        )
    resp = await client.get(USERS_URL, params={"limit": 2, "offset": 0})
    data = resp.json()
    assert len(data["users"]) == 2
    assert data["total"] == 5
    assert data["limit"] == 2
    assert data["offset"] == 0


@pytest.mark.asyncio
async def test_list_users_search(client):
    await client.post(USERS_URL, json=VALID_USER)
    await client.post(
        USERS_URL,
        json={"name": "Alice Smith", "birthday": "1992-03-10", "mother_name": "Mary"},
    )
    resp = await client.get(USERS_URL, params={"search": "john"})
    data = resp.json()
    assert data["total"] == 1
    assert data["users"][0]["name"] == "John Doe"


@pytest.mark.asyncio
async def test_list_users_excludes_deleted(client):
    create_resp = await client.post(USERS_URL, json=VALID_USER)
    user_id = create_resp.json()["id"]
    await client.delete(f"{USERS_URL}/{user_id}")
    resp = await client.get(USERS_URL)
    assert resp.json()["total"] == 0


# ─── GET ─────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_user(client):
    create_resp = await client.post(USERS_URL, json=VALID_USER)
    user_id = create_resp.json()["id"]
    resp = await client.get(f"{USERS_URL}/{user_id}")
    assert resp.status_code == 200
    assert resp.json()["name"] == "John Doe"


@pytest.mark.asyncio
async def test_get_user_not_found_404(client):
    resp = await client.get(f"{USERS_URL}/9999")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_get_user_deleted_404(client):
    create_resp = await client.post(USERS_URL, json=VALID_USER)
    user_id = create_resp.json()["id"]
    await client.delete(f"{USERS_URL}/{user_id}")
    resp = await client.get(f"{USERS_URL}/{user_id}")
    assert resp.status_code == 404


# ─── UPDATE ──────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_update_user_partial(client):
    create_resp = await client.post(USERS_URL, json=VALID_USER)
    user_id = create_resp.json()["id"]
    resp = await client.put(f"{USERS_URL}/{user_id}", json={"city": "London"})
    assert resp.status_code == 200
    assert resp.json()["city"] == "London"
    assert resp.json()["name"] == "John Doe"  # unchanged


@pytest.mark.asyncio
async def test_update_user_not_found_404(client):
    resp = await client.put(f"{USERS_URL}/9999", json={"city": "London"})
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_update_user_empty_body_400(client):
    create_resp = await client.post(USERS_URL, json=VALID_USER)
    user_id = create_resp.json()["id"]
    resp = await client.put(f"{USERS_URL}/{user_id}", json={})
    assert resp.status_code == 400
    assert "No fields" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_update_user_duplicate_409(client):
    await client.post(USERS_URL, json=VALID_USER)
    create_resp = await client.post(
        USERS_URL,
        json={"name": "Other User", "birthday": "1985-06-20", "mother_name": "Mom"},
    )
    user_id = create_resp.json()["id"]
    # Try to change name+birthday to match the first user
    resp = await client.put(
        f"{USERS_URL}/{user_id}",
        json={"name": "John Doe", "birthday": "1990-05-15"},
    )
    assert resp.status_code == 409


# ─── DELETE ──────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_delete_user(client):
    create_resp = await client.post(USERS_URL, json=VALID_USER)
    user_id = create_resp.json()["id"]
    resp = await client.delete(f"{USERS_URL}/{user_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == user_id


@pytest.mark.asyncio
async def test_delete_user_not_found_404(client):
    resp = await client.delete(f"{USERS_URL}/9999")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_user_already_deleted_404(client):
    create_resp = await client.post(USERS_URL, json=VALID_USER)
    user_id = create_resp.json()["id"]
    await client.delete(f"{USERS_URL}/{user_id}")
    resp = await client.delete(f"{USERS_URL}/{user_id}")
    assert resp.status_code == 404


# ─── AUTH ────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_unauthenticated_request_401(unauth_client):
    resp = await unauth_client.get(USERS_URL)
    assert resp.status_code == 401
