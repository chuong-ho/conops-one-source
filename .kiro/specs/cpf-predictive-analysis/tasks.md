# Implementation Plan: CPF Predictive Analysis Tool (CONOPS One Source)

## Overview

Implement the CONOPS One Source system as a containerized Python backend (FastAPI) with a JavaScript frontend, PostgreSQL database, and locally hosted Gemma model served by Ollama. The backend handles data ingestion, CONOPS generation, predictive analysis, QA (RAG), version control, notifications, question routing, keyword search, feedback, document comparison, integration gateway, audit logging, and access control. The frontend provides the web dashboard, QA chat interface, data source management UI, search UI, feedback UI, document comparison UI, and user management UI. Ollama serves the Gemma model with an OpenAI-compatible API endpoint, and the LLM Gateway connects to Ollama for all inference requests. All services are orchestrated via Docker Compose for single-machine deployment.

**Languages:** Python (backend services, API, data models, LLM integration, Docker config), JavaScript (web dashboard, QA chat UI, frontend components)

## Tasks

Note: when performing tasks, do it in the virtual environment at ./.venv

- [-] 1. Project structure, data models, and database setup
  - [x] 1.1 Create project directory structure and Python package scaffolding
    - Create `backend/` with sub-packages: `models/`, `services/`, `connectors/`, `api/`, `tests/`
    - Create `frontend/` directory for JavaScript UI
    - Set up `pyproject.toml` or `requirements.txt` with dependencies (FastAPI, SQLAlchemy, Hypothesis, psycopg2, etc.)
    - _Requirements: 9.1_

  - [-] 1.2 Define all SQLAlchemy data models and Pydantic schemas
    - Implement original models: `DataSourceConfig`, `NormalizedRecord`, `CONOPSDocument`, `SectionContent`, `ImpactAssessment`, `AffectedAsset`, `ResourceRecommendation`, `ChangeProposal`, `AuditEvent`, `QAInteraction`, `AssetStatus`, `IngestionEvent`, `User`, `Session`
    - Implement new models: `DocumentChangeEvent`, `Notification`, `NotificationPreferences`, `RoutedQuestion`, `FeedbackItem`, `DocumentComparison`, `SectionDiff`, `ChangeSummary`, `IntegrationConfig`, `WebhookRegistration`, `PluginRegistration`
    - Update `User` model: add `read_only` role, `requiresPasswordChange` boolean (default true), `deactivatedAt` datetime
    - Update `AuditEvent` model: add new event types (`document_change`, `user_management`, `feedback`, `external_integration`), add `immutable` flag
    - Update `QAInteraction` model: add `confidenceScore` float, `confidenceLevel` enum, `answered` boolean, `routedQuestionId` FK
    - Update `CONOPSDocument` model: add `status` ("published"/"superseded"), `publishedBy` field
    - Include all fields, types, constraints, and relationships as specified in the design
    - _Requirements: 1.3, 1.5, 2.2, 3.3, 6.2, 7.1, 7.4, 8.1, 10.1, 10.4, 11.4, 12.1, 13.2, 14.1, 14.2, 14.4, 15.1, 16.1, 17.2, 18.1, 19.2, 19.4_

  - [ ] 1.3 Create database migration scripts and initialization
    - Write Alembic migration or init script to create all tables in PostgreSQL
    - Seed an initial admin user with `requiresPasswordChange=true`
    - _Requirements: 8.1, 9.1, 14.1_

  - [ ]* 1.4 Write property tests for data models (Hypothesis)
    - **Property 1: Normalized records conform to schema with required metadata**
    - **Validates: Requirements 1.1, 1.3, 1.5**
    - **Property 8: Impact assessment structural completeness**
    - **Validates: Requirements 3.3**
    - **Property 15: Data source configuration requires all mandatory fields**
    - **Validates: Requirements 6.2**


- [ ] 2. LLM Gateway and Gemma integration via Ollama
  - [ ] 2.1 Create Ollama deployment script
    - Create `backend/scripts/setup_ollama.sh` that downloads and installs Ollama
    - Configure Ollama to serve the Gemma model with OpenAI-compatible API endpoint
    - Script should accept configurable parameters: model name, port
    - Include health check polling to wait for Ollama server readiness before returning
    - _Requirements: 9.3, 9.4, 9.5_

  - [ ] 2.2 Implement the LLM Gateway service
    - Create `backend/services/llm_gateway.py` with `generate()`, `embed()`, and `health_check()` methods
    - Configure to connect to the Ollama server's OpenAI-compatible API endpoint (e.g., `http://ollama:11434/v1`)
    - Use the OpenAI Python client library pointed at the local Ollama endpoint
    - Implement retry logic (up to 3 retries) and configurable timeout (default 120s) for model calls
    - Handle malformed model output with logging and single retry with adjusted prompt
    - Health check should verify Ollama is reachable and Gemma model is loaded via `/v1/models`
    - _Requirements: 9.2, 9.3, 9.5, 9.6_

  - [ ]* 2.3 Write property test for LLM Gateway (Hypothesis)
    - **Property 25: Ollama serves the correct Gemma model**
    - **Validates: Requirements 9.3, 9.5**

  - [ ]* 2.4 Write unit tests for LLM Gateway and Ollama integration
    - Test health check verifies Ollama endpoint and confirms Gemma model is loaded
    - Test timeout handling, retry on unreachable Ollama server, malformed output handling
    - Verify LLM Gateway connects to Ollama's OpenAI-compatible API
    - Test Ollama-specific error scenarios: server loading, no model loaded, GPU memory errors
    - _Requirements: 9.2, 9.3, 9.5_

