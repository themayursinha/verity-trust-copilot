import re
import uuid
from datetime import date, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_active_user
from app.models import EvidenceRecord, User
from app.schemas.evidence import (
    EvidenceCreate,
    EvidenceResponse,
    EvidenceUpdate,
)

router = APIRouter(prefix="/api/v1/evidence", tags=["evidence"])


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "evidence"


def parse_date(raw: str) -> date:
    raw_str = str(raw).strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d-%b-%Y", "%B %d, %Y"):
        try:
            return datetime.strptime(raw_str, fmt).date()
        except ValueError:
            continue
    return date.fromisoformat(raw_str)


def normalize_evidence_record(record: dict[str, Any]) -> dict[str, Any]:
    required = ["title", "type", "last_reviewed", "owner", "summary", "snippets"]
    missing = [field for field in required if not record.get(field)]
    if missing:
        raise ValueError(f"Evidence record missing required fields: {', '.join(missing)}")
    snippets = record.get("snippets")
    if not isinstance(snippets, list) or not snippets:
        raise ValueError("Evidence record must include at least one snippet.")

    parse_date(str(record["last_reviewed"]))
    title = str(record["title"]).strip()
    frameworks = record.get("frameworks", [])
    control_ids = record.get("control_ids", [])
    normalized: dict[str, Any] = {
        "id": str(record.get("id") or slugify(title)).strip(),
        "title": title,
        "type": str(record["type"]).strip(),
        "frameworks": [str(item).strip() for item in frameworks if isinstance(item, str) and item.strip()],
        "control_ids": [str(item).strip() for item in control_ids if isinstance(item, str) and item.strip()],
        "last_reviewed": str(record["last_reviewed"]).strip(),
        "owner": str(record["owner"]).strip(),
        "summary": str(record["summary"]).strip(),
        "snippets": [str(item).strip() for item in snippets if isinstance(item, str) and item.strip()],
    }
    if not normalized["snippets"]:
        raise ValueError("Evidence snippets cannot be blank.")
    return normalized


@router.get("/", response_model=list[EvidenceResponse])
async def list_evidence(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    result = await db.execute(
        select(EvidenceRecord)
        .where(EvidenceRecord.org_id == current_user.org_id)
        .order_by(EvidenceRecord.created_at.desc())
    )
    return result.scalars().all()


@router.get("/{evidence_id}", response_model=EvidenceResponse)
async def get_evidence(
    evidence_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    result = await db.execute(
        select(EvidenceRecord).where(
            EvidenceRecord.id == evidence_id,
            EvidenceRecord.org_id == current_user.org_id,
        )
    )
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidence not found")
    return record


@router.post("/", response_model=EvidenceResponse, status_code=status.HTTP_201_CREATED)
async def create_evidence(
    body: EvidenceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    record = EvidenceRecord(
        id=str(uuid.uuid4()),
        org_id=current_user.org_id,
        title=body.title,
        type=body.type,
        frameworks=body.frameworks,
        control_ids=body.control_ids,
        last_reviewed=body.last_reviewed,
        owner=body.owner,
        summary=body.summary,
        snippets=body.snippets,
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return record


@router.post("/import")
async def import_evidence(
    payload: dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    incoming = payload.get("records", payload.get("record"))
    if isinstance(incoming, dict):
        incoming_records = [incoming]
    elif isinstance(incoming, list):
        incoming_records = incoming
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Send an evidence record or a list of records.",
        )

    result = await db.execute(
        select(EvidenceRecord.id).where(EvidenceRecord.org_id == current_user.org_id)
    )
    existing_ids = set(result.scalars().all())

    stored: list[EvidenceResponse] = []
    for item in incoming_records:
        if not isinstance(item, dict):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Evidence records must be JSON objects.",
            )
        try:
            normalized = normalize_evidence_record(item)
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

        candidate = str(normalized["id"])
        suffix = 2
        while candidate in existing_ids:
            candidate = f"{normalized['id']}-{suffix}"
            suffix += 1

        record = EvidenceRecord(
            id=candidate,
            org_id=current_user.org_id,
            title=normalized["title"],
            type=normalized["type"],
            frameworks=normalized["frameworks"],
            control_ids=normalized["control_ids"],
            last_reviewed=parse_date(normalized["last_reviewed"]),
            owner=normalized["owner"],
            summary=normalized["summary"],
            snippets=normalized["snippets"],
        )
        existing_ids.add(candidate)
        db.add(record)

    await db.commit()

    result = await db.execute(
        select(EvidenceRecord)
        .where(EvidenceRecord.org_id == current_user.org_id)
        .order_by(EvidenceRecord.created_at.desc())
    )
    all_records = result.scalars().all()
    return {"stored": len(incoming_records), "evidence": all_records}


@router.put("/{evidence_id}", response_model=EvidenceResponse)
async def update_evidence(
    evidence_id: str,
    body: EvidenceUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    result = await db.execute(
        select(EvidenceRecord).where(
            EvidenceRecord.id == evidence_id,
            EvidenceRecord.org_id == current_user.org_id,
        )
    )
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidence not found")

    update_data = body.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(record, field, value)

    await db.commit()
    await db.refresh(record)
    return record


@router.delete("/{evidence_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_evidence(
    evidence_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    result = await db.execute(
        select(EvidenceRecord).where(
            EvidenceRecord.id == evidence_id,
            EvidenceRecord.org_id == current_user.org_id,
        )
    )
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidence not found")

    await db.delete(record)
    await db.commit()
    return None
