from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.dependencies import require_admin, get_current_active_user
from app.models.organization import Organization
from app.models.user import User
from app.schemas.org import InviteRequest, MemberResponse, MemberUpdate
from app.services.auth_service import hash_password

router = APIRouter(prefix="/api/v1/org", tags=["organization"])


@router.get("/members", response_model=list[MemberResponse])
async def list_members(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    result = await db.execute(select(User).where(User.org_id == current_user.org_id).order_by(User.created_at))
    return result.scalars().all()


@router.post("/members/invite", response_model=MemberResponse, status_code=status.HTTP_201_CREATED)
async def invite_member(
    body: InviteRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    existing = await db.execute(select(User).where(User.email == body.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    active_count = await db.scalar(
        select(func.count(User.id)).where(User.org_id == current_user.org_id, User.is_active == True)
    )

    org_result = await db.execute(select(Organization).where(Organization.id == current_user.org_id))
    org = org_result.scalar_one()
    if active_count >= org.max_seats:
        raise HTTPException(status_code=status.HTTP_402_PAYMENT_REQUIRED, detail="Seat limit reached")

    temp_password = "changeme-" + body.email.split("@")[0]
    user = User(
        org_id=current_user.org_id,
        email=body.email,
        password_hash=hash_password(temp_password),
        display_name=body.email.split("@")[0],
        role=body.role,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@router.put("/members/{user_id}", response_model=MemberResponse)
async def update_member(
    user_id: str,
    body: MemberUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    result = await db.execute(select(User).where(User.id == user_id, User.org_id == current_user.org_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")

    if body.role is not None:
        user.role = body.role
    if body.is_active is not None:
        user.is_active = body.is_active

    await db.commit()
    await db.refresh(user)
    return user


@router.delete("/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_member(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    result = await db.execute(select(User).where(User.id == user_id, User.org_id == current_user.org_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")

    if user.id == current_user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot remove yourself")

    await db.delete(user)
    await db.commit()
    return None


class LicenseActivateRequest(BaseModel):
    license_key: str


class BrandingUpdate(BaseModel):
    brand_color: str | None = None
    logo_url: str | None = None


@router.put("/branding")
async def update_branding(
    body: BrandingUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    result = await db.execute(
        select(Organization).where(Organization.id == current_user.org_id)
    )
    org = result.scalar_one()

    if body.brand_color is not None:
        if not body.brand_color.startswith("#") or len(body.brand_color) not in (4, 7):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="brand_color must be a hex color like #0f766e"
            )
        org.brand_color = body.brand_color

    if body.logo_url is not None:
        org.logo_url = body.logo_url if body.logo_url else None

    await db.commit()

    return {
        "brand_color": org.brand_color,
        "logo_url": org.logo_url,
    }


@router.get("/license")
async def license_status(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    org_result = await db.execute(
        select(Organization).where(Organization.id == current_user.org_id)
    )
    org = org_result.scalar_one()

    if not org.license_key:
        return {
            "status": "free",
            "max_seats": settings.LICENSE_FREE_SEATS,
            "message": "Free tier — upgrade for more seats",
        }

    from app.services.license_service import validate_license
    license_info = validate_license(org.license_key)

    return {
        "status": "valid" if license_info.valid else "invalid",
        "max_seats": license_info.max_seats,
        "org_name": license_info.org_name,
        "customer_email": license_info.customer_email,
        "expires_at": license_info.expires_at,
        "reason": license_info.reason,
        "valid": license_info.valid,
    }


@router.post("/license/activate")
async def activate_license(
    body: LicenseActivateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    from app.services.license_service import validate_license
    license_info = validate_license(body.license_key)

    if not license_info.valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid license: {license_info.reason}",
        )

    org_result = await db.execute(
        select(Organization).where(Organization.id == current_user.org_id)
    )
    org = org_result.scalar_one()
    org.license_key = body.license_key
    org.max_seats = license_info.max_seats
    await db.commit()

    return {
        "status": "activated",
        "max_seats": license_info.max_seats,
        "org_name": license_info.org_name,
    }


@router.get("/me", response_model=dict)
async def org_info(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    org_result = await db.execute(select(Organization).where(Organization.id == current_user.org_id))
    org = org_result.scalar_one()
    active_count = await db.scalar(
        select(func.count(User.id)).where(User.org_id == current_user.org_id, User.is_active == True)
    )
    return {
        "id": org.id,
        "name": org.name,
        "slug": org.slug,
        "brand_color": org.brand_color,
        "logo_url": org.logo_url,
        "max_seats": org.max_seats,
        "seats_used": active_count,
        "license_key": org.license_key,
        "created_at": org.created_at.isoformat() if org.created_at else None,
    }
