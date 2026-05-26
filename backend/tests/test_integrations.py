"""Integration tests for the integrations API and providers."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.mark.asyncio
async def test_list_providers(client, auth_headers):
    resp = await client.get("/api/v1/integrations/providers", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "providers" in data
    assert len(data["providers"]) >= 2


@pytest.mark.asyncio
async def test_list_integrations_empty(client, auth_headers):
    resp = await client.get("/api/v1/integrations/", headers=auth_headers)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_create_aws_integration_invalid_creds(client, auth_headers):
    resp = await client.post(
        "/api/v1/integrations/",
        json={
            "provider": "aws",
            "name": "Test AWS",
            "config": {"access_key_id": "fake", "secret_access_key": "fake", "region": "us-east-1"},
        },
        headers=auth_headers,
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_create_github_integration_invalid_creds(client, auth_headers):
    resp = await client.post(
        "/api/v1/integrations/",
        json={
            "provider": "github",
            "name": "Test GitHub",
            "config": {"access_token": "fake_token", "organization": "test-org"},
        },
        headers=auth_headers,
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_create_integration_unsupported_provider(client, auth_headers):
    resp = await client.post(
        "/api/v1/integrations/",
        json={"provider": "unsupported", "name": "Bad", "config": {}},
        headers=auth_headers,
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_dashboard_summary(client, auth_headers):
    resp = await client.get("/api/v1/integrations/dashboard/summary", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "integrations" in data
    assert "recent_results" in data


@pytest.mark.asyncio
async def test_get_results_not_found(client, auth_headers):
    resp = await client.get("/api/v1/integrations/nonexistent/results", headers=auth_headers)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_run_integration_not_found(client, auth_headers):
    resp = await client.post("/api/v1/integrations/nonexistent/run", headers=auth_headers)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_update_integration_not_found(client, auth_headers):
    resp = await client.put(
        "/api/v1/integrations/nonexistent",
        json={"name": "Updated"},
        headers=auth_headers,
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_integration_not_found(client, auth_headers):
    resp = await client.delete("/api/v1/integrations/nonexistent", headers=auth_headers)
    assert resp.status_code == 404


class TestAWSProvider:
    def test_provider_name(self):
        from app.services.integrations.aws_provider import AWSProvider

        provider = AWSProvider({"region": "us-east-1"})
        assert provider.provider_name == "aws"

    def test_test_definitions(self):
        from app.services.integrations.aws_provider import AWSProvider

        provider = AWSProvider({"region": "us-east-1"})
        assert len(provider.test_definitions) == 6

    @pytest.mark.asyncio
    async def test_connect_fails_no_creds(self):
        from app.services.integrations.aws_provider import AWSProvider

        provider = AWSProvider({"region": "us-east-1"})
        connected = await provider.connect()
        assert connected is False


class TestGitHubProvider:
    def test_provider_name(self):
        from app.services.integrations.github_provider import GitHubProvider

        provider = GitHubProvider({"access_token": "test"})
        assert provider.provider_name == "github"

    def test_test_definitions(self):
        from app.services.integrations.github_provider import GitHubProvider

        provider = GitHubProvider({"access_token": "test"})
        assert len(provider.test_definitions) == 3

    @pytest.mark.asyncio
    async def test_connect_fails_bad_token(self):
        from app.services.integrations.github_provider import GitHubProvider

        provider = GitHubProvider({"access_token": "invalid_token"})
        connected = await provider.connect()
        assert connected is False


class TestProviderRegistry:
    def test_get_aws_provider(self):
        from app.services.integrations import get_provider

        provider = get_provider("aws", {"region": "us-east-1"})
        assert provider is not None
        assert provider.provider_name == "aws"

    def test_get_github_provider(self):
        from app.services.integrations import get_provider

        provider = get_provider("github", {"access_token": "test"})
        assert provider is not None
        assert provider.provider_name == "github"

    def test_get_unknown_provider(self):
        from app.services.integrations import get_provider

        provider = get_provider("unknown", {})
        assert provider is None

    def test_list_providers(self):
        from app.services.integrations import list_providers

        providers = list_providers()
        assert len(providers) >= 2
        names = [p["name"] for p in providers]
        assert "aws" in names
        assert "github" in names


class TestBaseProvider:
    @pytest.mark.asyncio
    async def test_run_all_tests_empty(self):
        from app.services.integrations.base import BaseProvider

        provider = BaseProvider({})
        provider.test_definitions = []
        results = await provider.run_all_tests()
        assert results == []

    @pytest.mark.asyncio
    async def test_run_all_tests_missing_method(self):
        from app.services.integrations.base import BaseProvider

        provider = BaseProvider({})
        provider.test_definitions = [{"name": "Bad Test", "method": "nonexistent"}]
        results = await provider.run_all_tests()
        assert len(results) == 1
        assert results[0].status == "error"
