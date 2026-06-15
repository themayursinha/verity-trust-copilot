# Verity Trust Copilot - Architecture Documentation

## Table of Contents
1. [Project Overview](#1-project-overview)
2. [High-Level Architecture (HLD)](#2-high-level-architecture-hld)
3. [Low-Level Design (LLD)](#3-low-level-design-lld)
4. [Database Schema](#4-database-schema)
5. [API Structure](#5-api-structure)
6. [Authentication Flow](#6-authentication-flow)
7. [Module Dependencies](#7-module-dependencies)
8. [Key Data Flows](#8-key-data-flows)
9. [Frontend Architecture](#9-frontend-architecture)

---

## 1. Project Overview

**Project Name:** Verity Trust Copilot  
**Purpose:** Self-hosted security questionnaire automation powered by AI  
**Version:** 0.2.0

### Core Functionality
- Generate accurate, citation-backed answers to security questionnaires from approved evidence
- Multi-tenant SaaS with organization-based data isolation
- Public Trust Center portal for customer-facing compliance information
- Continuous compliance monitoring via AWS/GitHub integrations
- LLM-powered answer synthesis with multi-provider support

### Tech Stack

| Layer | Technology |
|-------|------------|
| **Backend** | FastAPI (Python 3.12) |
| **Frontend** | React 18 + TypeScript + Vite |
| **UI** | Tailwind CSS + shadcn/ui + Radix UI |
| **Database** | PostgreSQL 16 (async via asyncpg) |
| **Cache/Sessions** | Redis 7 |
| **ORM** | SQLAlchemy 2.0 (async) |
| **Migrations** | Alembic |
| **Auth** | JWT (RS256/HS256) with refresh token rotation |
| **Search** | BM25 (fallback) + Sentence Transformers (embeddings) |
| **AI/LLM** | OpenAI-compatible API + Ollama (local) |
| **Background Jobs** | APScheduler |
| **Observability** | structlog, Sentry, Prometheus |
| **Rate Limiting** | slowapi |
| **Deployment** | Docker Compose |

---

## 2. High-Level Architecture (HLD)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              CLIENT LAYER                                    │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────────┐  │
│  │   React SPA     │  │   Mobile App    │  │   Public Trust Center       │  │
│  │   (Frontend)    │  │   (Future)      │  │   (No Auth Required)        │  │
│  └────────┬────────┘  └────────┬────────┘  └──────────────┬──────────────┘  │
└───────────┼────────────────────┼──────────────────────────┼───────────────────┘
            │                    │                          │
            │ HTTPS             │ HTTPS                     │ HTTPS
            ▼                    ▼                          ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              API GATEWAY LAYER                              │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                        FastAPI Application                             │  │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────────┐  │  │
│  │  │  CORS      │  │  Rate      │  │  Security  │  │  License       │  │  │
│  │  │  Middleware│  │  Limiter   │  │  Headers   │  │  Middleware    │  │  │
│  │  └────────────┘  └────────────┘  └────────────┘  └────────────────┘  │  │
│  │  ┌────────────────────────────────────────────────────────────────┐   │  │
│  │  │                    17 API Routers                               │   │  │
│  │  │  auth, answers, approvals, dashboard, evidence, export,        │   │  │
│  │  │  health, integrations, llm, notifications, org, pentests,      │   │  │
│  │  │  policies, public, reports, trust_center, vanta, webhooks    │   │  │
│  │  └────────────────────────────────────────────────────────────────┘   │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
            │                    │                          │
            ▼                    ▼                          ▼
┌───────────────────┐  ┌───────────────────┐  ┌───────────────────────────┐
│    PostgreSQL      │  │      Redis        │  │     External Services     │
│    (Primary DB)    │  │  (Token Store)    │  │  ┌─────────────────────┐ │
│                   │  │                   │  │  │  LLM Providers       │ │
│  - Organizations  │  │  - JWT blacklist  │  │  │  (OpenAI, Anthropic, │ │
│  - Users          │  │  - Refresh tokens │  │  │   Gemini, Ollama)     │ │
│  - Evidence       │  │                   │  │  └─────────────────────┘ │
│  - Answers        │  │                   │  │  ┌─────────────────────┐ │
│  - Policies       │  │                   │  │  │  AWS Services        │ │
│  - Integrations   │  │                   │  │  │  (IAM, S3, EC2)     │ │
│  - Trust Center   │  │                   │  │  └─────────────────────┘ │
│                   │  │                   │  │  ┌─────────────────────┐ │
│                   │  │                   │  │  │  GitHub API          │ │
│                   │  │                   │  │  │  (Repos, Branches)   │ │
│                   │  │                   │  │  └─────────────────────┘ │
└───────────────────┘  └───────────────────┘  └───────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           BACKGROUND PROCESSES                               │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                     APScheduler (Hourly Jobs)                          │   │
│  │  ┌─────────────────────┐  ┌─────────────────────────────────────┐    │   │
│  │  │  Integration Checks │  │  Evidence Freshness Monitoring      │    │   │
│  │  │  - AWS Provider     │  │  (Future: automated reminders)      │    │   │
│  │  │  - GitHub Provider  │  │                                      │    │   │
│  │  └─────────────────────┘  └─────────────────────────────────────┘    │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Architecture Principles
1. **Multi-Tenancy:** All data is scoped by `org_id` with automatic filtering
2. **API-First:** All functionality exposed through RESTful APIs
3. **Async-First:** Full async/await for I/O operations
4. **Security by Design:** Input sanitization, security headers, rate limiting
5. **Graceful Degradation:** BM25 fallback when embeddings unavailable

---

## 3. Low-Level Design (LLD)

### Directory Structure

```
/home/mayur/code/jamie/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI app entry point
│   │   ├── config.py            # Pydantic settings
│   │   ├── database.py           # SQLAlchemy async engine
│   │   ├── dependencies.py       # FastAPI dependency injection
│   │   ├── cache.py             # Redis caching utilities
│   │   │
│   │   ├── core/                # Business logic core
│   │   │   ├── ai_engine.py     # Semantic search (embeddings)
│   │   │   ├── engine.py        # BM25 retrieval + answer generation
│   │   │   └── file_parser.py   # XLSX/DOCX/PDF parsing
│   │   │
│   │   ├── middleware/          # HTTP middleware
│   │   │   ├── __init__.py
│   │   │   ├── logging.py       # Request/response logging
│   │   │   ├── security.py      # Security headers, rate limiting
│   │   │   └── license.py       # License enforcement
│   │   │
│   │   ├── models/              # SQLAlchemy ORM models
│   │   │   ├── __init__.py      # Barrel export
│   │   │   ├── user.py
│   │   │   ├── organization.py
│   │   │   ├── evidence.py
│   │   │   ├── answer.py        # Answer, AnswerGeneration, Approval
│   │   │   ├── policy.py
│   │   │   ├── pentest.py
│   │   │   ├── questionnaire.py
│   │   │   ├── integration.py    # Integration, ComplianceTest, TestResult
│   │   │   ├── webhook.py       # Webhook, WebhookLog
│   │   │   ├── notification.py
│   │   │   ├── audit_log.py
│   │   │   └── trust_center.py  # Settings, Visit, Subscriber, Document
│   │   │
│   │   ├── routers/             # FastAPI route handlers
│   │   │   ├── __init__.py
│   │   │   ├── auth.py          # /api/v1/auth
│   │   │   ├── answers.py       # /api/v1/answers
│   │   │   ├── approvals.py     # /api/v1/approvals
│   │   │   ├── dashboard.py     # /api/v1/dashboard
│   │   │   ├── evidence.py      # /api/v1/evidence
│   │   │   ├── export.py        # /api/v1/export
│   │   │   ├── health.py        # /api/v1/health, /api/v1/ready
│   │   │   ├── integrations.py  # /api/v1/integrations
│   │   │   ├── llm.py           # /api/v1/llm
│   │   │   ├── notifications.py # /api/v1/notifications
│   │   │   ├── org.py           # /api/v1/org
│   │   │   ├── pentests.py      # /api/v1/pentests
│   │   │   ├── policies.py      # /api/v1/policies
│   │   │   ├── public.py        # /api/v1/public/trust-center
│   │   │   ├── reports.py       # /api/v1/reports
│   │   │   ├── trust_center.py  # /api/v1/trust-center
│   │   │   ├── vanta.py         # /api/v1/vanta
│   │   │   └── webhooks.py      # /api/v1/webhooks
│   │   │
│   │   ├── schemas/             # Pydantic request/response models
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── answer.py
│   │   │   ├── evidence.py
│   │   │   ├── notification.py
│   │   │   ├── organization.py
│   │   │   ├── org.py
│   │   │   └── webhook.py
│   │   │
│   │   └── services/            # Business logic services
│   │       ├── __init__.py
│   │       ├── auth_service.py   # JWT, password hashing, token management
│   │       ├── llm_service.py   # LLM API calls (multi-provider)
│   │       ├── llm_providers.py # Provider registry (10+ providers)
│   │       ├── scheduler.py     # APScheduler background tasks
│   │       ├── vanta_service.py # Vanta API integration
│   │       ├── vanta_mock.py    # Mock Vanta data
│   │       ├── license_service.py # Ed25519 license validation
│   │       ├── webhook_service.py # Webhook dispatch
│   │       └── integrations/
│   │           ├── __init__.py   # Provider registry
│   │           ├── base.py       # BaseProvider abstract class
│   │           ├── aws_provider.py
│   │           └── github_provider.py
│   │
│   ├── migrations/               # Alembic DB migrations
│   ├── emails/                  # Email templates
│   ├── tests/                   # Backend pytest tests
│   ├── data/                    # Sample data
│   ├── pyproject.toml
│   ├── requirements.txt
│   ├── Dockerfile
│   └── alembic.ini
│
├── frontend/
│   ├── src/
│   │   ├── App.tsx             # Root component with routing
│   │   ├── main.tsx            # Entry point
│   │   ├── index.css           # Global styles
│   │   │
│   │   ├── pages/              # Page components
│   │   │   ├── landing.tsx
│   │   │   ├── login.tsx
│   │   │   ├── register.tsx
│   │   │   ├── dashboard.tsx
│   │   │   ├── answers.tsx
│   │   │   ├── evidence.tsx
│   │   │   ├── policies.tsx
│   │   │   ├── pentests.tsx
│   │   │   ├── settings.tsx
│   │   │   ├── trust-center-admin.tsx
│   │   │   ├── trust-center-public.tsx
│   │   │   └── not-found.tsx
│   │   │
│   │   ├── components/         # Reusable UI components
│   │   │   ├── app-layout.tsx
│   │   │   ├── app-sidebar.tsx
│   │   │   ├── onboarding-wizard.tsx
│   │   │   └── ui/             # shadcn/ui components
│   │   │
│   │   ├── hooks/              # React hooks
│   │   │   └── useAuth.tsx     # Authentication context
│   │   │
│   │   ├── lib/                # Utilities
│   │   │   └── api.ts          # Axios API client with interceptors
│   │   │
│   │   └── types/             # TypeScript type definitions
│   │
│   ├── public/
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   ├── tailwind.config.ts
│   ├── Dockerfile
│   └── nginx.conf
│
├── scripts/                     # Utility scripts
├── data/                       # Sample questions
├── evidence/                   # Sample evidence
├── templates/                  # Answer templates
├── static/                    # Static assets
├── docker-compose.yml         # Development stack
├── docker-compose.prod.yml    # Production overrides
├── Makefile                   # Dev commands
└── README.md
```

---

## 4. Database Schema

### Entity Relationship Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           ORGANIZATION                                      │
│  ┌───────────────┐                                                         │
│  │ organizations  │◄──────────────────────────────────┐                     │
│  ├───────────────┤                                  │                     │
│  │ id (PK)       │                                  │                     │
│  │ name          │                                  │                     │
│  │ slug          │                                  │                     │
│  │ brand_color   │                                  │                     │
│  │ logo_url      │                                  │                     │
│  │ license_key   │                                  │                     │
│  │ max_seats     │                                  │                     │
│  │ created_at    │                                  │                     │
│  │ updated_at    │                                  │                     │
│  └───────────────┘                                  │                     │
│          │1                                          │1                     │
│          │                                           │                     │
│          ▼ M                                         │                     │
│  ┌───────────────┐                                  │                     │
│  │    users     │                                  │                     │
│  ├───────────────┤                                  │                     │
│  │ id (PK)       │                                  │                     │
│  │ org_id (FK) ──┼──────────────────────────────────┘                     │
│  │ email         │                                  │                     │
│  │ password_hash │                                  │                     │
│  │ display_name  │                                  │                     │
│  │ role          │                                  │                     │
│  │ is_active     │                                  │                     │
│  │ created_at    │                                  │                     │
│  │ updated_at    │                                  │                     │
│  └───────────────┘                                  │                     │
│          │1                                          │                     │
│          │ M                                         │                     │
│          ▼                                           │                     │
│  ┌───────────────┐        ┌──────────────────┐      │                     │
│  │answer_generations│      │  questionnaires  │      │                     │
│  ├───────────────┤        ├──────────────────┤      │                     │
│  │ id (PK)       │        │ id (PK)          │      │                     │
│  │ org_id (FK)   │◄───────│ org_id (FK) ─────┼──────┘                     │
│  │ as_of_date    │        │ name             │                            │
│  │ confidence_   │        │ original_        │                            │
│  │   counts      │        │   filename       │                            │
│  │ questionnaire_│        │ original_format  │                            │
│  │   id (FK)     │        │ original_content │                            │
│  │ engine_used   │        │ question_count   │                            │
│  │ created_at    │        │ answered_count   │                            │
│  └───────┬───────┘        │ status          │                            │
│          │1                │ created_by (FK)  │                            │
│          │ M               │ created_at      │                            │
│          ▼                 │ updated_at      │                            │
│  ┌───────────────┐        └──────────────────┘                            │
│  │   answers     │                                                     │
│  ├───────────────┤                                                     │
│  │ id (PK)       │                                                     │
│  │ generation_id │                                                     │
│  │   (FK) ───────┼─────────────────────────────────────────────┐     │
│  │ question      │                                                     │     │
│  │ answer_text   │                                                     │     │
│  │ confidence    │                                                     │     │
│  │ confidence_   │                                                     │     │
│  │   score      │                                                     │     │
│  │ confidence_   │                                                     │     │
│  │   rationale  │                                                     │     │
│  │ needs_human_  │                                                     │     │
│  │   review     │                                                     │     │
│  │ citations     │                                                     │     │
│  │ freshness     │                                                     │     │
│  │ assignee_id  │◄──────────────────┐                                 │     │
│  │ order_index  │                   │                                 │     │
│  │ source       │                   │                                 │     │
│  │ created_at   │                   │                                 │     │
│  └───────┬───────┘                   │                                 │     │
│          │1                          │                                 │     │
│          │ M                         │                                 │     │
│          ▼                           │                                 │     │
│  ┌───────────────┐                   │                                 │     │
│  │  approvals    │                   │                                 │     │
│  ├───────────────┤                   │                                 │     │
│  │ id (PK)       │                   │                                 │     │
│  │ answer_id (FK)├───────────────────┘                                 │     │
│  │ user_id (FK) ─┼─────────────────────────────────────────────┐     │
│  │ status        │                                             │     │
│  │ notes         │                                             │     │
│  │ created_at    │                                             │     │
│  └───────────────┘                                             │     │
└─────────────────────────────────────────────────────────────────┘     │
            │                                                        │
            ▼                                                        │
┌─────────────────────────────────────────────────────────────────────────────┐
│                          EVIDENCE & POLICIES                                │
│                                                                              │
│  ┌────────────────────┐        ┌────────────────────┐                      │
│  │  evidence_records  │        │      policies      │                      │
│  ├────────────────────┤        ├────────────────────┤                      │
│  │ id (PK)            │        │ id (PK)            │                      │
│  │ org_id (FK) ───────┼────────│ org_id (FK) ───────┘                      │
│  │ title              │        │ title              │                      │
│  │ type               │        │ category           │                      │
│  │ frameworks         │        │ content            │                      │
│  │ control_ids        │        │ status             │                      │
│  │ last_reviewed      │        │ version            │                      │
│  │ owner              │        │ review_interval_   │                      │
│  │ summary            │        │   months           │                      │
│  │ snippets           │        │ next_review        │                      │
│  │ created_at         │        │ created_at         │                      │
│  │ updated_at         │        │ updated_at         │                      │
│  └────────────────────┘        └────────────────────┘                      │
│                                                                              │
│  ┌────────────────────┐        ┌────────────────────┐                      │
│  │     pentests       │        │   audit_logs       │                      │
│  ├────────────────────┤        ├────────────────────┤                      │
│  │ id (PK)            │        │ id (PK)            │                      │
│  │ org_id (FK) ───────┼────────│ org_id (FK) ───────┘                      │
│  │ title              │        │ user_id (FK) ──────┘                      │
│  │ scope              │        │ resource_type      │                      │
│  │ methodology        │        │ resource_id       │                      │
│  │ start_date         │        │ action            │                      │
│  │ end_date           │        │ changes           │                      │
│  │ status             │        │ ip_address        │                      │
│  │ findings (JSONB)   │        │ created_at        │                      │
│  │ created_at         │        └────────────────────┘                      │
│  │ updated_at         │                                                    │
│  └────────────────────┘                                                    │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                          INTEGRATIONS                                         │
│                                                                              │
│  ┌────────────────────┐        ┌────────────────────┐                      │
│  │   integrations     │        │  compliance_tests  │                      │
│  ├────────────────────┤        ├────────────────────┤                      │
│  │ id (PK)            │◄────1───│ integration_id (FK)│                      │
│  │ org_id (FK) ───────┼─────────│ org_id (FK) ───────┘                      │
│  │ provider           │        │ name              │                      │
│  │ name               │        │ description       │                      │
│  │ enabled            │        │ frameworks        │                      │
│  │ config (JSONB)     │        │ control_ids       │                      │
│  │ last_run_at        │        │ category          │                      │
│  │ last_status        │        │ enabled           │                      │
│  │ last_error         │        │ created_at        │                      │
│  │ created_at         │        └─────────┬──────────┘                      │
│  │ updated_at         │                  │1                                │
│  └────────────────────┘                  │ M                                │
│          │1                              ▼                                 │
│          │ M                    ┌────────────────────┐                      │
│          ▼                    │   test_results     │                      │
│  ┌────────────────────┐      ├────────────────────┤                      │
│  │     webhooks       │      │ id (PK)            │                      │
│  ├────────────────────┤      │ org_id (FK) ───────┘                      │
│  │ id (PK)            │      │ test_id (FK) ──────┘                      │
│  │ org_id (FK) ───────┘      │ integration_id (FK)│                      │
│  │ url                 │      │ status            │                      │
│  │ secret              │      │ evidence (JSONB)  │                      │
│  │ name                │      │ message           │                      │
│  │ events (Text)       │      │ resources_checked │                      │
│  │ is_active           │      │ resources_failed  │                      │
│  │ custom_headers      │      │ created_at        │                      │
│  │ created_at         │      └────────────────────┘                      │
│  │ updated_at         │                                                    │
│  └────────┬───────────┘                                                    │
│           │1                                                              │
│           │ M                                                              │
│           ▼                                                                │
│  ┌────────────────────┐                                                   │
│  │    webhook_logs    │                                                   │
│  ├────────────────────┤                                                   │
│  │ id (PK)            │                                                   │
│  │ webhook_id (FK)     │                                                   │
│  │ org_id (FK)        │                                                   │
│  │ event              │                                                   │
│  │ payload            │                                                   │
│  │ response_status    │                                                   │
│  │ response_body      │                                                   │
│  │ success            │                                                   │
│  │ error              │                                                   │
│  │ created_at         │                                                   │
│  └────────────────────┘                                                   │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                           TRUST CENTER                                       │
│                                                                              │
│  ┌───────────────────────┐                                                  │
│  │  trust_center_settings │                                                  │
│  ├───────────────────────┤                                                  │
│  │ id (PK)               │                                                  │
│  │ org_id (FK) ──────────┼─────────────────────┐                            │
│  │ enabled               │                     │                            │
│  │ custom_domain         │                     │                            │
│  │ page_title            │                     │                            │
│  │ hero_headline         │                     │                            │
│  │ hero_subtext          │                     │                            │
│  │ brand_color           │                     │                            │
│  │ logo_url              │                     │                            │
│  │ favicon_url           │                     │                            │
│  │ show_certifications   │                     │                            │
│  │ show_controls         │                     │                            │
│  │ show_policies         │                     │                            │
│  │ show_ai_chatbot       │                     │                            │
│  │ show_subscribe         │                     │                            │
│  │ show_document_requests │                     │                            │
│  │ require_nda            │                     │                            │
│  │ created_at             │                     │                            │
│  │ updated_at             │                     │                            │
│  └───────────────────────┘                     │                            │
│          │1                                    │                            │
│          │ M                                  │ M                            │
│          ▼                                    ▼                              │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────────────┐  │
│  │ trust_center_   │    │ trust_center_   │    │ trust_center_          │  │
│  │ visits          │    │ subscribers     │    │ documents              │  │
│  ├─────────────────┤    ├─────────────────┤    ├─────────────────────────┤  │
│  │ id (PK)         │    │ id (PK)         │    │ id (PK)                │  │
│  │ org_id (FK)     │    │ org_id (FK)     │    │ org_id (FK) ──────────┘  │
│  │ visitor_ip      │    │ email           │    │ title                  │  │
│  │ page_viewed     │    │ name            │    │ description            │  │
│  │ referrer        │    │ company         │    │ document_type         │  │
│  │ user_agent      │    │ subscribed      │    │ file_url              │  │
│  │ chatbot_queries │    │ created_at      │    │ requires_nda          │  │
│  │ document_       │    └─────────────────┘    │ is_public             │  │
│  │   downloads     │                          │ download_count        │  │
│  │ created_at      │                          │ created_at            │  │
│  └─────────────────┘                          │ updated_at            │  │
│                                                └──────────┬──────────────┘  │
│                                                           │1                 │
│                                                           │ M                 │
│                                                           ▼                 │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                    trust_center_access_requests                          ││
│  ├─────────────────────────────────────────────────────────────────────────┤│
│  │ id (PK)                                                               ││
│  │ org_id (FK)                                                           ││
│  │ document_id (FK) ─────────────────────────────────────────────────────┼─┘│
│  │ requester_email                                                        ││
│  │ requester_name                                                         ││
│  │ requester_company                                                      ││
│  │ nda_accepted                                                          ││
│  │ status                                                                ││
│  │ approved_by (FK)                                                       ││
│  │ created_at                                                            ││
│  │ updated_at                                                            ││
│  └─────────────────────────────────────────────────────────────────────────┘│

┌─────────────────────────────────────────────────────────────────────────────┐
│                          NOTIFICATIONS                                       │
│                                                                              │
│  ┌────────────────────┐                                                     │
│  │   notifications    │                                                     │
│  ├────────────────────┤                                                     │
│  │ id (PK)            │                                                     │
│  │ org_id (FK) ───────┼─────────────────────────────────────────────┐     │
│  │ user_id (FK) ──────┘                                              │     │
│  │ type               │                                              │     │
│  │ title              │                                              │     │
│  │ message            │                                              │     │
│  │ is_read            │                                              │     │
│  │ link               │                                              │     │
│  │ priority           │                                              │     │
│  │ created_at         │                                              │     │
│  └────────────────────┘                                              │     │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Model Summary

| Model | Table | Purpose |
|-------|-------|---------|
| Organization | organizations | Tenant container |
| User | users | Authenticated users |
| EvidenceRecord | evidence_records | Compliance evidence |
| AnswerGeneration | answer_generations | Batch answer generation |
| Answer | answers | Individual Q&A |
| Approval | approvals | Answer review workflow |
| Questionnaire | questionnaires | Imported questionnaires |
| Policy | policies | Security policies |
| Pentest | pentests | Penetration tests |
| Integration | integrations | AWS/GitHub connections |
| ComplianceTest | compliance_tests | Integration test definitions |
| TestResult | test_results | Integration test results |
| Webhook | webhooks | Event notifications |
| WebhookLog | webhook_logs | Delivery attempts |
| Notification | notifications | In-app notifications |
| AuditLog | audit_logs | Activity tracking |
| TrustCenterSettings | trust_center_settings | Public portal config |
| TrustCenterVisit | trust_center_visits | Visitor analytics |
| TrustCenterSubscriber | trust_center_subscribers | Email subscriptions |
| TrustCenterDocument | trust_center_documents | Shared documents |
| TrustCenterAccessRequest | trust_center_access_requests | Document access requests |

---

## 5. API Structure

### Router Summary

| Router | Prefix | Auth | Description |
|--------|--------|------|-------------|
| `auth` | `/api/v1/auth` | No | Registration, login, token refresh |
| `answers` | `/api/v1/answers` | Yes | Answer generation, questionnaires |
| `approvals` | `/api/v1/approvals` | Yes | Answer review workflow |
| `dashboard` | `/api/v1/dashboard` | Yes | Compliance overview |
| `evidence` | `/api/v1/evidence` | Yes | Evidence CRUD |
| `export` | `/api/v1/export` | Yes | Multi-format exports |
| `health` | `/api/v1/health` | No | Health checks |
| `integrations` | `/api/v1/integrations` | Yes | AWS/GitHub management |
| `llm` | `/api/v1/llm` | Yes | LLM status and suggestions |
| `notifications` | `/api/v1/notifications` | Yes | In-app notifications |
| `org` | `/api/v1/org` | Yes | Organization management |
| `pentests` | `/api/v1/pentests` | Yes | Penetration test tracking |
| `policies` | `/api/v1/policies` | Yes | Policy management |
| `public` | `/api/v1/public/trust-center` | No | Public Trust Center |
| `reports` | `/api/v1/reports` | Yes | SOC 2 reports |
| `trust_center` | `/api/v1/trust-center` | Yes | Trust Center admin |
| `vanta` | `/api/v1/vanta` | Yes | Vanta integration |
| `webhooks` | `/api/v1/webhooks` | Yes | Webhook management |

### Endpoint Details

#### Auth Router (`/api/v1/auth`)
| Method | Path | Description |
|--------|------|-------------|
| POST | `/register` | Register new org + user |
| POST | `/login` | Authenticate user |
| POST | `/refresh` | Refresh access token |
| POST | `/logout` | Invalidate session |
| GET | `/me` | Get current user |

#### Answers Router (`/api/v1/answers`)
| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | List answer generations |
| GET | `/assigned` | List assigned answers |
| GET | `/sample` | Get sample questions |
| GET | `/knowledge-base/search` | Search knowledge base |
| GET | `/questionnaires` | List questionnaires |
| GET | `/{generation_id}` | Get specific generation |
| POST | `/` | Generate answers |
| POST | `/regenerate/{answer_id}` | Regenerate single answer |
| POST | `/import-file` | Import questionnaire |
| POST | `/assign` | Assign answer to user |
| POST | `/bulk-assign` | Bulk assign answers |
| PUT | `/{answer_id}` | Update answer |
| POST | `/learn` | Learn from approvals |
| POST | `/questionnaires` | Create questionnaire |
| PUT | `/questionnaires/{id}` | Update questionnaire |

#### Evidence Router (`/api/v1/evidence`)
| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | List evidence |
| GET | `/{id}` | Get evidence |
| POST | `/` | Create evidence |
| POST | `/import` | Bulk import |
| PUT | `/{id}` | Update evidence |
| DELETE | `/{id}` | Delete evidence |

#### Trust Center Router (`/api/v1/trust-center`)
| Method | Path | Description |
|--------|------|-------------|
| GET | `/settings` | Get settings |
| PUT | `/settings` | Update settings |
| GET | `/documents` | List documents |
| POST | `/documents` | Create document |
| PUT | `/documents/{id}` | Update document |
| DELETE | `/documents/{id}` | Delete document |
| GET | `/analytics` | Get analytics |
| GET | `/subscribers` | List subscribers |
| GET | `/access-requests` | List access requests |
| PUT | `/access-requests/{id}` | Approve request |

#### Public Trust Center (`/api/v1/public/trust-center/{org_slug}`)
| Method | Path | Description |
|--------|------|-------------|
| GET | `/{org_slug}` | Get public trust center |
| POST | `/{org_slug}/chat` | AI chatbot |
| POST | `/{org_slug}/subscribe` | Email subscription |
| POST | `/{org_slug}/request-access` | Request document access |
| GET | `/{org_slug}/documents/{id}` | Download document |

---

## 6. Authentication Flow

### JWT Token Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           AUTHENTICATION FLOW                                 │
│                                                                              │
│  1. REGISTRATION                                                            │
│  ┌──────────┐     POST /api/v1/auth/register    ┌──────────────────────┐   │
│  │  Client  │ ──────────────────────────────────►│  Server               │   │
│  └──────────┘                                    │                       │   │
│                                                   │ 1. Create Org        │   │
│                                                   │ 2. Create User        │   │
│  ┌──────────┐     AuthResponse{                 │ 3. Hash Password      │   │
│  │  Client  │ ◄──────────────────────────────── │ 4. Create Tokens     │   │
│  └──────────┘                                    └──────────────────────┘   │
│           │                                                │               │
│           │  {                                              │               │
│           │    access_token,  ──────────────────────────────┼──────┐       │
│           │    refresh_token,                               │      │       │
│           │    user,                                        │      │       │
│           │    organization                                 │      │       │
│           │  }                                              │      │       │
│           │                                                ▼      ▼       │
│           │                                        ┌──────────────────┐     │
│           │                                        │ Redis            │     │
│           │                                        │ rt:{user_id}:    │     │
│           │                                        │   {jti} = "1"   │     │
│           │                                        └──────────────────┘     │
│           │                                                             │
│           ▼                                                             │
│  2. API REQUESTS                                                          │
│  ┌──────────┐     GET /api/v1/answers             ┌──────────────────┐    │
│  │  Client  │ ──── Authorization: Bearer {at} ──►│  Server           │    │
│  └──────────┘                                    │                  │    │
│                                                   │ 1. Decode JWT   │    │
│                                                   │ 2. Check Redis  │    │
│                                                   │    blacklist    │    │
│                                                   │ 3. Query User   │    │
│                                                   │ 4. Return Data  │    │
│  ┌──────────┐     Response Data                   └──────────────────┘    │
│  │  Client  │ ◄─────────────────────────────────────────────────────    │
│  └──────────┘                                                             │
│                                                                              │
│  3. TOKEN REFRESH                                                          │
│  ┌──────────┐     POST /api/v1/auth/refresh         ┌──────────────────┐  │
│  │  Client  │ ──── {refresh_token} ───────────────►│  Server           │  │
│  └──────────┘                                       │                  │  │
│                                                    │ 1. Validate RT   │  │
│                                                    │ 2. Create new AT  │  │
│                                                    │ 3. Create new RT  │  │
│  ┌──────────┐     {                                 │ 4. Store new RT  │  │
│  │  Client  │ ◄── access_token,  ─────────────────│ 5. Invalidate old │  │
│  └──────────┘      refresh_token}                  └──────────────────┘  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Role-Based Access Control (RBAC)

| Role | Permissions |
|------|------------|
| `admin` | Full access, user management, integrations |
| `editor` | Evidence, answers, policies, pentests |
| `member` | View dashboard, assigned answers |
| `viewer` | Read-only access |

### Dependency Injection Pattern

```python
# FastAPI dependency chain
HTTPBearer ──► get_current_user ──► get_current_active_user
                                              │
                                              ▼
                                         require_admin
                                         require_editor
                                         require_viewer
```

---

## 7. Module Dependencies

### Dependency Graph

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            MAIN APPLICATION                                  │
│                              main.py                                         │
└────────────────────────────────┬────────────────────────────────────────────┘
                                 │
                    ┌────────────┼────────────┐
                    │            │            │
                    ▼            ▼            ▼
              ┌──────────┐ ┌──────────┐ ┌──────────┐
              │  config  │ │ database │ │middleware │
              │  .py     │ │  .py     │ │    /     │
              └────┬─────┘ └────┬─────┘ └────┬─────┘
                   │            │            │
                   │            │            ├──── logging.py
                   │            │            ├──── security.py
                   │            │            └──── license.py
                   │            │
                   │            └──────► Base (DeclarativeBase)
                   │                      │
                   │            ┌─────────┼─────────┐
                   │            │         │         │
                   │            ▼         ▼         ▼
                   │      ┌────────┐ ┌────────┐ ┌────────┐
                   │      │ models │ │routers │ │services│
                   │      │   /    │ │   /    │ │   /    │
                   │      └────┬───┘ └───┬────┘ └───┬────┘
                   │           │         │          │
                   │           │         │          ├──── auth_service.py
                   │           │         │          ├──── llm_service.py
                   │           │         │          ├──── llm_providers.py
                   │           │         │          ├──── scheduler.py
                   │           │         │          ├──── vanta_service.py
                   │           │         │          ├──── webhook_service.py
                   │           │         │          ├──── license_service.py
                   │           │         │          └──── integrations/
                   │           │         │                   ├──── base.py
                   │           │         │                   ├──── aws_provider.py
                   │           │         │                   └──── github_provider.py
                   │           │         │
                   │           │         ├──── auth.py
                   │           │         ├──── answers.py
                   │           │         ├──── approvals.py
                   │           │         ├──── dashboard.py
                   │           │         ├──── evidence.py
                   │           │         ├──── export.py
                   │           │         ├──── health.py
                   │           │         ├──── integrations.py
                   │           │         ├──── llm.py
                   │           │         ├──── notifications.py
                   │           │         ├──── org.py
                   │           │         ├──── pentests.py
                   │           │         ├──── policies.py
                   │           │         ├──── public.py
                   │           │         ├──── reports.py
                   │           │         ├──── trust_center.py
                   │           │         ├──── vanta.py
                   │           │         └──── webhooks.py
                   │           │
                   │           ├──── user.py ──────────► bcrypt, jwt
                   │           ├──── organization.py
                   │           ├──── evidence.py
                   │           ├──── answer.py
                   │           ├──── policy.py
                   │           ├──── pentest.py
                   │           ├──── integration.py
                   │           ├──── webhook.py
                   │           ├──── notification.py
                   │           ├──── audit_log.py
                   │           ├──── questionnaire.py
                   │           └──── trust_center.py
                   │
                   └──────────► pydantic_settings.BaseSettings
```

### Service Layer Dependencies

```python
# auth_service.py dependencies
├── bcrypt (password hashing)
├── PyJWT (token encoding/decoding)
├── redis.asyncio (token storage)
└── sqlalchemy (user lookup)

# llm_service.py dependencies
├── httpx (HTTP client)
├── app.config (settings)
└── app.services.llm_providers (provider configs)

# scheduler.py dependencies
├── APScheduler (job scheduling)
├── sqlalchemy (DB access)
└── app.services.integrations (provider registry)

# webhook_service.py dependencies
├── httpx (HTTP client)
├── hmac, hashlib (signing)
└── sqlalchemy (log storage)
```

---

## 8. Key Data Flows

### Answer Generation Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     ANSWER GENERATION FLOW                                    │
│                                                                              │
│  ┌──────────┐    POST /api/v1/answers                    ┌──────────────┐  │
│  │  Client  │ ──► {questions: [...], use_llm: true} ─────►│  Router      │  │
│  └──────────┘                                             └──────┬───────┘  │
│                                                                 │           │
│                                                                 ▼           │
│  ┌─────────────────────────────────────────────────────────────┴───────┐   │
│  │                      ANSWERS ROUTER                                │   │
│  │                                                                       │   │
│  │  1. Validate questions array                                       │   │
│  │  2. Query EvidenceRecord by org_id                                  │   │
│  │  3. Convert to EvidenceChunk[]                                      │   │
│  │  4. Initialize AI Engine                                            │   │
│  │  5. Index evidence chunks                                          │   │
│  │  6. For each question:                                             │   │
│  │     a. Search evidence (semantic or BM25)                          │   │
│  │     b. Compute confidence                                          │   │
│  │     c. Build citations & freshness                                  │   │
│  │     d. If use_llm && LLM configured:                               │   │
│  │        - Build evidence context                                     │   │
│  │        - Call LLM Service                                          │   │
│  │     e. Else:                                                       │   │
│  │        - Generate synthetic answer (rule-based)                      │   │
│  │  7. Create AnswerGeneration record                                  │   │
│  │  8. Create Answer records                                           │   │
│  │  9. Create AuditLog                                                │   │
│  │  10. Commit transaction                                             │   │
│  └─────────────────────────────────────────────────────────────────────────┘  │
│                                    │                                          │
│                                    ▼                                          │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                          AI ENGINE                                    │   │
│  │                                                                       │   │
│  │  ┌─────────────────┐    ┌─────────────────┐                           │   │
│  │  │ Sentence        │    │ BM25 Fallback   │                           │   │
│  │  │ Transformers    │    │ (if embeddings  │                           │   │
│  │  │ (preferred)     │    │  unavailable)   │                           │   │
│  │  │                 │    │                 │                           │   │
│  │  │ - Embed query   │    │ - Tokenize      │                           │   │
│  │  │ - Cosine sim    │    │ - IDF weighting │                           │   │
│  │  │ - Semantic match│    │ - Score docs    │                           │   │
│  │  └────────┬────────┘    └────────┬────────┘                           │   │
│  │           │                       │                                    │   │
│  │           └───────────┬───────────┘                                    │   │
│  │                       ▼                                                │   │
│  │              ┌─────────────────┐                                       │   │
│  │              │ RetrievalResult[]│                                      │   │
│  │              │ - evidence_id   │                                      │   │
│  │              │ - score         │                                      │   │
│  │              │ - rank          │                                      │   │
│  │              └────────┬─────────┘                                       │   │
│  │                       │                                                │   │
│  │                       ▼                                                │   │
│  │              ┌─────────────────┐    ┌─────────────────┐              │   │
│  │              │  Confidence      │───►│  Answer         │              │   │
│  │              │  Scoring        │    │  Synthesis      │              │   │
│  │              │                 │    │                 │              │   │
│  │              │ high: score>=10│    │ - Citations     │              │   │
│  │              │ medium: 5-10    │    │ - Freshness     │              │   │
│  │              │ low: <5          │    │ - Answer text   │              │   │
│  │              └─────────────────┘    └────────┬─────────┘              │   │
│  └──────────────────────────────────────────────────│──────────────────────┘  │
│                                                      │                       │
│                                                      ▼                       │
│  ┌──────────┐    AnswerGenerationResponse            ┌──────────────┐       │
│  │  Client  │ ◄─────────────────────────────────────│  Router      │       │
│  └──────────┘                                        └──────────────┘       │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Evidence Import Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        EVIDENCE IMPORT FLOW                                  │
│                                                                              │
│  POST /api/v1/evidence/import                                               │
│  Body: {records: [{title, type, frameworks, ...}, ...]}                    │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │  1. Validate payload structure                                          ││
│  │  2. Get existing evidence IDs for org                                  ││
│  │  3. For each incoming record:                                          ││
│  │     - Normalize fields (trim, lowercase, etc.)                         ││
│  │     - Handle ID conflicts (append suffix)                               ││
│  │     - Create EvidenceRecord                                             ││
│  │  4. Commit transaction                                                 ││
│  │  5. Return created records                                             ││
│  └─────────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────────┘
```

### Trust Center Chat Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      TRUST CENTER CHAT FLOW                                  │
│                                                                              │
│  POST /api/v1/public/trust-center/{org_slug}/chat                          │
│  Body: {question: "..."}                                                   │
│  Auth: None required                                                        │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │  1. Lookup org by slug                                                  ││
│  │  2. Verify Trust Center enabled                                         ││
│  │  3. Record visit (TrustCenterVisit)                                     ││
│  │  4. Search knowledge base (approved answers)                             ││
│  │  5. If KB hit: return cached answer                                    ││
│  │  6. Else:                                                               ││
│  │     - Index org's evidence                                              ││
│  │     - Search evidence                                                   ││
│  │     - Generate synthetic answer                                         ││
│  │  7. Return response                                                     ││
│  └─────────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 9. Frontend Architecture

### Component Hierarchy

```
App.tsx
├── BrowserRouter
│   ├── AuthProvider (Context)
│   │   └── useAuth Hook
│   │
│   └── Routes
│       │
│       ├── /login ──────────► LoginPage
│       ├── /register ────────► RegisterPage
│       ├── / ────────────────► LandingPage (if no auth)
│       │                       └── Navigate to /app/dashboard (if authed)
│       │
│       ├── /app (ProtectedRoute)
│       │   └── ProtectedLayoutWithOnboarding
│       │       ├── AppLayout
│       │       │   ├── AppSidebar
│       │       │   └── Outlet
│       │       │
│       │       └── OnboardingWizard (modal)
│       │           │
│       │           └── Routes (nested)
│       │               ├── /dashboard ────► DashboardPage
│       │               ├── /answers ──────► AnswersPage
│       │               ├── /evidence ─────► EvidencePage
│       │               ├── /policies ────► PoliciesPage
│       │               ├── /pentests ─────► PentestsPage
│       │               ├── /settings ─────► SettingsPage
│       │               └── /trust-center ─► TrustCenterAdmin
│       │
│       ├── /trust/{orgSlug} ──► PublicTrustCenter
│       │                         (No auth required)
│       │
│       └── * ─────────────────► NotFoundPage
```

### API Client Architecture

```typescript
// axios instance with interceptors
api = axios.create({ baseURL: "" })

// Request interceptor: attach token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token")
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// Response interceptor: handle 401 & refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401 && !originalRequest._retry) {
      // Queue failed requests
      // Attempt token refresh
      // Retry queued requests
    }
    return Promise.reject(error)
  }
)
```

### State Management

| State | Location | Management |
|-------|----------|------------|
| Auth | `useAuth` hook | React Context + localStorage |
| API Data | Page components | React Query (TanStack Query) |
| UI State | Components | Local useState |

### Key Dependencies

| Package | Purpose |
|---------|---------|
| react-router-dom | Routing |
| @tanstack/react-query | Server state, caching |
| axios | HTTP client |
| react-hook-form | Form management |
| zod | Schema validation |
| @radix-ui/* | UI primitives |
| tailwindcss | Styling |
| lucide-react | Icons |

---

## Appendix: Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | postgresql://... | PostgreSQL connection string |
| `REDIS_URL` | redis://... | Redis connection string |
| `SECRET_KEY` | - | JWT signing key |
| `JWT_PRIVATE_KEY_PATH` | - | RSA private key path |
| `JWT_PUBLIC_KEY_PATH` | - | RSA public key path |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | 30 | Access token TTL |
| `REFRESH_TOKEN_EXPIRE_DAYS` | 7 | Refresh token TTL |
| `CORS_ORIGINS` | http://localhost:5173 | Allowed origins |
| `LLM_API_KEY` | - | LLM provider API key |
| `LLM_PROVIDER` | openai | LLM provider name |
| `LLM_MODEL` | gpt-4o-mini | Model name |
| `VANTA_API_KEY` | - | Vanta API key |
| `VANTA_INTEGRATION_MODE` | mock | Vanta mode (mock/live) |
| `SENTRY_DSN` | - | Sentry error tracking |
| `ENVIRONMENT` | development | Environment label |

---

*Document generated: Tue May 26 2026*
*Project: Verity Trust Copilot v0.2.0*
