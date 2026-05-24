import json
import sys
import tempfile
import unittest
from collections import Counter
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from security_questionnaire_copilot import (
    FRESH_DAYS,
    STALE_DAYS,
    AnswerTemplate,
    EvidenceSnippet,
    Match,
    answer_question,
    build_results,
    confidence,
    evaluate_claim_checks,
    expand_terms,
    export_csv,
    freshness_status,
    generate_answer,
    load_evidence,
    load_questions,
    load_templates,
    match_template,
    parse_date,
    render_markdown,
    retrieve,
    score_snippet,
    tokenize,
)


def make_snippet(
    *,
    evidence_id="test-id",
    title="Test Evidence",
    evidence_type="policy",
    frameworks=None,
    control_ids=None,
    last_reviewed=None,
    owner="Security",
    snippet="This is a test evidence snippet about encryption.",
    summary="A test evidence record.",
):
    return EvidenceSnippet(
        evidence_id=evidence_id,
        title=title,
        evidence_type=evidence_type,
        frameworks=frameworks or [],
        control_ids=control_ids or [],
        last_reviewed=last_reviewed or date(2026, 1, 1),
        owner=owner,
        snippet=snippet,
        summary=summary,
    )


QUALITY_ENCRYPTION_SNIPPET = (
    "Customer data is encrypted in transit using TLS 1.2 or higher. "
    "Data is encrypted at rest using cloud-provider managed encryption."
)


class TestTokenize(unittest.TestCase):
    def test_basic_tokenization(self):
        tokens = tokenize("How do you handle encryption at rest?")
        expected = ["handle", "encryption", "rest"]
        self.assertEqual(tokens, expected)

    def test_empty_string(self):
        self.assertEqual(tokenize(""), [])

    def test_only_stopwords(self):
        self.assertEqual(tokenize("a an the is it of"), [])

    def test_short_tokens_filtered(self):
        self.assertEqual(tokenize("a bc def"), ["bc", "def"])

    def test_numbers_kept(self):
        tokens = tokenize("TLS 1.2 or higher")
        self.assertIn("tls", tokens)
        self.assertIn("1.2", tokens)

    def test_parentheses_stripped(self):
        tokens = tokenize("GDPR (Article 32)")
        self.assertIn("gdpr", tokens)
        self.assertIn("article", tokens)
        self.assertIn("32", tokens)

    def test_dash_kept(self):
        tokens = tokenize("at-rest encryption")
        self.assertIn("at-rest", tokens)

    def test_lowercasing(self):
        tokens = tokenize("Encryption Key Management")
        self.assertEqual(tokens, ["encryption", "key", "management"])


class TestExpandTerms(unittest.TestCase):
    def test_basic_expansion(self):
        terms = expand_terms(["encrypt"])
        self.assertGreater(terms.get("encrypt", 0), 0)
        for related in ["encryption", "tls", "key", "keys", "at-rest", "transit"]:
            self.assertAlmostEqual(terms.get(related, 0), 0.45)

    def test_no_synonyms(self):
        terms = expand_terms(["unrelatedword"])
        self.assertEqual(terms.get("unrelatedword"), 1)

    def test_empty_input(self):
        self.assertEqual(expand_terms([]), Counter())

    def test_multiple_tokens(self):
        terms = expand_terms(["encrypt", "incident"])
        self.assertIn("encrypt", terms)
        self.assertIn("breach", terms)
        self.assertIn("triage", terms)


class TestLoadTemplates(unittest.TestCase):
    def test_load_from_file(self):
        path = Path(__file__).resolve().parent.parent / "templates" / "answer_templates.json"
        templates = load_templates(path)
        self.assertGreater(len(templates), 0)
        self.assertIsInstance(templates[0], AnswerTemplate)
        self.assertTrue(hasattr(templates[0], "category"))
        self.assertTrue(hasattr(templates[0], "keywords"))
        self.assertTrue(hasattr(templates[0], "label"))

    def test_missing_file(self):
        templates = load_templates(Path("/nonexistent/templates.json"))
        self.assertEqual(templates, [])

    def test_template_has_intro(self):
        path = Path(__file__).resolve().parent.parent / "templates" / "answer_templates.json"
        templates = load_templates(path)
        encryption = [t for t in templates if t.category == "encryption"]
        self.assertEqual(len(encryption), 1)
        self.assertIsNotNone(encryption[0].intro)

    def test_template_has_keywords(self):
        path = Path(__file__).resolve().parent.parent / "templates" / "answer_templates.json"
        templates = load_templates(path)
        self.assertIn("encryption", templates[0].keywords)


