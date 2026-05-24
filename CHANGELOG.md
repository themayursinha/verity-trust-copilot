# Changelog

All notable changes to Verity Trust Copilot are documented in this file.

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
