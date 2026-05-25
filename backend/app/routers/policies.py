import uuid
from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_active_user
from app.models import AuditLog, Policy, User


class PolicyCreate(BaseModel):
    title: str
    category: str = "information-security"
    content: str = ""
    review_interval_months: int = 12


class PolicyUpdate(BaseModel):
    title: str | None = None
    category: str | None = None
    content: str | None = None
    review_interval_months: int | None = None


class PolicyResponse(BaseModel):
    id: str
    org_id: str
    title: str
    category: str | None = None
    content: str | None = None
    status: str
    version: int
    review_interval_months: int
    next_review: date | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


router = APIRouter(prefix="/api/v1/policies", tags=["policies"])


def _calc_next_review(from_dt: datetime, interval_months: int) -> date:
    y = from_dt.year + (from_dt.month + interval_months - 1) // 12
    m = (from_dt.month + interval_months - 1) % 12 + 1
    d = min(from_dt.day, 28)
    try:
        return date(y, m, d)
    except (ValueError, OverflowError):
        return date(y, m, 1)


async def _next_policy_id(db: AsyncSession, org_id: str) -> str:
    result = await db.execute(select(Policy.id).where(Policy.org_id == org_id))
    max_id = 0
    for (pid,) in result.all():
        try:
            max_id = max(max_id, int(pid))
        except (ValueError, TypeError):
            pass
    return str(max_id + 1)


async def _create_audit_log(
    db: AsyncSession,
    current_user: User,
    request: Request | None,
    resource_type: str,
    resource_id: str,
    action: str,
    changes: dict | None = None,
):
    ip = request.client.host if request and request.client else None
    log = AuditLog(
        id=str(uuid.uuid4()),
        org_id=current_user.org_id,
        user_id=current_user.id,
        resource_type=resource_type,
        resource_id=resource_id,
        action=action,
        changes=changes,
        ip_address=ip,
    )
    db.add(log)


@router.get("/", response_model=list[PolicyResponse])
async def list_policies(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    result = await db.execute(
        select(Policy).where(Policy.org_id == current_user.org_id).order_by(Policy.updated_at.desc())
    )
    return result.scalars().all()


@router.get("/{policy_id}", response_model=PolicyResponse)
async def get_policy(
    policy_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    result = await db.execute(
        select(Policy).where(
            Policy.id == policy_id,
            Policy.org_id == current_user.org_id,
        )
    )
    policy = result.scalar_one_or_none()
    if not policy:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Policy not found")
    return policy


@router.post("/", response_model=PolicyResponse, status_code=status.HTTP_201_CREATED)
async def create_policy(
    body: PolicyCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    title = body.title.strip()
    if not title:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Policy title is required.")

    now = datetime.now()
    policy = Policy(
        id=await _next_policy_id(db, current_user.org_id),
        org_id=current_user.org_id,
        title=title,
        category=body.category.strip(),
        content=body.content.strip(),
        status="draft",
        version=1,
        review_interval_months=body.review_interval_months,
        next_review=_calc_next_review(now, body.review_interval_months),
        created_at=now,
        updated_at=now,
    )
    db.add(policy)
    await _create_audit_log(
        db,
        current_user,
        request,
        resource_type="policy",
        resource_id=policy.id,
        action="created",
        changes={"title": policy.title, "category": policy.category},
    )
    await db.commit()
    await db.refresh(policy)
    return policy


@router.put("/{policy_id}", response_model=PolicyResponse)
async def update_policy(
    policy_id: str,
    body: PolicyUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    result = await db.execute(
        select(Policy).where(
            Policy.id == policy_id,
            Policy.org_id == current_user.org_id,
        )
    )
    policy = result.scalar_one_or_none()
    if not policy:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Policy not found")

    changes: dict = {}
    if body.title is not None:
        policy.title = body.title.strip()
        changes["title"] = policy.title
    if body.category is not None:
        policy.category = body.category.strip()
        changes["category"] = policy.category
    if body.content is not None:
        policy.content = body.content.strip()
        changes["content"] = True
    if body.review_interval_months is not None:
        policy.review_interval_months = body.review_interval_months
        policy.next_review = _calc_next_review(datetime.now(), body.review_interval_months)
        changes["review_interval_months"] = body.review_interval_months

    policy.version += 1

    await _create_audit_log(
        db,
        current_user,
        request,
        resource_type="policy",
        resource_id=policy.id,
        action="updated",
        changes=changes,
    )
    await db.commit()
    await db.refresh(policy)
    return policy


@router.delete("/{policy_id}")
async def delete_policy(
    policy_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    result = await db.execute(
        select(Policy).where(
            Policy.id == policy_id,
            Policy.org_id == current_user.org_id,
        )
    )
    policy = result.scalar_one_or_none()
    if not policy:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Policy not found")

    await _create_audit_log(
        db,
        current_user,
        request,
        resource_type="policy",
        resource_id=policy.id,
        action="deleted",
    )
    await db.delete(policy)
    await db.commit()
    return {"deleted": policy_id}
