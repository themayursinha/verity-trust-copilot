from datetime import datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_active_user
from app.models import Answer, AnswerGeneration, Approval, AuditLog, EvidenceRecord, Policy, User

router = APIRouter(prefix="/api/v1/dashboard", tags=["dashboard"])


@router.get("/overview")
async def dashboard_overview(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    frameworks: dict[str, dict[str, Any]] = {
        "iso-27001": {"id": "iso-27001", "coverage": 0.0, "evidence_count": 0, "control_count": 0},
        "soc-2": {"id": "soc-2", "coverage": 0.0, "evidence_count": 0, "control_count": 0},
        "gdpr": {"id": "gdpr", "coverage": 0.0, "evidence_count": 0, "control_count": 0},
        "dora": {"id": "dora", "coverage": 0.0, "evidence_count": 0, "control_count": 0},
    }

    evidence_result = await db.execute(
        select(EvidenceRecord).where(EvidenceRecord.org_id == current_user.org_id)
    )
    records = evidence_result.scalars().all()

    for rec in records:
        for fw in rec.frameworks or []:
            fw_lower = str(fw).lower().replace(" ", "-").replace("_", "-")
            if fw_lower in frameworks:
                frameworks[fw_lower]["evidence_count"] += 1
                ctrl_count = len(rec.control_ids or [])
                frameworks[fw_lower]["control_count"] += ctrl_count

    max_evidence = max((v["evidence_count"] for v in frameworks.values()), default=1)
    for v in frameworks.values():
        v["coverage"] = round(v["evidence_count"] / max(max_evidence, 1), 2)

    now = datetime.now()
    today = now.date()
    fresh = 0
    stale = 0
    fw_set: set[str] = set()
    for rec in records:
        for fw in rec.frameworks or []:
            fw_set.add(str(fw).lower().replace(" ", "-"))
        if rec.last_reviewed is not None:
            age_days = (today - rec.last_reviewed).days
            if age_days <= 180:
                fresh += 1
            elif age_days >= 365:
                stale += 1

    policies_result = await db.execute(
        select(Policy).where(Policy.org_id == current_user.org_id)
    )
    policies = policies_result.scalars().all()

    active_policies = sum(1 for p in policies if p.status == "active")
    draft_policies = sum(1 for p in policies if p.status in ("draft", None, ""))
    cutoff = today + timedelta(days=30)
    upcoming = sum(
        1 for p in policies if p.next_review is not None and p.next_review <= cutoff
    )

    approval_result = await db.execute(
        select(Approval).where(
            Approval.answer_id.in_(
                select(Answer.id).where(
                    Answer.generation_id.in_(
                        select(AnswerGeneration.id).where(
                            AnswerGeneration.org_id == current_user.org_id
                        )
                    )
                )
            )
        )
    )
    approvals = approval_result.scalars().all()

    approved = sum(1 for a in approvals if a.status == "approved")
    rejected = sum(1 for a in approvals if a.status == "rejected")
    unreviewed = sum(1 for a in approvals if a.status in ("unreviewed", None, ""))

    activity_result = await db.execute(
        select(AuditLog)
        .where(AuditLog.org_id == current_user.org_id)
        .order_by(AuditLog.created_at.desc())
        .limit(10)
    )
    activity_logs = activity_result.scalars().all()
    recent_activity = [
        {
            "action": log.action,
            "detail": str(log.changes) if log.changes else "",
            "timestamp": log.created_at.isoformat() if log.created_at else "",
        }
        for log in activity_logs
    ]

    return {
        "frameworks": list(frameworks.values()),
        "evidence": {
            "total": len(records),
            "fresh": fresh,
            "stale": stale,
            "frameworks_covered": len(fw_set),
        },
        "policies": {
            "total": len(policies),
            "active": active_policies,
            "draft": draft_policies,
            "upcoming_reviews": upcoming,
        },
        "approvals": {
            "total": len(approvals),
            "approved": approved,
            "rejected": rejected,
            "unreviewed": unreviewed,
        },
        "recent_activity": recent_activity,
    }
