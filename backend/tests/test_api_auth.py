"""Integration tests for authentication endpoints."""

import pytest


@pytest.mark.asyncio
async def test_register(client):
    resp = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "new@test.com",
            "password": "securepass123",
            "display_name": "New User",
            "organization_name": "New Org",
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["user"]["email"] == "new@test.com"
    assert data["user"]["role"] == "admin"
    assert data["organization"]["name"] == "New Org"


@pytest.mark.asyncio
async def test_register_duplicate_email(auth_data, client):
    resp = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "test2@example.com",
            "password": "testpass123",
            "display_name": "Dup",
            "organization_name": "Dup Org",
        },
    )
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_login(auth_data, client):
    resp = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "test2@example.com",
            "password": "testpass123",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["user"]["email"] == "test2@example.com"


@pytest.mark.asyncio
async def test_login_wrong_password(auth_data, client):
    resp = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "test2@example.com",
            "password": "wrongpassword",
        },
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_token_refresh(auth_data, client):
    rt = auth_data["refresh_token"]
    resp = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": rt},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["refresh_token"] != rt


@pytest.mark.asyncio
async def test_protected_route_without_auth(client):
    resp = await client.get("/api/v1/evidence/")
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_protected_route_with_auth(auth_headers, client):
    resp = await client.get("/api/v1/evidence/", headers=auth_headers)
    assert resp.status_code == 200
