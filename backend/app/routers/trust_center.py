"""Trust Center admin API — manage settings, documents, subscribers, analytics."""

from datetime import datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func as sqlfunc
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_active_user
from app.models.trust_center import (
    TrustCenterSettings,
    TrustCenterVisit,
    TrustCenterSubscriber,
    TrustCenterDocument,
    TrustCenterAccessRequest,
)
from app.models.user import User

router = APIRouter(prefix="/api/v1/trust-center", tags=["trust-center"])


def _settings_to_dict(s: TrustCenterSettings) -> dict[str, Any]:
    return {
        "id": s.id,
        "org_id": s.org_id,
        "enabled": s.enabled,
        "custom_domain": s.custom_domain,
        "page_title": s.page_title,
        "hero_headline": s.hero_headline,
        "hero_subtext": s.hero_subtext,
        "brand_color": s.brand_color,
        "logo_url": s.logo_url,
        "favicon_url": s.favicon_url,
        "show_certifications": s.show_certifications,
        "show_controls": s.show_controls,
        "show_policies": s.show_policies,
        "show_ai_chatbot": s.show_ai_chatbot,
        "show_subscribe": s.show_subscribe,
        "show_document_requests": s.show_document_requests,
        "require_nda": s.require_nda,
        "created_at": s.created_at.isoformat() if s.created_at else None,
        "updated_at": s.updated_at.isoformat() if s.updated_at else None,
    }


