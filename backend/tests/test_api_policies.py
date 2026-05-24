"""Integration tests for policy endpoints."""
import pytest


@pytest.mark.asyncio
async def test_create_policy(auth_headers, client):
    resp = await client.post(
        "/api/v1/policies",
        json={
            "title": "Data Protection Policy",
            "category": "data-protection",
            "content": "All data must be encrypted.",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["title"] == "Data Protection Policy"
    assert data["status"] == "draft"
    assert data["version"] == 1
    assert "next_review" in data


@pytest.mark.asyncio
async def test_list_policies(auth_headers, client):
    await client.post(
        "/api/v1/policies",
        json={
            "title": "Policy A",
            "category": "security",
            "content": "test",
        },
        headers=auth_headers,
    )
    await client.post(
        "/api/v1/policies",
        json={
            "title": "Policy B",
            "category": "security",
            "content": "test",
        },
        headers=auth_headers,
    )

    resp = await client.get("/api/v1/policies", headers=auth_headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 2


@pytest.mark.asyncio
async def test_update_policy(auth_headers, client):
    create_resp = await client.post(
        "/api/v1/policies",
        json={
            "title": "Old Title",
            "category": "security",
            "content": "old",
        },
        headers=auth_headers,
    )
    policy_id = create_resp.json()["id"]

    resp = await client.put(
        f"/api/v1/policies/{policy_id}",
        json={
            "title": "New Title",
            "content": "updated content",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["title"] == "New Title"
    assert data["version"] == 2


@pytest.mark.asyncio
async def test_delete_policy(auth_headers, client):
    create_resp = await client.post(
        "/api/v1/policies",
        json={
            "title": "Delete Me",
            "category": "security",
            "content": "test",
        },
        headers=auth_headers,
    )
    policy_id = create_resp.json()["id"]

    resp = await client.delete(f"/api/v1/policies/{policy_id}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json() == {"deleted": policy_id}
