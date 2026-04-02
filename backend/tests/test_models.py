"""Unit tests for SQLAlchemy ORM models and Pydantic schemas."""

import uuid
from datetime import datetime, timedelta

import pytest

from backend.models.database import (
    AssetStatus,
    AuditEvent,
    AuditEventType,
    Base,
    ChangeProposal,
    CONOPSDocument,
    ConnectivityStatus,
    DataCategory,
    DataSourceConfig,
    ImpactAssessment,
    ImpactType,
    IngestionEvent,
    IngestionStatus,
    NormalizedRecord,
    OperationalStatus,
    QAInteraction,
    Session,
    SourceStatus,
    SourceType,
    User,
    UserRole,
)
from backend.models.schemas import (
    AffectedAsset,
    AssetStatusCreate,
    AssetStatusResponse,
    AuditEventCreate,
    AuthRequest,
    ChangeProposalCreate,
    ChangeProposalResponse,
    CONOPSDocumentCreate,
    DataSourceConfigCreate,
    DataSourceConfigResponse,
    DataSourceConfigUpdate,
    ImpactAssessmentCreate,
    ImpactTypeEnum,
    IngestionEventCreate,
    NormalizedRecordCreate,
    PasswordChangeRequest,
    QAInteractionCreate,
    ResourceRecommendation,
    SectionContent,
    SessionCreate,
    SourceTypeEnum,
    UserCreate,
    UserResponse,
)


# --- SQLAlchemy ORM Model Tests ---

class TestSQLAlchemyModels:
    """Verify all ORM models can be instantiated with valid data."""

    def test_data_source_config_creation(self):
        ds = DataSourceConfig(
            name="Test Source",
            source_type=SourceType.network_share,
            connection_uri="smb://server/share",
            credentials="encrypted_creds",
        )
        assert ds.name == "Test Source"
        assert ds.source_type == SourceType.network_share
        assert ds.status == SourceStatus.inactive
        assert ds.connectivity_status == ConnectivityStatus.unknown

    def test_normalized_record_creation(self):
        rec = NormalizedRecord(
            source_id=uuid.uuid4(),
            source_type=SourceType.sharepoint,
            ingestion_timestamp=datetime.utcnow(),
            source_identifier="doc-123",
            data_category=DataCategory.operational,
            content={"key": "value"},
            metadata_={"tag": "test"},
        )
        assert rec.source_type == SourceType.sharepoint
        assert rec.data_category == DataCategory.operational

    def test_conops_document_creation(self):
        doc = CONOPSDocument(
            version=1,
            sections={
                "missionOverview": {"title": "Mission", "body": "...", "dataComplete": True, "missingSources": []},
            },
            incomplete_sections=[],
            source_data_refs=[],
        )
        assert doc.version == 1

    def test_impact_assessment_creation(self):
        ia = ImpactAssessment(
            proposal_id="prop-1",
            input_parameters={"desc": "test"},
            affected_assets=[],
            cascading_effects=[],
            resource_recommendations=[],
            has_high_risk_warning=False,
            conops_version_used=1,
        )
        assert ia.has_high_risk_warning is False

    def test_change_proposal_creation(self):
        cp = ChangeProposal(
            description="Relocate asset",
            target_assets=["asset-1"],
            proposed_changes=[{"type": "relocate"}],
            submitted_by="user-1",
        )
        assert cp.description == "Relocate asset"

    def test_audit_event_creation(self):
        ae = AuditEvent(
            event_type=AuditEventType.impact_assessment,
            user_id="user-1",
            details={"action": "analyze"},
            related_entity_id="ia-1",
            conops_version=2,
        )
        assert ae.event_type == AuditEventType.impact_assessment

    def test_qa_interaction_creation(self):
        qa = QAInteraction(
            session_id="sess-1",
            question="What is the mission?",
            answer="The mission is...",
            cited_sections=["missionOverview"],
            cited_source_data=["src-1"],
            conops_version_used=1,
            response_time_ms=250,
        )
        assert qa.response_time_ms == 250

    def test_asset_status_creation(self):
        a = AssetStatus(
            asset_id="asset-1",
            asset_name="USS Test",
            timestamp=datetime.utcnow(),
            readiness_score=0.85,
            operational_status=OperationalStatus.operational,
            maintenance_status="nominal",
            sustainment_data={},
        )
        assert a.readiness_score == 0.85

    def test_ingestion_event_creation(self):
        ie = IngestionEvent(
            source_id=uuid.uuid4(),
            source_name="Test Source",
            record_count=42,
            status=IngestionStatus.success,
            retry_count=0,
        )
        assert ie.record_count == 42

    def test_user_creation(self):
        u = User(
            username="admin",
            password_hash="hashed_pw",
            role=UserRole.admin,
            is_active=True,
        )
        assert u.role == UserRole.admin

    def test_session_creation(self):
        s = Session(
            user_id=uuid.uuid4(),
            token="opaque-token-abc",
            expires_at=datetime.utcnow() + timedelta(hours=1),
            is_valid=True,
        )
        assert s.is_valid is True

    def test_all_tables_registered(self):
        table_names = set(Base.metadata.tables.keys())
        expected = {
            "data_source_configs",
            "normalized_records",
            "conops_documents",
            "impact_assessments",
            "change_proposals",
            "audit_events",
            "qa_interactions",
            "asset_statuses",
            "ingestion_events",
            "users",
            "sessions",
        }
        assert expected.issubset(table_names)


