"""Tests for multi-user oracle reading endpoint."""

import pytest

MULTI_USER_URL = "/api/oracle/reading/multi-user"
READINGS_URL = "/api/oracle/readings"


def _two_users():
    return {
        "users": [
            {"name": "Alice", "birth_year": 1990, "birth_month": 3, "birth_day": 15},
            {"name": "Bob", "birth_year": 1988, "birth_month": 7, "birth_day": 22},
        ],
        "primary_user_index": 0,
        "include_interpretation": True,
    }


def _three_users():
    return {
        "users": [
            {"name": "Alice", "birth_year": 1990, "birth_month": 3, "birth_day": 15},
            {"name": "Bob", "birth_year": 1988, "birth_month": 7, "birth_day": 22},
            {"name": "Carol", "birth_year": 1995, "birth_month": 11, "birth_day": 5},
        ],
        "primary_user_index": 0,
    }


# ─── Basic Functionality ────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_two_user_analysis(client):
    resp = await client.post(MULTI_USER_URL, json=_two_users())
    assert resp.status_code == 200
    data = resp.json()
    assert data["user_count"] == 2
    assert data["pair_count"] == 1
    assert isinstance(data["computation_ms"], float)
    assert len(data["profiles"]) == 2
    assert len(data["pairwise_compatibility"]) == 1
    assert data["group_energy"] is not None
    assert data["group_dynamics"] is not None
    assert data["reading_id"] is not None


@pytest.mark.asyncio
async def test_three_user_analysis(client):
    resp = await client.post(MULTI_USER_URL, json=_three_users())
    assert resp.status_code == 200
    data = resp.json()
    assert data["user_count"] == 3
    assert data["pair_count"] == 3
    assert len(data["profiles"]) == 3
    assert len(data["pairwise_compatibility"]) == 3


@pytest.mark.asyncio
async def test_max_ten_users(client):
    users = [
        {
            "name": f"User{i}",
            "birth_year": 1980 + i,
            "birth_month": (i % 12) + 1,
            "birth_day": (i % 28) + 1,
        }
        for i in range(10)
    ]
    resp = await client.post(
        MULTI_USER_URL, json={"users": users, "primary_user_index": 0}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["user_count"] == 10
    assert data["pair_count"] == 45  # 10*9/2


@pytest.mark.asyncio
async def test_without_interpretation(client):
    body = _two_users()
    body["include_interpretation"] = False
    resp = await client.post(MULTI_USER_URL, json=body)
    assert resp.status_code == 200
    data = resp.json()
    assert data["ai_interpretation"] is None


@pytest.mark.asyncio
async def test_with_interpretation(client):
    resp = await client.post(MULTI_USER_URL, json=_two_users())
    assert resp.status_code == 200
    # AI interpretation may be None in test env (no API key) — that's fine


# ─── Profile Fields ──────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_profile_fields(client):
    resp = await client.post(MULTI_USER_URL, json=_two_users())
    assert resp.status_code == 200
    profile = resp.json()["profiles"][0]
    assert profile["name"] == "Alice"
    assert "element" in profile
    assert "animal" in profile
    assert "life_path" in profile


@pytest.mark.asyncio
async def test_compatibility_fields(client):
    resp = await client.post(MULTI_USER_URL, json=_two_users())
    assert resp.status_code == 200
    compat = resp.json()["pairwise_compatibility"][0]
    assert "user1" in compat
    assert "user2" in compat
    assert "overall" in compat
    assert isinstance(compat["overall"], float)


@pytest.mark.asyncio
async def test_group_energy_fields(client):
    resp = await client.post(MULTI_USER_URL, json=_two_users())
    assert resp.status_code == 200
    energy = resp.json()["group_energy"]
    assert "dominant_element" in energy
    assert "dominant_animal" in energy
    assert "joint_life_path" in energy


@pytest.mark.asyncio
async def test_group_dynamics_fields(client):
    resp = await client.post(MULTI_USER_URL, json=_two_users())
    assert resp.status_code == 200
    dynamics = resp.json()["group_dynamics"]
    assert "avg_compatibility" in dynamics
    assert "roles" in dynamics


# ─── Validation ──────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_too_few_users_422(client):
    body = {
        "users": [
            {"name": "Solo", "birth_year": 1990, "birth_month": 1, "birth_day": 1}
        ]
    }
    resp = await client.post(MULTI_USER_URL, json=body)
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_too_many_users_422(client):
    users = [
        {"name": f"U{i}", "birth_year": 1990, "birth_month": 1, "birth_day": 1}
        for i in range(11)
    ]
    resp = await client.post(MULTI_USER_URL, json={"users": users})
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_invalid_primary_index_422(client):
    body = _two_users()
    body["primary_user_index"] = 5
    resp = await client.post(MULTI_USER_URL, json=body)
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_invalid_birth_data_422(client):
    body = {
        "users": [
            {"name": "A", "birth_year": 1990, "birth_month": 13, "birth_day": 1},
            {"name": "B", "birth_year": 1990, "birth_month": 1, "birth_day": 1},
        ]
    }
    resp = await client.post(MULTI_USER_URL, json=body)
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_empty_name_422(client):
    body = {
        "users": [
            {"name": "", "birth_year": 1990, "birth_month": 1, "birth_day": 1},
            {"name": "B", "birth_year": 1990, "birth_month": 1, "birth_day": 1},
        ]
    }
    resp = await client.post(MULTI_USER_URL, json=body)
    assert resp.status_code == 422


# ─── DB Persistence ──────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_reading_appears_in_history(client):
    await client.post(MULTI_USER_URL, json=_two_users())
    resp = await client.get(READINGS_URL, params={"sign_type": "multi_user"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["readings"][0]["sign_type"] == "multi_user"


# ─── Auth ────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_readonly_403(readonly_client):
    resp = await readonly_client.post(MULTI_USER_URL, json=_two_users())
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_unauthenticated_401(unauth_client):
    resp = await unauth_client.post(MULTI_USER_URL, json=_two_users())
    assert resp.status_code == 401
