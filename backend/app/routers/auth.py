from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.organization import Organization
from app.models.user import User
from app.schemas.auth import (
    AuthResponse,
    LoginRequest,
    OrganizationResponse,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from app.services.auth_service import (
    REFRESH_TOKEN_EXPIRE,
    create_access_token,
    create_refresh_token,
    decode_token,
    get_current_user,
    hash_password,
    invalidate_refresh_family,
    store_refresh_token_family,
    verify_password,
)

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


def _build_auth_response(user: User, org: Organization) -> AuthResponse:
    access_token = create_access_token({"sub": user.id, "org_id": org.id, "role": user.role})
    refresh_token, rt_jti = create_refresh_token({"sub": user.id, "org_id": org.id})
    return AuthResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserResponse.model_validate(user),
        organization=OrganizationResponse.model_validate(org),
    )


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(select(User).where(User.email == body.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    org = Organization(name=body.organization_name, slug=body.organization_name.lower().replace(" ", "-"))
    db.add(org)
    await db.flush()

    user = User(
        org_id=org.id,
        email=body.email,
        password_hash=hash_password(body.password),
        display_name=body.display_name,
        role="admin",
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    resp = _build_auth_response(user, org)
    payload = decode_token(resp.refresh_token)
    rt_ttl = int(REFRESH_TOKEN_EXPIRE.total_seconds())
    await store_refresh_token_family(payload["jti"], user.id, rt_ttl)
    return resp


@router.post("/login", response_model=AuthResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    org_result = await db.execute(select(Organization).where(Organization.id == user.org_id))
    org = org_result.scalar_one()

    resp = _build_auth_response(user, org)
    payload = decode_token(resp.refresh_token)
    rt_ttl = int(REFRESH_TOKEN_EXPIRE.total_seconds())
    await store_refresh_token_family(payload["jti"], user.id, rt_ttl)
    return resp


@router.post("/refresh", response_model=TokenResponse)
async def refresh(body: RefreshRequest):
    payload = decode_token(body.refresh_token)
    if payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    user_id = payload.get("sub")
    org_id = payload.get("org_id")
    old_jti = payload.get("jti")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")

    access_token = create_access_token({"sub": user_id, "org_id": org_id})
    new_refresh_token, new_jti = create_refresh_token({"sub": user_id, "org_id": org_id})

    rt_ttl = int(REFRESH_TOKEN_EXPIRE.total_seconds())
    await store_refresh_token_family(new_jti, user_id, rt_ttl)
    if old_jti:
        await invalidate_refresh_family(user_id, old_jti)

    return TokenResponse(access_token=access_token, refresh_token=new_refresh_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(current_user: User = Depends(get_current_user)):
    return None
