import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func

from app.database import Base


class AnswerGeneration(Base):
    __tablename__ = "answer_generations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    org_id = Column(String(36), ForeignKey("organizations.id"), nullable=False)
    as_of_date = Column(Date, nullable=True)
    confidence_counts = Column(JSONB, default={"high": 0, "medium": 0, "low": 0})
    created_at = Column(DateTime, default=func.now())


class Answer(Base):
    __tablename__ = "answers"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    generation_id = Column(String(36), ForeignKey("answer_generations.id"), nullable=False)
    question = Column(Text, nullable=False)
    answer_text = Column(Text, nullable=False)
    confidence = Column(String(50), nullable=True)
    confidence_rationale = Column(Text, nullable=True)
    needs_human_review = Column(Boolean, default=False)
    citations = Column(JSONB, default=[])
    freshness = Column(JSONB, default=[])
    created_at = Column(DateTime, default=func.now())


class Approval(Base):
    __tablename__ = "approvals"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    answer_id = Column(String(36), ForeignKey("answers.id"), nullable=False)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    status = Column(String(50), default="unreviewed")
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now())