- [ ] 3. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 4. Data Ingestion Service and source connectors
  - [ ] 4.1 Implement the SourceConnector interface and connectors
    - Create `backend/connectors/base.py` with abstract `SourceConnector` class (`connect`, `fetch`, `test_connection`, `disconnect`)
    - Implement `NetworkShareConnector`, `SharePointConnector`, `WebPageConnector` in separate modules
    - Each connector implements connectivity validation and raw data fetching
    - _Requirements: 1.1, 1.2_

  - [ ] 4.2 Implement the Data Ingestion Service
    - Create `backend/services/data_ingestion.py` with methods: `add_source`, `edit_source`, `remove_source`, `list_sources`, `test_connectivity`, `trigger_ingestion`, `get_ingestion_status`
    - Implement data normalization: tag each record with source type, ingestion timestamp, and source identifier
    - Implement retry logic: 3 retries with exponential backoff (1s, 2s, 4s), log each failure, notify user after all retries exhausted
    - Implement scheduled (cron-based) and on-demand ingestion triggers
    - Validate connectivity and permissions before initiating ingestion
    - On source removal: mark associated ingested data as stale
    - Perform connectivity test on every source save and include result in response
    - Log all ingestion events to the Audit Service
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 6.1, 6.2, 6.3, 6.4, 6.5, 7.4_

  - [ ]* 4.3 Write property tests for Data Ingestion Service (Hypothesis)
    - **Property 2: Source connectivity validation before ingestion**
    - **Validates: Requirements 1.2**
    - **Property 3: Retry behavior on unreachable sources**
    - **Validates: Requirements 1.4**
    - **Property 16: Connectivity test on source save**
    - **Validates: Requirements 6.3**
    - **Property 17: Data source status includes required fields**
    - **Validates: Requirements 6.4**
    - **Property 18: Source removal marks associated data as stale**
    - **Validates: Requirements 6.5**

  - [ ]* 4.4 Write unit tests for Data Ingestion Service
    - Test scheduled vs. on-demand ingestion trigger modes
    - Test CRUD operations for data source management
    - Test error conditions: unreachable sources, invalid credentials, partial data fetch, normalization failure
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 6.1_


- [ ] 5. CONOPS Generator and Version Control Service
  - [ ] 5.1 Implement the Version Control Service
    - Create `backend/services/version_control.py` with methods: `publish_version`, `get_latest_version`, `get_version`, `list_versions`, `acquire_lock`, `release_lock`
    - Enforce monotonically increasing version numbers
    - Implement locking to prevent concurrent modification conflicts (only one publish succeeds)
    - Mark previous version as "superseded" when new version is published
    - Retain all historical versions for reference
    - Log version events to Audit Service
    - Trigger Notification Service on new version publish
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_

  - [ ] 5.2 Implement the CONOPS Generator service
    - Create `backend/services/conops_generator.py` with methods: `generate`, `update`, `get_latest`, `get_version`, `get_version_at_time`
    - Produce versioned CONOPS documents with all five required sections (mission overview, asset inventory, operational timelines, sustainment status, resource allocation summary)
    - Use LLM Gateway to synthesize normalized data into CONOPS content
    - Delegate version management to Version Control Service
    - Include `lastUpdatedAt` timestamp on every generated document
    - Mark sections as incomplete with missing source indicators when data is insufficient
    - Do not generate empty CONOPS when no data is available
    - Index CONOPS sections into vector store for QA retrieval
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

  - [ ]* 5.3 Write property tests for Version Control Service (Hypothesis)
    - **Property 26: Monotonically increasing CONOPS version numbers**
    - **Validates: Requirements 10.1, 10.4**
    - **Property 27: Latest version returned by default**
    - **Validates: Requirements 10.2**
    - **Property 28: Concurrent modification prevention**
    - **Validates: Requirements 10.3**
    - **Property 29: Version metadata on every CONOPS view**
    - **Validates: Requirements 10.5**

  - [ ]* 5.4 Write property tests for CONOPS Generator (Hypothesis)
    - **Property 4: CONOPS structural completeness**
    - **Validates: Requirements 2.2, 2.4**
    - **Property 5: CONOPS reflects latest data**
    - **Validates: Requirements 2.3**
    - **Property 6: Incomplete data indication**
    - **Validates: Requirements 2.5**

  - [ ]* 5.5 Write unit tests for CONOPS Generator and Version Control
    - Test generation with complete data, partial data, and no data
    - Test versioning: monotonic increment, superseded marking, historical retrieval
    - Test concurrent publish conflict resolution
    - Test lock acquisition and release
    - Test incomplete section indicators
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 10.1, 10.2, 10.3, 10.4, 10.5_

