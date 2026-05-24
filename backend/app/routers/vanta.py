import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_active_user
from app.models import AuditLog, EvidenceRecord, User

router = APIRouter(prefix="/api/v1/vanta", tags=["vanta"])


@router.get("/status")
async def vanta_status(
    current_user: User = Depends(get_current_active_user),
):
    return {
        "connected": False,
        "api_key_configured": False,
        "integration_mode": "mock",
        "organization_id": "",
        "last_sync": None,
    }


@router.post("/sync")
async def vanta_sync(
    payload: dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    org_id = str(payload.get("organization_id", "")).strip()
    now = datetime.now()
    now_date = now.date()
    now_str = now.isoformat(timespec="seconds")

    result = await db.execute(
        select(EvidenceRecord.id).where(EvidenceRecord.org_id == current_user.org_id)
    )
    existing_ids = set(result.scalars().all())

    mock_records = [
        {
            "id": "vanta-device-compliance",
            "title": "Mock Vanta Device Compliance Check",
            "type": "control-evidence",
            "frameworks": ["SOC 2", "ISO 27001"],
            "control_ids": ["CC6.1", "A.8.8"],
            "last_reviewed": now_date,
            "owner": "Security",
            "summary": "Mock Vanta import: device encryption, MFA, screen lock, antivirus, OS patch level.",
            "snippets": ["Mock Vanta import monitors device compliance across all employee laptops."],
        },
        {
            "id": "vanta-access-review",
            "title": "Mock Vanta Quarterly Access Review",
            "type": "control-evidence",
            "frameworks": ["SOC 2", "ISO 27001"],
            "control_ids": ["CC6.2", "A.5.15"],
            "last_reviewed": now_date,
            "owner": "IT",
            "summary": "Mock Vanta import for quarterly access review of production, identity, and admin systems.",
            "snippets": ["Mock Vanta import shows quarterly access reviews for production and admin systems."],
        },
        {
            "id": "vanta-security-training",
            "title": "Mock Vanta Security Training Report",
            "type": "control-evidence",
            "frameworks": ["SOC 2", "ISO 27001"],
            "control_ids": ["CC1.2", "A.6.3"],
            "last_reviewed": now_date,
            "owner": "Security",
            "summary": "Mock Vanta import for employee security training completion status.",
            "snippets": ["Mock Vanta import tracks security training completion for all employees."],
        },
    ]

    synced: list[str] = []
    for record in mock_records:
        if record["id"] not in existing_ids:
            evidence = EvidenceRecord(
                id=record["id"],
                org_id=current_user.org_id,
                title=record["title"],
                type=record["type"],
                frameworks=record["frameworks"],
                control_ids=record["control_ids"],
                last_reviewed=record["last_reviewed"],
                owner=record["owner"],
                summary=record["summary"],
                snippets=record["snippets"],
            )
            db.add(evidence)
            existing_ids.add(record["id"])
            synced.append(record["title"])

    audit = AuditLog(
        id=str(uuid.uuid4()),
        org_id=current_user.org_id,
        user_id=current_user.id,
        resource_type="vanta",
        resource_id="sync",
        action="mock_sync",
        changes={"synced": len(synced)},
    )
    db.add(audit)

    await db.commit()

    return {
        "status": "mock_success",
        "message": "Mock Vanta import completed. No external Vanta API was called and no API key was stored.",
        "synced_count": len(synced),
        "synced_titles": synced,
        "last_sync": now_str,
        "config": {
            "connected": True,
            "api_key_configured": False,
            "integration_mode": "mock",
            "organization_id": org_id,
            "last_sync": now_str,
        },
    }
