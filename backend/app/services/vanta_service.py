"""Vanta integration service — fetches evidence from Vanta API."""
from datetime import date, datetime
from typing import Any

import httpx

from app.config import settings


async def fetch_vanta_evidence() -> list[dict[str, Any]]:
    """Fetch evidence records from Vanta API. Returns list of evidence dicts."""
    if not settings.VANTA_API_KEY:
        return []

    headers = {
        "Authorization": f"Bearer {settings.VANTA_API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(
                f"{settings.VANTA_API_BASE}/v1/evidence",
                headers=headers,
                params={"limit": 100},
            )
            if response.status_code != 200:
                return []

            data = response.json()
            records = data.get("results", data.get("data", []))

            evidence = []
            for item in records:
                evidence.append({
                    "id": f"vanta-{item.get('id', '')}",
                    "title": item.get("title") or item.get("name") or "Vanta Evidence",
                    "type": "control-evidence",
                    "frameworks": item.get("frameworks") or item.get("controls", []) or [],
                    "control_ids": _extract_control_ids(item),
                    "last_reviewed": _parse_date(
                        item.get("lastTestedAt") or item.get("updatedAt")
                    ),
                    "owner": item.get("assignee", {}).get("name", "Vanta Import")
                    if isinstance(item.get("assignee"), dict)
                    else "Vanta Import",
                    "summary": (item.get("description") or item.get("evidence") or "")[:500],
                    "snippets": [
                        (item.get("description") or item.get("evidence") or "Imported from Vanta")
                    ],
                })

            return evidence

        except Exception:
            return []


def _extract_control_ids(item: dict) -> list[str]:
    """Extract control IDs from a Vanta evidence item."""
    controls = item.get("controls", [])
    if controls and isinstance(controls[0], dict):
        return [c.get("id", c.get("name", "")) for c in controls]
    return [str(c) for c in controls if c]


def _parse_date(value: Any) -> date:
    """Parse a date string from Vanta API into a date object."""
    if not value:
        return date.today()
    if isinstance(value, date):
        return value
    if isinstance(value, datetime):
        return value.date()
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).date()
    except (ValueError, TypeError):
        return date.today()