class TestMatchTemplate(unittest.TestCase):
    def setUp(self):
        self.templates = [
            AnswerTemplate(
                category="encryption",
                keywords=["encrypt", "encryption", "tls", "at-rest"],
                label="Encryption",
                intro="Encryption controls.",
            ),
            AnswerTemplate(
                category="access-control",
                keywords=["access", "sso", "mfa", "offboarding"],
                label="Access Control",
                intro="Access controls.",
            ),
        ]

    def test_matches_encryption(self):
        result = match_template("How do you encrypt data and use tls?", self.templates)
        self.assertIsNotNone(result)
        self.assertEqual(result.category, "encryption")

    def test_matches_access_control(self):
        result = match_template("How is sso and mfa access controlled?", self.templates)
        self.assertIsNotNone(result)
        self.assertEqual(result.category, "access-control")

    def test_no_match_single_keyword(self):
        result = match_template("How about encryption?", self.templates)
        self.assertIsNone(result)

    def test_no_match(self):
        result = match_template("What is the weather?", self.templates)
        self.assertIsNone(result)

    def test_empty_question(self):
        result = match_template("", self.templates)
        self.assertIsNone(result)

    def test_empty_templates(self):
        result = match_template("encryption tls", [])
        self.assertIsNone(result)


class TestParseDate(unittest.TestCase):
    def test_valid_date(self):
        self.assertEqual(parse_date("2026-05-21"), date(2026, 5, 21))

    def test_invalid_date(self):
        with self.assertRaises(ValueError):
            parse_date("not-a-date")

    def test_empty_string(self):
        with self.assertRaises(ValueError):
            parse_date("")


class TestFreshnessStatus(unittest.TestCase):
    def setUp(self):
        self.as_of = date(2026, 6, 1)

    def test_zero_days(self):
        status, age = freshness_status(self.as_of, self.as_of)
        self.assertEqual(status, "fresh")
        self.assertEqual(age, 0)

    def test_fresh_boundary(self):
        reviewed = self.as_of - timedelta(days=FRESH_DAYS)
        status, age = freshness_status(reviewed, self.as_of)
        self.assertEqual(status, "fresh")
        self.assertEqual(age, FRESH_DAYS)

    def test_stale_boundary_start(self):
        reviewed = self.as_of - timedelta(days=FRESH_DAYS + 1)
        status, age = freshness_status(reviewed, self.as_of)
        self.assertEqual(status, "stale")
        self.assertEqual(age, FRESH_DAYS + 1)

    def test_stale_boundary_end(self):
        reviewed = self.as_of - timedelta(days=STALE_DAYS)
        status, age = freshness_status(reviewed, self.as_of)
        self.assertEqual(status, "stale")
        self.assertEqual(age, STALE_DAYS)

    def test_outdated_boundary(self):
        reviewed = self.as_of - timedelta(days=STALE_DAYS + 1)
        status, age = freshness_status(reviewed, self.as_of)
        self.assertEqual(status, "outdated")
        self.assertEqual(age, STALE_DAYS + 1)

    def test_future_date(self):
        reviewed = self.as_of + timedelta(days=30)
        status, age = freshness_status(reviewed, self.as_of)
        self.assertEqual(status, "fresh")
        self.assertEqual(age, -30)


