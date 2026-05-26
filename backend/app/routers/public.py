"""Public Trust Center API — accessible without authentication."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.ai_engine import get_ai_engine
from app.database import get_db
from app.models.evidence import EvidenceRecord
from app.models.organization import Organization
from app.models.policy import Policy
from app.models.trust_center import (
    TrustCenterSettings,
    TrustCenterVisit,
    TrustCenterSubscriber,
    TrustCenterDocument,
    TrustCenterAccessRequest,
)

router = APIRouter(prefix="/api/v1/public/trust-center", tags=["public-trust-center"])


def _get_settings_dict(s: TrustCenterSettings | None) -> dict[str, Any]:
    if not s:
        return {"enabled": False}
    return {
        "enabled": s.enabled,
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
    }


async def _get_org_by_slug(slug: str, db: AsyncSession) -> Organization | None:
    result = await db.execute(select(Organization).where(Organization.slug == slug))
    return result.scalar_one_or_none()


async def _get_settings(org_id: str, db: AsyncSession) -> TrustCenterSettings | None:
    result = await db.execute(select(TrustCenterSettings).where(TrustCenterSettings.org_id == org_id))
    return result.scalar_one_or_none()


async def _record_visit(org_id: str, request: Request, db: AsyncSession) -> None:
    visit = TrustCenterVisit(
        org_id=org_id,
        visitor_ip=request.client.host if request.client else None,
        page_viewed="trust_center",
        referrer=request.headers.get("referer", ""),
        user_agent=request.headers.get("user-agent", ""),
    )
    db.add(visit)
    await db.commit()


@router.get("/{org_slug}")
async def get_trust_center(
    org_slug: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    org = await _get_org_by_slug(org_slug, db)
    if not org:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")

    settings = await _get_settings(org.id, db)
    if not settings or not settings.enabled:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Trust Center not enabled for this organization"
        )

    await _record_visit(org.id, request, db)

    certs = []
    if settings.show_certifications:
        cert_result = await db.execute(
            select(EvidenceRecord).where(
                EvidenceRecord.org_id == org.id,
                EvidenceRecord.type == "certification",
            )
        )
        for rec in cert_result.scalars().all():
            certs.append(
                {
                    "id": rec.id,
                    "title": rec.title,
                    "frameworks": rec.frameworks or [],
                    "last_reviewed": rec.last_reviewed.isoformat() if rec.last_reviewed else None,
                }
            )

    policies_list = []
    if settings.show_policies:
        pol_result = await db.execute(
            select(Policy)
            .where(
                Policy.org_id == org.id,
                Policy.status == "active",
            )
            .limit(20)
        )
        for p in pol_result.scalars().all():
            policies_list.append(
                {
                    "id": p.id,
                    "name": p.name,
                    "status": p.status,
                    "last_reviewed": p.last_reviewed.isoformat() if p.last_reviewed else None,
                    "version": p.version,
                }
            )

    documents = []
    doc_result = await db.execute(
        select(TrustCenterDocument).where(
            TrustCenterDocument.org_id == org.id,
            TrustCenterDocument.is_public.is_(True),
        )
    )
    for d in doc_result.scalars().all():
        documents.append(
            {
                "id": d.id,
                "title": d.title,
                "description": d.description,
                "document_type": d.document_type,
                "requires_nda": d.requires_nda,
                "download_count": d.download_count,
            }
        )

    return {
        "organization": {
            "name": org.name,
            "slug": org.slug,
        },
        "settings": _get_settings_dict(settings),
        "certifications": certs,
        "policies": policies_list,
        "documents": documents,
    }


@router.post("/{org_slug}/chat")
async def trust_center_chat(
    org_slug: str,
    body: dict[str, Any],
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    org = await _get_org_by_slug(org_slug, db)
    if not org:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")

    settings = await _get_settings(org.id, db)
    if not settings or not settings.enabled or not settings.show_ai_chatbot:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="AI chatbot not available")

    question = body.get("question", "").strip()
    if not question:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Please provide a question.")

    await _record_visit(org.id, request, db)

    engine = get_ai_engine()

    kb_results = engine.search_knowledge_base(question, top_k=3)

    if kb_results:
        answer = kb_results[0].get("answer_text", "")
        source = "knowledge_base"
        confidence = kb_results[0].get("confidence", "medium")
    else:
        ev_result = await db.execute(select(EvidenceRecord).where(EvidenceRecord.org_id == org.id))
        evidence_records = ev_result.scalars().all()

        from app.core.ai_engine import EvidenceChunk

        chunks = []
        for rec in evidence_records:
            for snippet_text in rec.snippets or []:
                chunks.append(
                    EvidenceChunk(
                        evidence_id=rec.id,
                        title=rec.title,
                        evidence_type=rec.type,
                        frameworks=rec.frameworks or [],
                        control_ids=rec.control_ids or [],
                        last_reviewed=rec.last_reviewed,
                        owner=rec.owner,
                        snippet=snippet_text,
                        summary=rec.summary or "",
                    )
                )
        engine.index_evidence(chunks)

        results = engine.search(question, top_k=3)
        if results:
            answer = engine.generate_synthetic_answer(question, results)
            source = "evidence"
            _, _, confidence = engine.compute_confidence(results, use_ai=engine.is_available)
        else:
            answer = "I don't have enough information to answer this question. Please contact the security team directly for more details."
            source = "fallback"
            confidence = "low"

    return {
        "question": question,
        "answer": answer,
        "source": source,
        "confidence": confidence,
    }


@router.post("/{org_slug}/subscribe")
async def subscribe(
    org_slug: str,
    body: dict[str, Any],
    db: AsyncSession = Depends(get_db),
):
    org = await _get_org_by_slug(org_slug, db)
    if not org:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")

    settings = await _get_settings(org.id, db)
    if not settings or not settings.enabled or not settings.show_subscribe:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscriptions not available")

    email = body.get("email", "").strip()
    if not email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email is required.")

    existing = await db.execute(
        select(TrustCenterSubscriber).where(
            TrustCenterSubscriber.org_id == org.id,
            TrustCenterSubscriber.email == email,
        )
    )
    subscriber = existing.scalar_one_or_none()

    if subscriber:
        subscriber.subscribed = True
        subscriber.name = body.get("name", subscriber.name)
        subscriber.company = body.get("company", subscriber.company)
    else:
        subscriber = TrustCenterSubscriber(
            org_id=org.id,
            email=email,
            name=body.get("name", ""),
            company=body.get("company", ""),
        )
        db.add(subscriber)

    await db.commit()
    return {"subscribed": True, "email": email}


@router.post("/{org_slug}/request-access")
async def request_access(
    org_slug: str,
    body: dict[str, Any],
    db: AsyncSession = Depends(get_db),
):
    org = await _get_org_by_slug(org_slug, db)
    if not org:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")

    settings = await _get_settings(org.id, db)
    if not settings or not settings.enabled or not settings.show_document_requests:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document access requests not available")

    email = body.get("email", "").strip()
    if not email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email is required.")

    access_req = TrustCenterAccessRequest(
        org_id=org.id,
        document_id=body.get("document_id"),
        requester_email=email,
        requester_name=body.get("name", ""),
        requester_company=body.get("company", ""),
        nda_accepted=body.get("nda_accepted", False),
        status="pending",
    )
    db.add(access_req)
    await db.commit()
    await db.refresh(access_req)

    return {
        "id": access_req.id,
        "status": access_req.status,
        "message": "Access request submitted. You will be notified when approved.",
    }


@router.get("/{org_slug}/documents/{document_id}")
async def download_document(
    org_slug: str,
    document_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    org = await _get_org_by_slug(org_slug, db)
    if not org:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")

    doc_result = await db.execute(
        select(TrustCenterDocument).where(
            TrustCenterDocument.id == document_id,
            TrustCenterDocument.org_id == org.id,
        )
    )
    doc = doc_result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    if doc.requires_nda:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This document requires an NDA. Please request access first.",
        )

    await db.execute(
        update(TrustCenterDocument)
        .where(TrustCenterDocument.id == document_id)
        .values(download_count=TrustCenterDocument.download_count + 1)
    )
    await db.commit()

    return {
        "id": doc.id,
        "title": doc.title,
        "file_url": doc.file_url,
        "description": doc.description,
    }
