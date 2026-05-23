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
It also lets you store evidence manually, upload evidence JSON, and export a selected answer as customer-ready markdown.

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
├── data/questions.json
├── evidence/evidence.json
├── outputs/answers.json
├── outputs/report.md
├── static/
├── security_questionnaire_copilot.py
├── web_app.py
└── README.md
```

## Architecture

1. Evidence records live in `evidence/evidence.json`.
   Each record includes a title, type, frameworks, control IDs, owner, `last_reviewed` date, summary, and approved snippets.

2. Customer questions live in `data/questions.json`.
   The script accepts either a JSON list or an object with a `questions` array.

3. Retrieval uses local scoring.
   The scorer tokenizes each question, expands a small synonym map, scores keyword overlap against evidence metadata and snippets, applies simple phrase boosts, and slightly penalizes stale or outdated evidence.

4. Answer drafting is extractive and conservative.
   The script builds draft answers from the matched evidence snippets and attaches citations such as `[S1:encryption-and-key-management]`.

5. Confidence and review workflow.
   Answers are marked `high`, `medium`, or `low`. Low-confidence answers are labeled `needs_human_review: true` and warn the user not to send unsupported claims.

6. Freshness checks.
   Evidence reviewed within 180 days is `fresh`, within 365 days is `stale`, and older evidence is `outdated`.

7. Local web UI.
   `web_app.py` uses Python's standard-library HTTP server to serve `static/` and expose local JSON endpoints. It does not call external APIs and does not require a frontend build step.

## Core Features

- Upload or store security evidence documents locally in `evidence/evidence.json`.
- Ask one or more customer security questions.
- Retrieve relevant evidence with simple local scoring.
- Generate draft answers only from matched evidence.
- Show citations and source snippets for every answer.
- Add high, medium, or low confidence scoring.
- Flag low-confidence answers for human review.
- Track stale and outdated evidence using `last_reviewed`.
- Export a selected answer as markdown in `outputs/customer_ready_answer.md`.

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

- Keyword scoring is intentionally simple and may miss paraphrases.
- There is no user interface, approval queue, or audit log.
- The sample evidence is fictional and should be replaced with real approved Jamie evidence before use.
- The script does not understand contracts, customer-specific commitments, or regional deployment boundaries unless those are present in evidence.
- Confidence is heuristic and should not be treated as legal or compliance approval.

## Production Improvements

- Add authenticated evidence ingestion from Vanta, Google Drive, Notion, Jira, and policy repositories.
- Use local embeddings or an approved private retrieval model for better semantic matching.
- Add role-based access control, audit logging, reviewer assignment, and approval states.
- Track evidence expiry, owners, renewal reminders, and customer-specific answer history.
- Add answer templates with Legal-approved wording for common questionnaire categories.
- Integrate with CRM workflows so Sales can request review without leaving the deal workspace.
- Add contradiction detection when multiple evidence sources disagree.
- Add export formats for portals, spreadsheets, and common security questionnaire tools.