class TestScoreSnippet(unittest.TestCase):
    def test_no_match(self):
        snippet = make_snippet(snippet="This is about unrelated content.")
        result = score_snippet("How about encryption?", snippet, date(2026, 6, 1))
        self.assertIsNone(result)

    def test_basic_match(self):
        snippet = make_snippet(snippet="We handle encryption at rest.")
        result = score_snippet("How do you handle encryption?", snippet, date(2026, 6, 1))
        self.assertIsNotNone(result)
        self.assertGreater(result.score, 0)
        self.assertIn("encryption", result.matched_terms)
        self.assertIn("handle", result.matched_terms)

    def test_stale_penalty(self):
        reviewed = date(2026, 1, 1)
        as_of = reviewed + timedelta(days=FRESH_DAYS + 1)
        snippet = make_snippet(snippet="We handle encryption.", last_reviewed=reviewed)
        result = score_snippet("encryption", snippet, as_of)
        self.assertIsNotNone(result)
        self.assertEqual(result.freshness, "stale")

    def test_outdated_penalty(self):
        reviewed = date(2024, 1, 1)
        as_of = reviewed + timedelta(days=STALE_DAYS + 1)
        snippet = make_snippet(snippet="We handle encryption.", last_reviewed=reviewed)
        result = score_snippet("encryption", snippet, as_of)
        self.assertIsNotNone(result)
        self.assertEqual(result.freshness, "outdated")

    def test_freshness_age_days(self):
        as_of = date(2026, 6, 1)
        reviewed = date(2026, 1, 1)
        snippet = make_snippet(snippet="encryption", last_reviewed=reviewed)
        result = score_snippet("encryption", snippet, as_of)
        self.assertIsNotNone(result)
        self.assertEqual(result.age_days, (as_of - reviewed).days)

    def test_match_fields_present(self):
        snippet = make_snippet(snippet="encryption")
        result = score_snippet("encryption", snippet, date(2026, 6, 1))
        self.assertIsNotNone(result)
        self.assertIsInstance(result.score, float)
        self.assertIsInstance(result.matched_terms, list)
        self.assertIn(result.freshness, ["fresh", "stale", "outdated"])

    def test_title_and_summary_scored(self):
        snippet = make_snippet(
            title="Encryption Key Management",
            summary="Overview of encryption key management practices.",
            snippet="Keys are stored securely.",
        )
        result = score_snippet("encryption key management", snippet, date(2026, 6, 1))
        self.assertIsNotNone(result)
        self.assertGreater(result.score, 0)


class TestRetrieve(unittest.TestCase):
    def test_no_matches(self):
        snippets = [make_snippet(snippet="unrelated content.")]
        results = retrieve("encryption", snippets, date(2026, 6, 1))
        self.assertEqual(results, [])

    def test_basic_retrieval(self):
        snippets = [
            make_snippet(evidence_id="a", snippet="encryption is important."),
            make_snippet(evidence_id="b", snippet="access control is important."),
        ]
        results = retrieve("encryption", snippets, date(2026, 6, 1))
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].snippet.evidence_id, "a")

    def test_sorted_by_score(self):
        snippets = [
            make_snippet(evidence_id="a", snippet="encryption encryption encryption."),
            make_snippet(evidence_id="b", snippet="encryption."),
        ]
        results = retrieve("encryption", snippets, date(2026, 6, 1))
        self.assertEqual(len(results), 2)
        self.assertGreater(results[0].score, results[1].score)

    def test_dedup_same_id_and_snippet(self):
        snippets = [
            make_snippet(evidence_id="a", snippet="encryption is important."),
            make_snippet(evidence_id="a", snippet="encryption is important."),
        ]
        results = retrieve("encryption", snippets, date(2026, 6, 1))
        self.assertEqual(len(results), 1)

    def test_max_matches_limit(self):
        snippets = [make_snippet(evidence_id=f"e{i}", snippet="encryption is essential.") for i in range(10)]
        results = retrieve("encryption essential", snippets, date(2026, 6, 1))
        self.assertLessEqual(len(results), 4)

    def test_empty_snippets(self):
        results = retrieve("encryption", [], date(2026, 6, 1))
        self.assertEqual(results, [])

    def test_score_cutoff_applied(self):
        snippets = [
            make_snippet(evidence_id="high", snippet="encryption encryption encryption encryption encryption."),
            make_snippet(evidence_id="low", snippet="random text that does not match the question."),
        ]
        results = retrieve("encryption", snippets, date(2026, 6, 1))
        ids = [r.snippet.evidence_id for r in results]
        self.assertIn("high", ids)
        self.assertNotIn("low", ids)