- [ ] 6. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 7. Predictive Analysis Engine
  - [ ] 7.1 Implement the Predictive Analysis Engine service
    - Create `backend/services/predictive_analysis.py` with methods: `analyze_change`, `get_recommendations`, `get_asset_status_at_time`
    - Use LLM Gateway to analyze proposed changes against operational and sustainment data
    - Generate ImpactAssessment with: affected assets list, impact type (positive/negative/neutral), confidence scores (0.0-1.0), mitigation actions for negative impacts
    - Identify cascading effects when multiple assets are affected
    - Set `hasHighRiskWarning` flag when any asset has negative impact with confidence above threshold
    - Incorporate maintenance schedules and sustainment timelines in predictions
    - Enforce 60-second timeout for analysis
    - Validate that target assets exist in current data before analysis
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6_

  - [ ] 7.2 Implement resource allocation recommendations
    - Generate up to 3 ranked recommendations by predicted effectiveness
    - Include tradeoffs and per-asset readiness score impacts for each recommendation
    - Consider current utilization, maintenance schedules, and mission priorities
    - _Requirements: 5.1, 5.2, 5.3, 5.4_

  - [ ]* 7.3 Write property tests for Predictive Analysis Engine (Hypothesis)
    - **Property 7: Impact assessment affected assets are valid**
    - **Validates: Requirements 3.2**
    - **Property 9: Cascading effects for multi-asset changes**
    - **Validates: Requirements 3.4**
    - **Property 10: High-risk warning flag**
    - **Validates: Requirements 3.6**
    - **Property 14: Resource recommendations are ranked, bounded, and include tradeoffs**
    - **Validates: Requirements 5.1, 5.3, 5.4**

  - [ ]* 7.4 Write unit tests for Predictive Analysis Engine
    - Test with single and multiple affected assets
    - Test timeout handling (>60s)
    - Test unknown asset validation error
    - Test boundary confidence scores (0.0, 1.0)
    - Test resource recommendation ranking and tradeoffs
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 5.1, 5.2, 5.3, 5.4_


- [ ] 8. QA Engine with confidence indicators and question routing
  - [ ] 8.1 Implement the QA Engine service
    - Create `backend/services/qa_engine.py` with methods: `ask`, `start_session`, `end_session`, `get_session_history`
    - Implement RAG pipeline: embed question via LLM Gateway, retrieve relevant CONOPS sections from vector store, generate answer with citations
    - Include `citedSections` and `citedSourceData` in every response
    - Include `confidenceScore` (0.0-1.0) and `confidenceLevel` ("high"/"medium"/"low") in every response
    - Maintain conversation context within a session for follow-up questions
    - Always use the latest CONOPS version for answers (track `conopsVersionUsed`)
    - When answer cannot be determined: set `answered=false`, route question to Question Routing Service, suggest related topics
    - Log every QA interaction to the Audit Service with CONOPS version
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 7.2, 11.1, 11.2, 11.3, 11.4, 11.5_

  - [ ]* 8.2 Write property tests for QA Engine (Hypothesis)
    - **Property 11: QA responses include citations**
    - **Validates: Requirements 4.2**
    - **Property 12: QA session context preservation**
    - **Validates: Requirements 4.4, 11.3**
    - **Property 13: QA uses latest CONOPS version**
    - **Validates: Requirements 4.5**
    - **Property 30: QA answers grounded in CONOPS with confidence indicators**
    - **Validates: Requirements 11.2, 11.4**
    - **Property 31: Unanswered questions routed to Question Routing Service**
    - **Validates: Requirements 11.5, 13.1**

  - [ ]* 8.3 Write unit tests for QA Engine
    - Test successful question answering with citations and confidence indicators
    - Test "no answer found" scenario: routing to Question Routing Service, suggested topics
    - Test session context for follow-up questions
    - Test behavior when no CONOPS is available
    - Test low confidence answer includes disclaimer
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 11.1, 11.2, 11.4, 11.5_

- [ ] 9. Notification Service
  - [ ] 9.1 Implement the Notification Service
    - Create `backend/services/notification_service.py` with methods: `send_notification`, `register_user`, `update_preferences`, `get_delivery_status`, `list_notifications`
    - Support email and in-app notification channels
    - Include CONOPS version number, publication timestamp, and modified section names in notifications
    - Implement retry logic: up to 3 retries with exponential backoff for failed deliveries
    - Mark notification as "failed" with recorded failureReason after all retries exhausted
    - Allow users to register and select preferred notification channels
    - Do not block CONOPS publishing if notification service is unavailable (queue for later)
    - Log all notification events to Audit Service
    - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5_

  - [ ]* 9.2 Write property tests for Notification Service (Hypothesis)
    - **Property 32: Notifications sent to all registered users on CONOPS publish**
    - **Validates: Requirements 12.1, 12.2**
    - **Property 33: Notification channel delivery matches user preferences**
    - **Validates: Requirements 12.3**
    - **Property 34: Notification delivery retry on failure**
    - **Validates: Requirements 12.5**

  - [ ]* 9.3 Write unit tests for Notification Service
    - Test notification registration and channel preference selection
    - Test notification content includes version, timestamp, and modified sections
    - Test retry logic on delivery failure
    - Test notification queuing when service is unavailable
    - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5_

