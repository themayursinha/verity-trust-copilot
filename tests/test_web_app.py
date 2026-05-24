import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from web_app import (
    normalize_evidence_record,
    parse_questions,
    render_customer_ready_markdown,
    slugify,
)


class TestSlugify(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(slugify("Encryption Key Management"), "encryption-key-management")

    def test_already_slug(self):
        self.assertEqual(slugify("encryption"), "encryption")

    def test_special_chars(self):
        self.assertEqual(slugify("ISO 27001 (ISMS)"), "iso-27001-isms")

    def test_empty(self):
        self.assertEqual(slugify(""), "evidence")

    def test_only_special_chars(self):
        self.assertEqual(slugify("@#$%^&"), "evidence")

    def test_leading_trailing_dashes(self):
        self.assertEqual(slugify("-encryption-"), "encryption")

    def test_mixed_case(self):
        self.assertEqual(slugify("GDPR Privacy Program"), "gdpr-privacy-program")


class TestParseQuestions(unittest.TestCase):
    def test_questions_list(self):
        result = parse_questions({"questions": ["Q1?", "Q2?", "Q3?"]})
        self.assertEqual(result, ["Q1?", "Q2?", "Q3?"])

    def test_question_text(self):
        result = parse_questions({"question_text": "Q1?\nQ2?\nQ3?"})
        self.assertEqual(result, ["Q1?", "Q2?", "Q3?"])

    def test_empty_questions_list(self):
        result = parse_questions({"questions": []})
        self.assertEqual(result, [])

    def test_blank_lines_filtered(self):
        result = parse_questions({"question_text": "Q1?\n\nQ2?\n  \nQ3?"})
        self.assertEqual(result, ["Q1?", "Q2?", "Q3?"])

    def test_blank_items_filtered(self):
        result = parse_questions({"questions": ["Q1?", "", "Q2?", "  "]})
        self.assertEqual(result, ["Q1?", "Q2?"])

    def test_stripped_whitespace(self):
        result = parse_questions({"questions": ["  Q1?  ", "  Q2?  "]})
        self.assertEqual(result, ["Q1?", "Q2?"])

    def test_no_valid_fields(self):
        result = parse_questions({"unknown": "data"})
        self.assertEqual(result, [])

    def test_empty_dict(self):
        result = parse_questions({})
        self.assertEqual(result, [])


class TestNormalizeEvidenceRecord(unittest.TestCase):
    def test_minimal_valid_record(self):
        record = {
            "title": "Test Evidence",
            "type": "policy",
            "last_reviewed": "2026-05-01",
            "owner": "Security",
            "summary": "A test.",
            "snippets": ["Snippet one."],
        }
        normalized = normalize_evidence_record(record)
        self.assertEqual(normalized["title"], "Test Evidence")
        self.assertEqual(normalized["type"], "policy")
        self.assertEqual(normalized["last_reviewed"], "2026-05-01")
        self.assertEqual(normalized["owner"], "Security")
        self.assertEqual(normalized["summary"], "A test.")
        self.assertEqual(normalized["snippets"], ["Snippet one."])
        self.assertIn("id", normalized)

    def test_id_generated_from_title(self):
        record = {
            "title": "Encryption Standard",
            "type": "standard",
            "last_reviewed": "2026-05-01",
            "owner": "Security",
            "summary": "A test.",
            "snippets": ["Snippet."],
        }
        normalized = normalize_evidence_record(record)
        self.assertEqual(normalized["id"], "encryption-standard")

    def test_explicit_id(self):
        record = {
            "id": "custom-id",
            "title": "Test",
            "type": "policy",
            "last_reviewed": "2026-05-01",
            "owner": "Security",
            "summary": "A test.",
            "snippets": ["Snippet."],
        }
        normalized = normalize_evidence_record(record)
        self.assertEqual(normalized["id"], "custom-id")

    def test_missing_required_field(self):
        record = {
            "title": "Test",
            "type": "policy",
            "last_reviewed": "2026-05-01",
            "owner": "Security",
            "snippets": ["Snippet."],
        }
        with self.assertRaises(ValueError) as ctx:
            normalize_evidence_record(record)
        self.assertIn("missing", str(ctx.exception).lower())

    def test_empty_snippets(self):
        record = {
            "title": "Test",
            "type": "policy",
            "last_reviewed": "2026-05-01",
            "owner": "Security",
            "summary": "A test.",
            "snippets": [],
        }
        with self.assertRaises(ValueError) as ctx:
            normalize_evidence_record(record)
        self.assertIn("snippet", str(ctx.exception).lower())

    def test_blank_snippets_filtered_out(self):
        record = {
            "title": "Test",
            "type": "policy",
            "last_reviewed": "2026-05-01",
            "owner": "Security",
            "summary": "A test.",
            "snippets": ["Valid snippet.", "", "  "],
        }
        normalized = normalize_evidence_record(record)
        self.assertEqual(normalized["snippets"], ["Valid snippet."])

    def test_invalid_date(self):
        record = {
            "title": "Test",
            "type": "policy",
            "last_reviewed": "not-a-date",
            "owner": "Security",
            "summary": "A test.",
            "snippets": ["Snippet."],
        }
        with self.assertRaises(ValueError):
            normalize_evidence_record(record)

    def test_frameworks_and_control_ids_parsed(self):
        record = {
            "title": "Test",
            "type": "policy",
            "frameworks": ["ISO 27001", "GDPR"],
            "control_ids": ["A.5.1", "Art. 32"],
            "last_reviewed": "2026-05-01",
            "owner": "Security",
            "summary": "A test.",
            "snippets": ["Snippet."],
        }
        normalized = normalize_evidence_record(record)
        self.assertEqual(normalized["frameworks"], ["ISO 27001", "GDPR"])
        self.assertEqual(normalized["control_ids"], ["A.5.1", "Art. 32"])

    def test_blank_frameworks_filtered(self):
        record = {
            "title": "Test",
            "type": "policy",
            "frameworks": ["ISO 27001", "", "GDPR"],
            "last_reviewed": "2026-05-01",
            "owner": "Security",
            "summary": "A test.",
            "snippets": ["Snippet."],
        }
        normalized = normalize_evidence_record(record)
        self.assertEqual(normalized["frameworks"], ["ISO 27001", "GDPR"])


class TestRenderCustomerReadyMarkdown(unittest.TestCase):
    def test_basic_render(self):
        answer = {
            "question": "How is data encrypted?",
            "answer": "Data is encrypted in transit. [S1:encryption]",
            "confidence": "high",
            "needs_human_review": False,
            "citations": [
                {
                    "citation": "S1:encryption",
                    "title": "Encryption Standard",
                    "source_id": "encryption",
                    "last_reviewed": "2026-04-01",
                }
            ],
            "freshness": [
                {
                    "source": "encryption",
                    "status": "fresh",
                    "last_reviewed": "2026-04-01",
                    "age_days": 61,
                }
            ],
        }
        md = render_customer_ready_markdown(answer)

        self.assertIn("# Customer Security Answer", md)
        self.assertIn("## Question", md)
        self.assertIn("How is data encrypted?", md)
        self.assertIn("## Draft Answer", md)
        self.assertIn("Data is encrypted in transit.", md)
        self.assertIn("**Confidence:** high", md)
        self.assertIn("**Needs human review:** false", md)
        self.assertIn("## Sources", md)
        self.assertIn("S1:encryption", md)
        self.assertIn("## Freshness", md)
        self.assertIn("fresh", md)

    def test_no_citations(self):
        answer = {
            "question": "Question?",
            "answer": "No evidence.",
            "confidence": "low",
            "needs_human_review": True,
            "citations": [],
            "freshness": [],
        }
        md = render_customer_ready_markdown(answer)
        self.assertIn("No sources found. Do not send without review.", md)
        self.assertIn("No freshness checks available.", md)

    def test_missing_fields(self):
        md = render_customer_ready_markdown({})
        self.assertIn("**Confidence:** unknown", md)
        self.assertIn("**Needs human review:** false", md)
        self.assertIn("No sources found.", md)
        self.assertIn("No freshness checks available.", md)

    def test_citations_and_freshness_as_none(self):
        answer = {
            "question": "Q",
            "answer": "A",
            "confidence": "high",
            "needs_human_review": False,
            "citations": None,
            "freshness": None,
        }
        md = render_customer_ready_markdown(answer)
        self.assertIn("No sources found.", md)
        self.assertIn("No freshness checks available.", md)


class TestApprovalPersistence(unittest.TestCase):
    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        self.approvals_path = self.tmpdir / "approvals.json"

    def test_approval_round_trip(self):
        import web_app
        original = web_app.APPROVALS_PATH
        web_app.APPROVALS_PATH = self.approvals_path
        try:
            approvals = web_app.load_approvals()
            self.assertEqual(approvals, {})
            approval_data = {
                "How is encryption handled?": {
                    "status": "approved",
                    "reviewer": "Alice",
                    "reviewed_at": "2026-05-24T12:00:00",
                    "notes": "Looks good.",
                }
            }
            web_app.save_approvals(approval_data)
            loaded = web_app.load_approvals()
            self.assertEqual(loaded, approval_data)
            self.assertEqual(loaded["How is encryption handled?"]["status"], "approved")
            self.assertEqual(loaded["How is encryption handled?"]["reviewer"], "Alice")
        finally:
            web_app.APPROVALS_PATH = original

    def test_load_empty_missing_file(self):
        import web_app
        original = web_app.APPROVALS_PATH
        path = self.tmpdir / "nonexistent.json"
        web_app.APPROVALS_PATH = path
        try:
            approvals = web_app.load_approvals()
            self.assertEqual(approvals, {})
        finally:
            web_app.APPROVALS_PATH = original

    def test_set_approval_validates_question(self):
        import web_app
        handler = web_app.CopilotHandler
        handler.APPROVALS_PATH = self.approvals_path
        with self.assertRaises(ValueError):
            handler.set_approval(None, {})

    def test_set_approval_validates_status(self):
        import web_app
        handler = web_app.CopilotHandler
        with self.assertRaises(ValueError):
            handler.set_approval(None, {"question": "Q?", "status": "invalid"})


if __name__ == "__main__":
    unittest.main()
