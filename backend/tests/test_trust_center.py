"""Integration tests for Trust Center admin and public APIs."""

import pytest


@pytest.mark.asyncio
async def test_get_settings_default(client, auth_headers):
    resp = await client.get("/api/v1/trust-center/settings", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["enabled"] is False
    assert data["configured"] is False


@pytest.mark.asyncio
async def test_update_and_get_settings(client, auth_headers):
    resp = await client.put(
        "/api/v1/trust-center/settings",
        json={
            "enabled": True,
            "page_title": "Acme Trust Center",
            "hero_headline": "Security You Can Trust",
            "hero_subtext": "Real-time compliance status and documentation.",
            "brand_color": "#2563eb",
            "show_ai_chatbot": True,
            "show_subscribe": True,
            "show_document_requests": True,
            "show_certifications": True,
            "show_controls": True,
            "show_policies": True,
        },
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["enabled"] is True
    assert data["page_title"] == "Acme Trust Center"
    assert data["brand_color"] == "#2563eb"

    get_resp = await client.get("/api/v1/trust-center/settings", headers=auth_headers)
    assert get_resp.status_code == 200
    assert get_resp.json()["enabled"] is True
    assert get_resp.json()["configured"] is True


@pytest.mark.asyncio
async def test_document_crud(client, auth_headers):
    create_resp = await client.post(
        "/api/v1/trust-center/documents",
        json={
            "title": "SOC 2 Type II Report",
            "description": "Latest SOC 2 report covering 2026.",
            "document_type": "report",
            "requires_nda": True,
            "is_public": False,
        },
        headers=auth_headers,
    )
    assert create_resp.status_code == 201
    doc_id = create_resp.json()["id"]

    list_resp = await client.get("/api/v1/trust-center/documents", headers=auth_headers)
    assert list_resp.status_code == 200
    assert len(list_resp.json()) >= 1

    update_resp = await client.put(
        f"/api/v1/trust-center/documents/{doc_id}",
        json={"title": "Updated SOC 2 Report"},
        headers=auth_headers,
    )
    assert update_resp.status_code == 200

    delete_resp = await client.delete(f"/api/v1/trust-center/documents/{doc_id}", headers=auth_headers)
    assert delete_resp.status_code == 204


@pytest.mark.asyncio
async def test_analytics(client, auth_headers):
    resp = await client.get("/api/v1/trust-center/analytics", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "total_visits" in data
    assert "unique_visitors" in data
    assert "subscriber_count" in data
    assert "daily_visits" in data


@pytest.mark.asyncio
async def test_analytics_with_days_param(client, auth_headers):
    resp = await client.get("/api/v1/trust-center/analytics?days=7", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["period_days"] == 7


@pytest.mark.asyncio
async def test_list_subscribers(client, auth_headers):
    resp = await client.get("/api/v1/trust-center/subscribers", headers=auth_headers)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_list_access_requests(client, auth_headers):
    resp = await client.get("/api/v1/trust-center/access-requests", headers=auth_headers)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_settings_update_preserves_existing(client, auth_headers):
    await client.put(
        "/api/v1/trust-center/settings",
        json={"enabled": True, "page_title": "First Title"},
        headers=auth_headers,
    )
    await client.put(
        "/api/v1/trust-center/settings",
        json={"hero_headline": "Updated Headline"},
        headers=auth_headers,
    )
    resp = await client.get("/api/v1/trust-center/settings", headers=auth_headers)
    data = resp.json()
    assert data["page_title"] == "First Title"
    assert data["hero_headline"] == "Updated Headline"


@pytest.mark.asyncio
async def test_access_request_list(client, auth_headers):
    await client.put(
        "/api/v1/trust-center/settings",
        json={"enabled": True, "show_document_requests": True},
        headers=auth_headers,
    )
    resp = await client.get("/api/v1/trust-center/access-requests", headers=auth_headers)
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_update_document_not_found(client, auth_headers):
    resp = await client.put(
        "/api/v1/trust-center/documents/nonexistent",
        json={"title": "Test"},
        headers=auth_headers,
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_document_not_found(client, auth_headers):
    resp = await client.delete("/api/v1/trust-center/documents/nonexistent", headers=auth_headers)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_public_trust_center_404(client):
    resp = await client.get("/api/v1/public/trust-center/nonexistent-org")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_public_subscribe_404(client):
    resp = await client.post(
        "/api/v1/public/trust-center/nonexistent-org/subscribe",
        json={"email": "test@acme.com", "name": "Test User", "company": "Acme Corp"},
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_public_request_access_404(client):
    resp = await client.post(
        "/api/v1/public/trust-center/nonexistent-org/request-access",
        json={"email": "test@acme.com", "name": "Test User", "company": "Acme Corp", "nda_accepted": True},
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_public_chat_404(client):
    resp = await client.post(
        "/api/v1/public/trust-center/nonexistent-org/chat",
        json={"question": "What certifications do you have?"},
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_public_subscribe_no_email(client):
    resp = await client.post(
        "/api/v1/public/trust-center/nonexistent-org/subscribe",
        json={"email": ""},
    )
    assert resp.status_code == 404
