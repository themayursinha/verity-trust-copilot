# Changelog

All notable changes to Verity Trust Copilot are documented in this file.

## [0.2.0] - 2026-05-26

### Multi-Provider LLM (BYOK)
- Support for 10+ LLM providers: OpenAI, Anthropic Claude, Google Gemini, Groq, Together AI, DeepSeek, Mistral, xAI Grok, Fireworks, Ollama, and custom OpenAI-compatible endpoints.
- Native API support for Anthropic Messages API and Google Gemini generateContent API.
- Provider presets with pre-configured base URLs and recommended models.
- `GET /api/v1/llm/providers` endpoint lists all available providers with model options.
- BYOK (Bring Your Own Key) model — configure `LLM_PROVIDER` and `LLM_API_KEY` for any service. Ollama requires no API key.

### AI Engine (Phase 1)
- **Semantic embedding retrieval** replacing BM25 keyword search with sentence-transformers (all-MiniLM-L6-v2) and cosine similarity. Graceful BM25 fallback when sentence-transformers is unavailable.
- **LLM answer synthesis** wired into the main answer generation pipeline. Supports OpenAI-compatible APIs and local Ollama (llama3.2) for fully offline AI.
- **Knowledge base learning** — approved answers are indexed and reused. Searchable via `/api/v1/answers/knowledge-base/search`.
- **AI confidence scoring** based on embedding similarity metrics, not just term frequency.

### Questionnaire Automation (Phase 2)
- **PDF questionnaire import** via pypdf, alongside existing xlsx/docx support.
- **Original format export** — completed questionnaires exported as filled .xlsx and .docx files matching the original format.
- **Question assignment and delegation** — assign individual answers or bulk-assign to team members. List assigned answers, track completion.
- **Questionnaire CRUD** — create named questionnaires, track status (draft → in_progress → completed).
- **Regenerate answers** — re-generate individual answers with updated evidence or LLM settings.
- **`/api/v1/auth/me`** endpoint for current user identity.

### Public Trust Center (Phase 3)
- **Branded public portal** — custom domain, colors, logo, hero text. Zero-auth page at `/trust/:orgSlug`.
- **AI chatbot widget** — floating chat interface answers visitor questions from the organization's knowledge base and evidence.
- **Gated document access** — upload documents with NDA requirements. Visitors request access, admins approve/reject.
- **Email subscriptions** — visitors subscribe for security update notifications.
- **Visitor analytics** — track visits, unique visitors, chatbot queries, document downloads, daily breakdown.
- **Configurable sections** — toggle certifications, policies, controls, chatbot, subscriptions, documents per organization.

### Continuous Compliance Monitoring (Phase 4)
- **Integration framework** — pluggable provider architecture with async test runners.
- **AWS provider** — 6 compliance tests: IAM MFA enforcement, root access key detection, S3 bucket encryption, S3 public access, overly-permissive security groups, CloudTrail multi-region logging.
- **GitHub provider** — 3 compliance tests: default branch protection, public repository detection, Dependabot vulnerability alerts enabled.
- **Background scheduler** — APScheduler runs all enabled integrations every 1 hour.
- **Test results** — pass/fail/error status with resource-level detail and evidence payloads.
- **Integration CRUD** — create, list, update, delete integrations with connection validation on creation.
- **Dashboard summary** — `/api/v1/integrations/dashboard/summary` with healthy/degraded/error counts.

### Fixes
- CI: resolved ruff format, lint, and mypy type errors across all files (5 iterations).
- `Policy` model field references corrected in Trust Center public API.
- SQLAlchemy `Column` type issues resolved in scheduler dict key.
- LLM service return type corrected for 3-tuple.

### Tests
- **96 tests passing** (was 32): 19 AI engine unit tests, 16 Trust Center tests, 22 integration tests, 18 answers API tests, plus preserved original 21 tests.
- Backend test coverage now spans AI engine, answers, evidence policies, pentests, auth, dashboard, Trust Center, and integrations.

---

## [0.1.0] - 2026-05-24

### Added
- FastAPI backend with async PostgreSQL (SQLAlchemy 2.0) and Redis for caching and session storage
- React SPA with TypeScript, shadcn/ui, and Tailwind CSS v4
- JWT authentication with RS256 signing, access/refresh token rotation, and password hashing via passlib[bcrypt]
- Multi-tenant architecture with organization-level data isolation
- RBAC roles: admin, editor, viewer, member with permission enforcement on all endpoints
- BM25-powered answer generation from evidence database with field-weighted scoring, synonym expansion, and TF saturation (k1=1.5)
- Compliance dashboard (ISO 27001, SOC 2, GDPR, DORA coverage tracking with real-time stats)
- Policy management with version tracking, review scheduling, and policy status monitoring
- Pentest tracker with findings management, severity classification, and remediation tracking
- Answer approval workflow (approve/reject with reviewer notes and audit trail)
- Export to Markdown (customer-ready reports), CSV (tabular), JSON (structured)
- Evidence CRUD with JSON import (bulk upload from file or programmatic source)
- Team member management with seat enforcement and invitation workflow
- Docker Compose deployment (development config + production config with resource limits, health checks, and Docker secrets for JWT keys)
- Landing page with feature showcase, hero section, and interactive navigation
- Onboarding wizard for first-time users (organization setup, evidence import, team invites)
- Rate limiting via slowapi (per-endpoint, IP-based, configurable thresholds)
- Input sanitization middleware (XSS prevention, SQL injection guard)
- Security headers middleware (CSP, HSTS, X-Content-Type-Options, X-Frame-Options, Referrer-Policy)
- Structured logging via structlog (JSON output, request ID tracing)
- Sentry error tracking with environment-aware configuration
- Prometheus metrics endpoint (`/metrics`) with request counts, latency histograms, and error rates
- 5-job CI/CD pipeline: lint (ruff), typecheck (mypy), test (pytest), frontend typecheck (tsc), build (npm run build)
- Database backup script (gzipped pg_dump with timestamped filenames)
- Database restore script (gunzip + psql restore with safety checks)
- RSA key generation script for JWT signing (`scripts/generate-keys.sh`)
- Email templates: welcome, password reset, team invitation, license expiry notification
- Health check endpoint for container orchestration (`/api/v1/health`)
- OpenAPI (Swagger) documentation auto-generated at `/docs`

### Preserved
- Original BM25 engine (`security_questionnaire_copilot.py`) with full field-weighted retrieval, category detection, and confidence scoring
- All existing Python unit tests (117 tests, 100% pass rate)
- JavaScript evidence quality tests (6 tests, 100% pass rate)
- `web_app.py` local prototype (can run independently for local-only usage)
