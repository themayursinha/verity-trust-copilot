import uuid

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.sql import func

from app.database import Base


class Questionnaire(Base):
    __tablename__ = "questionnaires"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    org_id = Column(String(36), ForeignKey("organizations.id"), nullable=False)
    name = Column(String(500), nullable=False)
    original_filename = Column(String(500), nullable=True)
    original_format = Column(String(20), nullable=True)
    original_content = Column(Text, nullable=True)
    question_count = Column(Integer, default=0)
    answered_count = Column(Integer, default=0)
    status = Column(String(50), default="draft")
    created_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
