from fastapi import Depends, HTTPException, status

from app.models.user import User
from app.services.auth_service import get_current_user


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is deactivated")
    return current_user


async def get_current_org_id(current_user: User = Depends(get_current_user)) -> str:
    return current_user.org_id


def require_role(*roles: str):
    async def role_checker(current_user: User = Depends(get_current_active_user)) -> User:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{current_user.role}' not permitted. Required: {', '.join(roles)}",
            )
        return current_user

    return role_checker


require_admin = require_role("admin")
require_editor = require_role("admin", "editor")
require_viewer = require_role("admin", "editor", "viewer", "member")
