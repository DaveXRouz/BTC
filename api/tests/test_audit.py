"""Tests for Oracle audit logging."""

import pytest

USERS_URL = "/api/oracle/users"
AUDIT_URL = "/api/oracle/audit"


VALID_USER = {
    "name": "John Doe",
    "birthday": "1990-05-15",
    "mother_name": "Jane Doe",
}


# ─── Audit Entry Generation ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_user_generates_audit(client):
    await client.post(USERS_URL, json=VALID_USER)
    resp = await client.get(AUDIT_URL)
    data = resp.json()
    assert data["total"] >= 1
    actions = [e["action"] for e in data["entries"]]
    assert "oracle_user.create" in actions


@pytest.mark.asyncio
async def test_read_user_generates_audit(client):
    create_resp = await client.post(USERS_URL, json=VALID_USER)
    user_id = create_resp.json()["id"]
    await client.get(f"{USERS_URL}/{user_id}")
    resp = await client.get(AUDIT_URL)
    actions = [e["action"] for e in resp.json()["entries"]]
    assert "oracle_user.read" in actions


@pytest.mark.asyncio
async def test_update_user_generates_audit(client):
    create_resp = await client.post(USERS_URL, json=VALID_USER)
    user_id = create_resp.json()["id"]
    await client.put(f"{USERS_URL}/{user_id}", json={"city": "London"})
    resp = await client.get(AUDIT_URL)
    actions = [e["action"] for e in resp.json()["entries"]]
    assert "oracle_user.update" in actions


@pytest.mark.asyncio
async def test_delete_user_generates_audit(client):
    create_resp = await client.post(USERS_URL, json=VALID_USER)
    user_id = create_resp.json()["id"]
    await client.delete(f"{USERS_URL}/{user_id}")
    resp = await client.get(AUDIT_URL)
    actions = [e["action"] for e in resp.json()["entries"]]
    assert "oracle_user.delete" in actions


@pytest.mark.asyncio
async def test_list_users_generates_audit(client):
    await client.get(USERS_URL)
    resp = await client.get(AUDIT_URL)
    actions = [e["action"] for e in resp.json()["entries"]]
    assert "oracle_user.list" in actions


# ─── Audit Entry Content ───────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_audit_captures_api_key_hash(client):
    await client.post(USERS_URL, json=VALID_USER)
    resp = await client.get(AUDIT_URL)
    entries = resp.json()["entries"]
    create_entry = next(e for e in entries if e["action"] == "oracle_user.create")
    assert create_entry["api_key_hash"] == "test-key-hash"


@pytest.mark.asyncio
async def test_audit_captures_resource_id(client):
    create_resp = await client.post(USERS_URL, json=VALID_USER)
    user_id = create_resp.json()["id"]
    resp = await client.get(AUDIT_URL)
    entries = resp.json()["entries"]
    create_entry = next(e for e in entries if e["action"] == "oracle_user.create")
    assert create_entry["resource_id"] == user_id


# ─── Audit Filtering ───────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_audit_filter_by_action(client):
    await client.post(USERS_URL, json=VALID_USER)
    await client.get(USERS_URL)
    resp = await client.get(AUDIT_URL, params={"action": "oracle_user.create"})
    data = resp.json()
    assert all(e["action"] == "oracle_user.create" for e in data["entries"])


@pytest.mark.asyncio
async def test_audit_filter_by_resource_id(client):
    create_resp = await client.post(USERS_URL, json=VALID_USER)
    user_id = create_resp.json()["id"]
    await client.get(f"{USERS_URL}/{user_id}")
    resp = await client.get(AUDIT_URL, params={"resource_id": user_id})
    data = resp.json()
    assert all(e["resource_id"] == user_id for e in data["entries"])


# ─── Audit Access Control ──────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_audit_admin_only(readonly_client):
    resp = await readonly_client.get(AUDIT_URL)
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_audit_admin_allowed(client):
    resp = await client.get(AUDIT_URL)
    assert resp.status_code == 200
