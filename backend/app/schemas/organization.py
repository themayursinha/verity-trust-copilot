from datetime import datetime

from pydantic import BaseModel


class OrganizationResponse(BaseModel):
    id: str
    name: str
    slug: str
    max_seats: int
    license_key: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class MemberResponse(BaseModel):
    id: str
    email: str
    display_name: str
    role: str
    is_active: bool

    model_config = {"from_attributes": True}


class InviteMemberRequest(BaseModel):
    email: str
    role: str = "member"
