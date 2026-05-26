import uuid

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func

from app.database import Base


class Integration(Base):
    __tablename__ = "integrations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    org_id = Column(String(36), ForeignKey("organizations.id"), nullable=False)
    provider = Column(String(50), nullable=False)
    name = Column(String(255), nullable=False)
    enabled = Column(Boolean, default=True)
    config = Column(JSONB, default={})
    last_run_at = Column(DateTime, nullable=True)
    last_status = Column(String(50), default="pending")
    last_error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class ComplianceTest(Base):
    __tablename__ = "compliance_tests"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    org_id = Column(String(36), ForeignKey("organizations.id"), nullable=False)
    integration_id = Column(String(36), ForeignKey("integrations.id"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    frameworks = Column(JSONB, default=[])
    control_ids = Column(JSONB, default=[])
    category = Column(String(100), default="general")
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())


class TestResult(Base):
    __tablename__ = "test_results"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    org_id = Column(String(36), ForeignKey("organizations.id"), nullable=False)
    test_id = Column(String(36), ForeignKey("compliance_tests.id"), nullable=True)
    integration_id = Column(String(36), ForeignKey("integrations.id"), nullable=False)
    status = Column(String(50), default="pending")
    evidence = Column(JSONB, default={})
    message = Column(Text, nullable=True)
    resources_checked = Column(Integer, default=0)
    resources_failed = Column(Integer, default=0)
    created_at = Column(DateTime, default=func.now())
