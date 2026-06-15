import pytest


@pytest.mark.asyncio
class TestNotificationsAPI:
    async def test_list_notifications_empty(self, client, auth_headers):
        response = await client.get("/api/v1/notifications", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    async def test_get_unread_count(self, client, auth_headers):
        response = await client.get("/api/v1/notifications/unread-count", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "count" in data

    async def test_mark_all_read(self, client, auth_headers):
        response = await client.patch("/api/v1/notifications/read-all", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "marked_read" in data

    async def test_delete_notification_not_found(self, client, auth_headers):
        response = await client.delete(
            "/api/v1/notifications/00000000-0000-0000-0000-000000000000",
            headers=auth_headers,
        )
        assert response.status_code == 404

    async def test_unauthenticated_access(self, client):
        response = await client.get("/api/v1/notifications")
        assert response.status_code == 401