- [ ] 10. Question Routing Service
  - [ ] 10.1 Implement the Question Routing Service
    - Create `backend/services/question_routing.py` with methods: `route_question`, `assign_to_sme`, `submit_answer`, `escalate`, `get_question`, `search_questions`, `list_pending`
    - Route unanswered questions to CONOPS owner or designated SME
    - Track question status lifecycle: pending → assigned → answered → closed
    - Set corresponding timestamp fields on each status transition
    - Implement 48-hour escalation: send reminder to assigned SME and notify CONOPS owner
    - Notify original questioner when answer is provided (via Notification Service)
    - Handle SME unavailability: fallback to CONOPS owner, re-route if SME deactivated
    - Maintain searchable log of all routed questions and resolutions
    - Log all routing events to Audit Service
    - _Requirements: 13.1, 13.2, 13.3, 13.4, 13.5_

  - [ ]* 10.2 Write property tests for Question Routing Service (Hypothesis)
    - **Property 35: Routed question status lifecycle**
    - **Validates: Requirements 13.2**
    - **Property 36: Original questioner notified when routed question answered**
    - **Validates: Requirements 13.3**
    - **Property 37: Escalation after 48 hours**
    - **Validates: Requirements 13.4**
    - **Property 38: Routed question search round trip**
    - **Validates: Requirements 13.5**

  - [ ]* 10.3 Write unit tests for Question Routing Service
    - Test routing to SME and fallback to CONOPS owner
    - Test status transitions and invalid transition rejection
    - Test escalation timer and notification
    - Test re-routing when assigned SME is deactivated
    - _Requirements: 13.1, 13.2, 13.3, 13.4, 13.5_

- [ ] 11. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.


- [ ] 12. Access Control Service (extended user management)
  - [ ] 12.1 Implement the Access Control Service
    - Create `backend/services/access_control.py` with methods: `register_user`, `deactivate_user`, `reactivate_user`, `list_users`, `change_password`, `authenticate`, `check_access`, `get_session`, `logout`
    - Enforce three roles: admin, standard, read_only
    - Hash passwords securely (bcrypt), enforce password complexity requirements
    - Enforce admin-only access for user management operations (return 403 for non-admin)
    - Implement account deactivation without deletion (set `isActive=false`, `deactivatedAt` timestamp, preserve audit history)
    - Deactivated account login attempts return generic auth error
    - Implement first-login password change: `requiresPasswordChange=true` on registration, block access to all resources except password change until completed
    - Update `lastLoginAt` on successful authentication
    - Generate opaque session tokens with expiration
    - Read-only users attempting write operations get 403 with clear message
    - Handle errors: duplicate username, non-existent user, invalid password complexity, invalid credentials (generic error message)
    - Log all user management events to Audit Service
    - _Requirements: 8.1, 8.2, 8.3, 14.1, 14.2, 14.3, 14.4, 14.5_

  - [ ]* 12.2 Write property tests for Access Control Service (Hypothesis)
    - **Property 22: User add/remove round trip**
    - **Validates: Requirements 8.1, 8.2**
    - **Property 23: Password change invalidates old credentials**
    - **Validates: Requirements 8.2**
    - **Property 24: Last login time updates on authentication**
    - **Validates: Requirements 8.3**
    - **Property 39: Role-based access control enforcement**
    - **Validates: Requirements 14.2, 14.3**
    - **Property 40: User registration requires unique username and password complexity**
    - **Validates: Requirements 14.1**
    - **Property 41: Account deactivation preserves audit history**
    - **Validates: Requirements 14.4**
    - **Property 42: First-login password change required**
    - **Validates: Requirements 14.5**

  - [ ]* 12.3 Write unit tests for Access Control Service
    - Test non-admin user attempting admin operations returns 403
    - Test duplicate username rejection
    - Test session expiration and invalidation
    - Test deactivated user login attempt returns generic auth error
    - Test first-login password change flow end-to-end
    - Test read-only user attempting write operation returns 403
    - Test account deactivation preserves audit records
    - _Requirements: 8.1, 8.2, 8.3, 14.1, 14.2, 14.3, 14.4, 14.5_

- [ ] 13. Search Service
  - [ ] 13.1 Implement the Search Service
    - Create `backend/services/search_service.py` with methods: `search`, `reindex`, `get_suggestions`
    - Provide keyword-based search across all CONOPS sections
    - Support boolean operators (AND, OR, NOT), exact phrase matching, and wildcard searches
    - Rank results by relevance
    - Highlight matching keywords in returned results
    - Re-index document content on CONOPS updates
    - Handle search timeout (>5s): return partial results with timeout indicator
    - Handle invalid query syntax with validation error
    - Fallback to direct document search if search index is unavailable
    - _Requirements: 15.1, 15.2, 15.3, 15.4, 15.5_

  - [ ]* 13.2 Write property tests for Search Service (Hypothesis)
    - **Property 43: Keyword search returns matching results**
    - **Validates: Requirements 15.1, 15.3**
    - **Property 44: Search results highlight matching keywords**
    - **Validates: Requirements 15.4**
    - **Property 45: Search index reflects latest CONOPS version**
    - **Validates: Requirements 15.5**

  - [ ]* 13.3 Write unit tests for Search Service
    - Test keyword search with boolean operators (AND, OR, NOT)
    - Test exact phrase matching and wildcard searches
    - Test relevance ranking order
    - Test re-indexing on CONOPS update
    - Test search with empty query returns validation error
    - Test search timeout returns partial results
    - _Requirements: 15.1, 15.2, 15.3, 15.4, 15.5_

