"""Integration provider registry."""

from app.services.integrations.base import BaseProvider
from app.services.integrations.aws_provider import AWSProvider
from app.services.integrations.github_provider import GitHubProvider


_registry: dict[str, type[BaseProvider]] = {
    "aws": AWSProvider,
    "github": GitHubProvider,
}


def get_provider(name: str, config: dict) -> BaseProvider | None:
    provider_class = _registry.get(name)
    if provider_class is None:
        return None
    return provider_class(config)


def list_providers() -> list[dict]:
    return [
        {
            "name": name,
            "display_name": cls.provider_name,
            "test_count": len(cls.test_definitions),
            "tests": cls.test_definitions,
        }
        for name, cls in _registry.items()
    ]