@router.get("/settings")
async def get_settings(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    result = await db.execute(
        select(TrustCenterSettings).where(TrustCenterSettings.org_id == current_user.org_id)
    )
    settings = result.scalar_one_or_none()
    if not settings:
        return {"enabled": False, "configured": False}
    return {**_settings_to_dict(settings), "configured": True}


@router.put("/settings")
async def update_settings(
    body: dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    result = await db.execute(
        select(TrustCenterSettings).where(TrustCenterSettings.org_id == current_user.org_id)
    )
    settings = result.scalar_one_or_none()

    if not settings:
        settings = TrustCenterSettings(org_id=current_user.org_id, **body)
        db.add(settings)
    else:
        allowed = {
            "enabled", "custom_domain", "page_title", "hero_headline", "hero_subtext",
            "brand_color", "logo_url", "favicon_url", "show_certifications",
            "show_controls", "show_policies", "show_ai_chatbot", "show_subscribe",
            "show_document_requests", "require_nda",
        }
        for key, value in body.items():
            if key in allowed:
                setattr(settings, key, value)

    await db.commit()
    await db.refresh(settings)
    return {**_settings_to_dict(settings), "configured": True}


@router.get("/documents")
async def list_documents(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    result = await db.execute(
        select(TrustCenterDocument)
        .where(TrustCenterDocument.org_id == current_user.org_id)
        .order_by(TrustCenterDocument.created_at.desc())
    )
    documents = result.scalars().all()
    return [
        {
            "id": d.id,
            "title": d.title,
            "description": d.description,
            "document_type": d.document_type,
            "file_url": d.file_url,
            "requires_nda": d.requires_nda,
            "is_public": d.is_public,
            "download_count": d.download_count,
            "created_at": d.created_at.isoformat() if d.created_at else None,
        }
        for d in documents
    ]


@router.post("/documents", status_code=status.HTTP_201_CREATED)
async def create_document(
    body: dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    doc = TrustCenterDocument(
        org_id=current_user.org_id,
        title=body.get("title", "Untitled"),
        description=body.get("description", ""),
        document_type=body.get("document_type", "report"),
        file_url=body.get("file_url", ""),
        requires_nda=body.get("requires_nda", False),
        is_public=body.get("is_public", False),
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)
    return {
        "id": doc.id,
        "title": doc.title,
        "description": doc.description,
        "document_type": doc.document_type,
        "file_url": doc.file_url,
        "requires_nda": doc.requires_nda,
        "is_public": doc.is_public,
        "download_count": doc.download_count,
        "created_at": doc.created_at.isoformat() if doc.created_at else None,
    }


@router.put("/documents/{document_id}")
async def update_document(
    document_id: str,
    body: dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    result = await db.execute(
        select(TrustCenterDocument).where(
            TrustCenterDocument.id == document_id,
            TrustCenterDocument.org_id == current_user.org_id,
        )
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    allowed = {"title", "description", "document_type", "file_url", "requires_nda", "is_public"}
    for key, value in body.items():
        if key in allowed:
            setattr(doc, key, value)

    await db.commit()
    await db.refresh(doc)
    return {"id": doc.id, "title": doc.title, "status": "updated"}


@router.delete("/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    result = await db.execute(
        select(TrustCenterDocument).where(
            TrustCenterDocument.id == document_id,
            TrustCenterDocument.org_id == current_user.org_id,
        )
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    await db.delete(doc)
    await db.commit()


@router.get("/analytics")
async def get_analytics(
    days: int = Query(default=30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    since = datetime.now() - timedelta(days=days)

    visit_count_result = await db.execute(
        select(sqlfunc.count(TrustCenterVisit.id)).where(
            TrustCenterVisit.org_id == current_user.org_id,
            TrustCenterVisit.created_at >= since,
        )
    )
    total_visits = visit_count_result.scalar() or 0

    unique_ips_result = await db.execute(
        select(sqlfunc.count(sqlfunc.distinct(TrustCenterVisit.visitor_ip))).where(
            TrustCenterVisit.org_id == current_user.org_id,
            TrustCenterVisit.created_at >= since,
        )
    )
    unique_visitors = unique_ips_result.scalar() or 0

    chatbot_queries_result = await db.execute(
        select(sqlfunc.sum(TrustCenterVisit.chatbot_queries)).where(
            TrustCenterVisit.org_id == current_user.org_id,
            TrustCenterVisit.created_at >= since,
        )
    )
    total_chatbot_queries = chatbot_queries_result.scalar() or 0

    doc_downloads_result = await db.execute(
        select(sqlfunc.sum(TrustCenterVisit.document_downloads)).where(
            TrustCenterVisit.org_id == current_user.org_id,
            TrustCenterVisit.created_at >= since,
        )
    )
    total_downloads = doc_downloads_result.scalar() or 0

    subscriber_count_result = await db.execute(
        select(sqlfunc.count(TrustCenterSubscriber.id)).where(
            TrustCenterSubscriber.org_id == current_user.org_id,
            TrustCenterSubscriber.subscribed.is_(True),
        )
    )
    subscriber_count = subscriber_count_result.scalar() or 0

    access_requests_result = await db.execute(
        select(sqlfunc.count(TrustCenterAccessRequest.id)).where(
            TrustCenterAccessRequest.org_id == current_user.org_id,
        )
    )
    pending_requests = access_requests_result.scalar() or 0

    daily_visits_result = await db.execute(
        select(
            sqlfunc.date(TrustCenterVisit.created_at).label("date"),
            sqlfunc.count(TrustCenterVisit.id).label("count"),
        )
        .where(
            TrustCenterVisit.org_id == current_user.org_id,
            TrustCenterVisit.created_at >= since,
        )
        .group_by(sqlfunc.date(TrustCenterVisit.created_at))
        .order_by(sqlfunc.date(TrustCenterVisit.created_at))
    )
    daily_visits = [
        {"date": str(row.date), "count": row.count} for row in daily_visits_result.all()
    ]

    return {
        "period_days": days,
        "total_visits": total_visits,
        "unique_visitors": unique_visitors,
        "total_chatbot_queries": total_chatbot_queries,
        "total_document_downloads": total_downloads,
        "subscriber_count": subscriber_count,
        "pending_access_requests": pending_requests,
        "daily_visits": daily_visits,
    }


@router.get("/subscribers")
async def list_subscribers(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    result = await db.execute(
        select(TrustCenterSubscriber)
        .where(TrustCenterSubscriber.org_id == current_user.org_id)
        .order_by(TrustCenterSubscriber.created_at.desc())
    )
    subscribers = result.scalars().all()
    return [
        {
            "id": s.id,
            "email": s.email,
            "name": s.name,
            "company": s.company,
            "subscribed": s.subscribed,
            "created_at": s.created_at.isoformat() if s.created_at else None,
        }
        for s in subscribers
    ]


@router.get("/access-requests")
async def list_access_requests(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    result = await db.execute(
        select(TrustCenterAccessRequest)
        .where(TrustCenterAccessRequest.org_id == current_user.org_id)
        .order_by(TrustCenterAccessRequest.created_at.desc())
    )
    requests = result.scalars().all()
    return [
        {
            "id": r.id,
            "document_id": r.document_id,
            "requester_email": r.requester_email,
            "requester_name": r.requester_name,
            "requester_company": r.requester_company,
            "nda_accepted": r.nda_accepted,
            "status": r.status,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in requests
    ]


@router.put("/access-requests/{request_id}")
async def approve_access_request(
    request_id: str,
    body: dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    result = await db.execute(
        select(TrustCenterAccessRequest).where(
            TrustCenterAccessRequest.id == request_id,
            TrustCenterAccessRequest.org_id == current_user.org_id,
        )
    )
    req = result.scalar_one_or_none()
    if not req:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Access request not found")

    if "status" in body:
        req.status = body["status"]
        if body["status"] == "approved":
            req.approved_by = current_user.id

    await db.commit()
    return {"id": req.id, "status": req.status}