class TestConfidence(unittest.TestCase):
    def make_match(self, score, freshness="fresh", evidence_id="source-a"):
        snippet = make_snippet(evidence_id=evidence_id)
        return Match(
            snippet=snippet,
            score=score,
            matched_terms=["test"],
            freshness=freshness,
            age_days=0,
        )

    def test_empty_matches(self):
        level, rationale = confidence([])
        self.assertEqual(level, "low")
        self.assertIn("No approved evidence matched", rationale)

    def test_high_confidence(self):
        matches = [
            self.make_match(score=6.0, freshness="fresh", evidence_id="src-a"),
            self.make_match(score=5.9, freshness="fresh", evidence_id="src-b"),
        ]
        level, _ = confidence(matches)
        self.assertEqual(level, "high")

    def test_high_confidence_single_source(self):
        matches = [
            self.make_match(score=6.0, freshness="fresh", evidence_id="src-a"),
            self.make_match(score=5.9, freshness="fresh", evidence_id="src-a"),
        ]
        level, _ = confidence(matches)
        self.assertEqual(level, "high")

    def test_medium_confidence(self):
        matches = [
            self.make_match(score=4.0, freshness="fresh", evidence_id="src-a"),
        ]
        level, _ = confidence(matches)
        self.assertEqual(level, "medium")

    def test_low_confidence_low_score(self):
        matches = [
            self.make_match(score=1.0, freshness="fresh", evidence_id="src-a"),
        ]
        level, _ = confidence(matches)
        self.assertEqual(level, "low")

    def test_low_confidence_outdated(self):
        matches = [
            self.make_match(score=6.0, freshness="outdated", evidence_id="src-a"),
            self.make_match(score=5.0, freshness="outdated", evidence_id="src-b"),
        ]
        level, _ = confidence(matches)
        self.assertEqual(level, "low")

    def test_medium_with_stale_allowed(self):
        matches = [
            self.make_match(score=4.0, freshness="stale", evidence_id="src-a"),
        ]
        level, _ = confidence(matches)
        self.assertEqual(level, "medium")


class TestClaimChecks(unittest.TestCase):
    def test_fedramp_negative_evidence_requires_review(self):
        snippets = [
            make_snippet(
                evidence_id="unsupported-fedramp",
                title="Unsupported Claims Register",
                snippet="Verity does not currently have approved evidence to claim FedRAMP authorization.",
                summary="Tracks claims Verity must not make because there is no approved evidence.",
                last_reviewed=date(2026, 5, 1),
            )
        ]
        result = answer_question("Are you FedRAMP authorized?", snippets, date(2026, 6, 1))

        self.assertEqual(result["confidence"], "low")
        self.assertTrue(result["needs_human_review"])
        self.assertEqual(result["claim_checks"][0]["category"], "fedramp")
        self.assertEqual(result["claim_checks"][0]["status"], "review_required")

    def test_hipaa_without_support_requires_review(self):
        snippets = [
            make_snippet(
                evidence_id="privacy",
                title="Privacy Program",
                snippet="Verity processes customer data under documented privacy controls.",
                summary="Privacy controls are documented.",
                last_reviewed=date(2026, 5, 1),
            )
        ]

        result = answer_question("Are you HIPAA compliant?", snippets, date(2026, 6, 1))

        self.assertEqual(result["confidence"], "low")
        self.assertTrue(result["needs_human_review"])
        self.assertEqual(result["claim_checks"][0]["category"], "hipaa")

    def test_iso_certified_question_with_alignment_only_requires_review(self):
        snippets = [
            make_snippet(
                evidence_id="iso-27001-isms",
                title="ISO 27001 Information Security Management System",
                frameworks=["ISO 27001"],
                snippet="Verity operates an ISO 27001-aligned ISMS.",
                summary="Verity maintains an ISO 27001-aligned information security management system.",
                last_reviewed=date(2026, 5, 1),
            )
        ]

        result = answer_question("Are you ISO 27001 certified?", snippets, date(2026, 6, 1))

        self.assertEqual(result["confidence"], "low")
        self.assertTrue(result["needs_human_review"])
        categories = {check["category"] for check in result["claim_checks"]}
        self.assertIn("iso-27001-certification", categories)

    def test_customer_specific_commitment_requires_review(self):
        matches = []
        checks = evaluate_claim_checks("Can you commit to our custom SLA in the contract?", matches)

        self.assertEqual(checks[0]["category"], "customer-specific-commitment")
        self.assertEqual(checks[0]["status"], "review_required")


