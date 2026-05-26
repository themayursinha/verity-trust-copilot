# Verity Trust Copilot

**Self-hosted security questionnaire automation powered by AI.** Generate accurate, citation-backed answers
from your approved evidence library using semantic embedding retrieval with LLM synthesis.

[![CI](https://github.com/themayursinha/verity-trust-copilot/actions/workflows/ci.yml/badge.svg)](https://github.com/themayursinha/verity-trust-copilot/actions/workflows/ci.yml)

## Features

- **AI-Powered Retrieval** — Semantic embedding search (all-MiniLM-L6-v2) understands meaning, not just keywords. Cosine similarity matching across evidence snippets with graceful BM25 fallback when sentence-transformers is unavailable.
- **LLM Answer Synthesis** — Optional LLM integration (OpenAI-compatible or local Ollama) drafts accurate, well-cited answers from retrieved evidence. Runs fully offline with Ollama + Llama 3.2 for maximum data privacy.
- **Knowledge Base Learning** — Approved answers are indexed and reused. Each completed questionnaire improves future results. Search the knowledge base to find previously approved responses.
- **Conservative by Design** — Never fabricates claims. Every answer cites verifiable evidence with source identifiers. AI-generated answers always carry `needs_human_review: true` until approved.
- **Questionnaire Management** — Import questions from Excel, Word, and PDF files. Create named questionnaires, track progress, and export completed responses back in the original format (XLSX/DOCX).
- **Question Assignment** — Delegate individual answers or entire questionnaires to team members. View assigned questions, bulk assign, and track completion status.
- **Compliance Dashboard** — Track framework coverage for ISO 27001, SOC 2, GDPR, and DORA. Monitor evidence freshness, approval statistics, policy summaries, and recent activity.
- **Team Collaboration** — Multi-tenant architecture with RBAC roles (admin, editor, viewer). Approve, reject, and annotate answers with reviewer notes and audit trails.
- **Self-Hosted** — Docker Compose deployment with PostgreSQL and Redis. Your evidence library and credentials stay on your infrastructure. Optional Ollama integration for fully local AI.
- **JSON Import** — Bulk import evidence from JSON files or programmatic sources. Mock Vanta integration for local demo imports.
- **Multiple Export Formats** — Export completed questionnaires as XLSX, DOCX, CSV, JSON, or customer-ready Markdown.
- **Public Trust Center** — Proactively showcase certifications, active policies, and compliance status on a branded public portal. Includes AI chatbot for visitor questions, gated document access with NDA workflow, email subscriptions, and visitor analytics dashboard.
- **Continuous Compliance Monitoring** — Connect AWS and GitHub for automated evidence collection. Hourly checks verify IAM MFA, S3 encryption, security group rules, CloudTrail logging, branch protection, repo visibility, and Dependabot. Results automatically populate your evidence library.
- **Integration Framework** — Pluggable provider architecture for AWS, GitHub, and future integrations. Background scheduler runs checks hourly. Test results track pass/fail status with resource-level detail.

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Or: Python 3.12+ and Node.js 22

### Development

```bash
# Clone and start
git clone https://github.com/themayursinha/verity-trust-copilot.git
cd verity-trust-copilot

# With Docker
docker compose up

# Without Docker
cd backend && pip install -e ".[dev]" && uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
cd frontend && npm ci && npm run dev
```

Open http://localhost:5173 (or http://localhost:8000/docs for API docs)

### Production

```bash
# Generate RSA keys for JWT signing
bash scripts/generate-keys.sh

# Configure environment
cp .env.example .env
# Edit .env with secure values (SECRET_KEY, POSTGRES_PASSWORD, etc.)

# Start production stack
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

The production stack includes resource limits, health checks, secrets management for JWT keys, and automatic container restarts.

## Project Structure

```
.
├── backend/
│   ├── app/
│   │   ├── core/            # BM25 retrieval engine, answer templates
│   │   ├── middleware/       # Security headers, request logging
│   │   ├── models/           # SQLAlchemy models (User, Org, Evidence, etc.)
│   │   ├── routers/          # FastAPI route handlers
│   │   ├── schemas/          # Pydantic request/response schemas
│   │   └── services/         # Business logic (auth, etc.)
│   ├── migrations/           # Alembic database migrations
│   └── tests/                # Backend test suite (pytest)
├── frontend/
│   └── src/                  # React 18 + TypeScript + Vite
├── static/                   # Legacy vanilla JS static pages
├── scripts/                  # Backup, restore, key generation
├── data/                     # Sample security questions
├── evidence/                 # Sample evidence library
├── templates/                # Answer template definitions
├── docker-compose.yml        # Development stack
├── docker-compose.prod.yml   # Production overrides
└── Makefile                  # Dev, test, lint, build targets
```

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI (Python 3.12) |
| Frontend | React 18 + TypeScript + Vite |
| UI | Tailwind CSS + shadcn/ui |
| Database | PostgreSQL 16 |
| Cache / Session Store | Redis 7 |
| ORM | SQLAlchemy 2.0 (async) |
| Migrations | Alembic |
| Auth | JWT (RS256) with refresh token rotation |
| Search | Custom BM25 (field-weighted, synonym-aware) |
| Observability | structlog, Sentry, Prometheus metrics |
| Rate Limiting | slowapi |
| Deployment | Docker Compose with health checks and resource limits |
| CI/CD | GitHub Actions (lint, typecheck, test, build) |

## API Documentation

Once running, visit http://localhost:8000/docs for interactive OpenAPI (Swagger) documentation.

Key endpoint groups:
- `/api/v1/auth` — Registration, login, token refresh
- `/api/v1/answers` — Generate and manage questionnaire answers
- `/api/v1/evidence` — CRUD for evidence records
- `/api/v1/dashboard` — Compliance stats and framework coverage
- `/api/v1/policies` — Security policy management
- `/api/v1/pentests` — Penetration test tracking
- `/api/v1/export` — Export answers as CSV, JSON, or Markdown
- `/api/v1/health` — Health check endpoint

## Configuration

See `.env.example` for all environment variables. Key settings:

| Variable | Description |
|---|---|
| `SECRET_KEY` | JWT signing key (required) |
| `POSTGRES_USER` | PostgreSQL user (default: `postgres`) |
| `POSTGRES_PASSWORD` | PostgreSQL password (required) |
| `POSTGRES_DB` | PostgreSQL database name (default: `verity`) |
| `JWT_PRIVATE_KEY_PATH` | Path to RSA private key for JWT signing |
| `JWT_PUBLIC_KEY_PATH` | Path to RSA public key for JWT verification |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access token lifetime (default: `30`) |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Refresh token lifetime (default: `7`) |
| `CORS_ORIGINS` | Allowed CORS origins (default: `http://localhost:5173`) |
| `SENTRY_DSN` | Sentry error tracking (optional) |
| `TELEMETRY_ENABLED` | Anonymous usage statistics (opt-in, default: `false`) |
| `ENVIRONMENT` | Environment label (`development` / `production`) |

## Backup & Restore

```bash
# Backup
bash scripts/backup.sh

# Restore
bash scripts/restore.sh backups/verity_20260101_120000.sql.gz
```

## Architecture

1. **Evidence Management** — Evidence records include title, type, frameworks, control IDs, owner, `last_reviewed` date, summary, and approved snippets. Stored in PostgreSQL for multi-tenant access.
2. **Questionnaire Processing** — Customer questions are matched against the evidence library using field-weighted BM25. Titles, frameworks, and control IDs receive higher weight than raw snippet text.
3. **Template Matching** — 11 category definitions (encryption, GDPR, ISO 27001, etc.) match against question keywords. When a template matches (≥2 keywords), the answer is structured with category-specific framing and caveats.
4. **Answer Drafting** — Extractive and conservative. Answers are built from matched evidence snippets with source citations. The system will not invent details when evidence is absent.
5. **Confidence Scoring** — Answers are classified `high`, `medium`, or `low`. Low-confidence answers are flagged for human review. Freshness penalties apply: evidence < 180 days is `fresh`, < 365 days is `stale`, ≥ 365 days is `outdated`.
6. **Review Workflow** — Reviewers can approve or reject each answer with notes. Approvals are persisted and surfaced in the compliance dashboard.

## Development

### Setup

```bash
# Create virtual environment and install dependencies
python3 -m venv .venv
source .venv/bin/activate
make setup
```

### Available Commands

```bash
make check          # Run lint, format-check, typecheck, and tests
make test           # Run Python and TypeScript tests
make lint           # Run ruff linting
make format-check   # Check formatting with ruff
make typecheck      # Run mypy type checking
make dev-backend    # Start backend with hot reload
make dev-frontend   # Start frontend dev server
make db-migrate     # Run database migrations
make generate-keys  # Generate RSA key pair for JWT
make docker-prod    # Start production Docker stack
```

## License

Proprietary. Self-hosted deployment with per-seat licensing.
