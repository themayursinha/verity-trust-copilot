# UX Polish Design

## Purpose

Make the current Security Questionnaire Copilot prototype feel credible in a stakeholder demo while preserving its local, minimal architecture. The polish pass should make evidence quality visible at a glance so viewers can quickly understand why a draft answer is or is not well supported.

## Context

The repo is a small local prototype with:

- `security_questionnaire_copilot.py` for local retrieval, answer drafting, confidence, freshness, and output generation.
- `web_app.py` for a Python standard-library HTTP server and JSON endpoints.
- `static/index.html`, `static/styles.css`, and `static/app.js` for the browser UI.
- Local JSON files for questions and evidence.

The current UI already supports sample questions, answer generation, evidence upload/storage, citations, freshness checks, and markdown export. The polish pass should improve presentation and states without adding new product workflow or external dependencies.

## Goals

- Keep the existing workbench layout recognizable.
- Make the prototype demo-ready through stronger hierarchy, spacing, responsive behavior, and visual state handling.
- Emphasize evidence quality on answer cards with an evidence score strip.
- Make the detail panel explain trust clearly through confidence rationale, freshness, and citations.
- Use minimum code and avoid speculative features.

## Non-Goals

- Add approval workflows, reviewer assignment, audit logs, authentication, or integrations.
- Change retrieval, scoring, or answer-generation behavior.
- Redesign persistence or output formats.
- Add external APIs or frontend build tooling.

## UX Direction

Use a trust-focused Workbench Dashboard. The app remains a single-screen workspace with a sidebar/status rail, question composer, answer list, and selected-answer detail panel. The primary visual improvement is an evidence quality layer that helps users scan support strength before reading every source.

The design optimizes for demo readiness. It should look polished and credible when sample questions are loaded and generated, and it should make weak or unsupported answers visually honest.

## Components

### Sidebar

Turn the sidebar into a compact trust summary. It should show questions processed, reviews required, sources used, and evidence library freshness. Any static coverage graphics should be removed or made clearly connected to real evidence state, because decorative coverage weakens trust.

### Composer

Make the composer quieter and more purposeful. Keep question input, freshness date, sample loading, and generate action visible. Loading, validation, and API errors should appear near the composer so users know what action caused them.

### Answer List

Make the answer list the main scanning surface. Each answer card should show:

- Question text.
- Confidence badge.
- Human review marker when required.
- Citation count.
- Freshness summary.
- Evidence score strip.

The selected card should have a stable, obvious active state.

### Evidence Score Strip

Derive the strip from existing answer fields in the frontend. Use three compact segments:

- Confidence: high, medium, or low.
- Sources: none, one citation, or multiple citations.
- Freshness: all fresh, has stale, has outdated, or no evidence.

The strip is display-only. It should not change answer confidence or backend scoring.

### Detail Panel

Make the detail panel the trust explanation for the selected answer. It should show:

- Selected question.
- Confidence and confidence rationale.
- Human review warning when required.
- Draft answer.
- Freshness checks.
- Sources and snippets.
- Export action.

The hierarchy should make evidence quality obvious before export, without hiding the draft answer.

## Data Flow

Keep backend endpoints and output formats unchanged. `/api/answer` already returns the fields needed by the UI:

- `confidence`
- `needs_human_review`
- `confidence_rationale`
- `freshness`
- `citations`

Add small pure frontend helpers in `static/app.js` to map an answer object to display labels and CSS classes for score-strip segments and freshness summaries.

## States

Polish these states:

- Empty: clear no-results state that prompts the user to generate drafts, without fake confidence or fake evidence.
- Loading: disabled generate button, stable layout, and visible progress copy.
- Error: styled message near the composer that does not erase existing results unless necessary.
- No evidence: strong warning state with no citations and human-review language.
- Selected answer: active state that is obvious with mouse and keyboard.

## Responsiveness

Desktop should keep the workbench layout: sidebar plus main content, with answer list and detail panel side by side.

Medium screens may compress the sidebar into a narrower rail or top summary band. The answer list and detail panel must remain usable.

Mobile should stack content in this order:

1. Composer.
2. Trust metrics.
3. Answer list.
4. Selected answer detail.

The evidence score strip must remain legible and should not cause large layout jumps.

## Error Handling

Keep errors local and explicit:

- Blank input focuses the question field and shows a status message.
- API errors render as a styled error state near the composer.
- Missing citations and missing freshness render as warnings, not empty space.
- Export errors remain visible in status text.

## Testing

Verification should include:

- Run the local web app.
- Generate sample drafts.
- Confirm answer cards show evidence score strips for high, medium, low, stale/outdated, and no-citation cases where sample data supports them.
- Confirm selected-answer detail shows confidence rationale, freshness, sources, and warnings clearly.
- Check desktop and mobile viewport behavior.
- Confirm markdown export still works.

## Success Criteria

The app is demo-ready when a stakeholder can load the sample questions, generate drafts, and immediately see which answers are well supported by evidence, which need human review, and why.