class TestGenerateAnswer(unittest.TestCase):
    def make_match(
        self, score=5.0, freshness="fresh", snippet_text="Approved evidence snippet.", evidence_id="test-id"
    ):
        snippet = make_snippet(snippet=snippet_text, evidence_id=evidence_id)
        return Match(
            snippet=snippet,
            score=score,
            matched_terms=["test"],
            freshness=freshness,
            age_days=0,
        )

    def test_no_matches(self):
        answer = generate_answer("Some question?", [], "low")
        self.assertIn("Needs human review", answer)
        self.assertIn("could not find approved evidence", answer)

    def test_low_confidence(self):
        matches = [self.make_match(score=1.0)]
        answer = generate_answer("Some question?", matches, "low")
        self.assertIn("Needs human review", answer)

    def test_normal_confidence(self):
        matches = [self.make_match(score=5.0, snippet_text="Data is encrypted at rest.")]
        answer = generate_answer("How is data encrypted?", matches, "high")
        self.assertIn("Draft answer based on approved evidence", answer)
        self.assertIn("Data is encrypted at rest", answer)

    def test_citations_included(self):
        matches = [
            self.make_match(score=5.0, snippet_text="First snippet.", evidence_id="src-a"),
            self.make_match(score=4.0, snippet_text="Second snippet.", evidence_id="src-b"),
        ]
        answer = generate_answer("Question?", matches, "medium")
        self.assertIn("[S1:src-a]", answer)
        self.assertIn("[S2:src-b]", answer)

    def test_template_intro_included(self):
        template = AnswerTemplate(
            category="encryption",
            keywords=["encrypt", "encryption"],
            label="Encryption",
            intro="Customer data is encrypted using the following controls:",
        )
        matches = [self.make_match(score=5.0, snippet_text="TLS 1.2 is used.")]
        answer = generate_answer("How is encryption handled?", matches, "high", template)
        self.assertIn("Draft answer based on approved evidence for Encryption", answer)
        self.assertIn("Customer data is encrypted using the following controls", answer)
        self.assertIn("TLS 1.2 is used", answer)

    def test_template_outro_included(self):
        template = AnswerTemplate(
            category="fedramp",
            keywords=["fedramp"],
            label="FedRAMP",
            intro="Verity does not hold FedRAMP authorization.",
            outro="Do not communicate FedRAMP authorization to customers.",
        )
        matches = [self.make_match(score=5.0, snippet_text="No evidence for FedRAMP.")]
        answer = generate_answer("Are you FedRAMP authorized?", matches, "high", template)
        self.assertIn("Do not communicate FedRAMP authorization", answer)

    def test_template_outro_suppressed_on_low_confidence(self):
        template = AnswerTemplate(
            category="fedramp",
            keywords=["fedramp"],
            label="FedRAMP",
            intro="Verity does not hold FedRAMP authorization.",
            outro="Do not communicate FedRAMP authorization to customers.",
        )
        matches = [self.make_match(score=0.5, snippet_text="Weak evidence.")]
        answer = generate_answer("Are you FedRAMP authorized?", matches, "low", template)
        self.assertNotIn("Do not communicate FedRAMP authorization", answer)
        self.assertIn("Needs human review", answer)

    def test_template_none_uses_default_lead(self):
        matches = [self.make_match(score=5.0, snippet_text="Data is encrypted.")]
        answer = generate_answer("How is encryption handled?", matches, "high")
        self.assertIn("Draft answer based on approved evidence:", answer)
        self.assertNotIn("approved evidence for", answer)


