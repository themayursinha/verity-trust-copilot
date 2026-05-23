# Security Questionnaire Copilot Report

Generated: 2026-05-22T11:13:59
Evidence freshness date: 2026-05-22

## Summary

- Questions processed: 10
- High confidence: 7
- Medium confidence: 2
- Low confidence / human review: 1

## Draft Answers

### 1. Are you ISO 27001 certified or aligned, and how do you manage your ISMS?

**Confidence:** high
**Needs human review:** no

Draft answer based on approved evidence: Jamie operates an ISO 27001-aligned ISMS covering risk management, asset inventory, access control, supplier security, incident response, and secure development. [S1:iso-27001-isms] Information security policies are reviewed at least annually and after material business, product, or regulatory changes. [S2:iso-27001-isms] Internal control reviews track findings, remediation owners, due dates, and evidence of closure. [S3:iso-27001-isms] Vanta monitors employee MFA, device encryption, screen lock, antivirus status, security training completion, and offboarding tasks. [S4:vanta-control-evidence]

**Freshness checks:**
- `iso-27001-isms` last reviewed 2026-04-15 (37 days old): fresh
- `iso-27001-isms` last reviewed 2026-04-15 (37 days old): fresh
- `iso-27001-isms` last reviewed 2026-04-15 (37 days old): fresh
- `vanta-control-evidence` last reviewed 2026-05-01 (21 days old): fresh

**Sources:**
- [S1:iso-27001-isms] ISO 27001 Information Security Management System (`iso-27001-isms`, certification, reviewed 2026-04-15)
- [S2:iso-27001-isms] ISO 27001 Information Security Management System (`iso-27001-isms`, certification, reviewed 2026-04-15)
- [S3:iso-27001-isms] ISO 27001 Information Security Management System (`iso-27001-isms`, certification, reviewed 2026-04-15)
- [S4:vanta-control-evidence] Vanta Evidence Export (`vanta-control-evidence`, control-evidence, reviewed 2026-05-01)

### 2. Do you encrypt customer meeting data at rest and in transit?

**Confidence:** high
**Needs human review:** no

Draft answer based on approved evidence: Customer data is encrypted in transit using TLS 1.2 or higher for application, API, and administrative connections. [S1:encryption-and-key-management] Customer data stored in managed databases, object storage, backups, and logs is encrypted at rest using cloud-provider managed encryption. [S2:encryption-and-key-management] Administrative access to encryption and key-management settings is restricted to approved infrastructure administrators and logged. [S3:encryption-and-key-management]

**Freshness checks:**
- `encryption-and-key-management` last reviewed 2026-04-01 (51 days old): fresh
- `encryption-and-key-management` last reviewed 2026-04-01 (51 days old): fresh
- `encryption-and-key-management` last reviewed 2026-04-01 (51 days old): fresh

**Sources:**
- [S1:encryption-and-key-management] Encryption and Key Management Standard (`encryption-and-key-management`, standard, reviewed 2026-04-01)
- [S2:encryption-and-key-management] Encryption and Key Management Standard (`encryption-and-key-management`, standard, reviewed 2026-04-01)
- [S3:encryption-and-key-management] Encryption and Key Management Standard (`encryption-and-key-management`, standard, reviewed 2026-04-01)

### 3. Do you use our meeting transcripts or summaries to train AI models?

**Confidence:** high
**Needs human review:** no

Draft answer based on approved evidence: AI processing controls include access restrictions, purpose limitation, vendor review, and documented handling rules for prompts, transcripts, and generated summaries. [S1:ai-data-usage] Jamie does not use customer meeting content to train third-party foundation models unless the customer has explicitly opted in through a written agreement. [S2:ai-data-usage] Customer meeting content is used to provide and improve the contracted Jamie service according to customer instructions and applicable agreements. [S3:ai-data-usage]

**Freshness checks:**
- `ai-data-usage` last reviewed 2026-04-30 (22 days old): fresh
- `ai-data-usage` last reviewed 2026-04-30 (22 days old): fresh
- `ai-data-usage` last reviewed 2026-04-30 (22 days old): fresh

**Sources:**
- [S1:ai-data-usage] AI Data Usage Commitment (`ai-data-usage`, product-privacy-commitment, reviewed 2026-04-30)
- [S2:ai-data-usage] AI Data Usage Commitment (`ai-data-usage`, product-privacy-commitment, reviewed 2026-04-30)
- [S3:ai-data-usage] AI Data Usage Commitment (`ai-data-usage`, product-privacy-commitment, reviewed 2026-04-30)

### 4. How long do you retain meeting transcripts and can customers request deletion?

**Confidence:** high
**Needs human review:** no

