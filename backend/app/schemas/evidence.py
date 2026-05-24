from datetime import date, datetime

from pydantic import BaseModel


class EvidenceBase(BaseModel):
    title: str
    type: str
    frameworks: list = []
    control_ids: list = []
    last_reviewed: date
    owner: str
    summary: str
    snippets: list = []


class EvidenceCreate(EvidenceBase):
    pass


class EvidenceUpdate(BaseModel):
    title: str | None = None
    type: str | None = None
    frameworks: list | None = None
    control_ids: list | None = None
    last_reviewed: date | None = None
    owner: str | None = None
    summary: str | None = None
    snippets: list | None = None


class EvidenceResponse(EvidenceBase):
    id: str
    org_id: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class EvidenceListResponse(BaseModel):
    items: list[EvidenceResponse]
    total: int