class TestAnswerQuestion(unittest.TestCase):
    def test_full_answer_structure(self):
        snippets = [
            make_snippet(
                evidence_id="encryption",
                title="Encryption Standard",
                snippet="Data is encrypted in transit using TLS.",
                last_reviewed=date(2026, 5, 1),
            )
        ]
        result = answer_question("How is data encrypted?", snippets, date(2026, 6, 1))

        self.assertIn("question", result)
        self.assertIn("answer", result)
        self.assertIn("confidence", result)
        self.assertIn("needs_human_review", result)
        self.assertIn("template_category", result)
        self.assertIn("confidence_rationale", result)
        self.assertIn("freshness", result)
        self.assertIn("citations", result)

        self.assertEqual(result["question"], "How is data encrypted?")
        self.assertIsInstance(result["needs_human_review"], bool)
        self.assertIn(result["confidence"], ["high", "medium", "low"])
        self.assertIsInstance(result["citations"], list)
        self.assertIsInstance(result["freshness"], list)

    def test_no_evidence_match(self):
        snippets = [make_snippet(snippet="Unrelated content about gardening.")]
        result = answer_question("How is encryption handled?", snippets, date(2026, 6, 1))
        self.assertEqual(result["confidence"], "low")
        self.assertTrue(result["needs_human_review"])

    def test_citation_structure(self):
        snippets = [
            make_snippet(evidence_id="encryption", snippet="TLS is used for encryption."),
        ]
        result = answer_question("encryption", snippets, date(2026, 6, 1))

        citation = result["citations"][0]
        self.assertEqual(citation["citation"], "S1:encryption")
        self.assertEqual(citation["source_id"], "encryption")
        self.assertEqual(citation["score"], citation.get("score"))
        self.assertEqual(citation["matched_terms"], citation.get("matched_terms"))

    def test_template_matching_with_templates(self):
        templates = [
            AnswerTemplate(
                category="encryption",
                keywords=["encrypt", "encryption", "tls", "at-rest"],
                label="Encryption",
                intro="Encryption controls.",
            ),
        ]
        snippets = [
            make_snippet(
                evidence_id="encryption",
                snippet=(
                    "TLS is used for encryption encryption encryption encryption "
                    "encryption encryption encryption encryption at rest."
                ),
                last_reviewed=date(2026, 5, 1),
            ),
            make_snippet(
                evidence_id="unrelated",
                snippet="This is a snippet about unrelated content.",
                last_reviewed=date(2026, 5, 1),
            ),
            make_snippet(
                evidence_id="also-unrelated",
                snippet="This is also completely unrelated.",
                last_reviewed=date(2026, 5, 1),
            ),
        ]
        result = answer_question("How is encryption and tls handled?", snippets, date(2026, 6, 1), templates)
        self.assertEqual(result["template_category"], "encryption")
        self.assertIn("Draft answer based on approved evidence for Encryption", result["answer"])

    def test_no_template_without_templates_param(self):
        snippets = [
            make_snippet(evidence_id="encryption", snippet="TLS is used for encryption."),
        ]
        result = answer_question("encryption", snippets, date(2026, 6, 1))
        self.assertIsNone(result["template_category"])


class TestBuildResults(unittest.TestCase):
    def test_multiple_questions(self):
        snippets = [
            make_snippet(snippet="encryption is used."),
            make_snippet(evidence_id="access", snippet="access control is enforced."),
        ]
        results = build_results(
            ["How is encryption handled?", "How is access controlled?"],
            snippets,
            date(2026, 6, 1),
        )

        self.assertEqual(results["summary"]["questions_processed"], 2)
        self.assertEqual(len(results["answers"]), 2)
        self.assertIn("generated_at", results)
        self.assertIn("as_of_date", results)

    def test_confidence_counts(self):
        snippets: list[EvidenceSnippet] = []
        results = build_results(
            ["A question with no matching evidence at all."],
            snippets,
            date(2026, 6, 1),
        )
        self.assertEqual(results["summary"]["confidence_counts"].get("low", 0), 1)
        self.assertEqual(results["summary"]["human_reviews_required"], 1)

    def test_confidence_counts_high(self):
        snippet = make_snippet(
            evidence_id="e1",
            snippet="encryption encryption encryption encryption encryption encryption.",
        )
        results = build_results(
            ["encryption"],
            [snippet],
            date(2026, 6, 1),
        )
        self.assertIn(
            results["answers"][0]["confidence"],
            ["high", "medium", "low"],
        )


