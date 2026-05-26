"""Base integration provider and result types."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class TestResult:
    test_name: str
    status: str
    message: str = ""
    evidence: dict[str, Any] = field(default_factory=dict)
    resources_checked: int = 0
    resources_failed: int = 0


class BaseProvider:
    provider_name: str = "base"
    test_definitions: list[dict[str, Any]] = []

    def __init__(self, config: dict[str, Any]):
        self.config = config

    async def connect(self) -> bool:
        return True

    async def run_all_tests(self) -> list[TestResult]:
        results: list[TestResult] = []
        for test_def in self.test_definitions:
            method_name = test_def.get("method", "")
            if not method_name:
                continue
            method = getattr(self, method_name, None)
            if not method:
                results.append(
                    TestResult(
                        test_name=test_def["name"],
                        status="error",
                        message=f"Method {method_name} not found on provider",
                    )
                )
                continue
            try:
                result = await method()
                result.test_name = test_def["name"]
                results.append(result)
            except Exception as e:
                results.append(
                    TestResult(
                        test_name=test_def["name"],
                        status="error",
                        message=str(e),
                    )
                )
        return results