- [ ] 14. Audit Trail Service (extended with immutability and section-level history)
  - [ ] 14.1 Implement the Audit Trail Service
    - Create `backend/services/audit_service.py` with methods: `log_event`, `log_document_change`, `query`, `get_section_history`, `generate_report`
    - Log all system events: impact assessments, QA interactions, ingestion events, CONOPS generation, document changes, user management, feedback, external integrations
    - Store records in immutable, append-only log — reject any attempt to modify or delete records
    - Support section-level change history via `DocumentChangeEvent` (section name, change type, previous/new content, change summary)
    - Support filtering by user, date range, section, change type, and event type
    - Return section history in chronological order
    - Implement retry and queuing for audit log write failures (never silently drop events)
    - Retain audit records for the lifetime of the system with no automatic purging
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 16.1, 16.2, 16.3, 16.4, 16.5_

  - [ ] 14.2 Implement point-in-time asset status retrieval
    - Add `get_asset_status_at_time(asset_id, timestamp)` to the Predictive Analysis Engine
    - Return asset state as recorded at or immediately before the given timestamp
    - _Requirements: 7.5_

  - [ ]* 14.3 Write property tests for Audit Trail Service (Hypothesis)
    - **Property 19: Audit log completeness**
    - **Validates: Requirements 7.1, 7.2, 7.4**
    - **Property 20: Audit report date range filtering**
    - **Validates: Requirements 7.3**
    - **Property 21: Point-in-time asset status retrieval**
    - **Validates: Requirements 7.5**
    - **Property 46: CONOPS document change audit with section-level granularity**
    - **Validates: Requirements 16.1, 16.2**
    - **Property 47: Section history and audit filtering**
    - **Validates: Requirements 16.3, 16.4**

  - [ ]* 14.4 Write unit tests for Audit Trail Service
    - Test immutability: reject modify/delete attempts on audit records
    - Test section-level change history retrieval
    - Test filtering by user, date range, section, change type
    - Test audit log write failure retry and queuing
    - Test chronological ordering of section history
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 16.1, 16.2, 16.3, 16.4, 16.5_

- [ ] 15. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.


- [ ] 16. Feedback Service
  - [ ] 16.1 Implement the Feedback Service
    - Create `backend/services/feedback_service.py` with methods: `submit_feedback`, `get_feedback`, `update_status`, `list_feedback`, `link_to_change`
    - Accept feedback on specific CONOPS sections with categories: error, inconsistency, suggestion, general
    - Assign unique tracking identifier on submission, set initial status to "submitted"
    - Route feedback to CONOPS owner or designated SME for review
    - Track status lifecycle: submitted → under_review → resolved/rejected
    - Notify submitting user on status changes (via Notification Service)
    - Record resolution details and link to resulting CONOPS version when resolved
    - Validate that referenced CONOPS section exists; return error for non-existent sections
    - Queue feedback for manual assignment if SME routing fails
    - Log all feedback events to Audit Service
    - _Requirements: 17.1, 17.2, 17.3, 17.4, 17.5_

  - [ ]* 16.2 Write property tests for Feedback Service (Hypothesis)
    - **Property 48: Feedback submission with categorization and tracking**
    - **Validates: Requirements 17.1, 17.2**
    - **Property 49: Feedback routing and status lifecycle**
    - **Validates: Requirements 17.3, 17.4, 17.5**

  - [ ]* 16.3 Write unit tests for Feedback Service
    - Test feedback submission with all categories
    - Test status transitions and notification to submitter
    - Test linking feedback to CONOPS version on resolution
    - Test feedback on non-existent CONOPS section returns validation error
    - Test SME routing failure queues for manual assignment
    - _Requirements: 17.1, 17.2, 17.3, 17.4, 17.5_

- [ ] 17. Document Comparison Service
  - [ ] 17.1 Implement the Document Comparison Service
    - Create `backend/services/document_comparison.py` with methods: `compare`, `compare_sections`, `get_change_summary`, `quick_compare`
    - Generate diff between any two historical CONOPS versions highlighting additions, deletions, and modifications
    - Produce `ChangeSummary` with counts: sectionsModified, sectionsAdded, sectionsRemoved, totalChanges
    - Support section filtering: return only changes for specified sections
    - Implement `quick_compare(version)`: compare with immediately preceding version, equivalent to `compare(version-1, version)`
    - Handle edge cases: version not found (404), same version compared (empty diff), quick-compare on version 1 (error: no preceding version)
    - _Requirements: 18.1, 18.2, 18.3, 18.4, 18.5_

  - [ ]* 17.2 Write property tests for Document Comparison Service (Hypothesis)
    - **Property 50: Document comparison correctness**
    - **Validates: Requirements 18.1, 18.3**
    - **Property 51: Document comparison version coverage and quick-compare equivalence**
    - **Validates: Requirements 18.2, 18.4, 18.5**

  - [ ]* 17.3 Write unit tests for Document Comparison Service
    - Test comparison between two different versions
    - Test section filtering returns only specified sections
    - Test quick-compare equivalence with explicit compare(N-1, N)
    - Test comparing same version returns empty diff
    - Test quick-compare on version 1 returns appropriate error
    - Test version not found returns 404
    - _Requirements: 18.1, 18.2, 18.3, 18.4, 18.5_