class TestRenderMarkdown(unittest.TestCase):
    def test_basic_rendering(self):
        results = {
            "generated_at": "2026-06-01T12:00:00",
            "as_of_date": "2026-06-01",
            "summary": {
                "questions_processed": 1,
                "confidence_counts": {"high": 1},
                "human_reviews_required": 0,
            },
            "answers": [
                {
                    "question": "How is encryption handled?",
                    "answer": "Draft answer based on approved evidence: Data is encrypted. [S1:encryption]",
                    "confidence": "high",
                    "needs_human_review": False,
                    "confidence_rationale": "Strong keyword coverage.",
                    "freshness": [
                        {
                            "source": "encryption",
                            "last_reviewed": "2026-04-01",
                            "age_days": 61,
                            "status": "fresh",
                        }
                    ],
                    "citations": [
                        {
                            "citation": "S1:encryption",
                            "source_id": "encryption",
                            "title": "Encryption Standard",
                            "type": "standard",
                            "frameworks": ["ISO 27001"],
                            "control_ids": ["A.8.24"],
                            "owner": "Security",
                            "last_reviewed": "2026-04-01",
                            "snippet": "Data is encrypted.",
                            "score": 5.0,
                            "matched_terms": ["encryption"],
                        }
                    ],
                }
            ],
        }
        md = render_markdown(results)

        self.assertIn("Verity Trust Copilot Report", md)
        self.assertIn("Generated: 2026-06-01T12:00:00", md)
        self.assertIn("Questions processed: 1", md)
        self.assertIn("High confidence: 1", md)
        self.assertIn("How is encryption handled?", md)
        self.assertIn("Draft answer based on approved evidence", md)
        self.assertIn("S1:encryption", md)
        self.assertIn("Guardrail", md)

    def test_needs_review_marking(self):
        results = {
            "generated_at": "2026-06-01T12:00:00",
            "as_of_date": "2026-06-01",
            "summary": {
                "questions_processed": 1,
                "confidence_counts": {"low": 1},
                "human_reviews_required": 1,
            },
            "answers": [
                {
                    "question": "Are we FedRAMP authorized?",
                    "answer": "Needs human review. No approved evidence found.",
                    "confidence": "low",
                    "needs_human_review": True,
                    "confidence_rationale": "No evidence.",
                    "freshness": [],
                    "citations": [],
                }
            ],
        }
        md = render_markdown(results)
        self.assertIn("Needs human review:** yes", md)
        self.assertIn("Low confidence / human review: 1", md)

    def test_no_citations_handling(self):
        results = {
            "generated_at": "2026-06-01T12:00:00",
            "as_of_date": "2026-06-01",
            "summary": {
                "questions_processed": 1,
                "confidence_counts": {"low": 1},
                "human_reviews_required": 1,
            },
            "answers": [
                {
                    "question": "Question?",
                    "answer": "No evidence.",
                    "confidence": "low",
                    "needs_human_review": True,
                    "confidence_rationale": "No evidence.",
                    "freshness": [],
                    "citations": [],
                }
            ],
        }
        md = render_markdown(results)
        self.assertIn("No matching evidence found.", md)
        self.assertIn("No citations available.", md)


