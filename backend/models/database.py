"""SQLAlchemy ORM models for CONOPS One Source."""

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""
    pass


# --- Enums ---

class SourceType(str, enum.Enum):
    network_share = "network_share"
    sharepoint = "sharepoint"
    web_page = "web_page"


class SourceStatus(str, enum.Enum):
    active = "active"
    inactive = "inactive"
    error = "error"


class ConnectivityStatus(str, enum.Enum):
    connected = "connected"
    disconnected = "disconnected"
    unknown = "unknown"


class DataCategory(str, enum.Enum):
    operational = "operational"
    sustainment = "sustainment"


class ImpactType(str, enum.Enum):
    positive = "positive"
    negative = "negative"
    neutral = "neutral"


class AuditEventType(str, enum.Enum):
    impact_assessment = "impact_assessment"
    qa_interaction = "qa_interaction"
    ingestion = "ingestion"
    conops_generation = "conops_generation"


class OperationalStatus(str, enum.Enum):
    operational = "operational"
    degraded = "degraded"
    non_operational = "non_operational"


class IngestionStatus(str, enum.Enum):
    success = "success"
    failure = "failure"
    partial = "partial"


class UserRole(str, enum.Enum):
    admin = "admin"
    standard = "standard"


# --- ORM Models ---

class DataSourceConfig(Base):
    __tablename__ = "data_source_configs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    source_type: Mapped[SourceType] = mapped_column(Enum(SourceType), nullable=False)
    connection_uri: Mapped[str] = mapped_column(Text, nullable=False)
    credentials: Mapped[str] = mapped_column(Text, nullable=False, comment="Encrypted credentials")
    schedule: Mapped[str | None] = mapped_column(String(100), nullable=True, comment="Cron expression or null")
    status: Mapped[SourceStatus] = mapped_column(Enum(SourceStatus), nullable=False, default=SourceStatus.inactive)
    last_successful_ingestion: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    connectivity_status: Mapped[ConnectivityStatus] = mapped_column(
        Enum(ConnectivityStatus), nullable=False, default=ConnectivityStatus.unknown
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    normalized_records: Mapped[list["NormalizedRecord"]] = relationship(back_populates="source", cascade="all, delete-orphan")
    ingestion_events: Mapped[list["IngestionEvent"]] = relationship(back_populates="source", cascade="all, delete-orphan")


class NormalizedRecord(Base):
    __tablename__ = "normalized_records"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("data_source_configs.id"), nullable=False)
    source_type: Mapped[SourceType] = mapped_column(Enum(SourceType), nullable=False)
    ingestion_timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    source_identifier: Mapped[str] = mapped_column(String(500), nullable=False)
    data_category: Mapped[DataCategory] = mapped_column(Enum(DataCategory), nullable=False)
    content: Mapped[dict] = mapped_column(JSON, nullable=False)
    metadata_: Mapped[dict] = mapped_column("metadata", JSON, nullable=False, default=dict)

    # Relationships
    source: Mapped["DataSourceConfig"] = relationship(back_populates="normalized_records")


class CONOPSDocument(Base):
    __tablename__ = "conops_documents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    last_updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    sections: Mapped[dict] = mapped_column(JSON, nullable=False, comment="Dict of section_key -> SectionContent")
    incomplete_sections: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    source_data_refs: Mapped[list] = mapped_column(JSON, nullable=False, default=list, comment="List of NormalizedRecord UUIDs")


class ImpactAssessment(Base):
    __tablename__ = "impact_assessments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    proposal_id: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    input_parameters: Mapped[dict] = mapped_column(JSON, nullable=False, comment="Serialized ChangeProposal")
    affected_assets: Mapped[list] = mapped_column(JSON, nullable=False, default=list, comment="List of AffectedAsset dicts")
    cascading_effects: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    resource_recommendations: Mapped[list] = mapped_column(JSON, nullable=False, default=list, comment="List of ResourceRecommendation dicts")
    has_high_risk_warning: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    conops_version_used: Mapped[int] = mapped_column(Integer, nullable=False)


class ChangeProposal(Base):
    __tablename__ = "change_proposals"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    target_assets: Mapped[list] = mapped_column(JSON, nullable=False, default=list, comment="List of asset ID strings")
    proposed_changes: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    submitted_by: Mapped[str] = mapped_column(String(255), nullable=False)
    submitted_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_type: Mapped[AuditEventType] = mapped_column(Enum(AuditEventType), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    user_id: Mapped[str] = mapped_column(String(255), nullable=False)
    details: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    related_entity_id: Mapped[str] = mapped_column(String(255), nullable=False)
    conops_version: Mapped[int | None] = mapped_column(Integer, nullable=True)


class QAInteraction(Base):
    __tablename__ = "qa_interactions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[str] = mapped_column(String(255), nullable=False)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    cited_sections: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    cited_source_data: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    conops_version_used: Mapped[int] = mapped_column(Integer, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    response_time_ms: Mapped[int] = mapped_column(Integer, nullable=False)


class AssetStatus(Base):
    __tablename__ = "asset_statuses"

    asset_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, primary_key=True)
    asset_name: Mapped[str] = mapped_column(String(255), nullable=False)
    readiness_score: Mapped[float] = mapped_column(Float, nullable=False)
    operational_status: Mapped[OperationalStatus] = mapped_column(Enum(OperationalStatus), nullable=False)
    maintenance_status: Mapped[str] = mapped_column(String(255), nullable=False)
    last_known_location: Mapped[str | None] = mapped_column(String(500), nullable=True)
    sustainment_data: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)


class IngestionEvent(Base):
    __tablename__ = "ingestion_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("data_source_configs.id"), nullable=False)
    source_name: Mapped[str] = mapped_column(String(255), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    record_count: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[IngestionStatus] = mapped_column(Enum(IngestionStatus), nullable=False)
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    source: Mapped["DataSourceConfig"] = relationship(back_populates="ingestion_events")


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), nullable=False, default=UserRole.standard)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Relationships
    sessions: Mapped[list["Session"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    token: Mapped[str] = mapped_column(String(500), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    is_valid: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="sessions")
