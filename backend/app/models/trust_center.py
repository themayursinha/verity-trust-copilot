import uuid

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.sql import func

from app.database import Base


class TrustCenterSettings(Base):
    __tablename__ = "trust_center_settings"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    org_id = Column(String(36), ForeignKey("organizations.id"), nullable=False, unique=True)
    enabled = Column(Boolean, default=False)
    custom_domain = Column(String(255), nullable=True)
    page_title = Column(String(255), default="Trust Center")
    hero_headline = Column(String(500), default="Your Trust, Our Priority")
    hero_subtext = Column(Text, nullable=True)
    brand_color = Column(String(7), default="#0f766e")
    logo_url = Column(String(500), nullable=True)
    favicon_url = Column(String(500), nullable=True)
    show_certifications = Column(Boolean, default=True)
    show_controls = Column(Boolean, default=True)
    show_policies = Column(Boolean, default=True)
    show_ai_chatbot = Column(Boolean, default=True)
    show_subscribe = Column(Boolean, default=True)
    show_document_requests = Column(Boolean, default=True)
    require_nda = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class TrustCenterVisit(Base):
    __tablename__ = "trust_center_visits"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    org_id = Column(String(36), ForeignKey("organizations.id"), nullable=False)
    visitor_ip = Column(String(45), nullable=True)
    page_viewed = Column(String(255), nullable=True)
    referrer = Column(String(500), nullable=True)
    user_agent = Column(String(500), nullable=True)
    chatbot_queries = Column(Integer, default=0)
    document_downloads = Column(Integer, default=0)
    created_at = Column(DateTime, default=func.now())


class TrustCenterSubscriber(Base):
    __tablename__ = "trust_center_subscribers"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    org_id = Column(String(36), ForeignKey("organizations.id"), nullable=False)
    email = Column(String(255), nullable=False)
    name = Column(String(255), nullable=True)
    company = Column(String(255), nullable=True)
    subscribed = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())


class TrustCenterDocument(Base):
    __tablename__ = "trust_center_documents"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    org_id = Column(String(36), ForeignKey("organizations.id"), nullable=False)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    document_type = Column(String(50), default="report")
    file_url = Column(String(1000), nullable=True)
    requires_nda = Column(Boolean, default=False)
    is_public = Column(Boolean, default=False)
    download_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class TrustCenterAccessRequest(Base):
    __tablename__ = "trust_center_access_requests"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    org_id = Column(String(36), ForeignKey("organizations.id"), nullable=False)
    document_id = Column(String(36), ForeignKey("trust_center_documents.id"), nullable=True)
    requester_email = Column(String(255), nullable=False)
    requester_name = Column(String(255), nullable=True)
    requester_company = Column(String(255), nullable=True)
    nda_accepted = Column(Boolean, default=False)
    status = Column(String(50), default="pending")
    approved_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