Draft answer based on approved evidence: Meeting transcripts, summaries, and related customer content follow customer-configured retention settings where available. [S1:data-retention-deletion] Deletion requests for customer content are handled through documented support and administrative workflows with completion tracking. [S2:data-retention-deletion] Backups age out according to backup retention schedules; restored data remains subject to the active deletion and retention process. [S3:data-retention-deletion] Jamie acts as a processor for customer meeting content and processes personal data according to customer instructions under a data processing agreement. [S4:gdpr-privacy-program]

**Freshness checks:**
- `data-retention-deletion` last reviewed 2026-01-18 (124 days old): fresh
- `data-retention-deletion` last reviewed 2026-01-18 (124 days old): fresh
- `data-retention-deletion` last reviewed 2026-01-18 (124 days old): fresh
- `gdpr-privacy-program` last reviewed 2026-03-10 (73 days old): fresh

**Sources:**
- [S1:data-retention-deletion] Meeting Data Retention and Deletion Policy (`data-retention-deletion`, policy, reviewed 2026-01-18)
- [S2:data-retention-deletion] Meeting Data Retention and Deletion Policy (`data-retention-deletion`, policy, reviewed 2026-01-18)
- [S3:data-retention-deletion] Meeting Data Retention and Deletion Policy (`data-retention-deletion`, policy, reviewed 2026-01-18)
- [S4:gdpr-privacy-program] GDPR Privacy and Data Protection Program (`gdpr-privacy-program`, policy, reviewed 2026-03-10)

### 5. Do you maintain a list of subprocessors and notify customers about changes?

**Confidence:** medium
**Needs human review:** no

Draft answer based on approved evidence: Jamie maintains a current subprocessor list that identifies hosting, analytics, customer support, and AI infrastructure providers where applicable. [S1:subprocessor-register] Customers are notified of material subprocessor changes according to the data processing agreement. [S2:subprocessor-register] Subprocessors are reviewed before onboarding for security posture, data processing role, transfer mechanism, and contractual commitments. [S3:subprocessor-register] The privacy program includes data minimization, purpose limitation, access restrictions, subprocessor due diligence, and data subject request support. [S4:gdpr-privacy-program]

**Freshness checks:**
- `subprocessor-register` last reviewed 2026-05-05 (17 days old): fresh
- `subprocessor-register` last reviewed 2026-05-05 (17 days old): fresh
- `subprocessor-register` last reviewed 2026-05-05 (17 days old): fresh
- `gdpr-privacy-program` last reviewed 2026-03-10 (73 days old): fresh

**Sources:**
- [S1:subprocessor-register] Subprocessor Register (`subprocessor-register`, register, reviewed 2026-05-05)
- [S2:subprocessor-register] Subprocessor Register (`subprocessor-register`, register, reviewed 2026-05-05)
- [S3:subprocessor-register] Subprocessor Register (`subprocessor-register`, register, reviewed 2026-05-05)
- [S4:gdpr-privacy-program] GDPR Privacy and Data Protection Program (`gdpr-privacy-program`, policy, reviewed 2026-03-10)

### 6. How is employee access to production and customer data controlled?

**Confidence:** high
**Needs human review:** no

Draft answer based on approved evidence: Access is reviewed quarterly for production systems, administrative tools, identity groups, and privileged roles. [S1:access-control] Access reviews are tracked quarterly for production systems, identity provider groups, administrative roles, and customer-data tools. [S2:vanta-control-evidence] Production and customer-data system access requires SSO, MFA, manager approval, and least-privilege role assignment. [S3:access-control] Vanta monitors employee MFA, device encryption, screen lock, antivirus status, security training completion, and offboarding tasks. [S4:vanta-control-evidence]

**Freshness checks:**
- `access-control` last reviewed 2026-03-22 (61 days old): fresh
- `vanta-control-evidence` last reviewed 2026-05-01 (21 days old): fresh
- `access-control` last reviewed 2026-03-22 (61 days old): fresh
- `vanta-control-evidence` last reviewed 2026-05-01 (21 days old): fresh

**Sources:**
- [S1:access-control] Access Control and Joiner-Mover-Leaver Procedure (`access-control`, procedure, reviewed 2026-03-22)
- [S2:vanta-control-evidence] Vanta Evidence Export (`vanta-control-evidence`, control-evidence, reviewed 2026-05-01)
- [S3:access-control] Access Control and Joiner-Mover-Leaver Procedure (`access-control`, procedure, reviewed 2026-03-22)
- [S4:vanta-control-evidence] Vanta Evidence Export (`vanta-control-evidence`, control-evidence, reviewed 2026-05-01)

### 7. What is your incident response process and do you support GDPR breach notification?

**Confidence:** high
**Needs human review:** no

