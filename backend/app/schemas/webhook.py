import json
from datetime import datetime
from typing import List, Optional, Union

from pydantic import BaseModel, field_validator


class WebhookBase(BaseModel):
    url: str
    name: str
    events: List[str]
    custom_headers: Optional[str] = None


class WebhookCreate(WebhookBase):
    pass


class WebhookUpdate(BaseModel):
    url: Optional[str] = None
    name: Optional[str] = None
    events: Optional[List[str]] = None
    custom_headers: Optional[str] = None
    is_active: Optional[bool] = None


class WebhookResponse(WebhookBase):
    id: str
    org_id: str
    is_active: bool
    secret: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}

    @field_validator("events", mode="before")
    @classmethod
    def parse_events(cls, v: Union[str, List]) -> List[str]:
        if isinstance(v, str):
            return json.loads(v)
        return v


class WebhookLogResponse(BaseModel):
    id: str
    webhook_id: str
    event: str
    payload: Optional[str]
    response_status: Optional[int]
    success: bool
    error: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


WEBHOOK_EVENTS = [
    "answer.approved",
    "answer.rejected",
    "answer.created",
    "evidence.created",
    "evidence.updated",
    "evidence.stale",
    "integration.failed",
    "integration.recovered",
    "policy.review_due",
    "questionnaire.completed",
]
