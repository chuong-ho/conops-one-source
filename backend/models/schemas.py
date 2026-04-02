"""Pydantic schemas for CONOPS One Source API validation and serialization."""

import uuid
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator


# --- Enums ---

class SourceTypeEnum(str, Enum):
    network_share = "network_share"
    sharepoint = "sharepoint"
    web_page = "web_page"


class SourceStatusEnum(str, Enum):
    active = "active"
    inactive = "inactive"
    error = "error"


class ConnectivityStatusEnum(str, Enum):
    connected = "connected"
    disconnected = "disconnected"
    unknown = "unknown"


class DataCategoryEnum(str, Enum):
    operational = "operational"
    sustainment = "sustainment"


class ImpactTypeEnum(str, Enum):
    positive = "positive"
    negative = "negative"
    neutral = "neutral"


class AuditEventTypeEnum(str, Enum):
    impact_assessment = "impact_assessment"
    qa_interaction = "qa_interaction"
    ingestion = "ingestion"
    conops_generation = "conops_generation"


class OperationalStatusEnum(str, Enum):
    operational = "operational"
    degraded = "degraded"
    non_operational = "non_operational"


class IngestionStatusEnum(str, Enum):
    success = "success"
    failure = "failure"
    partial = "partial"


class UserRoleEnum(str, Enum):
    admin = "admin"
    standard = "standard"


# --- DataSourceConfig Schemas ---

class DataSourceConfigBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    source_type: SourceTypeEnum
    connection_uri: str = Field(..., min_length=1)
    credentials: str = Field(..., min_length=1)
    schedule: str | None = Field(None, max_length=100)


class DataSourceConfigCreate(DataSourceConfigBase):
    pass


class DataSourceConfigUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    source_type: SourceTypeEnum | None = None
    connection_uri: str | None = Field(None, min_length=1)
    credentials: str | None = Field(None, min_length=1)
    schedule: str | None = Field(None, max_length=100)
    status: SourceStatusEnum | None = None


class DataSourceConfigResponse(DataSourceConfigBase):
    id: uuid.UUID
    status: SourceStatusEnum
    last_successful_ingestion: datetime | None = None
    connectivity_status: ConnectivityStatusEnum
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# --- NormalizedRecord Schemas ---

class NormalizedRecordBase(BaseModel):
    source_type: SourceTypeEnum
    source_identifier: str = Field(..., min_length=1, max_length=500)
    data_category: DataCategoryEnum
    content: dict[str, Any]
    metadata: dict[str, Any] = Field(default_factory=dict)


class NormalizedRecordCreate(NormalizedRecordBase):
    source_id: uuid.UUID
    ingestion_timestamp: datetime


class NormalizedRecordResponse(NormalizedRecordBase):
    id: uuid.UUID
    source_id: uuid.UUID
    ingestion_timestamp: datetime

    model_config = {"from_attributes": True}


# --- SectionContent Schema (embedded, not a DB table) ---

class SectionContent(BaseModel):
    title: str
    body: str
    data_complete: bool
    missing_sources: list[str] = Field(default_factory=list)


# --- CONOPSDocument Schemas ---

class CONOPSDocumentBase(BaseModel):
    sections: dict[str, SectionContent]
    incomplete_sections: list[dict[str, Any]] = Field(default_factory=list)
    source_data_refs: list[str] = Field(default_factory=list)


class CONOPSDocumentCreate(CONOPSDocumentBase):
    version: int = Field(..., ge=1)


class CONOPSDocumentResponse(CONOPSDocumentBase):
    id: uuid.UUID
    version: int
    created_at: datetime
    last_updated_at: datetime

    model_config = {"from_attributes": True}


# --- AffectedAsset Schema (embedded in ImpactAssessment) ---

class AffectedAsset(BaseModel):
    asset_id: str
    asset_name: str
    impact_type: ImpactTypeEnum
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    mitigation_actions: list[str] = Field(default_factory=list)
    readiness_score_delta: float

    @model_validator(mode="after")
    def validate_mitigation_actions(self) -> "AffectedAsset":
        if self.impact_type == ImpactTypeEnum.negative and not self.mitigation_actions:
            raise ValueError("mitigation_actions required for negative impact")
        if self.impact_type != ImpactTypeEnum.negative and self.mitigation_actions:
            raise ValueError("mitigation_actions only allowed for negative impact")
        return self


# --- ResourceRecommendation Schema ---

