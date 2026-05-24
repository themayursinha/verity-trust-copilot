#!/usr/bin/env python3
"""Local web UI for Security Questionnaire Copilot."""

from __future__ import annotations

import argparse
import json
import re
from datetime import date, datetime
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from security_questionnaire_copilot import (
    build_results,
    export_csv,
    load_evidence,
    load_questions,
    parse_date,
    write_outputs,
)

ROOT = Path(__file__).resolve().parent
STATIC_DIR = ROOT / "static"
EVIDENCE_PATH = ROOT / "evidence" / "evidence.json"
QUESTIONS_PATH = ROOT / "data" / "questions.json"
OUTPUT_DIR = ROOT / "outputs"
APPROVALS_PATH = OUTPUT_DIR / "approvals.json"
CONTENT_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
    ".json": "application/json; charset=utf-8",
}


def parse_questions(payload: dict[str, Any]) -> list[str]:
    questions = payload.get("questions")
    if isinstance(questions, list):
        return [str(item).strip() for item in questions if str(item).strip()]
    question_text = payload.get("question_text")
    if isinstance(question_text, str):
        return [line.strip() for line in question_text.splitlines() if line.strip()]
    return []


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "evidence"


def load_evidence_records() -> list[dict[str, Any]]:
    return json.loads(EVIDENCE_PATH.read_text(encoding="utf-8"))


def normalize_evidence_record(record: dict[str, Any]) -> dict[str, Any]:
    required = ["title", "type", "last_reviewed", "owner", "summary", "snippets"]
    missing = [field for field in required if not record.get(field)]
    if missing:
        raise ValueError(f"Evidence record missing required fields: {', '.join(missing)}")
    snippets = record.get("snippets")
    if not isinstance(snippets, list) or not snippets:
        raise ValueError("Evidence record must include at least one snippet.")

    parse_date(str(record["last_reviewed"]))
    title = str(record["title"]).strip()
    frameworks = record.get("frameworks", [])
    control_ids = record.get("control_ids", [])
    normalized: dict[str, Any] = {
        "id": str(record.get("id") or slugify(title)).strip(),
        "title": title,
        "type": str(record["type"]).strip(),
        "frameworks": [str(item).strip() for item in frameworks if isinstance(item, str) and item.strip()],
        "control_ids": [str(item).strip() for item in control_ids if isinstance(item, str) and item.strip()],
        "last_reviewed": str(record["last_reviewed"]).strip(),
        "owner": str(record["owner"]).strip(),
        "summary": str(record["summary"]).strip(),
        "snippets": [str(item).strip() for item in snippets if isinstance(item, str) and item.strip()],
    }
    if not normalized["snippets"]:
        raise ValueError("Evidence snippets cannot be blank.")
    return normalized


def save_evidence_records(records: list[dict[str, Any]]) -> None:
    EVIDENCE_PATH.write_text(json.dumps(records, indent=2), encoding="utf-8")


def load_approvals() -> dict[str, Any]:
    if not APPROVALS_PATH.exists():
        return {}
    return json.loads(APPROVALS_PATH.read_text(encoding="utf-8"))


def save_approvals(approvals: dict[str, Any]) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    APPROVALS_PATH.write_text(json.dumps(approvals, indent=2), encoding="utf-8")


def render_customer_ready_markdown(answer: dict[str, Any]) -> str:
    lines = [
        "# Customer Security Answer",
        "",
        "## Question",
        "",
        str(answer.get("question", "")),
        "",
        "## Draft Answer",
        "",
        str(answer.get("answer", "")),
        "",
        f"**Confidence:** {answer.get('confidence', 'unknown')}",
        f"**Needs human review:** {str(answer.get('needs_human_review', False)).lower()}",
        "",
        "## Sources",
        "",
    ]
    citations = answer.get("citations") if isinstance(answer.get("citations"), list) else []
    if citations:
        for citation in citations:
            if not isinstance(citation, dict):
                continue
            lines.append(
                "- {citation} {title} ({source_id}, reviewed {last_reviewed})".format(
                    citation=citation.get("citation", ""),
                    title=citation.get("title", ""),
                    source_id=citation.get("source_id", ""),
                    last_reviewed=citation.get("last_reviewed", ""),
                )
            )
    else:
        lines.append("- No sources found. Do not send without review.")
    lines.extend(["", "## Freshness", ""])
    freshness = answer.get("freshness") if isinstance(answer.get("freshness"), list) else []
    if freshness:
        for item in freshness:
            if not isinstance(item, dict):
                continue
            lines.append(
                "- {source}: {status}, reviewed {last_reviewed}, {age_days} days old".format(
                    source=item.get("source", ""),
                    status=item.get("status", ""),
                    last_reviewed=item.get("last_reviewed", ""),
                    age_days=item.get("age_days", ""),
                )
            )
    else:
        lines.append("- No freshness checks available.")
    lines.append("")
    return "\n".join(lines)


