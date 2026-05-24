"""Integration tests for evidence endpoints."""
import pytest


@pytest.mark.asyncio
async def test_create_evidence(auth_headers, client):
    resp = await client.post(
        "/api/v1/evidence",
        json={
            "title": "ISO 27001 Certificate",
            "type": "certification",
            "frameworks": ["iso-27001"],
            "control_ids": ["A.5.1"],
            "last_reviewed": "2026-01-15",
            "owner": "Security Team",
            "summary": "ISO 27001:2022 certification",
            "snippets": ["We maintain ISO 27001:2022 certification."],
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["title"] == "ISO 27001 Certificate"
    assert data["type"] == "certification"
    assert "id" in data


@pytest.mark.asyncio
async def test_list_evidence(auth_headers, client):
    await client.post(
        "/api/v1/evidence",
        json={
            "title": "Test Evidence",
            "type": "doc",
            "frameworks": [],
            "control_ids": [],
            "last_reviewed": "2026-01-01",
            "owner": "Me",
            "summary": "test",
            "snippets": ["test"],
        },
        headers=auth_headers,
    )

    resp = await client.get("/api/v1/evidence", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 1
    assert data[0]["title"] == "Test Evidence"


@pytest.mark.asyncio
async def test_get_evidence_by_id(auth_headers, client):
    create_resp = await client.post(
        "/api/v1/evidence",
        json={
            "title": "Get Me",
            "type": "doc",
            "frameworks": [],
            "control_ids": [],
            "last_reviewed": "2026-01-01",
            "owner": "Me",
            "summary": "test",
            "snippets": ["test"],
        },
        headers=auth_headers,
    )
    evidence_id = create_resp.json()["id"]

    resp = await client.get(f"/api/v1/evidence/{evidence_id}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["title"] == "Get Me"


@pytest.mark.asyncio
async def test_get_evidence_not_found(auth_headers, client):
    resp = await client.get("/api/v1/evidence/nonexistent-id", headers=auth_headers)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_evidence(auth_headers, client):
    create_resp = await client.post(
        "/api/v1/evidence",
        json={
            "title": "Delete Me",
            "type": "doc",
            "frameworks": [],
            "control_ids": [],
            "last_reviewed": "2026-01-01",
            "owner": "Me",
            "summary": "test",
            "snippets": ["test"],
        },
        headers=auth_headers,
    )
    evidence_id = create_resp.json()["id"]

    resp = await client.delete(f"/api/v1/evidence/{evidence_id}", headers=auth_headers)
    assert resp.status_code == 204

    get_resp = await client.get(f"/api/v1/evidence/{evidence_id}", headers=auth_headers)
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_tenant_isolation(auth_headers, client):
    """Verify org B cannot see org A's evidence."""
    await client.post(
        "/api/v1/evidence",
        json={
            "title": "Org A Evidence",
            "type": "doc",
            "frameworks": [],
            "control_ids": [],
            "last_reviewed": "2026-01-01",
            "owner": "Me",
            "summary": "test",
            "snippets": ["test"],
        },
        headers=auth_headers,
    )

    resp2 = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "orgb@test.com",
            "password": "testpass123",
            "display_name": "Org B User",
            "organization_name": "Org B",
        },
    )
    orgb_token = resp2.json()["access_token"]
    orgb_headers = {"Authorization": f"Bearer {orgb_token}"}

    resp = await client.get("/api/v1/evidence", headers=orgb_headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 0