- [ ] 18. Integration Gateway
  - [ ] 18.1 Implement the Integration Gateway
    - Create `backend/services/integration_gateway.py` with methods: `handle_request`, `register_webhook`, `remove_webhook`, `list_webhooks`, `trigger_event`, `register_plugin`, `list_plugins`
    - Provide documented API for external systems to query CONOPS data, submit questions, and retrieve analysis results
    - Implement webhook registration: validate URL, store secret for HMAC signature verification, subscribe to event types
    - Deliver event payloads to active webhooks for subscribed events (CONOPS update, impact assessment, system events)
    - Implement webhook retry: up to 3 retries, increment failureCount, deactivate after configurable consecutive failures
    - Implement plugin architecture: register plugins with name, version, entry point, capabilities; activate/deactivate without modifying core code
    - Authenticate all external requests and enforce access control policies via Access Control Service
    - Log all external interactions to Audit Trail Service (successful and rejected)
    - Handle rate limiting: return 429 with retry-after header
    - _Requirements: 19.1, 19.2, 19.3, 19.4, 19.5_

  - [ ]* 18.2 Write property tests for Integration Gateway (Hypothesis)
    - **Property 52: Webhook delivery for subscribed events**
    - **Validates: Requirements 19.2**
    - **Property 53: Integration Gateway authentication and access control**
    - **Validates: Requirements 19.3**
    - **Property 54: Integration Gateway audit logging**
    - **Validates: Requirements 19.5**

  - [ ]* 18.3 Write unit tests for Integration Gateway
    - Test webhook registration with valid and invalid URLs
    - Test event delivery to subscribed webhooks
    - Test webhook retry and deactivation after consecutive failures
    - Test plugin registration and listing
    - Test unauthenticated request rejection (401)
    - Test unauthorized request rejection (403)
    - Test rate limiting returns 429
    - Test all interactions logged to Audit Trail Service
    - _Requirements: 19.1, 19.2, 19.3, 19.4, 19.5_

- [ ] 19. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.


- [ ] 20. REST API layer
  - [ ] 20.1 Implement API endpoints for Data Ingestion and Source Management
    - Create FastAPI router in `backend/api/ingestion.py`
    - Endpoints: `POST /sources`, `PUT /sources/{id}`, `DELETE /sources/{id}`, `GET /sources`, `POST /sources/{id}/test`, `POST /ingestion/trigger`, `GET /ingestion/{job_id}/status`
    - Include authentication middleware (session token validation)
    - _Requirements: 1.1, 1.2, 1.6, 6.1, 6.2, 6.3, 6.4, 6.5_

  - [ ] 20.2 Implement API endpoints for CONOPS and Version Control
    - Create FastAPI router in `backend/api/conops.py`
    - Endpoints: `POST /conops/generate`, `GET /conops/latest`, `GET /conops/version/{id}`, `GET /conops/at-time`, `GET /conops/versions`, `POST /conops/lock`, `DELETE /conops/lock`
    - Every CONOPS response includes version number, publication timestamp, and authoring source
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 10.1, 10.2, 10.3, 10.4, 10.5_

  - [ ] 20.3 Implement API endpoints for Predictive Analysis
    - Create FastAPI router in `backend/api/analysis.py`
    - Endpoints: `POST /analysis/change`, `GET /analysis/{id}/recommendations`, `GET /assets/{id}/status-at-time`
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 5.1, 5.2, 5.3, 5.4, 7.5_

  - [ ] 20.4 Implement API endpoints for QA
    - Create FastAPI router in `backend/api/qa.py`
    - Endpoints: `POST /qa/sessions`, `POST /qa/sessions/{id}/ask`, `DELETE /qa/sessions/{id}`, `GET /qa/sessions/{id}/history`
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 11.1, 11.2, 11.3, 11.4, 11.5_

  - [ ] 20.5 Implement API endpoints for Audit Trail
    - Create FastAPI router in `backend/api/audit.py`
    - Endpoints: `GET /audit/report`, `GET /audit/events`, `GET /audit/sections/{name}/history`
    - Support filtering by user, date range, section, change type
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 16.1, 16.2, 16.3, 16.4_

  - [ ] 20.6 Implement API endpoints for User Management and Access Control
    - Create FastAPI router in `backend/api/users.py`
    - Endpoints: `POST /auth/login`, `POST /auth/logout`, `POST /auth/change-password`, `GET /users`, `POST /users`, `DELETE /users/{id}`, `PUT /users/{id}/password`, `PUT /users/{id}/deactivate`, `PUT /users/{id}/reactivate`
    - Admin-only middleware for user management endpoints
    - First-login password change redirect
    - _Requirements: 8.1, 8.2, 8.3, 14.1, 14.2, 14.3, 14.4, 14.5_

  - [ ] 20.7 Implement API endpoints for Notifications
    - Create FastAPI router in `backend/api/notifications.py`
    - Endpoints: `POST /notifications/register`, `PUT /notifications/preferences`, `GET /notifications`, `GET /notifications/{id}/status`
    - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5_

  - [ ] 20.8 Implement API endpoints for Question Routing
    - Create FastAPI router in `backend/api/questions.py`
    - Endpoints: `GET /questions`, `GET /questions/{id}`, `POST /questions/{id}/assign`, `POST /questions/{id}/answer`, `POST /questions/{id}/escalate`, `GET /questions/pending`
    - _Requirements: 13.1, 13.2, 13.3, 13.4, 13.5_

  - [ ] 20.9 Implement API endpoints for Search
    - Create FastAPI router in `backend/api/search.py`
    - Endpoints: `GET /search`, `GET /search/suggestions`, `POST /search/reindex`
    - _Requirements: 15.1, 15.2, 15.3, 15.4, 15.5_

  - [ ] 20.10 Implement API endpoints for Feedback
    - Create FastAPI router in `backend/api/feedback.py`
    - Endpoints: `POST /feedback`, `GET /feedback`, `GET /feedback/{id}`, `PUT /feedback/{id}/status`, `POST /feedback/{id}/link`
    - _Requirements: 17.1, 17.2, 17.3, 17.4, 17.5_

  - [ ] 20.11 Implement API endpoints for Document Comparison
    - Create FastAPI router in `backend/api/comparison.py`
    - Endpoints: `GET /compare`, `GET /compare/sections`, `GET /compare/summary`, `GET /compare/quick/{version}`
    - _Requirements: 18.1, 18.2, 18.3, 18.4, 18.5_

  - [ ] 20.12 Implement API endpoints for Integration Gateway
    - Create FastAPI router in `backend/api/integrations.py`
    - Endpoints: `POST /integrations/webhooks`, `DELETE /integrations/webhooks/{id}`, `GET /integrations/webhooks`, `POST /integrations/plugins`, `GET /integrations/plugins`
    - External-facing API endpoints for CONOPS queries, question submission, analysis retrieval
    - _Requirements: 19.1, 19.2, 19.3, 19.4, 19.5_

