"""Tests for the AI-powered answer engine."""

import sys
from datetime import date
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.ai_engine import AIEngine, EvidenceChunk, get_ai_engine, reset_ai_engine


@pytest.fixture
def sample_chunks():
    return [
        EvidenceChunk(
            evidence_id="ev-1",
            title="Encryption and Key Management",
            evidence_type="infrastructure",
            frameworks=["soc2", "iso27001"],
            control_ids=["CC6.1", "A.10.1.1"],
            last_reviewed=date.today(),
            owner="security@example.com",
            snippet="All customer data is encrypted at rest using AES-256 and in transit using TLS 1.3.",
            summary="Encryption standards for data protection.",
        ),
        EvidenceChunk(
            evidence_id="ev-2",
            title="Access Control Policy",
            evidence_type="policy",
            frameworks=["soc2", "gdpr"],
            control_ids=["CC6.2"],
            last_reviewed=date.today(),
            owner="security@example.com",
            snippet="Role-based access control with MFA enforced for all production systems.",
            summary="Access control and authentication policies.",
        ),
        EvidenceChunk(
            evidence_id="ev-3",
            title="Incident Response Plan",
            evidence_type="plan",
            frameworks=["soc2", "iso27001"],
            control_ids=["CC7.3"],
            last_reviewed=date(2024, 1, 15),
            owner="security@example.com",
            snippet="Incidents are triaged within 1 hour and notified to customers within 24 hours.",
            summary="Incident response and notification procedures.",
        ),
    ]


class TestAIEngine:
    def test_init(self):
        engine = AIEngine()
        assert engine._model is None
        assert engine._chunks == []
        assert engine._embeddings is None

    def test_chunk_to_text(self):
        chunk = EvidenceChunk(
            evidence_id="ev-1",
            title="Test Policy",
            evidence_type="policy",
            frameworks=["soc2"],
            control_ids=["CC1.1"],
            last_reviewed=date.today(),
            owner="test@test.com",
            snippet="Test snippet content.",
            summary="Test summary.",
        )
        text = AIEngine._chunk_to_text(chunk)
        assert "Test Policy" in text
        assert "soc2" in text
        assert "CC1.1" in text
        assert "Test snippet content." in text
        assert "Test summary." in text

    def test_search_no_chunks(self):
        engine = AIEngine()
        results = engine.search("How do you encrypt data?")
        assert results == []

    def test_fallback_bm25_search(self, sample_chunks):
        engine = AIEngine()
        engine._chunks = sample_chunks

        results = engine.search("encryption data protection")
        assert len(results) > 0
        assert results[0].chunk.evidence_id == "ev-1"

    def test_fallback_bm25_search_no_match(self, sample_chunks):
        engine = AIEngine()
        engine._chunks = sample_chunks

        results = engine.search("quantum computing physics")
        assert len(results) <= 1

    def test_compute_confidence_high(self, sample_chunks):
        engine = AIEngine()
        engine._chunks = sample_chunks
        results = engine.search("encryption data protection")

        confidence, score, rationale = engine.compute_confidence(results)
        assert confidence in ("high", "medium", "low")
        assert isinstance(score, float)
        assert len(rationale) > 0

    def test_compute_confidence_no_results(self):
        engine = AIEngine()
        confidence, score, rationale = engine.compute_confidence([])
        assert confidence == "low"
        assert score == 0.0
        assert "No matching evidence" in rationale

    def test_build_citations(self, sample_chunks):
        engine = AIEngine()
        engine._chunks = sample_chunks
        results = engine.search("encryption")

        citations = engine.build_citations(results)
        assert len(citations) > 0
        assert "source_id" in citations[0]
        assert "title" in citations[0]
        assert "citation" in citations[0]

    def test_build_freshness(self, sample_chunks):
        engine = AIEngine()
        engine._chunks = sample_chunks
        results = engine.search("encryption")

        freshness = engine.build_freshness(results)
        assert len(freshness) > 0
        assert "source" in freshness[0]
        assert "status" in freshness[0]

    def test_build_evidence_context(self, sample_chunks):
        engine = AIEngine()
        engine._chunks = sample_chunks
        results = engine.search("encryption")

        context = engine.build_evidence_context(results)
        assert len(context) > 0
        assert "title" in context[0]
        assert "snippets" in context[0]

    def test_generate_synthetic_answer(self, sample_chunks):
        engine = AIEngine()
        engine._chunks = sample_chunks
        results = engine.search("encryption")

        answer = engine.generate_synthetic_answer("How do you encrypt data?", results)
        assert len(answer) > 0
        assert "S1:" in answer or "[S1:" in answer

    def test_generate_synthetic_answer_no_results(self):
        engine = AIEngine()
        answer = engine.generate_synthetic_answer("Test question?", [])
        assert "No evidence available" in answer

    def test_get_ai_engine_singleton(self):
        reset_ai_engine()
        engine1 = get_ai_engine()
        engine2 = get_ai_engine()
        assert engine1 is engine2

    def test_search_knowledge_base_empty(self):
        engine = AIEngine()
        results = engine.search_knowledge_base("test query")
        assert results == []

    def test_index_evidence_empty(self):
        engine = AIEngine()
        engine.index_evidence([])
        assert engine._chunks == []
        assert engine._embeddings is None


class TestAIEngineWithoutTransformers:
    @pytest.fixture(autouse=True)
    def setup_no_transformers(self):
        with patch("app.core.ai_engine._has_transformers", False):
            yield

    def test_is_available_false(self):
        engine = AIEngine()
        assert not engine.is_available

    def test_index_evidence_skips_embedding(self, sample_chunks):
        engine = AIEngine()
        engine.index_evidence(sample_chunks)
        assert len(engine._chunks) == len(sample_chunks)
        assert engine._embeddings is None

    def test_search_falls_back_to_bm25(self, sample_chunks):
        engine = AIEngine()
        engine._chunks = sample_chunks
        results = engine.search("encryption")
        assert len(results) > 0

    def test_initialize_without_transformers(self):
        engine = AIEngine()
        engine.initialize()
        assert engine._initialized
        assert engine._model is None
