# CONOPS One Source — centralized situational awareness tool

An AI-powered system that provides commanders and participants with centralized situational awareness, with predictive insights into the impact of proposed changes to CPF asset operations.

## What It Does

- **Multi-source data ingestion** — Collects and normalizes operational and sustainment data from network shares, SharePoint sites, and web pages.
- **Unified CONOPS generation** — Synthesizes all ingested data into a single, versioned Concept of Operations document with mission overview, asset inventory, operational timelines, sustainment status, and resource allocation.
- **Predictive impact analysis** — Evaluates proposed changes against current data to produce impact assessments with confidence scores, cascading effect analysis, and resource reallocation recommendations.
- **Natural language Q&A** — Ask questions about the CONOPS in plain English and get cited, contextual answers powered by RAG (Retrieval-Augmented Generation).
- **Version control** — Maintains a single source of truth for the CONOPS document with full version history, change tracking, and document comparison.
- **Collaboration** — Routes unanswered questions to subject matter experts, supports user feedback on CONOPS content, and sends automated change notifications.
- **Audit trail** — Immutable, append-only logging of all system actions for full traceability and accountability.
- **Access control** — Role-based access (admin, standard, read-only) with secure authentication and account management.

## Tech Stack

| Component | Technology |
|-----------|------------|
| Backend | Python, FastAPI |
| Frontend | JavaScript (React) |
| Database | PostgreSQL |
| Vector Store | For RAG-based search and Q&A |
| LLM | Gemma (local, served via Ollama) |
| Deployment | Docker Compose (single-machine) |

## Architecture

All AI inference runs locally — no cloud LLM dependencies. The Gemma model is served by Ollama with an OpenAI-compatible API endpoint. The entire stack is containerized and orchestrated via Docker Compose for portable, single-command deployment.

## Getting Started

### Prerequisites

- Docker and Docker Compose
- Git

### Deploy

```bash
git clone <repo-url>
cd conops-one-source
docker compose up
```

Ollama will automatically download and configure the Gemma model on first start.

## Project Structure

```
backend/
  api/          # FastAPI route handlers
  connectors/   # Data source connectors (network share, SharePoint, web)
  models/       # SQLAlchemy ORM models and Pydantic schemas
  services/     # Business logic (ingestion, CONOPS generation, analysis, QA, etc.)
  tests/        # Unit and property-based tests
frontend/       # React web dashboard
```