class TestExportCSV(unittest.TestCase):
    def test_basic_export(self):
        results = {
            "generated_at": "2026-06-01T12:00:00",
            "as_of_date": "2026-06-01",
            "summary": {"questions_processed": 1, "confidence_counts": {"high": 1}, "human_reviews_required": 0},
            "answers": [
                {
                    "question": "How is encryption handled?",
                    "answer": "Draft answer: Data is encrypted. [S1:encryption]",
                    "confidence": "high",
                    "needs_human_review": False,
                    "template_category": "encryption",
                    "citations": [{"citation": "S1:encryption"}],
                    "freshness": [{"source": "encryption", "status": "fresh"}],
                }
            ],
        }
        csv_output = export_csv(results)
        self.assertIn("Question", csv_output)
        self.assertIn("How is encryption handled?", csv_output)
        self.assertIn("high", csv_output)
        self.assertIn("S1:encryption", csv_output)
        self.assertIn("encryption: fresh", csv_output)

    def test_empty_answers(self):
        results = {
            "generated_at": "2026-06-01T12:00:00",
            "as_of_date": "2026-06-01",
            "summary": {"questions_processed": 0, "confidence_counts": {}, "human_reviews_required": 0},
            "answers": [],
        }
        csv_output = export_csv(results)
        self.assertIn("Question", csv_output)
        self.assertEqual(len(csv_output.strip().splitlines()), 1)

    def test_multiple_answers(self):
        results = {
            "generated_at": "2026-06-01T12:00:00",
            "as_of_date": "2026-06-01",
            "summary": {
                "questions_processed": 2,
                "confidence_counts": {"high": 1, "low": 1},
                "human_reviews_required": 1,
            },
            "answers": [
                {
                    "question": "Q1?",
                    "answer": "A1",
                    "confidence": "high",
                    "needs_human_review": False,
                    "template_category": "encryption",
                    "citations": [{"citation": "S1:encryption"}],
                    "freshness": [{"source": "encryption", "status": "fresh"}],
                },
                {
                    "question": "Q2?",
                    "answer": "A2",
                    "confidence": "low",
                    "needs_human_review": True,
                    "template_category": None,
                    "citations": [],
                    "freshness": [],
                },
            ],
        }
        csv_output = export_csv(results)
        lines = csv_output.strip().splitlines()
        self.assertEqual(len(lines), 3)
        self.assertIn("Q1?", lines[1])
        self.assertIn("Q2?", lines[2])
        self.assertIn("encryption", lines[1])


class TestLoadEvidence(unittest.TestCase):
    def test_load_from_json(self):
        data = [
            {
                "id": "test-1",
                "title": "Test Evidence",
                "type": "policy",
                "frameworks": ["GDPR"],
                "control_ids": ["Art. 5"],
                "last_reviewed": "2026-01-15",
                "owner": "Security",
                "summary": "A test record.",
                "snippets": ["Snippet one.", "Snippet two."],
            }
        ]
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(data, f)
            f.flush()
            snippets = load_evidence(Path(f.name))

        self.assertEqual(len(snippets), 2)
        for snippet in snippets:
            self.assertEqual(snippet.evidence_id, "test-1")
            self.assertEqual(snippet.title, "Test Evidence")
            self.assertEqual(snippet.evidence_type, "policy")
            self.assertEqual(snippet.frameworks, ["GDPR"])
            self.assertEqual(snippet.control_ids, ["Art. 5"])
            self.assertEqual(snippet.owner, "Security")
            self.assertEqual(snippet.last_reviewed, date(2026, 1, 15))
        self.assertEqual(snippets[0].snippet, "Snippet one.")
        self.assertEqual(snippets[1].snippet, "Snippet two.")


class TestLoadQuestions(unittest.TestCase):
    def test_list_format(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(["Q1?", "Q2?", "Q3?"], f)
            f.flush()
            questions = load_questions(Path(f.name))
        self.assertEqual(questions, ["Q1?", "Q2?", "Q3?"])

    def test_object_format(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({"questions": ["Q1?", "Q2?"]}, f)
            f.flush()
            questions = load_questions(Path(f.name))
        self.assertEqual(questions, ["Q1?", "Q2?"])

    def test_invalid_format(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({"not_questions": []}, f)
            f.flush()
        with self.assertRaises(ValueError):
            load_questions(Path(f.name))

    def test_empty_list(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump([], f)
            f.flush()
            questions = load_questions(Path(f.name))
        self.assertEqual(questions, [])


if __name__ == "__main__":
    unittest.main()
