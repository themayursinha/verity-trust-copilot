import uuid

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.sql import func

from app.database import Base


class Webhook(Base):
    __tablename__ = "webhooks"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    org_id = Column(String(36), primary_key=True)
    url = Column(String(500), nullable=False)
    secret = Column(String(255), nullable=True)
    name = Column(String(255), nullable=False)
    events = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    custom_headers = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class WebhookLog(Base):
    __tablename__ = "webhook_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    webhook_id = Column(String(36), nullable=False)
    org_id = Column(String(36), nullable=False)
    event = Column(String(100), nullable=False)
    payload = Column(Text, nullable=True)
    response_status = Column(Integer, nullable=True)
    response_body = Column(Text, nullable=True)
    success = Column(Boolean, default=False)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now())