#!/usr/bin/env python3
"""Local web UI for Verity Trust Copilot."""

from __future__ import annotations

import argparse
import contextlib
import json
import re
from datetime import date, datetime, timedelta
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
POLICIES_PATH = ROOT / "data" / "policies.json"
ACTIVITY_PATH = OUTPUT_DIR / "activity.json"
VANTA_CONFIG_PATH = ROOT / "data" / "vanta_config.json"
PENTESTS_PATH = ROOT / "data" / "pentests.json"
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


def load_policies() -> list[dict[str, Any]]:
    if not POLICIES_PATH.exists():
        return []
    return json.loads(POLICIES_PATH.read_text(encoding="utf-8"))


def save_policies(policies: list[dict[str, Any]]) -> None:
    POLICIES_PATH.parent.mkdir(parents=True, exist_ok=True)
    POLICIES_PATH.write_text(json.dumps(policies, indent=2), encoding="utf-8")


def next_policy_id(policies: list[dict[str, Any]]) -> str:
    max_id = 0
    for p in policies:
        with contextlib.suppress(ValueError, TypeError):
            max_id = max(max_id, int(p.get("id", "0")))
    return str(max_id + 1)


def append_activity(action: str, detail: str = "") -> None:
    ACTIVITY_PATH.parent.mkdir(parents=True, exist_ok=True)
    activities = []
    if ACTIVITY_PATH.exists():
        activities = json.loads(ACTIVITY_PATH.read_text(encoding="utf-8"))
    activities.append(
        {
            "action": action,
            "detail": detail,
            "timestamp": datetime.now().isoformat(timespec="seconds"),
        }
    )
    if len(activities) > 100:
        activities = activities[-100:]
    ACTIVITY_PATH.write_text(json.dumps(activities, indent=2), encoding="utf-8")


def load_activity() -> list[dict[str, Any]]:
    if not ACTIVITY_PATH.exists():
        return []
    return json.loads(ACTIVITY_PATH.read_text(encoding="utf-8"))


def load_vanta_config() -> dict[str, Any]:
    if not VANTA_CONFIG_PATH.exists():
        return {
            "connected": False,
            "api_key_configured": False,
            "integration_mode": "mock",
            "organization_id": "",
            "last_sync": None,
        }
    config = json.loads(VANTA_CONFIG_PATH.read_text(encoding="utf-8"))
    config.pop("api_key", None)
    config.pop("token", None)
    config["api_key_configured"] = False
    config["integration_mode"] = "mock"
    return config


def save_vanta_config(config: dict[str, Any]) -> None:
    safe_config = dict(config)
    safe_config.pop("api_key", None)
    safe_config.pop("token", None)
    safe_config["api_key_configured"] = False
    safe_config["integration_mode"] = "mock"
    VANTA_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    VANTA_CONFIG_PATH.write_text(json.dumps(safe_config, indent=2), encoding="utf-8")


def load_pentests() -> list[dict[str, Any]]:
    if not PENTESTS_PATH.exists():
        return []
    return json.loads(PENTESTS_PATH.read_text(encoding="utf-8"))


def save_pentests(pentests: list[dict[str, Any]]) -> None:
    PENTESTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    PENTESTS_PATH.write_text(json.dumps(pentests, indent=2), encoding="utf-8")


