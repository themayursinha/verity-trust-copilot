#!/usr/bin/env python3
"""Local Security Questionnaire Copilot.

The prototype intentionally avoids external APIs. It retrieves approved evidence,
drafts conservative answers from matched snippets, and flags weak or stale support.
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import math
import re
from collections import Counter
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any

FRESH_DAYS = 180
STALE_DAYS = 365
MAX_MATCHES = 4

STOPWORDS = {
    "a",
    "about",
    "after",
    "all",
    "an",
    "and",
    "any",
    "are",
    "as",
    "at",
    "be",
    "by",
    "can",
    "customer",
    "customers",
    "data",
    "do",
    "does",
    "for",
    "from",
    "have",
    "how",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "our",
    "the",
    "their",
    "to",
    "we",
    "what",
    "with",
    "you",
    "your",
}

SYNONYMS = {
    "ai": {"model", "models", "foundation", "training", "train", "prompts", "transcripts", "summaries"},
    "train": {"training", "models", "foundation", "ai"},
    "retention": {"retain", "retained", "deletion", "delete", "backups", "transcripts"},
    "delete": {"deletion", "retention", "erase", "removal"},
    "encrypt": {"encryption", "tls", "key", "keys", "at-rest", "transit"},
    "encrypted": {"encryption", "tls", "key", "keys", "at-rest", "transit"},
    "access": {"least", "privilege", "mfa", "sso", "offboarding", "roles"},
    "incident": {"breach", "triage", "containment", "notification", "gdpr"},
    "subprocessors": {"subprocessor", "vendor", "vendors", "supplier", "third-party", "subcontractor"},
    "dora": {"resilience", "ict", "operational", "third-party", "risk"},
    "pentest": {"penetration", "test", "testing", "api", "application", "vulnerability"},
    "fedramp": {"authorization", "authorized"},
    "iso": {"27001", "isms", "certification", "aligned"},
    "gdpr": {"privacy", "processor", "breach", "notification", "dpa"},
    "vanta": {"evidence", "controls", "compliance", "mfa", "device"},
    "backup": {"backups", "retention", "restore", "recovery", "continuity"},
    "breach": {"incident", "notification", "gdpr", "containment", "triage", "compromise"},
    "vendor": {"vendors", "supplier", "third-party", "subprocessor", "subprocessors"},
    "third-party": {"third-party", "vendor", "vendors", "supplier", "subprocessor", "subprocessors"},
    "soc": {"soc2", "soc-2", "report", "audit", "controls"},
    "audit": {"audits", "auditing", "review", "examination", "assessment"},
    "certification": {"certifications", "certified", "accreditation", "attestation"},
    "policy": {"policies", "procedure", "procedures", "standard", "standards"},
    "compliance": {"compliant", "regulatory", "requirements", "obligations"},
    "notification": {"notify", "notifications", "alert", "reporting", "disclosure"},
    "vulnerability": {"vulnerabilities", "scanning", "remediation", "patch", "cve"},
    "sso": {"single-sign-on", "identity", "authentication", "login"},
    "mfa": {"multi-factor", "two-factor", "2fa", "authentication", "sso"},
}


@dataclass(frozen=True)
class EvidenceSnippet:
    evidence_id: str
    title: str
    evidence_type: str
    frameworks: list[str]
    control_ids: list[str]
    last_reviewed: date
    owner: str
    snippet: str
    summary: str


@dataclass(frozen=True)
class Match:
    snippet: EvidenceSnippet
    score: float
    matched_terms: list[str]
    freshness: str
    age_days: int


@dataclass
class AnswerTemplate:
    category: str
    keywords: list[str]
    label: str
    intro: str | None = None
    outro: str | None = None


DEFAULT_TEMPLATES_PATH = Path(__file__).resolve().parent / "templates" / "answer_templates.json"


def load_templates(path: Path) -> list[AnswerTemplate]:
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    return [AnswerTemplate(**item) for item in data]


def match_template(question: str, templates: list[AnswerTemplate]) -> AnswerTemplate | None:
    q_tokens = set(tokenize(question))
    best_template: AnswerTemplate | None = None
    best_count = 0
    for tmpl in templates:
        count = sum(1 for kw in tmpl.keywords if kw in q_tokens)
        if count > best_count and count >= 2:
            best_count = count
            best_template = tmpl
    return best_template


def tokenize(text: str) -> list[str]:
    raw_tokens = re.findall(r"[a-zA-Z0-9][a-zA-Z0-9\-()\.]*", text.lower())
    normalized: list[str] = []
    for token in raw_tokens:
        token = token.strip(".()")
        if len(token) < 2 or token in STOPWORDS:
            continue
        normalized.append(token)
    return normalized


def expand_terms(tokens: list[str]) -> dict[str, float]:
    terms: dict[str, float] = dict(Counter(tokens))
    for token in tokens:
        for related in SYNONYMS.get(token, set()):
            terms[related] = terms.get(related, 0.0) + 0.45
    return terms


def compute_idf(snippets: list[EvidenceSnippet]) -> dict[str, float]:
    n = len(snippets)
    if n == 0:
        return {}
    df: Counter[str] = Counter()
    for snippet in snippets:
        evidence_text = " ".join(
            [
                snippet.title,
                snippet.evidence_type,
                " ".join(snippet.frameworks),
                " ".join(snippet.control_ids),
                snippet.summary,
                snippet.snippet,
            ]
        )
        for term in set(tokenize(evidence_text)):
            df[term] += 1

    idf: dict[str, float] = {}
    for term, doc_count in df.items():
        idf[term] = math.log(1.0 + n / (1.0 + doc_count))
    return idf


def parse_date(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()


def load_evidence(path: Path) -> list[EvidenceSnippet]:
    records = json.loads(path.read_text(encoding="utf-8"))
    snippets: list[EvidenceSnippet] = []
    for record in records:
        for snippet in record["snippets"]:
            snippets.append(
                EvidenceSnippet(
                    evidence_id=record["id"],
                    title=record["title"],
                    evidence_type=record["type"],
                    frameworks=record.get("frameworks", []),
                    control_ids=record.get("control_ids", []),
                    last_reviewed=parse_date(record["last_reviewed"]),
                    owner=record["owner"],
                    snippet=snippet,
                    summary=record["summary"],
                )
            )
    return snippets


def load_questions(path: Path) -> list[str]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, list):
        return [str(item) for item in payload]
    if isinstance(payload, dict) and isinstance(payload.get("questions"), list):
        return [str(item) for item in payload["questions"]]
    raise ValueError("Questions file must be a JSON list or an object with a 'questions' list.")


def freshness_status(last_reviewed: date, as_of: date) -> tuple[str, int]:
    age_days = (as_of - last_reviewed).days
    if age_days <= FRESH_DAYS:
        return "fresh", age_days
    if age_days <= STALE_DAYS:
        return "stale", age_days
    return "outdated", age_days


def score_snippet(
    question: str, snippet: EvidenceSnippet, as_of: date, idf: dict[str, float] | None = None
) -> Match | None:
    q_tokens = tokenize(question)
    q_terms = expand_terms(q_tokens)
    evidence_text = " ".join(
        [
            snippet.title,
            snippet.evidence_type,
            " ".join(snippet.frameworks),
            " ".join(snippet.control_ids),
            snippet.summary,
            snippet.snippet,
        ]
    )
    e_tokens = tokenize(evidence_text)
    e_terms = Counter(e_tokens)

    matched_terms: list[str] = []
    score = 0.0
    for term, weight in q_terms.items():
        if e_terms.get(term, 0) > 0:
            matched_terms.append(term)
            idf_weight = idf.get(term, 1.0) if idf else 1.0
            score += weight * idf_weight * (1.0 + math.log1p(e_terms[term]))

    q_phrases = re.findall(r"\b[a-z0-9][a-z0-9\-]+(?:\s+[a-z0-9][a-z0-9\-]+){1,3}\b", question.lower())
    evidence_lower = evidence_text.lower()
    for phrase in q_phrases:
        meaningful = [token for token in tokenize(phrase) if token not in STOPWORDS]
        if len(meaningful) >= 2 and " ".join(meaningful) in evidence_lower:
            score += 2.0

    freshness, age_days = freshness_status(snippet.last_reviewed, as_of)
    if freshness == "stale":
        score *= 0.9
    elif freshness == "outdated":
        score *= 0.7

    if score <= 0:
        return None
    return Match(
        snippet=snippet,
        score=round(score, 3),
        matched_terms=sorted(set(matched_terms)),
        freshness=freshness,
        age_days=age_days,
    )


def retrieve(question: str, snippets: list[EvidenceSnippet], as_of: date) -> list[Match]:
    idf = compute_idf(snippets)
    matches = [match for snippet in snippets if (match := score_snippet(question, snippet, as_of, idf))]
    matches.sort(key=lambda match: match.score, reverse=True)
    if not matches:
        return []

    cutoff = max(0.6, matches[0].score * 0.4)
    matches = [match for match in matches if match.score >= cutoff]

    deduped: list[Match] = []
    seen = set()
    for match in matches:
        key = (match.snippet.evidence_id, match.snippet.snippet)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(match)
        if len(deduped) == MAX_MATCHES:
            break
    return deduped


def confidence(matches: list[Match]) -> tuple[str, str]:
    if not matches:
        return "low", "No approved evidence matched the question."

    top = matches[0].score
    fresh_matches = sum(1 for match in matches if match.freshness == "fresh")
    unique_sources = len({match.snippet.evidence_id for match in matches})
    has_outdated = any(match.freshness == "outdated" for match in matches)

    if top >= 5.8 and fresh_matches >= 1 and not has_outdated and (unique_sources >= 2 or len(matches) >= 2):
        return "high", "Strong keyword coverage across fresh or current approved evidence."
    if top >= 3.2 and not has_outdated:
        return (
            "medium",
            "Relevant evidence was found, but coverage is narrower or includes stale "
            "evidence that should be checked before sending.",
        )
    return "low", "Evidence is weak, outdated, or too narrow for a supported customer-facing answer."


def citation_id(match: Match, index: int) -> str:
    return f"S{index}:{match.snippet.evidence_id}"


def generate_answer(
    question: str, matches: list[Match], level: str, template: AnswerTemplate | None = None
) -> str:
    if not matches:
        return (
            "Needs human review. I could not find approved evidence that supports an answer to this question. "
            "Do not make a customer-facing claim until Security, Privacy, or Legal adds approved evidence."
        )

    if level == "low":
        lead = (
            "Needs human review. The evidence below may be relevant, but it is not "
            "strong enough for an unsupported claim."
        )
    elif template and template.intro:
        lead = f"Draft answer based on approved evidence for {template.label}: {template.intro}"
    else:
        lead = "Draft answer based on approved evidence:"

    sentences = [lead]
    for index, match in enumerate(matches, start=1):
        sentences.append(f"{match.snippet.snippet} [{citation_id(match, index)}]")

    if template and template.outro and level != "low":
        sentences.append(template.outro)
    return " ".join(sentences)


def answer_question(
    question: str,
    snippets: list[EvidenceSnippet],
    as_of: date,
    templates: list[AnswerTemplate] | None = None,
) -> dict[str, Any]:
    matches = retrieve(question, snippets, as_of)
    level, rationale = confidence(matches)
    needs_review = level == "low"
    matched_template = match_template(question, templates) if templates else None
    return {
        "question": question,
        "answer": generate_answer(question, matches, level, matched_template),
        "confidence": level,
        "needs_human_review": needs_review,
        "template_category": matched_template.category if matched_template else None,
        "confidence_rationale": rationale,
        "freshness": [
            {
                "source": match.snippet.evidence_id,
                "last_reviewed": match.snippet.last_reviewed.isoformat(),
                "age_days": match.age_days,
                "status": match.freshness,
            }
            for match in matches
        ],
        "citations": [
            {
                "citation": citation_id(match, index),
                "source_id": match.snippet.evidence_id,
                "title": match.snippet.title,
                "type": match.snippet.evidence_type,
                "frameworks": match.snippet.frameworks,
                "control_ids": match.snippet.control_ids,
                "owner": match.snippet.owner,
                "last_reviewed": match.snippet.last_reviewed.isoformat(),
                "snippet": match.snippet.snippet,
                "score": match.score,
                "matched_terms": match.matched_terms,
            }
            for index, match in enumerate(matches, start=1)
        ],
    }


def render_markdown(results: dict[str, Any]) -> str:
    lines = [
        "# Security Questionnaire Copilot Report",
        "",
        f"Generated: {results['generated_at']}",
        f"Evidence freshness date: {results['as_of_date']}",
        "",
        "## Summary",
        "",
        f"- Questions processed: {results['summary']['questions_processed']}",
        f"- High confidence: {results['summary']['confidence_counts'].get('high', 0)}",
        f"- Medium confidence: {results['summary']['confidence_counts'].get('medium', 0)}",
        f"- Low confidence / human review: {results['summary']['confidence_counts'].get('low', 0)}",
        "",
        "## Draft Answers",
        "",
    ]

    for idx, item in enumerate(results["answers"], start=1):
        review = " yes" if item["needs_human_review"] else " no"
        lines.extend(
            [
                f"### {idx}. {item['question']}",
                "",
                f"**Confidence:** {item['confidence']}",
                f"**Needs human review:**{review}",
                "",
                item["answer"],
                "",
                "**Freshness checks:**",
            ]
        )
        if item["freshness"]:
            for check in item["freshness"]:
                lines.append(
                    "- `{source}` last reviewed {reviewed} ({age} days old): {status}".format(
                        source=check["source"],
                        reviewed=check["last_reviewed"],
                        age=check["age_days"],
                        status=check["status"],
                    )
                )
        else:
            lines.append("- No matching evidence found.")
        lines.extend(["", "**Sources:**"])
        if item["citations"]:
            for citation in item["citations"]:
                lines.append(
                    "- [{citation}] {title} (`{source_id}`, {type}, reviewed {reviewed})".format(
                        citation=citation["citation"],
                        title=citation["title"],
                        source_id=citation["source_id"],
                        type=citation["type"],
                        reviewed=citation["last_reviewed"],
                    )
                )
        else:
            lines.append("- No citations available.")
        lines.append("")

    lines.extend(
        [
            "## Guardrail",
            "",
            (
                "Answers are assembled only from retrieved evidence snippets. "
                "Low-confidence results are explicitly marked for human review so "
                "the team can avoid unsupported claims while still accelerating "
                "routine questionnaire work."
            ),
            "",
        ]
    )
    return "\n".join(lines)


def build_results(
    questions: list[str], evidence: list[EvidenceSnippet], as_of: date, templates: list[AnswerTemplate] | None = None
) -> dict[str, Any]:
    if templates is None:
        templates = load_templates(DEFAULT_TEMPLATES_PATH)
    answers = [answer_question(question, evidence, as_of, templates) for question in questions]
    counts = Counter(answer["confidence"] for answer in answers)
    category_counts: dict[str, int] = Counter()
    for answer in answers:
        cat = answer.get("template_category")
        if cat:
            category_counts[cat] += 1
    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "as_of_date": as_of.isoformat(),
        "summary": {
            "questions_processed": len(questions),
            "confidence_counts": dict(counts),
            "human_reviews_required": sum(1 for answer in answers if answer["needs_human_review"]),
            "template_categories": dict(category_counts),
        },
        "answers": answers,
    }


def export_csv(results: dict[str, Any]) -> str:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Question",
        "Answer",
        "Confidence",
        "Needs Human Review",
        "Template Category",
        "Sources",
        "Source Count",
        "Freshness Status",
    ])
    for answer in results["answers"]:
        sources = "; ".join(c["citation"] for c in answer.get("citations", []))
        freshness = "; ".join(
            f"{f['source']}: {f['status']}" for f in answer.get("freshness", [])
        )
        writer.writerow([
            answer.get("question", ""),
            answer.get("answer", ""),
            answer.get("confidence", ""),
            str(answer.get("needs_human_review", False)),
            answer.get("template_category", ""),
            sources,
            len(answer.get("citations", [])),
            freshness,
        ])
    return output.getvalue()


def write_outputs(results: dict[str, Any], output_dir: Path) -> tuple[Path, Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "answers.json"
    markdown_path = output_dir / "report.md"
    csv_path = output_dir / "answers.csv"
    json_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    markdown_path.write_text(render_markdown(results), encoding="utf-8")
    csv_path.write_text(export_csv(results), encoding="utf-8")
    return json_path, markdown_path, csv_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Draft security questionnaire answers from approved local evidence.")
    parser.add_argument("--evidence", default="evidence/evidence.json", type=Path, help="Path to evidence JSON.")
    parser.add_argument("--questions", default="data/questions.json", type=Path, help="Path to questions JSON.")
    parser.add_argument("--output-dir", default="outputs", type=Path, help="Directory for JSON and Markdown outputs.")
    parser.add_argument("--as-of", default=date.today().isoformat(), help="Freshness date in YYYY-MM-DD format.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    as_of = parse_date(args.as_of)
    evidence = load_evidence(args.evidence)
    questions = load_questions(args.questions)
    results = build_results(questions, evidence, as_of)
    json_path, markdown_path, csv_path = write_outputs(results, args.output_dir)
    print(f"Wrote {json_path}")
    print(f"Wrote {markdown_path}")
    print(f"Wrote {csv_path}")
    print(
        "Processed {questions} questions: {counts}".format(
            questions=results["summary"]["questions_processed"],
            counts=results["summary"]["confidence_counts"],
        )
    )


if __name__ == "__main__":
    main()
