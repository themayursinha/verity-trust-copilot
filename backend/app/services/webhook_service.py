import hashlib
import hmac
import json
import logging

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.webhook import Webhook, WebhookLog
from app.schemas.webhook import WEBHOOK_EVENTS

logger = logging.getLogger(__name__)

DISPATCH_TIMEOUT = 10


async def dispatch_webhook(
    db: AsyncSession,
    org_id: str,
    event: str,
    payload: dict,
) -> None:
    if event not in WEBHOOK_EVENTS:
        return

    result = await db.execute(
        select(Webhook).where(
            Webhook.org_id == org_id,
            Webhook.is_active,
        )
    )
    webhooks = result.scalars().all()

    for webhook in webhooks:
        events = json.loads(webhook.events or "[]")
        if event not in events:
            continue

        await _send_webhook(db, webhook, event, payload)


async def _send_webhook(
    db: AsyncSession,
    webhook: Webhook,
    event: str,
    payload: dict,
) -> None:
    body = json.dumps({"event": event, "payload": payload})
    headers = {"Content-Type": "application/json"}

    if webhook.custom_headers:
        try:
            extra = json.loads(webhook.custom_headers)
            headers.update(extra)
        except Exception:
            pass

    signature = ""
    if webhook.secret:
        signature = hmac.new(
            webhook.secret.encode(),
            body.encode(),
            hashlib.sha256,
        ).hexdigest()
        headers["X-Webhook-Signature"] = f"sha256={signature}"

    headers["X-Webhook-Event"] = event
    headers["X-Webhook-ID"] = webhook.id

    log = WebhookLog(
        webhook_id=webhook.id,
        org_id=webhook.org_id,
        event=event,
        payload=body,
    )
    db.add(log)

    try:
        async with httpx.AsyncClient(timeout=DISPATCH_TIMEOUT) as client:
            response = await client.post(webhook.url, content=body, headers=headers)
        log.response_status = response.status_code
        log.response_body = response.text[:2000] if response.text else ""
        log.success = 200 <= response.status_code < 300
    except httpx.TimeoutException:
        log.success = False
        log.error = "Request timed out"
    except Exception as e:
        log.success = False
        log.error = str(e)[:500]

    await db.commit()