def next_pentest_id(pentests: list[dict[str, Any]]) -> str:
    max_id = 0
    for p in pentests:
        with contextlib.suppress(ValueError, TypeError):
            max_id = max(max_id, int(p.get("id", "0")))
    return str(max_id + 1)


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
    server_version = "VerityTrustCopilot/0.1"

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
        if path == "/api/dashboard/overview":
            self.dashboard_overview()
            return
        if path == "/api/policies":
            self.send_json(load_policies())
            return
        if path == "/api/vanta/status":
            self.send_json(load_vanta_config())
            return
        if re.match(r"^/api/policies/\d+$", path):
            self.get_policy(path)
            return
        if path == "/api/pentests":
            self.send_json(load_pentests())
            return
        if re.match(r"^/api/pentests/\d+$", path):
            self.get_pentest(path)
            return
        if path.startswith("/static/"):
            requested = (STATIC_DIR / path.removeprefix("/static/")).resolve()
            if STATIC_DIR in requested.parents or requested == STATIC_DIR:
                self.serve_file(requested)
                return
        self.send_error(HTTPStatus.NOT_FOUND)

    def dashboard_overview(self) -> None:
        records = load_evidence_records()

        frameworks: dict[str, dict[str, Any]] = {
            "iso-27001": {"id": "iso-27001", "coverage": 0.0, "evidence_count": 0, "control_count": 0},
            "soc-2": {"id": "soc-2", "coverage": 0.0, "evidence_count": 0, "control_count": 0},
            "gdpr": {"id": "gdpr", "coverage": 0.0, "evidence_count": 0, "control_count": 0},
            "dora": {"id": "dora", "coverage": 0.0, "evidence_count": 0, "control_count": 0},
        }
        for rec in records:
            for fw in rec.get("frameworks", []):
                fw_lower = fw.lower().replace(" ", "-").replace("_", "-")
                if fw_lower in frameworks:
                    frameworks[fw_lower]["evidence_count"] += 1
                    ctrl_count = len(rec.get("control_ids", []))
                    frameworks[fw_lower]["control_count"] += ctrl_count

        max_evidence = max((v["evidence_count"] for v in frameworks.values()), default=1)
        for v in frameworks.values():
            v["coverage"] = round(v["evidence_count"] / max(max_evidence, 1), 2)

        now = datetime.now()
        fresh = stale = 0
        fw_set = set()
        for rec in records:
            for fw in rec.get("frameworks", []):
                fw_set.add(fw.lower().replace(" ", "-"))
            try:
                lr = parse_date(str(rec.get("last_reviewed", "")))
                age_days = (now.date() - lr).days
                if age_days <= 180:
                    fresh += 1
                elif age_days >= 365:
                    stale += 1
            except (ValueError, TypeError):
                pass

        approvals = load_approvals()
        approved = sum(1 for a in approvals.values() if a.get("status") == "approved")
        rejected = sum(1 for a in approvals.values() if a.get("status") == "rejected")
        unreviewed = sum(1 for a in approvals.values() if a.get("status") in ("unreviewed", ""))

        policies = load_policies()
        active_policies = sum(1 for p in policies if p.get("status") == "active")
        draft_policies = sum(1 for p in policies if p.get("status") in ("draft", ""))
        now_dt = datetime.now()
        cutoff = now_dt.date() + timedelta(days=30)
        upcoming = sum(1 for p in policies if p.get("next_review") and parse_date(p["next_review"]) <= cutoff)

        activity = load_activity()

        self.send_json(
            {
                "frameworks": list(frameworks.values()),
                "evidence": {
                    "total": len(records),
                    "fresh": fresh,
                    "stale": stale,
                    "frameworks_covered": len(fw_set),
                },
                "policies": {
                    "total": len(policies),
                    "active": active_policies,
                    "draft": draft_policies,
                    "upcoming_reviews": upcoming,
                },
                "approvals": {
                    "total": len(approvals),
                    "approved": approved,
                    "rejected": rejected,
                    "unreviewed": unreviewed,
                },
                "recent_activity": activity[-10:] if activity else [],
            }
        )

    def get_policy(self, path: str) -> None:
        policy_id = path.split("/")[-1]
        policies = load_policies()
        for p in policies:
            if p.get("id") == policy_id:
                self.send_json(p)
                return
        self.send_error(HTTPStatus.NOT_FOUND)

    def get_pentest(self, path: str) -> None:
        pentest_id = path.split("/")[-1]
        pentests = load_pentests()
        for p in pentests:
            if p.get("id") == pentest_id:
                self.send_json(p)
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

            if path == "/api/policies":
                self.create_policy(payload)
                return

            if path == "/api/vanta/sync":
                self.vanta_sync(payload)
                return

            if path == "/api/pentests":
                self.create_pentest(payload)
                return

            if re.match(r"^/api/pentests/\d+/findings$", path):
                self.add_finding(path, payload)
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

    def do_PUT(self) -> None:
        path = urlparse(self.path).path
        policy_match = re.match(r"^/api/policies/(\d+)$", path)
        pentest_match = re.match(r"^/api/pentests/(\d+)$", path)
        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length) or b"{}")
            if policy_match:
                self.update_policy(policy_match.group(1), payload)
                return
            if pentest_match:
                self.update_pentest(pentest_match.group(1), payload)
                return
        except ValueError as exc:
            self.send_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)
        self.send_error(HTTPStatus.NOT_FOUND)

    def do_DELETE(self) -> None:
        path = urlparse(self.path).path
        policy_match = re.match(r"^/api/policies/(\d+)$", path)
        pentest_match = re.match(r"^/api/pentests/(\d+)$", path)
        finding_match = re.match(r"^/api/pentests/(\d+)/findings/(\d+)$", path)
        if policy_match:
            self.delete_policy(policy_match.group(1))
            return
        if pentest_match:
            self.delete_pentest(pentest_match.group(1))
            return
        if finding_match:
            self.delete_finding(finding_match.group(1), finding_match.group(2))
            return
        self.send_error(HTTPStatus.NOT_FOUND)

    def create_policy(self, payload: dict[str, Any]) -> None:
        title = str(payload.get("title", "")).strip()
        if not title:
            raise ValueError("Policy title is required.")
        policies = load_policies()
        created_at: str = datetime.now().isoformat(timespec="seconds")
        review_interval: int = int(payload.get("review_interval_months", 12))
        policy = {
            "id": next_policy_id(policies),
            "title": title,
            "category": str(payload.get("category", "information-security")).strip(),
            "content": str(payload.get("content", "")).strip(),
            "status": "draft",
            "version": 1,
            "review_interval_months": review_interval,
            "created_at": created_at,
            "updated_at": datetime.now().isoformat(timespec="seconds"),
        }
        next_date = self._calc_next_review(created_at, review_interval)
        policy["next_review"] = next_date
        policies.append(policy)
        save_policies(policies)
        append_activity("Policy created", title)
        self.send_json(policy, HTTPStatus.CREATED)

    def update_policy(self, policy_id: str, payload: dict[str, Any]) -> None:
        policies = load_policies()
        for p in policies:
            if p.get("id") == policy_id:
                title = str(payload.get("title", p.get("title", ""))).strip()
                p["title"] = title
                p["category"] = str(payload.get("category", p.get("category", "information-security"))).strip()
                p["content"] = str(payload.get("content", p.get("content", ""))).strip()
                if "review_interval_months" in payload:
                    interval: int = int(payload["review_interval_months"])
                    p["review_interval_months"] = interval
                    next_date = self._calc_next_review(str(p["updated_at"]), interval)
                    p["next_review"] = next_date
                p["updated_at"] = datetime.now().isoformat(timespec="seconds")
                save_policies(policies)
                append_activity("Policy updated", title)
                self.send_json(p)
                return
        self.send_error(HTTPStatus.NOT_FOUND)

    def delete_policy(self, policy_id: str) -> None:
        policies = load_policies()
        for i, p in enumerate(policies):
            if p.get("id") == policy_id:
                removed = policies.pop(i)
                save_policies(policies)
                append_activity("Policy deleted", removed.get("title", ""))
                self.send_json({"deleted": policy_id})
                return
        self.send_error(HTTPStatus.NOT_FOUND)

    @staticmethod
    def _calc_next_review(from_iso: str, interval_months: int) -> str:
        try:
            from_dt = datetime.fromisoformat(from_iso)
        except (ValueError, TypeError):
            from_dt = datetime.now()
        y = from_dt.year + (from_dt.month + interval_months - 1) // 12
        m = (from_dt.month + interval_months - 1) % 12 + 1
        d = min(from_dt.day, 28)
        try:
            next_dt = from_dt.replace(year=y, month=m, day=d)
        except (ValueError, OverflowError):
            next_dt = from_dt.replace(year=y, month=m, day=1)
        return next_dt.date().isoformat()

    def create_pentest(self, payload: dict[str, Any]) -> None:
        title = str(payload.get("title", "")).strip()
        if not title:
            raise ValueError("Pentest title is required.")
        pentests = load_pentests()
        pentest = {
            "id": next_pentest_id(pentests),
            "title": title,
            "scope": str(payload.get("scope", "")).strip(),
            "methodology": str(payload.get("methodology", "")).strip(),
            "start_date": str(payload.get("start_date", "")).strip(),
            "end_date": str(payload.get("end_date", "")).strip(),
            "status": str(payload.get("status", "planned")).strip(),
            "findings": [],
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "updated_at": datetime.now().isoformat(timespec="seconds"),
        }
        if pentest["status"] not in ("planned", "in-progress", "completed"):
            pentest["status"] = "planned"
        pentests.append(pentest)
        save_pentests(pentests)
        append_activity("Pentest created", title)
        self.send_json(pentest, HTTPStatus.CREATED)

    def update_pentest(self, pentest_id: str, payload: dict[str, Any]) -> None:
        pentests = load_pentests()
        for p in pentests:
            if p.get("id") == pentest_id:
                if "title" in payload:
                    p["title"] = str(payload["title"]).strip()
                if "scope" in payload:
                    p["scope"] = str(payload["scope"]).strip()
                if "methodology" in payload:
                    p["methodology"] = str(payload["methodology"]).strip()
                if "start_date" in payload:
                    p["start_date"] = str(payload["start_date"]).strip()
                if "end_date" in payload:
                    p["end_date"] = str(payload["end_date"]).strip()
                if "status" in payload:
                    s = str(payload["status"]).strip()
                    if s in ("planned", "in-progress", "completed"):
                        p["status"] = s
                p["updated_at"] = datetime.now().isoformat(timespec="seconds")
                save_pentests(pentests)
                append_activity("Pentest updated", p["title"])
                self.send_json(p)
                return
        self.send_error(HTTPStatus.NOT_FOUND)

    def delete_pentest(self, pentest_id: str) -> None:
        pentests = load_pentests()
        for i, p in enumerate(pentests):
            if p.get("id") == pentest_id:
                removed = pentests.pop(i)
                save_pentests(pentests)
                append_activity("Pentest deleted", removed.get("title", ""))
                self.send_json({"deleted": pentest_id})
                return
        self.send_error(HTTPStatus.NOT_FOUND)

    def add_finding(self, path: str, payload: dict[str, Any]) -> None:
        pentest_id = path.split("/")[-2]
        pentests = load_pentests()
        for p in pentests:
            if p.get("id") == pentest_id:
                title = str(payload.get("title", "")).strip()
                if not title:
                    raise ValueError("Finding title is required.")
                max_fid = 0
                for f in p.get("findings", []):
                    with contextlib.suppress(ValueError, TypeError):
                        max_fid = max(max_fid, int(f.get("id", "0")))
                finding = {
                    "id": str(max_fid + 1),
                    "title": title,
                    "severity": str(payload.get("severity", "medium")).strip(),
                    "description": str(payload.get("description", "")).strip(),
                    "remediation": str(payload.get("remediation", "")).strip(),
                    "status": str(payload.get("status", "open")).strip(),
                    "assigned_to": str(payload.get("assigned_to", "")).strip(),
                    "due_date": str(payload.get("due_date", "")).strip(),
                }
                if finding["severity"] not in ("critical", "high", "medium", "low", "info"):
                    finding["severity"] = "medium"
                if finding["status"] not in ("open", "in-progress", "resolved", "accepted"):
                    finding["status"] = "open"
                p.setdefault("findings", []).append(finding)
                p["updated_at"] = datetime.now().isoformat(timespec="seconds")
                save_pentests(pentests)
                append_activity("Finding added", f"{finding['title']} ({pentest_id})")
                self.send_json(finding, HTTPStatus.CREATED)
                return
        self.send_error(HTTPStatus.NOT_FOUND)

    def delete_finding(self, pentest_id: str, finding_id: str) -> None:
        pentests = load_pentests()
        for p in pentests:
            if p.get("id") == pentest_id:
                findings = p.get("findings", [])
                for i, f in enumerate(findings):
                    if f.get("id") == finding_id:
                        removed = findings.pop(i)
                        p["findings"] = findings
                        p["updated_at"] = datetime.now().isoformat(timespec="seconds")
                        save_pentests(pentests)
                        append_activity("Finding deleted", removed.get("title", ""))
                        self.send_json({"deleted": finding_id})
                        return
                self.send_error(HTTPStatus.NOT_FOUND)
                return
        self.send_error(HTTPStatus.NOT_FOUND)

    def vanta_sync(self, payload: dict[str, Any]) -> None:
        vanta_config = load_vanta_config()
        org_id = str(payload.get("organization_id", "")).strip()

        if org_id:
            vanta_config["organization_id"] = org_id

        now_str = datetime.now().isoformat(timespec="seconds")
        vanta_config["last_sync"] = now_str
        vanta_config["connected"] = True
        vanta_config["api_key_configured"] = False
        vanta_config["integration_mode"] = "mock"
        save_vanta_config(vanta_config)

        evidence = load_evidence_records()
        existing_ids = {rec.get("id") for rec in evidence}
        synced = []
        mock_records = [
            {
                "id": "vanta-device-compliance",
                "title": "Mock Vanta Device Compliance Check",
                "type": "control-evidence",
                "frameworks": ["SOC 2", "ISO 27001"],
                "control_ids": ["CC6.1", "A.8.8"],
                "last_reviewed": now_str[:10],
                "owner": "Security",
                "summary": "Mock Vanta import: device encryption, MFA, screen lock, antivirus, OS patch level.",
                "snippets": ["Mock Vanta import monitors device compliance across all employee laptops."],
            },
            {
                "id": "vanta-access-review",
                "title": "Mock Vanta Quarterly Access Review",
                "type": "control-evidence",
                "frameworks": ["SOC 2", "ISO 27001"],
                "control_ids": ["CC6.2", "A.5.15"],
                "last_reviewed": now_str[:10],
                "owner": "IT",
                "summary": "Mock Vanta import for quarterly access review of production, identity, and admin systems.",
                "snippets": ["Mock Vanta import shows quarterly access reviews for production and admin systems."],
            },
            {
                "id": "vanta-security-training",
                "title": "Mock Vanta Security Training Report",
                "type": "control-evidence",
                "frameworks": ["SOC 2", "ISO 27001"],
                "control_ids": ["CC1.2", "A.6.3"],
                "last_reviewed": now_str[:10],
                "owner": "Security",
                "summary": "Mock Vanta import for employee security training completion status.",
                "snippets": ["Mock Vanta import tracks security training completion for all employees."],
            },
        ]
        for record in mock_records:
            if record["id"] not in existing_ids:
                evidence.append(record)
                existing_ids.add(record["id"])
                synced.append(record["title"])

        save_evidence_records(evidence)
        append_activity("Mock Vanta import completed", f"Imported {len(synced)} evidence records")
        self.send_json(
            {
                "status": "mock_success",
                "message": "Mock Vanta import completed. No external Vanta API was called and no API key was stored.",
                "synced_count": len(synced),
                "synced_titles": synced,
                "last_sync": now_str,
                "config": vanta_config,
            }
        )

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
    parser = argparse.ArgumentParser(description="Run the local Verity Trust Copilot UI.")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind.")
    parser.add_argument("--port", default=8000, type=int, help="Port to bind.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    server = ThreadingHTTPServer((args.host, args.port), CopilotHandler)
    print(f"Verity Trust Copilot running at http://{args.host}:{args.port}")
    print("Press Ctrl+C to stop.")
    server.serve_forever()


if __name__ == "__main__":
    main()
