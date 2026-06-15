# Verity Trust Copilot - Dataflow Diagrams

## Table of Contents
1. [Level 0: Context Diagram](#level-0-context-diagram)
2. [Level 1: Major Processes](#level-1-major-processes)
3. [Level 2: Core Answer Generation Pipeline](#level-2-core-answer-generation-pipeline)
4. [Level 2: Authentication & Token Lifecycle](#level-2-authentication--token-lifecycle)
5. [Level 2: Background Scheduler & Integration Flow](#level-2-background-scheduler--integration-flow)
6. [Level 2: Trust Center (Public) Flow](#level-2-trust-center-public-flow)
7. [Level 2: Webhook Dispatch Flow](#level-2-webhook-dispatch-flow)
8. [Level 2: Redis & Cache Flow](#level-2-redis--cache-flow)
9. [Data Store Summary](#data-store-summary)
10. [External Service Summary](#external-service-summary)

---

## Level 0: Context Diagram

```
                        ┌─────────────────────┐
                        │   External LLM       │
                        │   Providers          │
                        │  (OpenAI, Anthropic, │
                        │   Google, Ollama)    │
                        └──────────┬──────────┘
                                   │ completions
                                   │ (outbound HTTP)
┌──────────────┐                   │
│  Frontend    │───────────────────┼───────────────────────────────────┐
│  React SPA   │  HTTPS (REST API) │                                   │
│  (TypeScript)│                   │                                   │
└──────────────┘                   ▼                                   │
                          ┌────────────────────┐                       │
┌──────────────┐          │   Verity Backend    │                       │
│  Public      │──────────│   FastAPI +         │                       │
│  Trust Center│  HTTPS   │   APScheduler       │                       │
│  Visitors    │  (no auth)│                    │                       │
└──────────────┘          └────────┬───────────┘                       │
                                   │                                   │
                         ┌─────────┼─────────┐                         │
                         │         │         │                         │
                         ▼         ▼         ▼                         ▼
                  ┌──────────┐ ┌────────┐ ┌────────┐ ┌──────────────────────┐
                  │PostgreSQL│ │ Redis  │ │ AWS    │ │ GitHub API           │
                  │ 16       │ │ 7      │ │ APIs   │ │ (repos, Dependabot)  │
                  │(asyncpg) │ │(cache/ │ │(IAM,   │ └──────────────────────┘
                  └──────────┘ │tokens) │ │ S3,    │
                               └────────┘ │ EC2,   │
                                          │Trail)  │
                                          └────────┘
```

---

## Level 1: Major Processes

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         VERITY TRUST COPILOT                                │
│                                                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                  │
│  │   P1: Auth   │───▶│  P2: Core    │───▶│  P3: Evidence│                  │
│  │   Service    │    │  Domain      │    │  Service     │                  │
│  │              │    │  (Answers,   │    │              │                  │
│  │  JWT/RBAC    │    │  Approvals,  │    │  CRUD, Bulk  │                  │
│  │  Token mgmt  │    │  Questionnaires)  │  Import,     │                  │
│  └──────┬───────┘    └──────┬───────┘    │  Vanta Sync  │                  │
│         │                   │            └──────┬───────┘                  │
│         ▼                   ▼                   ▼                          │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                  │
│  │   P4: Org    │    │  P5: AI      │    │  P6: Search  │                  │
│  │   Management │    │  Engine      │    │  Service     │                  │
│  │              │    │              │    │              │                  │
│  │  Members,    │    │  LLM calls,  │    │  Semantic    │                  │
│  │  Branding,   │    │  Prompt      │    │  (transformers)                 │
│  │  Licensing   │    │  Builder     │    │  BM25 fallback│                 │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘                  │
│         │                   │                   │                          │
│         ▼                   ▼                   ▼                          │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                  │
│  │   P7: Report │    │  P8: Trust   │    │  P9:         │                  │
│  │   Generator  │    │  Center      │    │  Integrations│                  │
│  │              │    │              │    │              │                  │
│  │  SOC2, Audit │    │  Public Chat │    │  AWS, GitHub │                  │
│  │  Package     │    │  Documents   │    │  Scheduler   │                  │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘                  │
│         │                   │                   │                          │
│         ▼                   ▼                   ▼                          │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                  │
│  │   P10:       │    │  P11:        │    │  P12:        │                  │
│  │  Export      │    │  Webhook     │    │  Notification│                  │
│  │              │    │  Dispatch    │    │  Service     │                  │
│  │  MD,CSV,     │    │              │    │              │                  │
│  │  XLSX,DOCX   │    │  HMAC-signed │    │  CRUD,       │                  │
│  │              │    │  HTTP POST   │    │  read/unread │                  │
│  └──────────────┘    └──────────────┘    └──────────────┘                  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Level 2: Core Answer Generation Pipeline

This is the most critical dataflow in the system — the AI-powered answer generation pipeline.

```
                         ┌─────────────────────────────────────┐
                         │     ANSWER GENERATION PIPELINE       │
                         └─────────────────────────────────────┘

POST /api/v1/answers
  │
  ▼
┌─────────────────────────────────────────────────────────────┐
│  Step 1: Receive & Validate                                  │
│  {questions[], as_of?, questionnaire_id?, use_llm?}         │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│  Step 2: Fetch Evidence                                      │
│  SELECT * FROM evidence_records WHERE org_id = :org_id      │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│  Step 3: Convert to EvidenceChunk[]                          │
│  Flatten: title + snippet + summary + frameworks + control_ids│
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│  Step 4: Index Evidence (AIEngine.index_evidence)            │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ If sentence-transformers available:                     │ │
│  │   encode(chunks) → 384-dim vectors (all-MiniLM-L6-v2) │ │
│  │ Else: skip (BM25 fallback)                             │ │
│  └────────────────────────────────────────────────────────┘ │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│  Step 5: For Each Question ─────────────────────────────────►│
│                                                             │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ 5a: SEARCH (AIEngine.search)                           │ │
│  │    Semantic: cosine(query_vec, evidence_vecs) → top_k  │ │
│  │    BM25: tokenize → expand(synonyms) → score → rank    │ │
│  │    Returns: [{chunk, score, rank}]                     │ │
│  └──────────────────────────┬─────────────────────────────┘ │
│                             │                               │
│  ┌──────────────────────────▼─────────────────────────────┐ │
│  │ 5b: CONFIDENCE (AIEngine.compute_confidence)           │ │
│  │    Semantic: high(≥0.7,≥2), medium(≥0.5), low(<0.5)   │ │
│  │    BM25: high(≥10,≥2), medium(≥5), low(<5)            │ │
│  └──────────────────────────┬─────────────────────────────┘ │
│                             │                               │
│  ┌──────────────────────────▼─────────────────────────────┐ │
│  │ 5c: CITATIONS (build_citations)                        │ │
│  │    [{source_id, title, snippet, score, last_reviewed}] │ │
│  └──────────────────────────┬─────────────────────────────┘ │
│                             │                               │
│  ┌──────────────────────────▼─────────────────────────────┐ │
│  │ 5d: FRESHNESS (build_freshness)                        │ │
│  │    [{source, status: fresh/stale/outdated, age_days}]  │ │
│  └──────────────────────────┬─────────────────────────────┘ │
│                             │                               │
│  ┌──────────────────────────▼─────────────────────────────┐ │
│  │ 5e: LLM ANSWER (if use_llm && configured)             │ │
│  │    ┌─────────────────────────────────────────────────┐ │ │
│  │    │ build_evidence_context(results)                 │ │ │
│  │    │ → {title, type, frameworks, summary, snippets}  │ │ │
│  │    └──────────────────────┬──────────────────────────┘ │ │
│  │                           │                            │ │
│  │    ┌──────────────────────▼──────────────────────────┐ │ │
│  │    │ generate_llm_answer()                           │ │ │
│  │    │ SYSTEM_PROMPT + user_prompt(evidence_context)   │ │ │
│  │    │         │                                       │ │ │
│  │    │         ▼                                       │ │ │
│  │    │ ┌─────────────────────────────────────────────┐ │ │ │
│  │    │ │ Provider Router:                            │ │ │ │
│  │    │ │  OpenAI:  POST {base}/chat/completions      │ │ │ │
│  │    │ │  Anthropic: POST {base}/messages             │ │ │ │
│  │    │ │  Google:  POST {base}/models/{m}:generate   │ │ │ │
│  │    │ │  Ollama:  POST {base}/api/chat              │ │ │ │
│  │    │ └─────────────────────────────────────────────┘ │ │ │
│  │    │ Returns: {answer_text, model, usage}           │ │ │
│  │    └────────────────────────────────────────────────┘ │ │
│  │                                                       │ │
│  │    If LLM fails → fall through to 5f                  │ │
│  └──────────────────────────┬─────────────────────────────┘ │
│                             │                               │
│  ┌──────────────────────────▼─────────────────────────────┐ │
│  │ 5f: SYNTHETIC ANSWER (fallback)                        │ │
│  │    Concatenate snippets with citation markers          │ │
│  │    [S1:evidence_id] snippet text...                    │ │
│  └──────────────────────────┬─────────────────────────────┘ │
│                             │                               │
│                             ▼                               │
│           Answer {question, answer_text, confidence,        │
│                  citations[], freshness[], source}           │
│                                                             │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│  Step 6: Persist Results                                     │
│  INSERT INTO answer_generations (org_id, as_of_date,        │
│    confidence_counts, questionnaire_id, engine_used)        │
│  INSERT INTO answers (generation_id, question, answer_text, │
│    confidence, citations, freshness, source, order_index)   │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│  Step 7: Audit Log                                           │
│  INSERT INTO audit_logs (resource_type="answers",           │
│    action="generate", changes={count, engine, llm_used})    │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│  Step 8: Update Questionnaire (if questionnaire_id)          │
│  UPDATE questionnaires SET answered_count=N, status='in_progress'│
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
                    AnswerGenerationResponse
                    {id, answers[], confidence_counts}
```

---

## Level 2: Authentication & Token Lifecycle

```
┌─────────────────────────────────────────────────────────────────┐
│                  AUTHENTICATION FLOW                             │
└─────────────────────────────────────────────────────────────────┘

     POST /register                         POST /login
     {email,password,name,org}              {email,password}
          │                                       │
          ▼                                       ▼
   ┌──────────────┐                      ┌──────────────┐
   │ Validate      │                      │ Verify       │
   │ uniqueness    │                      │ bcrypt hash  │
   └──────┬───────┘                      └──────┬───────┘
          │                                       │
          ▼                                       ▼
   ┌──────────────┐                      ┌──────────────┐
   │ Create Org   │                      │ Lookup User  │
   │ Create User  │                      │ + Org        │
   │ (role=admin) │                      └──────┬───────┘
   └──────┬───────┘                             │
          │                                      │
          └──────────────┬───────────────────────┘
                         │
                         ▼
              ┌─────────────────────┐
              │ Generate JWT        │
              │ ┌─────────────────┐ │
              │ │ Access Token    │ │  HS256, 30min TTL
              │ │ {user_id, org,  │ │
              │ │  role, jti,exp} │ │
              │ └─────────────────┘ │
              │ ┌─────────────────┐ │
              │ │ Refresh Token   │ │  HS256, 7 day TTL
              │ │ {user_id, jti,  │ │
              │ │  type:"refresh"}│ │
              │ └─────────────────┘ │
              └──────────┬──────────┘
                         │
                         ▼
              ┌─────────────────────┐
              │ Redis Storage       │
              │ SET rt:{uid}:{jti}  │  Refresh token family
              │ TTL: 7 days         │
              └─────────────────────┘

     POST /refresh                           POST /logout
     {refresh_token}                         Bearer {token}
          │                                       │
          ▼                                       ▼
   ┌──────────────┐                      ┌──────────────┐
   │ Decode JWT   │                      │ Decode JWT   │
   │ type=refresh │                      │ Extract jti  │
   └──────┬───────┘                      └──────┬───────┘
          │                                       │
          ▼                                       ▼
   ┌──────────────┐                      ┌──────────────┐
   │ Check Redis  │                      │ SET bl:{jti} │
   │ rt:{uid}:{jti│                      │ TTL: 30min   │
   │ exists?      │                      │ (blacklist)  │
   └──────┬───────┘                      └──────────────┘
          │
          ▼
   ┌──────────────┐
   │ Generate new │
   │ access+refresh│
   │ Delete old rt│
   │ Store new rt │
   └──────────────┘


REQUEST AUTHORIZATION (deps.py):
────────────────────────────────
  Request
    │
    ▼
  HTTPBearer → extract token
    │
    ▼
  decode_token(token)
    │
    ▼
  _is_token_blacklisted(jti)?  ──YES──▶ 401 Unauthorized
    │
    NO
    ▼
  get_user_from_db(user_id)
    │
    ▼
  ┌───────────────────────────┐
  │ get_current_user()        │ → User object
  │ get_current_active_user() │ → check is_active
  │ require_role("admin")     │ → check role ∈ ["admin"]
  │ require_role("editor")    │ → check role ∈ ["admin","editor"]
  └───────────────────────────┘
```

---

## Level 2: Background Scheduler & Integration Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│              BACKGROUND SCHEDULER & INTEGRATION FLOW                 │
└─────────────────────────────────────────────────────────────────────┘

APP STARTUP (lifespan)
    │
    ▼
┌─────────────────────────────────────────────────────────────────────┐
│ APScheduler.start()                                                  │
│ add_job(_run_all_integrations, trigger="interval", hours=1)         │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
              ┌────────────────┘ (every 1 hour)
              │
              ▼
┌─────────────────────────────────────────────────────────────────────┐
│  _run_all_integrations()                                            │
│  SELECT * FROM integrations WHERE enabled = true                    │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
              ┌────────────────┴────────────────┐
              ▼                                 ▼
    ┌──────────────────┐              ┌──────────────────┐
    │ AWS Integration  │              │ GitHub Integration│
    │ provider         │              │ provider          │
    └────────┬─────────┘              └────────┬─────────┘
             │                                  │
             ▼                                  ▼
    ┌──────────────────┐              ┌──────────────────┐
    │ STS:             │              │ GET /user        │
    │ get_caller_identity│            │ (test auth)      │
    └────────┬─────────┘              └────────┬─────────┘
             │                                  │
             ▼                                  ▼
    ┌──────────────────────────────────────────────────────────────┐
    │ run_all_tests()                                               │
    │                                                               │
    │ AWS Tests:                         GitHub Tests:              │
    │ ├─ IAM Users Have MFA             ├─ Branch Protected        │
    │ ├─ No Root Access Keys            ├─ No Public Repos         │
    │ ├─ S3 Encrypted                   └─ Dependabot Enabled      │
    │ ├─ S3 Not Public                                               │
    │ ├─ Security Groups No Open                                     │
    │ └─ CloudTrail Enabled                                          │
    └──────────────────────────────┬────────────────────────────────┘
                                   │
                                   ▼
    ┌──────────────────────────────────────────────────────────────┐
    │ For each test result:                                         │
    │                                                               │
    │  1. Match to ComplianceTest (by test_name)                    │
    │     └─ Create new ComplianceTest if not exists                │
    │                                                               │
    │  2. INSERT INTO test_results                                  │
    │     (org_id, test_id, integration_id, status, evidence,      │
    │      message, resources_checked, resources_failed)            │
    │                                                               │
    │  3. UPDATE integrations                                       │
    │     SET last_status=healthy|degraded|error,                   │
    │         last_run_at=now, last_error=null|msg                  │
    └──────────────────────────────┬────────────────────────────────┘
                                   │
                                   ▼
                          Commit to PostgreSQL
```

---

## Level 2: Trust Center (Public) Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                 PUBLIC TRUST CENTER FLOW (No Auth)                   │
└─────────────────────────────────────────────────────────────────────┘

  Visitor Browser
        │
        │ GET /api/v1/public/trust-center/{org_slug}
        ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Lookup org by slug                                                 │
│  SELECT * FROM organizations WHERE slug = :slug                    │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Check settings.enabled                                            │
│  SELECT * FROM trust_center_settings WHERE org_id = :org_id       │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
              ┌────────────────┴────────────────┐
              │ enabled=false                   │ enabled=true
              ▼                                 ▼
        404 Not Found              ┌─────────────────────────────────┐
                                   │ Record Visit                    │
                                   │ INSERT INTO trust_center_visits │
                                   │ (org_id, visitor_ip, page,      │
                                   │  referrer, user_agent)          │
                                   └────────────┬────────────────────┘
                                                │
                                                ▼
                                   ┌─────────────────────────────────┐
                                   │ Fetch Public Data               │
                                   │                                 │
                                   │ Certifications:                 │
                                   │  WHERE type='certification'     │
                                   │                                 │
                                   │ Active Policies:                │
                                   │  WHERE status='active'          │
                                   │                                 │
                                   │ Public Documents:               │
                                   │  WHERE is_public=true           │
                                   └────────────┬────────────────────┘
                                                │
                                                ▼
                                      PublicTCData Response


  POST /api/v1/public/trust-center/{org_slug}/chat
  {question}
        │
        ▼
┌─────────────────────────────────────────────────────────────────────┐
│  1. Record visit (chatbot_queries++)                                │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│  2. Search Knowledge Base (in-memory)                              │
│     encode(question) → cosine(query_vec, kb_embeddings)            │
│     threshold >= 0.5 → top 3 results                               │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
              ┌────────────────┴────────────────┐
              │ KB match found                  │ No KB match
              ▼                                 ▼
     Return KB answer              ┌─────────────────────────────────┐
     source="knowledge_base"       │ 3. Search Evidence              │
                                   │    fetch org evidence           │
                                   │    index_evidence(chunks)       │
                                   │    semantic_search(question)    │
                                   └────────────┬────────────────────┘
                                                │
                                   ┌────────────┴────────────┐
                                   │ evidence found          │ no evidence
                                   ▼                         ▼
                          ┌────────────────┐       ┌────────────────┐
                          │ 4. Generate    │       │ Fallback:      │
                          │ synthetic ans  │       │ "Please contact│
                          │ from snippets  │       │  support..."   │
                          └───────┬────────┘       └───────┬────────┘
                                  │                         │
                                  └────────────┬────────────┘
                                               ▼
                                    ChatAnswer Response
                                    {answer, source, confidence}
```

---

## Level 2: Webhook Dispatch Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                    WEBHOOK DISPATCH FLOW                             │
└─────────────────────────────────────────────────────────────────────┘

Internal Event Trigger
(approved/rejected/failed/stale/completed/etc.)
        │
        ▼
┌─────────────────────────────────────────────────────────────────────┐
│ dispatch_webhook(db, org_id, event, payload)                        │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 1. Validate event ∈ WEBHOOK_EVENTS                                 │
│    Events: answer.approved, answer.rejected, answer.created,       │
│            evidence.created, evidence.updated, evidence.stale,     │
│            integration.failed, integration.recovered,              │
│            policy.review_due, questionnaire.completed              │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 2. Query active webhooks for org                                   │
│    SELECT * FROM webhooks WHERE org_id=:org AND is_active=true     │
│    AND events CONTAINS :event                                      │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
              ┌────────────────┴────────────────┐
              ▼                                 ▼
    ┌──────────────────┐              ┌──────────────────┐
    │ Webhook A        │              │ Webhook B        │
    │ subscribed to    │              │ subscribed to    │
    │ this event       │              │ this event       │
    └────────┬─────────┘              └────────┬─────────┘
             │                                  │
             ▼                                  ▼
    ┌──────────────────────────────────────────────────────────────┐
    │ For each webhook:                                             │
    │                                                               │
    │ 3a. Build body: {event, payload}                             │
    │                                                               │
    │ 3b. Build headers:                                            │
    │     Content-Type: application/json                            │
    │     X-Webhook-Event: {event}                                  │
    │     X-Webhook-ID: {webhook_id}                                │
    │     + custom_headers (if any)                                 │
    │                                                               │
    │ 3c. HMAC-SHA256 signature:                                    │
    │     signature = HMAC(secret, body_json)                       │
    │     X-Webhook-Signature: sha256={hex(signature)}              │
    │                                                               │
    │ 3d. INSERT INTO webhook_logs (pending)                        │
    │                                                               │
    │ 3e. HTTP POST webhook.url (10s timeout)                       │
    │     ┌─────────────────────────────────────────────────────┐   │
    │     │ Success: log response_status, response_body         │   │
    │     │ Timeout: log "Request timed out"                     │   │
    │     │ Error:   log error message                           │   │
    │     └─────────────────────────────────────────────────────┘   │
    │                                                               │
    │ 3f. UPDATE webhook_logs SET success=T/F, response_status=N    │
    └──────────────────────────────────────────────────────────────┘
```

---

## Level 2: Redis & Cache Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                    REDIS & CACHE FLOW                                │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│ KEY PATTERNS                                                        │
│                                                                     │
│ ┌─────────────────────────────────────────────────────────────────┐ │
│ │ bl:{jti}            Blacklisted JWT (30min TTL)                 │ │
│ │ rt:{user_id}:{jti}  Refresh token family (7 day TTL)           │ │
│ │ cache:{key}         Generic cache (300s default TTL)            │ │
│ └─────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘

Auth Service:
─────────────
  login/register
      │
      ▼
  SET rt:{user_id}:{jti} = "1"  ──── 7 day TTL
      │
      ▼
  refresh()
      │
      ▼
  SCAN rt:{user_id}:*  ──── delete all except current
  SET rt:{user_id}:{new_jti} = "1"  ──── 7 day TTL
      │
      ▼
  logout()
      │
      ▼
  SET bl:{jti} = "1"  ──── 30min TTL


Cache Service:
──────────────
  cache_get(key)
      │
      ▼
  GET cache:{key}  ──── hit? → JSON parse → return value
      │                  miss? → return None
      ▼
  cache_set(key, value, ttl=300)
      │
      ▼
  SETEX cache:{key} TTL (JSON serialize value)

  cache_invalidate(pattern)
      │
      ▼
  SCAN cache:{pattern}*  ──── DELETE matching keys
```

---

## Data Store Summary

| Store | Purpose | Access Pattern |
|-------|---------|---------------|
| **PostgreSQL** | Primary data (19 tables) | Async via asyncpg/SQLAlchemy |
| **Redis** | Token blacklist, refresh tokens, cache | async redis.io |
| **In-memory (AIEngine)** | Knowledge base embeddings | Sentence-transformers vectors |

---

## External Service Summary

| Service | Protocol | Auth | Purpose |
|---------|----------|------|---------|
| LLM Providers | HTTP REST | API key | Answer generation |
| AWS (IAM/S3/EC2/CloudTrail) | boto3 | Access key/secret | Compliance checks |
| GitHub API | HTTP REST | Personal access token | Repo/Dependabot checks |
| Vanta API | HTTP REST | API key | Evidence sync |
| Sentry | HTTP | DSN | Error tracking |