class ResourceRecommendation(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    rank: int = Field(..., ge=1, le=3)
    description: str
    predicted_effectiveness: float = Field(..., ge=0.0, le=1.0)
    tradeoffs: list[dict[str, Any]] = Field(default_factory=list)
    affected_asset_readiness_scores: dict[str, float] = Field(default_factory=dict)


# --- ChangeProposal Schemas ---

class ChangeProposalBase(BaseModel):
    description: str = Field(..., min_length=1)
    target_assets: list[str] = Field(..., min_length=1)
    proposed_changes: list[dict[str, Any]] = Field(default_factory=list)
    submitted_by: str = Field(..., min_length=1, max_length=255)


class ChangeProposalCreate(ChangeProposalBase):
    pass


class ChangeProposalResponse(ChangeProposalBase):
    id: uuid.UUID
    submitted_at: datetime

    model_config = {"from_attributes": True}


# --- ImpactAssessment Schemas ---

class ImpactAssessmentBase(BaseModel):
    proposal_id: str
    affected_assets: list[AffectedAsset] = Field(default_factory=list)
    cascading_effects: list[dict[str, Any]] = Field(default_factory=list)
    resource_recommendations: list[ResourceRecommendation] = Field(default_factory=list)
    has_high_risk_warning: bool = False
    conops_version_used: int


class ImpactAssessmentCreate(ImpactAssessmentBase):
    input_parameters: dict[str, Any]


class ImpactAssessmentResponse(ImpactAssessmentBase):
    id: uuid.UUID
    created_at: datetime
    input_parameters: dict[str, Any]

    model_config = {"from_attributes": True}


# --- AuditEvent Schemas ---

class AuditEventBase(BaseModel):
    event_type: AuditEventTypeEnum
    user_id: str
    details: dict[str, Any] = Field(default_factory=dict)
    related_entity_id: str
    conops_version: int | None = None


class AuditEventCreate(AuditEventBase):
    pass


class AuditEventResponse(AuditEventBase):
    id: uuid.UUID
    timestamp: datetime

    model_config = {"from_attributes": True}


# --- QAInteraction Schemas ---

class QAInteractionBase(BaseModel):
    session_id: str
    question: str = Field(..., min_length=1)
    answer: str
    cited_sections: list[str] = Field(default_factory=list)
    cited_source_data: list[str] = Field(default_factory=list)
    conops_version_used: int
    response_time_ms: int = Field(..., ge=0)


class QAInteractionCreate(QAInteractionBase):
    pass


class QAInteractionResponse(QAInteractionBase):
    id: uuid.UUID
    timestamp: datetime

    model_config = {"from_attributes": True}


# --- AssetStatus Schemas ---

class AssetStatusBase(BaseModel):
    asset_id: str
    asset_name: str
    readiness_score: float = Field(..., ge=0.0, le=1.0)
    operational_status: OperationalStatusEnum
    maintenance_status: str
    last_known_location: str | None = None
    sustainment_data: dict[str, Any] = Field(default_factory=dict)


class AssetStatusCreate(AssetStatusBase):
    timestamp: datetime


class AssetStatusResponse(AssetStatusBase):
    timestamp: datetime

    model_config = {"from_attributes": True}


# --- IngestionEvent Schemas ---

class IngestionEventBase(BaseModel):
    source_name: str = Field(..., min_length=1, max_length=255)
    record_count: int = Field(..., ge=0)
    status: IngestionStatusEnum
    retry_count: int = Field(default=0, ge=0)
    error_message: str | None = None


class IngestionEventCreate(IngestionEventBase):
    source_id: uuid.UUID


class IngestionEventResponse(IngestionEventBase):
    id: uuid.UUID
    source_id: uuid.UUID
    timestamp: datetime

    model_config = {"from_attributes": True}


# --- User Schemas ---

class UserBase(BaseModel):
    username: str = Field(..., min_length=1, max_length=255)
    role: UserRoleEnum = UserRoleEnum.standard


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)


class UserResponse(UserBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    last_login_at: datetime | None = None
    is_active: bool

    model_config = {"from_attributes": True}


class UserListEntry(BaseModel):
    id: uuid.UUID
    username: str
    role: UserRoleEnum
    last_login_at: datetime | None = None
    is_active: bool

    model_config = {"from_attributes": True}


# --- Session Schemas ---

class SessionBase(BaseModel):
    expires_at: datetime


class SessionCreate(SessionBase):
    user_id: uuid.UUID
    token: str


class SessionResponse(SessionBase):
    id: uuid.UUID
    user_id: uuid.UUID
    token: str
    created_at: datetime
    is_valid: bool

    model_config = {"from_attributes": True}


# --- Auth Schemas ---

class AuthRequest(BaseModel):
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)


class AuthResult(BaseModel):
    token: str
    user: UserResponse
    expires_at: datetime


class PasswordChangeRequest(BaseModel):
    new_password: str = Field(..., min_length=8)