# --- Pydantic Schema Tests ---

class TestPydanticSchemas:
    """Verify Pydantic schemas validate correctly."""

    def test_data_source_config_create_valid(self):
        schema = DataSourceConfigCreate(
            name="My Source",
            source_type=SourceTypeEnum.network_share,
            connection_uri="smb://server/share",
            credentials="encrypted",
        )
        assert schema.name == "My Source"

    def test_data_source_config_create_missing_name(self):
        with pytest.raises(Exception):
            DataSourceConfigCreate(
                name="",
                source_type=SourceTypeEnum.network_share,
                connection_uri="smb://server/share",
                credentials="encrypted",
            )

    def test_data_source_config_update_partial(self):
        schema = DataSourceConfigUpdate(name="Updated Name")
        assert schema.name == "Updated Name"
        assert schema.source_type is None

    def test_normalized_record_create_valid(self):
        schema = NormalizedRecordCreate(
            source_id=uuid.uuid4(),
            source_type=SourceTypeEnum.sharepoint,
            ingestion_timestamp=datetime.utcnow(),
            source_identifier="doc-1",
            data_category="operational",
            content={"data": "value"},
        )
        assert schema.source_identifier == "doc-1"

    def test_section_content_valid(self):
        sc = SectionContent(
            title="Mission Overview",
            body="Content here",
            data_complete=True,
            missing_sources=[],
        )
        assert sc.data_complete is True

    def test_conops_document_create_valid(self):
        sections = {
            "missionOverview": SectionContent(title="Mission", body="...", data_complete=True),
        }
        schema = CONOPSDocumentCreate(version=1, sections=sections)
        assert schema.version == 1

    def test_affected_asset_negative_requires_mitigation(self):
        with pytest.raises(Exception):
            AffectedAsset(
                asset_id="a1",
                asset_name="Asset 1",
                impact_type=ImpactTypeEnum.negative,
                confidence_score=0.8,
                mitigation_actions=[],
                readiness_score_delta=-0.1,
            )

    def test_affected_asset_positive_no_mitigation(self):
        asset = AffectedAsset(
            asset_id="a1",
            asset_name="Asset 1",
            impact_type=ImpactTypeEnum.positive,
            confidence_score=0.9,
            mitigation_actions=[],
            readiness_score_delta=0.1,
        )
        assert asset.impact_type == ImpactTypeEnum.positive

    def test_affected_asset_negative_with_mitigation(self):
        asset = AffectedAsset(
            asset_id="a1",
            asset_name="Asset 1",
            impact_type=ImpactTypeEnum.negative,
            confidence_score=0.7,
            mitigation_actions=["Increase maintenance"],
            readiness_score_delta=-0.2,
        )
        assert len(asset.mitigation_actions) == 1

    def test_affected_asset_positive_rejects_mitigation(self):
        with pytest.raises(Exception):
            AffectedAsset(
                asset_id="a1",
                asset_name="Asset 1",
                impact_type=ImpactTypeEnum.positive,
                confidence_score=0.9,
                mitigation_actions=["Should not be here"],
                readiness_score_delta=0.1,
            )

    def test_affected_asset_confidence_score_bounds(self):
        with pytest.raises(Exception):
            AffectedAsset(
                asset_id="a1",
                asset_name="Asset 1",
                impact_type=ImpactTypeEnum.neutral,
                confidence_score=1.5,
                readiness_score_delta=0.0,
            )

    def test_resource_recommendation_valid(self):
        rec = ResourceRecommendation(
            rank=1,
            description="Reallocate resources",
            predicted_effectiveness=0.85,
            tradeoffs=[{"desc": "Reduced capacity elsewhere"}],
            affected_asset_readiness_scores={"a1": 0.9},
        )
        assert rec.rank == 1

    def test_resource_recommendation_rank_bounds(self):
        with pytest.raises(Exception):
            ResourceRecommendation(
                rank=4,
                description="Invalid rank",
                predicted_effectiveness=0.5,
            )

    def test_change_proposal_create_valid(self):
        schema = ChangeProposalCreate(
            description="Move asset",
            target_assets=["asset-1"],
            proposed_changes=[{"type": "relocate"}],
            submitted_by="user-1",
        )
        assert len(schema.target_assets) == 1

    def test_change_proposal_requires_target_assets(self):
        with pytest.raises(Exception):
            ChangeProposalCreate(
                description="Move asset",
                target_assets=[],
                proposed_changes=[],
                submitted_by="user-1",
            )

    def test_user_create_valid(self):
        schema = UserCreate(
            username="testuser",
            password="securepass123",
        )
        assert schema.role == "standard"

    def test_user_create_short_password(self):
        with pytest.raises(Exception):
            UserCreate(username="testuser", password="short")

    def test_auth_request_valid(self):
        schema = AuthRequest(username="admin", password="pass123")
        assert schema.username == "admin"

    def test_password_change_request_valid(self):
        schema = PasswordChangeRequest(new_password="newpass123")
        assert schema.new_password == "newpass123"

    def test_ingestion_event_create_valid(self):
        schema = IngestionEventCreate(
            source_id=uuid.uuid4(),
            source_name="Test Source",
            record_count=10,
            status="success",
        )
        assert schema.record_count == 10

    def test_asset_status_create_valid(self):
        schema = AssetStatusCreate(
            asset_id="a1",
            asset_name="USS Test",
            timestamp=datetime.utcnow(),
            readiness_score=0.95,
            operational_status="operational",
            maintenance_status="nominal",
        )
        assert schema.readiness_score == 0.95

    def test_asset_status_readiness_bounds(self):
        with pytest.raises(Exception):
            AssetStatusCreate(
                asset_id="a1",
                asset_name="USS Test",
                timestamp=datetime.utcnow(),
                readiness_score=-0.1,
                operational_status="operational",
                maintenance_status="nominal",
            )

    def test_qa_interaction_create_valid(self):
        schema = QAInteractionCreate(
            session_id="sess-1",
            question="What is the mission?",
            answer="The mission is...",
            cited_sections=["missionOverview"],
            cited_source_data=["src-1"],
            conops_version_used=1,
            response_time_ms=200,
        )
        assert schema.conops_version_used == 1
