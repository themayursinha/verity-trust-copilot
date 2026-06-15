import pytest


@pytest.mark.asyncio
class TestWebhooksAPI:
    async def test_list_webhooks_empty(self, client, auth_headers):
        response = await client.get("/api/v1/webhooks", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    async def test_create_webhook(self, client, auth_headers):
        payload = {
            "url": "https://example.com/webhook",
            "name": "Test Webhook",
            "events": ["integration.failed"],
        }
        response = await client.post(
            "/api/v1/webhooks",
            headers=auth_headers,
            json=payload,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Webhook"
        assert data["url"] == "https://example.com/webhook"
        assert "secret" in data

    async def test_create_webhook_invalid_event(self, client, auth_headers):
        response = await client.post(
            "/api/v1/webhooks",
            headers=auth_headers,
            json={
                "url": "https://example.com/webhook",
                "name": "Test",
                "events": ["invalid.event"],
            },
        )
        assert response.status_code == 400

    async def test_delete_webhook_not_found(self, client, auth_headers):
        response = await client.delete(
            "/api/v1/webhooks/00000000-0000-0000-0000-000000000000",
            headers=auth_headers,
        )
        assert response.status_code == 404

    async def test_webhook_logs_not_found(self, client, auth_headers):
        response = await client.get(
            "/api/v1/webhooks/00000000-0000-0000-0000-000000000000/logs",
            headers=auth_headers,
        )
        assert response.status_code == 404

    async def test_test_webhook_not_found(self, client, auth_headers):
        response = await client.post(
            "/api/v1/webhooks/00000000-0000-0000-0000-000000000000/test",
            headers=auth_headers,
        )
        assert response.status_code == 404