- [ ] 21. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.


- [ ] 22. Frontend - Web Dashboard and all UI components (JavaScript)
  - [ ] 22.1 Set up frontend project structure
    - Initialize JavaScript frontend project (e.g., React) in `frontend/`
    - Set up build tooling, routing, and API client utility
    - _Requirements: 9.1_

  - [ ] 22.2 Implement login page and authentication flow
    - Build login form with username/password
    - Store session token and handle session expiration redirects
    - Implement first-login password change flow (redirect to password change before granting access)
    - _Requirements: 8.1, 14.1, 14.5_

  - [ ] 22.3 Implement CONOPS display page with version info
    - Render the unified CONOPS document with all five sections
    - Display version number, publication timestamp, and authoring source on every view
    - Display last-updated timestamp
    - Show incomplete section indicators with missing source names
    - _Requirements: 2.1, 2.2, 2.4, 2.5, 10.5_

  - [ ] 22.4 Implement Predictive Analysis submission and results UI
    - Build form for submitting a ChangeProposal
    - Display ImpactAssessment results: affected assets, impact types, confidence scores, mitigation actions
    - Display cascading effects and high-risk warning indicators
    - Display ranked resource recommendations with tradeoffs
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.6, 5.1, 5.3, 5.4_

  - [ ] 22.5 Implement QA Chat Interface with confidence indicators
    - Build chat UI for natural language questions about CONOPS
    - Display answers with cited sections, source data, confidence score, and confidence level
    - Maintain session context for follow-up questions
    - Show "information not available" with suggested topics when no answer is found
    - Indicate when question has been routed to SME
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 11.1, 11.2, 11.4, 11.5_

  - [ ] 22.6 Implement Data Source Management UI
    - Build CRUD interface for data sources (add, edit, remove with confirmation)
    - Display source status: connectivity status, last successful ingestion time
    - Trigger on-demand ingestion and show ingestion status
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 1.6_

  - [ ] 22.7 Implement User Management UI (admin only)
    - Build user listing page showing all users with last login time and role
    - Add/remove/deactivate/reactivate user forms and password change functionality
    - Support three roles: admin, standard, read_only
    - Restrict access to admin role only
    - _Requirements: 8.1, 8.2, 8.3, 14.1, 14.2, 14.4_

  - [ ] 22.8 Implement Search UI
    - Build search interface with keyword input, boolean operator support
    - Display results with highlighted matching keywords and relevance ranking
    - _Requirements: 15.1, 15.2, 15.3, 15.4_

  - [ ] 22.9 Implement Feedback UI
    - Build feedback submission form with section selector and category picker
    - Display feedback status tracking and resolution details
    - _Requirements: 17.1, 17.2, 17.4_

  - [ ] 22.10 Implement Document Comparison UI
    - Build version selector for comparing two CONOPS versions
    - Display side-by-side or inline diff view with additions, deletions, modifications highlighted
    - Show change summary with section counts
    - Support section filtering and quick-compare from current version view
    - _Requirements: 18.1, 18.2, 18.3, 18.4, 18.5_

  - [ ] 22.11 Implement Notification preferences and in-app notifications UI
    - Build notification preferences page for channel selection (email, in-app)
    - Display in-app notification list with read/unread status
    - _Requirements: 12.3, 12.4_

  - [ ] 22.12 Implement Audit Report UI
    - Build date range selector for audit report generation
    - Display audit report listing impact assessments, QA interactions, ingestion events, and document changes
    - Support filtering by user, section, change type
    - _Requirements: 7.1, 7.2, 7.3, 16.3, 16.4_

