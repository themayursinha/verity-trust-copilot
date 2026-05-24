import uuid
from datetime import datetime

from sqlalchemy import Column, Date, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func

from app.database import Base


class EvidenceRecord(Base):
    __tablename__ = "evidence_records"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    org_id = Column(String(36), ForeignKey("organizations.id"), nullable=False)
    title = Column(String(500), nullable=False)
    type = Column(String(255), nullable=False)
    frameworks = Column(JSONB, default=[])
    control_ids = Column(JSONB, default=[])
    last_reviewed = Column(Date, nullable=False)
    owner = Column(String(255), nullable=False)
    summary = Column(Text, nullable=False)
    snippets = Column(JSONB, nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
