"""Integration tests for dashboard endpoint."""
import pytest


@pytest.mark.asyncio
async def test_dashboard_empty(auth_headers, client):
    resp = await client.get("/api/v1/dashboard/overview", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "frameworks" in data
    assert "evidence" in data
    assert "policies" in data
    assert "approvals" in data
    assert data["evidence"]["total"] == 0


@pytest.mark.asyncio
async def test_dashboard_with_data(auth_headers, client):
    await client.post(
        "/api/v1/evidence",
        json={
            "title": "Evidence 1",
            "type": "doc",
            "frameworks": ["iso-27001", "soc-2"],
            "control_ids": ["A.5.1"],
            "last_reviewed": "2026-05-01",
            "owner": "Security",
            "summary": "test",
            "snippets": ["test snippet"],
        },
        headers=auth_headers,
    )

    await client.post(
        "/api/v1/policies",
        json={
            "title": "Policy 1",
            "category": "security",
            "content": "test content",
        },
        headers=auth_headers,
    )

    resp = await client.get("/api/v1/dashboard/overview", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["evidence"]["total"] == 1
    assert data["evidence"]["fresh"] == 1
    assert data["evidence"]["frameworks_covered"] == 2
    assert data["policies"]["total"] == 1
