"""GitHub integration provider — branch protection, repo visibility, Dependabot checks."""

from __future__ import annotations

from typing import Any

import httpx

from app.services.integrations.base import BaseProvider, TestResult

GITHUB_API_BASE = "https://api.github.com"


class GitHubProvider(BaseProvider):
    provider_name = "github"

    test_definitions = [
        {"name": "Default Branch Protected", "method": "check_branch_protection", "category": "version-control", "frameworks": ["soc2"], "control_ids": ["CC8.1"]},
        {"name": "No Public Repositories", "method": "check_repo_visibility", "category": "version-control", "frameworks": ["soc2", "iso27001"], "control_ids": ["CC6.1"]},
        {"name": "Dependabot Alerts Enabled", "method": "check_dependabot", "category": "version-control", "frameworks": ["soc2"], "control_ids": ["CC7.1"]},
    ]

    def __init__(self, config: dict[str, Any]):
        super().__init__(config)
        self._token = config.get("access_token", "")
        self._org = config.get("organization", "")
        self._headers = {
            "Authorization": f"Bearer {self._token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    async def connect(self) -> bool:
        if not self._token:
            return False
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(f"{GITHUB_API_BASE}/user", headers=self._headers)
                return resp.status_code == 200
        except Exception:
            return False

    async def _list_repos(self) -> list[dict[str, Any]]:
        repos: list[dict[str, Any]] = []
        url = f"{GITHUB_API_BASE}/orgs/{self._org}/repos" if self._org else f"{GITHUB_API_BASE}/user/repos"

        async with httpx.AsyncClient(timeout=15.0) as client:
            page = 1
            while True:
                resp = await client.get(url, headers=self._headers, params={"per_page": 100, "page": page, "type": "all"})
                if resp.status_code != 200:
                    break
                batch = resp.json()
                if not batch:
                    break
                repos.extend(batch)
                if len(batch) < 100:
                    break
                page += 1

        return repos

    async def check_branch_protection(self) -> TestResult:
        try:
            repos = await self._list_repos()
            if not repos:
                return TestResult(test_name="", status="pass", message="No repositories found", evidence={"total_repos": 0})

            unprotected = 0
            details: list[dict[str, Any]] = []

            async with httpx.AsyncClient(timeout=15.0) as client:
                for repo in repos:
                    repo_name = repo.get("name", "")
                    owner = repo.get("owner", {}).get("login", "")
                    if not repo_name or repo.get("archived"):
                        continue
                    branch_url = f"{GITHUB_API_BASE}/repos/{owner}/{repo_name}/branches/{repo.get('default_branch', 'main')}/protection"
                    resp = await client.get(branch_url, headers=self._headers)
                    if resp.status_code != 200:
                        unprotected += 1
                        details.append({"repo": repo_name, "protected": False})

            total = sum(1 for r in repos if not r.get("archived"))
            if total == 0:
                return TestResult(test_name="", status="pass", message="No active repositories", evidence={"total_repos": 0})
            status = "fail" if unprotected > 0 else "pass"
            return TestResult(test_name="", status=status, message=f"{unprotected}/{total} repos without branch protection" if unprotected else "All repos have branch protection", resources_checked=total, resources_failed=unprotected, evidence={"repos": details})
        except Exception as e:
            return TestResult(test_name="", status="error", message=str(e))

    async def check_repo_visibility(self) -> TestResult:
        try:
            repos = await self._list_repos()
            if not repos:
                return TestResult(test_name="", status="pass", message="No repositories found", evidence={"total_repos": 0})

            public_repos = [r for r in repos if not r.get("private") and not r.get("archived")]
            total = len(repos)
            public_count = len(public_repos)
            status = "fail" if public_count > 0 else "pass"
            return TestResult(test_name="", status=status, message=f"{public_count}/{total} public repositories" if public_count else "All repositories are private", resources_checked=total, resources_failed=public_count, evidence={"public_repos": [r.get("name") for r in public_repos]})
        except Exception as e:
            return TestResult(test_name="", status="error", message=str(e))

    async def check_dependabot(self) -> TestResult:
        try:
            repos = await self._list_repos()
            if not repos:
                return TestResult(test_name="", status="pass", message="No repositories found", evidence={"total_repos": 0})

            no_dependabot = 0
            details: list[dict[str, Any]] = []

            async with httpx.AsyncClient(timeout=15.0) as client:
                for repo in repos:
                    repo_name = repo.get("name", "")
                    owner = repo.get("owner", {}).get("login", "")
                    if not repo_name or repo.get("archived"):
                        continue
                    alerts_url = f"{GITHUB_API_BASE}/repos/{owner}/{repo_name}/vulnerability-alerts"
                    resp = await client.get(alerts_url, headers=self._headers)
                    if resp.status_code == 404:
                        no_dependabot += 1
                        details.append({"repo": repo_name, "dependabot": "disabled"})

            active = sum(1 for r in repos if not r.get("archived"))
            if active == 0:
                return TestResult(test_name="", status="pass", message="No active repositories", evidence={"total_repos": 0})
            status = "fail" if no_dependabot > 0 else "pass"
            return TestResult(test_name="", status=status, message=f"{no_dependabot}/{active} repos without Dependabot" if no_dependabot else "Dependabot enabled on all repos", resources_checked=active, resources_failed=no_dependabot, evidence={"repos": details})
        except Exception as e:
            return TestResult(test_name="", status="error", message=str(e))
