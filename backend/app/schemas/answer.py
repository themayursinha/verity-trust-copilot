from datetime import datetime

from pydantic import BaseModel


class AnswerGenerateRequest(BaseModel):
    questions: list[str]
    as_of: str | None = None
    questionnaire_id: str | None = None
    use_llm: bool = True


class AnswerResponse(BaseModel):
    id: str
    generation_id: str
    question: str
    answer_text: str
    confidence: str | None
    confidence_score: float | None = None
    confidence_rationale: str | None
    needs_human_review: bool
    citations: list
    freshness: list
    assignee_id: str | None = None
    order_index: int = 0
    source: str = "ai"
    created_at: datetime

    model_config = {"from_attributes": True}


class AnswerGenerationResponse(BaseModel):
    id: str
    org_id: str
    as_of_date: str | None
    confidence_counts: dict
    answers: list[AnswerResponse]
    questionnaire_id: str | None = None
    original_filename: str | None = None
    original_format: str | None = None
    engine_used: str = "ai"
    created_at: datetime

    model_config = {"from_attributes": True}


class AnswerAssignmentRequest(BaseModel):
    answer_id: str
    assignee_id: str


class AnswerBulkAssignmentRequest(BaseModel):
    answer_ids: list[str]
    assignee_id: str


class ApprovalCreate(BaseModel):
    status: str
    notes: str = ""


class ExportRequest(BaseModel):
    format: str = "markdown"


class QuestionnaireCreate(BaseModel):
    name: str
    questions: list[str]
    original_filename: str | None = None
    original_format: str | None = None
    original_content: str | None = None


class QuestionnaireResponse(BaseModel):
    id: str
    org_id: str
    name: str
    original_filename: str | None
    original_format: str | None
    question_count: int
    answered_count: int
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class LearnFromApprovalRequest(BaseModel):
    answer_ids: list[str]
