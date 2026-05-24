from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class MemberResponse(BaseModel):
    id: str
    email: str
    display_name: str
    role: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class MemberUpdate(BaseModel):
    role: Optional[str] = None
    is_active: Optional[bool] = None


class InviteRequest(BaseModel):
    email: str
    role: str = "member"
