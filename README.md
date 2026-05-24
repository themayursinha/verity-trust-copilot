# Security Questionnaire Copilot

A small local Python prototype for drafting enterprise security-questionnaire answers from a trusted evidence knowledge base.

The goal is to reduce sales friction without creating unsupported security claims. The copilot retrieves approved evidence, drafts answers only from matched snippets, adds citations, checks evidence freshness, and marks weak answers for human review.

## Quick Start

Run the web UI:

```bash
python3 web_app.py
```

Then open:

```text
http://127.0.0.1:8000
```

The UI loads sample questions, generates cited draft answers, shows confidence and freshness checks, and writes the same artifacts to `outputs/`.
It also lets you store evidence manually, upload evidence JSON, approve/reject answers, and export as CSV, JSON, or customer-ready markdown.

Additional tools are available from the top navigation bar:

| Page | Route | Purpose |
|------|-------|---------|
| **Dashboard** | `/static/dashboard.html` | Framework coverage, evidence/policy/approval stats, activity log, Vanta sync |
| **Policies** | `/static/policies.html` | Create, version, and schedule review of security policies |
| **Pentests** | `/static/pentests.html` | Track penetration testing engagements and findings |

Run the CLI:

```bash
python3 security_questionnaire_copilot.py --as-of 2026-05-21
```

Outputs:

- `outputs/answers.json` for machine-readable answers.
- `outputs/report.md` for a reviewer-friendly questionnaire report.

You can pass your own JSON question list:

```bash
python3 security_questionnaire_copilot.py \
  --questions data/questions.json \
  --evidence evidence/evidence.json \
  --output-dir outputs
```

## Project Structure

```text
.
├── data/
│   └── questions.json              # Sample security questions
├── evidence/
│   └── evidence.json               # Approved evidence library
├── templates/
│   └── answer_templates.json       # 11 answer template categories
├── outputs/                        # Generated answers, reports, approvals
├── static/
│   ├── index.html                  # Main copilot UI
│   ├── dashboard.html              # Compliance dashboard
│   ├── policies.html               # Policy center
│   ├── pentests.html               # Pentest tracker
│   ├── app.js
│   ├── dashboard.js
│   ├── policies.js
│   ├── pentests.js
│   ├── styles.css
│   └── evidence_quality.js
├── security_questionnaire_copilot.py
├── web_app.py
└── README.md
```

## Architecture

1. Evidence records live in `evidence/evidence.json`.
   Each record includes a title, type, frameworks, control IDs, owner, `last_reviewed` date, summary, and approved snippets.

2. Customer questions live in `data/questions.json`.
   The script accepts either a JSON list or an object with a `questions` array.

3. Retrieval uses field-weighted BM25 scoring.
   Titles, frameworks, and control IDs receive higher weight than raw snippet text. TF saturation (k1=1.5) prevents keyword spam from dominating. IDF uses `log(1 + (N - df + 0.5) / (df + 0.5))` for smoother rare-term boosts. Outdated evidence (≥365 days) is penalized.

4. Answer templates improve relevance.
   11 category definitions (encryption, gdpr, iso-27001, etc.) match against question keywords. When a template matches (≥2 keywords), the answer is structured with the template's suggested framing, caveats, and review guidance.

5. Answer drafting is extractive and conservative.
   The script builds draft answers from the matched evidence snippets and attaches citations such as `[S1:encryption-and-key-management]`.

6. Confidence and review workflow.
   Answers are marked `high`, `medium`, or `low`. Low-confidence answers are labeled `needs_human_review: true` and warn the user not to send unsupported claims. Reviewers can approve or reject each answer with notes.

7. Freshness checks.
   Evidence reviewed within 180 days is `fresh`, within 365 days is `stale`, and older evidence is `outdated`.

8. Local web UI with four tools.
   `web_app.py` uses Python's standard-library HTTP server to serve `static/` and expose local JSON endpoints. It does not call external APIs and does not require a frontend build step. The top navigation links to the answer generator, compliance dashboard, policy center, and pentest tracker.

## Core Features

- Upload or store security evidence documents locally in `evidence/evidence.json`.
- Ask one or more customer security questions.
- Retrieve relevant evidence with field-weighted BM25 scoring.
- Match question keywords against 11 answer template categories.
- Generate draft answers only from matched evidence with template-aware framing.
- Show citations and source snippets for every answer.
- Add high, medium, or low confidence scoring with freshness penalties.
- Flag low-confidence answers for human review.
- Approve or reject each answer with reviewer name and notes (persisted to `outputs/approvals.json`).
- Export answers as CSV, JSON, or customer-ready markdown.
- **Compliance Dashboard** — framework coverage bars (ISO 27001, SOC 2, GDPR, DORA), evidence freshness stats, policy summary, approval counts, recent activity log.
- **Policy Center** — create, version, schedule reviews for security policies.
- **Penetration Testing Tracker** — manage engagements and per-finding details (severity, status, assignee, remediation).
- **Vanta Integration** — connect your Vanta API key and sync evidence automatically into the local library.

## Included Evidence Areas

The sample knowledge base includes evidence for:

- ISO 27001 ISMS alignment
- GDPR privacy and processor controls
- DORA ICT and operational resilience mapping
- Vanta control evidence
- Encryption and key management
- Meeting data retention and deletion
- AI data usage and model-training commitments
- Subprocessors and vendor review
- Access control and offboarding
- Incident response and breach assessment
- External penetration testing
- Unsupported claims such as FedRAMP and HIPAA

## Security Considerations

- No external APIs are used, so questionnaire content and evidence stay local.
- The prototype only drafts from approved snippets and cites every source used.
- Unsupported topics are intentionally flagged for review instead of being answered creatively.
- Evidence ownership and `last_reviewed` metadata make it easier to route stale or weak answers to Security, Privacy, Legal, or GRC.
- The markdown report is designed for human approval before sending responses to customers.

## How This Reduces Sales Friction

Security questionnaires often block late-stage enterprise deals because teams must repeatedly answer similar questions about encryption, AI data use, subprocessors, access control, incident response, and certifications.

This prototype speeds up the first draft by finding relevant approved evidence and formatting a cited response. Sales and security teams can focus review time on exceptions, stale evidence, or new customer requirements instead of rewriting common answers from scratch.

## How This Prevents Unsupported Claims

The script does not invent missing details. If evidence is absent, weak, or outdated, the answer is marked low confidence and `needs_human_review`.

For example, the sample evidence includes an unsupported-claims register stating that Jamie does not currently have approved evidence for FedRAMP authorization. A FedRAMP question should therefore be handled cautiously instead of producing a false certification claim.

## Limitations

- Keyword scoring (BM25) is still lexical and may miss semantic paraphrases.
- The sample evidence is fictional and should be replaced with real approved Jamie evidence before use.
- The dashboard, policies, and pentest data are local-only (no sync with external GRC platforms beyond Vanta).
- The script does not understand contracts, customer-specific commitments, or regional deployment boundaries unless those are present in evidence.
- Confidence is heuristic and should not be treated as legal or compliance approval.

## Production Improvements

- Use local embeddings or an approved private retrieval model for better semantic matching.
- Add role-based access control and audit logging.
- Track evidence expiry, owners, renewal reminders, and customer-specific answer history.
- Integrate with CRM workflows so Sales can request review without leaving the deal workspace.
- Add contradiction detection when multiple evidence sources disagree.
- Add export formats for additional security questionnaire portals.
