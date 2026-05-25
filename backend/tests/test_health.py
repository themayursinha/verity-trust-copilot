"""Basic smoke test for the FastAPI application."""

import pytest


@pytest.mark.asyncio
async def test_health_endpoint():
    """Verify the FastAPI app can be imported and has a health router."""
    from app.main import app
    from app.routers.health import router

    assert app is not None
    assert router is not None


def test_config_loads():
    """Verify settings load with defaults."""
    from app.config import settings

    assert settings.ENVIRONMENT == "development"
    assert settings.ACCESS_TOKEN_EXPIRE_MINUTES == 30
