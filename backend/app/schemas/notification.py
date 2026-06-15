from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class NotificationBase(BaseModel):
    type: str
    title: str
    message: Optional[str] = None
    link: Optional[str] = None
    priority: str = "normal"


class NotificationCreate(NotificationBase):
    user_id: Optional[str] = None


class NotificationUpdate(BaseModel):
    is_read: Optional[bool] = None


class NotificationResponse(NotificationBase):
    id: str
    org_id: str
    user_id: Optional[str]
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True