class CopilotHandler(BaseHTTPRequestHandler):
    server_version = "SecurityQuestionnaireCopilot/0.1"

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/":
            self.serve_file(STATIC_DIR / "index.html")
            return
        if path == "/api/sample":
            self.send_json({"questions": load_questions(QUESTIONS_PATH)})
            return
        if path == "/api/evidence":
            self.send_json({"evidence": load_evidence_records()})
            return
        if path == "/api/approvals":
            self.send_json({"approvals": load_approvals()})
            return
        if path.startswith("/static/"):
            requested = (STATIC_DIR / path.removeprefix("/static/")).resolve()
            if STATIC_DIR in requested.parents or requested == STATIC_DIR:
                self.serve_file(requested)
                return
        self.send_error(HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length) or b"{}")

            if path == "/api/evidence":
                self.store_evidence(payload)
                return

            if path == "/api/export":
                self.export_answer(payload)
                return

            if path == "/api/export/csv":
                self.export_csv_answer(payload)
                return

            if path == "/api/export/json":
                self.export_json_answer(payload)
                return

            if path == "/api/approval":
                self.set_approval(payload)
                return

            if path != "/api/answer":
                self.send_error(HTTPStatus.NOT_FOUND)
                return

            as_of = parse_date(str(payload.get("as_of") or date.today().isoformat()))
            questions = parse_questions(payload)
            if not questions:
                self.send_json({"error": "Add at least one security question."}, HTTPStatus.BAD_REQUEST)
                return

            evidence = load_evidence(EVIDENCE_PATH)
            results = build_results(questions, evidence, as_of)
            write_outputs(results, OUTPUT_DIR)
            self.send_json(results)
        except ValueError as exc:
            self.send_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)
        except Exception as exc:  # pragma: no cover - keeps local demo failures readable.
            self.send_json({"error": f"Unexpected server error: {exc}"}, HTTPStatus.INTERNAL_SERVER_ERROR)

    def store_evidence(self, payload: dict[str, Any]) -> None:
        incoming = payload.get("records", payload.get("record"))
        if isinstance(incoming, dict):
            incoming_records = [incoming]
        elif isinstance(incoming, list):
            incoming_records = incoming
        else:
            raise ValueError("Send an evidence record or a list of records.")

        records = load_evidence_records()
        existing_ids = {str(record.get("id")) for record in records}
        normalized_records: list[dict[str, Any]] = []
        for item in incoming_records:
            if not isinstance(item, dict):
                raise ValueError("Evidence records must be JSON objects.")
            normalized = normalize_evidence_record(item)
            base_id = str(normalized["id"])
            candidate = base_id
            suffix = 2
            while candidate in existing_ids:
                candidate = f"{base_id}-{suffix}"
                suffix += 1
            normalized["id"] = candidate
            existing_ids.add(candidate)
            normalized_records.append(normalized)

        records.extend(normalized_records)
        save_evidence_records(records)
        self.send_json({"stored": len(normalized_records), "evidence": records}, HTTPStatus.CREATED)

    def export_answer(self, payload: dict[str, Any]) -> None:
        answer = payload.get("answer")
        if not isinstance(answer, dict):
            raise ValueError("Send an answer object to export.")
        markdown = render_customer_ready_markdown(answer)
        export_path = OUTPUT_DIR / "customer_ready_answer.md"
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        export_path.write_text(markdown, encoding="utf-8")
        self.send_json({"path": str(export_path), "markdown": markdown})

    def export_csv_answer(self, payload: dict[str, Any]) -> None:
        answer = payload.get("answer")
        if not isinstance(answer, dict):
            raise ValueError("Send an answer object to export.")
        results = {
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "as_of_date": date.today().isoformat(),
            "summary": {
                "questions_processed": 1,
                "confidence_counts": {answer.get("confidence", "low"): 1},
                "human_reviews_required": 1 if answer.get("needs_human_review") else 0,
            },
            "answers": [answer],
        }
        csv_content = export_csv(results)
        export_path = OUTPUT_DIR / "customer_ready_answer.csv"
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        export_path.write_text(csv_content, encoding="utf-8")
        self.send_json({"path": str(export_path), "csv": csv_content})

    def export_json_answer(self, payload: dict[str, Any]) -> None:
        answer = payload.get("answer")
        if not isinstance(answer, dict):
            raise ValueError("Send an answer object to export.")
        results = {
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "as_of_date": date.today().isoformat(),
            "summary": {
                "questions_processed": 1,
                "confidence_counts": {answer.get("confidence", "low"): 1},
                "human_reviews_required": 1 if answer.get("needs_human_review") else 0,
            },
            "answers": [answer],
        }
        json_content = json.dumps(results, indent=2)
        export_path = OUTPUT_DIR / "customer_ready_answer.json"
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        export_path.write_text(json_content, encoding="utf-8")
        self.send_json({"path": str(export_path), "json": json_content})

    def set_approval(self, payload: dict[str, Any]) -> None:
        question = payload.get("question")
        if not isinstance(question, str) or not question.strip():
            raise ValueError("Send a non-empty 'question' string.")
        status = payload.get("status", "unreviewed")
        if status not in ("unreviewed", "approved", "rejected"):
            raise ValueError("Status must be 'approved', 'rejected', or 'unreviewed'.")
        approvals = load_approvals()
        approvals[question.strip()] = {
            "status": status,
            "reviewer": str(payload.get("reviewer", "")).strip(),
            "reviewed_at": datetime.now().isoformat(timespec="seconds"),
            "notes": str(payload.get("notes", "")).strip(),
        }
        save_approvals(approvals)
        self.send_json({"question": question.strip(), **approvals[question.strip()]})

    def serve_file(self, path: Path) -> None:
        if not path.exists() or not path.is_file():
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        content_type = CONTENT_TYPES.get(path.suffix, "application/octet-stream")
        body = path.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_json(self, payload: object, status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(payload, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:
        print(f"{self.address_string()} - {format % args}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the local Security Questionnaire Copilot UI.")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind.")
    parser.add_argument("--port", default=8000, type=int, help="Port to bind.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    server = ThreadingHTTPServer((args.host, args.port), CopilotHandler)
    print(f"Security Questionnaire Copilot running at http://{args.host}:{args.port}")
    print("Press Ctrl+C to stop.")
    server.serve_forever()


if __name__ == "__main__":
    main()
