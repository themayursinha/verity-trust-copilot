import secrets
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.webhook import Webhook, WebhookLog
from app.schemas.webhook import (
    WebhookCreate,
    WebhookResponse,
    WebhookUpdate,
    WebhookLogResponse,
    WEBHOOK_EVENTS,
)

router = APIRouter(prefix="/api/v1/webhooks", tags=["webhooks"])


@router.get("", response_model=List[WebhookResponse])
async def list_webhooks(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in ("admin",):
        raise HTTPException(status_code=403, detail="Admin required")
    result = await db.execute(
        select(Webhook).where(Webhook.org_id == current_user.org_id)
    )
    return result.scalars().all()


@router.post("", response_model=WebhookResponse, status_code=201)
async def create_webhook(
    data: WebhookCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in ("admin",):
        raise HTTPException(status_code=403, detail="Admin required")
    for ev in data.events:
        if ev not in WEBHOOK_EVENTS:
            raise HTTPException(status_code=400, detail=f"Unknown event: {ev}")

    import json
    webhook = Webhook(
        org_id=current_user.org_id,
        url=data.url,
        name=data.name,
        events=json.dumps(data.events),
        custom_headers=data.custom_headers,
        secret=secrets.token_hex(32),
    )
    db.add(webhook)
    await db.commit()
    await db.refresh(webhook)
    return webhook


@router.patch("/{webhook_id}", response_model=WebhookResponse)
async def update_webhook(
    webhook_id: str,
    data: WebhookUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in ("admin",):
        raise HTTPException(status_code=403, detail="Admin required")
    result = await db.execute(
        select(Webhook).where(
            Webhook.id == webhook_id,
            Webhook.org_id == current_user.org_id,
        )
    )
    webhook = result.scalar_one_or_none()
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")

    if data.url is not None:
        webhook.url = data.url
    if data.name is not None:
        webhook.name = data.name
    if data.events is not None:
        for ev in data.events:
            if ev not in WEBHOOK_EVENTS:
                raise HTTPException(status_code=400, detail=f"Unknown event: {ev}")
        import json
        webhook.events = json.dumps(data.events)
    if data.custom_headers is not None:
        webhook.custom_headers = data.custom_headers
    if data.is_active is not None:
        webhook.is_active = data.is_active

    await db.commit()
    await db.refresh(webhook)
    return webhook


@router.delete("/{webhook_id}")
async def delete_webhook(
    webhook_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in ("admin",):
        raise HTTPException(status_code=403, detail="Admin required")
    result = await db.execute(
        select(Webhook).where(
            Webhook.id == webhook_id,
            Webhook.org_id == current_user.org_id,
        )
    )
    webhook = result.scalar_one_or_none()
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")
    await db.delete(webhook)
    await db.commit()
    return {"deleted": True}


@router.post("/{webhook_id}/test")
async def test_webhook(
    webhook_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in ("admin",):
        raise HTTPException(status_code=403, detail="Admin required")
    result = await db.execute(
        select(Webhook).where(
            Webhook.id == webhook_id,
            Webhook.org_id == current_user.org_id,
        )
    )
    webhook = result.scalar_one_or_none()
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")

    from app.services.webhook_service import dispatch_webhook
    await dispatch_webhook(db, current_user.org_id, "integration.failed", {"test": True})
    return {"sent": True}


@router.get("/{webhook_id}/logs", response_model=List[WebhookLogResponse])
async def get_webhook_logs(
    webhook_id: str,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in ("admin",):
        raise HTTPException(status_code=403, detail="Admin required")
    result = await db.execute(
        select(Webhook).where(
            Webhook.id == webhook_id,
            Webhook.org_id == current_user.org_id,
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Webhook not found")

    result = await db.execute(
        select(WebhookLog)
        .where(WebhookLog.webhook_id == webhook_id)
        .order_by(WebhookLog.created_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
    )
    return result.scalars().all()