Draft answer based on approved evidence: Potential personal data breaches are assessed for regulatory and customer notification obligations, including GDPR timing requirements where applicable. [S1:incident-response] Security incidents are triaged by severity, assigned an incident owner, and tracked through containment, eradication, recovery, and post-incident review. [S2:incident-response] Incident exercises and tabletop reviews are used to test roles, escalation paths, communication templates, and evidence collection. [S3:incident-response] Technical and organizational measures include encryption, least-privilege access, audit logging, incident response, and retention controls. [S4:gdpr-privacy-program]

**Freshness checks:**
- `incident-response` last reviewed 2026-02-14 (97 days old): fresh
- `incident-response` last reviewed 2026-02-14 (97 days old): fresh
- `incident-response` last reviewed 2026-02-14 (97 days old): fresh
- `gdpr-privacy-program` last reviewed 2026-03-10 (73 days old): fresh

**Sources:**
- [S1:incident-response] Security Incident Response Plan (`incident-response`, plan, reviewed 2026-02-14)
- [S2:incident-response] Security Incident Response Plan (`incident-response`, plan, reviewed 2026-02-14)
- [S3:incident-response] Security Incident Response Plan (`incident-response`, plan, reviewed 2026-02-14)
- [S4:gdpr-privacy-program] GDPR Privacy and Data Protection Program (`gdpr-privacy-program`, policy, reviewed 2026-03-10)

### 8. Have you completed penetration testing for the application and API?

**Confidence:** medium
**Needs human review:** no

Draft answer based on approved evidence: Jamie completed an external penetration test of the web application and API in 2025 by an independent security provider. [S1:pentest-2025] The test scope included authenticated application workflows, API authorization checks, common web vulnerabilities, and cloud-exposed attack surface. [S2:pentest-2025] No critical findings remained open after remediation and retesting; remediation evidence is tracked by Security Engineering. [S3:pentest-2025]

**Freshness checks:**
- `pentest-2025` last reviewed 2025-09-12 (252 days old): stale
- `pentest-2025` last reviewed 2025-09-12 (252 days old): stale
- `pentest-2025` last reviewed 2025-09-12 (252 days old): stale

**Sources:**
- [S1:pentest-2025] External Penetration Test Executive Summary (`pentest-2025`, test-report, reviewed 2025-09-12)
- [S2:pentest-2025] External Penetration Test Executive Summary (`pentest-2025`, test-report, reviewed 2025-09-12)
- [S3:pentest-2025] External Penetration Test Executive Summary (`pentest-2025`, test-report, reviewed 2025-09-12)

### 9. Can you support DORA operational resilience requirements for financial institutions?

**Confidence:** high
**Needs human review:** no

Draft answer based on approved evidence: Jamie maintains an ICT risk register covering availability, confidentiality, integrity, vendor dependency, and operational resilience risks. [S1:dora-operational-resilience] Operational resilience activities include backup checks, incident exercises, post-incident reviews, and continuity planning for critical customer workflows. [S2:dora-operational-resilience] Supplier risk records identify critical providers, security review status, data categories processed, and contingency considerations. [S3:dora-operational-resilience]

**Freshness checks:**
- `dora-operational-resilience` last reviewed 2026-02-20 (91 days old): fresh
- `dora-operational-resilience` last reviewed 2026-02-20 (91 days old): fresh
- `dora-operational-resilience` last reviewed 2026-02-20 (91 days old): fresh

**Sources:**
- [S1:dora-operational-resilience] DORA ICT Risk and Operational Resilience Mapping (`dora-operational-resilience`, framework-mapping, reviewed 2026-02-20)
- [S2:dora-operational-resilience] DORA ICT Risk and Operational Resilience Mapping (`dora-operational-resilience`, framework-mapping, reviewed 2026-02-20)
- [S3:dora-operational-resilience] DORA ICT Risk and Operational Resilience Mapping (`dora-operational-resilience`, framework-mapping, reviewed 2026-02-20)

### 10. Are you FedRAMP authorized?

**Confidence:** low
**Needs human review:** yes

Needs human review. The evidence below may be relevant, but it is not strong enough for an unsupported claim. Jamie does not currently have approved evidence to claim FedRAMP authorization. [S1:unsupported-fedramp]

**Freshness checks:**
- `unsupported-fedramp` last reviewed 2026-05-10 (12 days old): fresh

**Sources:**
- [S1:unsupported-fedramp] Unsupported Claims Register (`unsupported-fedramp`, negative-evidence-register, reviewed 2026-05-10)

## Guardrail

Answers are assembled only from retrieved evidence snippets. Low-confidence results are explicitly marked for human review so the team can avoid unsupported claims while still accelerating routine questionnaire work.
