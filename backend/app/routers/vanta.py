"""Vanta and Drata integration router."""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.dependencies import get_current_active_user
from app.models import AuditLog, EvidenceRecord, User
from app.services.vanta_mock import generate_mock_records
from app.services.vanta_service import fetch_vanta_evidence

router = APIRouter(prefix="/api/v1/vanta", tags=["vanta"])


class VantaSyncRequest(BaseModel):
    organization_id: str = ""


@router.get("/status")
async def vanta_status(
    current_user: User = Depends(get_current_active_user),
):
    return {
        "connected": settings.vanta_configured,
        "api_key_configured": bool(settings.VANTA_API_KEY),
        "integration_mode": settings.VANTA_INTEGRATION_MODE,
        "api_base": settings.VANTA_API_BASE if settings.vanta_configured else None,
        "organization_id": "",
        "last_sync": None,
    }


@router.post("/sync")
async def vanta_sync(
    body: VantaSyncRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    org_id = current_user.org_id

    if settings.vanta_configured:
        incoming_records = await fetch_vanta_evidence()
        mode = "live"
    else:
        incoming_records = generate_mock_records()
        mode = "mock"

    if not incoming_records:
        return {
            "status": f"{mode}_empty",
            "message": f"No evidence found from Vanta ({mode} mode).",
            "synced_count": 0,
            "synced_titles": [],
            "integration_mode": mode,
        }

    result = await db.execute(
        select(EvidenceRecord.id).where(EvidenceRecord.org_id == org_id)
    )
    existing_ids = set(result.scalars().all())

    synced = []
    for record in incoming_records:
        rec_id = record["id"]
        if rec_id in existing_ids:
            continue
        evidence = EvidenceRecord(
            org_id=org_id,
            id=rec_id,
            title=record["title"][:500],
            type=record.get("type", "control-evidence"),
            frameworks=record.get("frameworks", []) or [],
            control_ids=record.get("control_ids", []) or [],
            last_reviewed=record["last_reviewed"],
            owner=record.get("owner", "Vanta Import"),
            summary=record.get("summary", "") or "Imported from Vanta",
            snippets=record.get("snippets", []) or ["Imported from Vanta"],
        )
        db.add(evidence)
        existing_ids.add(rec_id)
        synced.append(record["title"])

    audit = AuditLog(
        org_id=org_id,
        user_id=current_user.id,
        resource_type="vanta",
        resource_id="sync",
        action="vanta_sync",
        changes={
            "mode": mode,
            "synced": len(synced),
            "titles": synced,
        },
    )
    db.add(audit)
    await db.commit()

    return {
        "status": f"{mode}_success",
        "message": f"Vanta sync complete ({mode} mode). {len(synced)} records imported.",
        "synced_count": len(synced),
        "synced_titles": synced,
        "integration_mode": mode,
    }
