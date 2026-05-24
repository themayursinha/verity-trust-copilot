from datetime import datetime

from pydantic import BaseModel


class AnswerGenerateRequest(BaseModel):
    questions: list[str]
    as_of: str | None = None


class AnswerResponse(BaseModel):
    id: str
    generation_id: str
    question: str
    answer_text: str
    confidence: str | None
    confidence_rationale: str | None
    needs_human_review: bool
    citations: list
    freshness: dict
    created_at: datetime

    model_config = {"from_attributes": True}


class AnswerGenerationResponse(BaseModel):
    id: str
    org_id: str
    as_of_date: str | None
    confidence_counts: dict
    answers: list[AnswerResponse]
    created_at: datetime

    model_config = {"from_attributes": True}


class ApprovalCreate(BaseModel):
    status: str
    notes: str = ""


class ExportRequest(BaseModel):
    format: str = "markdown"