- [ ] 23. Docker containerization and deployment
  - [ ] 23.1 Create Dockerfiles for backend and frontend
    - Write `backend/Dockerfile` for the Python FastAPI application
    - Write `frontend/Dockerfile` for the JavaScript frontend (build + serve with nginx or similar)
    - _Requirements: 9.1_

  - [ ] 23.2 Create Docker Compose configuration
    - Write `docker-compose.yml` orchestrating: backend app, frontend, PostgreSQL, Ollama server (serving Gemma model with OpenAI-compatible API), vector store
    - Configure Ollama container with: Gemma model auto-download on first start, GPU passthrough, exposed OpenAI-compatible endpoint on port 11434
    - Configure LLM Gateway environment variables to point to Ollama container endpoint
    - Configure networking, volumes, environment variables, and health checks
    - Include Ollama health check endpoint in Docker Compose depends_on conditions
    - Ensure single-command deployment (`docker compose up`)
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5_

  - [ ]* 23.3 Write smoke test for Docker build and startup
    - Verify all containers build and start successfully
    - Verify backend health endpoint responds
    - Verify Ollama container is running and healthy
    - Verify Ollama is serving the Gemma model via `/v1/models` endpoint
    - Verify Gemma model is accessible via LLM Gateway through Ollama's OpenAI-compatible API
    - _Requirements: 9.1, 9.2, 9.3, 9.5_


- [ ] 24. Integration wiring and end-to-end flows
  - [ ] 24.1 Wire ingestion pipeline to CONOPS generation and notifications
    - Connect Data Ingestion Service completion events to trigger CONOPS Generator
    - CONOPS Generator delegates versioning to Version Control Service
    - Version Control Service triggers Notification Service on new version publish
    - Ensure CONOPS generation indexes sections into vector store for QA and Search
    - Search Service re-indexes on CONOPS update
    - Verify data flows from ingestion through normalization to CONOPS update to notifications
    - _Requirements: 1.3, 2.1, 2.3, 4.5, 10.1, 10.4, 12.1, 15.5_

  - [ ] 24.2 Wire QA Engine to Question Routing Service
    - Connect QA Engine unanswered question flow to Question Routing Service
    - Question Routing Service uses Notification Service for SME assignment and answer notifications
    - Verify end-to-end: ask question → no answer → route to SME → SME answers → user notified
    - _Requirements: 11.5, 13.1, 13.3_

  - [ ] 24.3 Wire Feedback Service to Question Routing and Notification
    - Connect Feedback Service routing to Question Routing Service for SME assignment
    - Connect Feedback Service status changes to Notification Service for user updates
    - _Requirements: 17.3, 17.4_

  - [ ] 24.4 Wire Integration Gateway to Access Control and Audit
    - All Integration Gateway requests authenticated via Access Control Service
    - All Integration Gateway interactions logged to Audit Trail Service
    - Webhook events triggered by Version Control Service (CONOPS updates) and Predictive Analysis Engine (new assessments)
    - _Requirements: 19.2, 19.3, 19.5_

  - [ ] 24.5 Wire all services to Audit Trail Service
    - Ensure every impact assessment, QA interaction, ingestion event, CONOPS generation, user management action, feedback event, and external integration is logged
    - Verify audit report generation includes all event types
    - Verify document change events are logged with section-level granularity
    - _Requirements: 7.1, 7.2, 7.4, 16.1, 16.2, 19.5_

  - [ ]* 24.6 Write integration tests for end-to-end flows
    - Test: ingest data → generate CONOPS → version created → notifications sent → search re-indexed
    - Test: ask QA question → no answer → routed to SME → SME answers → user notified
    - Test: submit change proposal → receive impact assessment → verify audit log entry
    - Test: add user → login → first-login password change → perform action → verify last login updated
    - Test: submit feedback → routed to SME → resolved → linked to CONOPS version
    - Test: external API request → authenticated → access controlled → audit logged
    - Test: compare two CONOPS versions → verify diff correctness
    - _Requirements: 1.1, 2.1, 3.1, 4.1, 7.1, 8.1, 10.1, 11.5, 12.1, 13.1, 14.5, 15.5, 17.3, 18.1, 19.3_

- [ ] 25. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Python (with Hypothesis) is used for all backend property-based tests
- JavaScript is used only for frontend UI components (tasks 22.x)
- Each property test references specific correctness properties from the design document (Properties 1-54)
- Checkpoints ensure incremental validation at logical boundaries
- All services communicate with the local Gemma model via the LLM Gateway, which connects to Ollama's OpenAI-compatible API endpoint
- Task 1.1 is already completed; task 1.2 is in progress and needs updating with new models
- Requirements 10-19 are covered by new task groups: Version Control (5.1), Notification (9), Question Routing (10), Access Control (12), Search (13), Audit Trail extended (14), Feedback (16), Document Comparison (17), Integration Gateway (18)
