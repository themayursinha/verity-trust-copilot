"""AI-powered answer engine with semantic retrieval and LLM synthesis.

Replaces BM25 keyword search with embedding-based semantic retrieval
(sentence-transformers) with graceful fallback. Supports LLM synthesis
of answers from retrieved evidence and knowledge base learning.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date
from typing import Any

import numpy as np


logger = logging.getLogger("verity.ai_engine")

EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
EMBEDDING_DIM = 384

_has_transformers = False
try:
    from sentence_transformers import SentenceTransformer

    _has_transformers = True
except ImportError:
    logger.info("sentence-transformers not installed — falling back to BM25 keyword retrieval")


@dataclass
class EvidenceChunk:
    evidence_id: str
    title: str
    evidence_type: str
    frameworks: list[str]
    control_ids: list[str]
    last_reviewed: date | None
    owner: str
    snippet: str
    summary: str


@dataclass
class RetrievalResult:
    chunk: EvidenceChunk
    score: float
    rank: int


@dataclass
class GeneratedAnswer:
    question: str
    answer_text: str
    confidence: str
    confidence_score: float
    confidence_rationale: str
    needs_human_review: bool
    citations: list[dict[str, Any]]
    freshness: list[dict[str, Any]]
    source: str = "ai"
    model: str | None = None


class AIEngine:
    def __init__(self) -> None:
        self._model: Any = None
        self._chunks: list[EvidenceChunk] = []
        self._embeddings: np.ndarray | None = None
        self._initialized = False
        self._knowledge_base: dict[str, dict[str, Any]] = {}
        self._kb_embeddings: np.ndarray | None = None
        self._kb_keys: list[str] = []

    @property
    def is_available(self) -> bool:
        return _has_transformers

    def initialize(self) -> None:
        if self._initialized:
            return
        if _has_transformers:
            try:
                self._model = SentenceTransformer(EMBEDDING_MODEL_NAME)
                logger.info(f"Loaded embedding model: {EMBEDDING_MODEL_NAME}")
            except Exception as e:
                logger.warning(f"Failed to load embedding model: {e}. Falling back to BM25.")
        self._initialized = True

    def index_evidence(self, chunks: list[EvidenceChunk]) -> None:
        self._chunks = chunks
        if not self.is_available or not self._model:
            return

        if not chunks:
            self._embeddings = None
            return

        texts = [self._chunk_to_text(c) for c in chunks]
        try:
            self._embeddings = self._model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
            logger.info(f"Indexed {len(chunks)} evidence chunks ({self._embeddings.shape[1]} dim)")
        except Exception as e:
            logger.error(f"Failed to generate embeddings: {e}")
            self._embeddings = None

    def index_knowledge_base(self, entries: list[dict[str, Any]]) -> None:
        if not self.is_available or not self._model:
            return
        if not entries:
            return

        self._kb_keys = []
        texts = []
        for entry in entries:
            key = entry.get("question", "")
            answer = entry.get("answer_text", "")
            if key and answer:
                self._kb_keys.append(key)
                texts.append(f"{key} {answer}")

        if texts:
            try:
                self._kb_embeddings = self._model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
                self._knowledge_base = {k: e for k, e in zip(self._kb_keys, entries)}
                logger.info(f"Indexed {len(entries)} knowledge base entries")
            except Exception as e:
                logger.error(f"Failed to index knowledge base: {e}")

    @staticmethod
    def _chunk_to_text(chunk: EvidenceChunk) -> str:
        parts = [
            chunk.title,
            chunk.evidence_type,
            " ".join(chunk.frameworks),
            " ".join(chunk.control_ids),
            chunk.summary,
            chunk.snippet,
        ]
        return " ".join(p for p in parts if p)

    def search(self, query: str, top_k: int = 5) -> list[RetrievalResult]:
        if not self._chunks:
            return []

        if self.is_available and self._model is not None and self._embeddings is not None and len(self._embeddings) > 0:
            return self._semantic_search(query, top_k)
        return self._fallback_bm25_search(query, top_k)

    def search_knowledge_base(self, query: str, top_k: int = 3, threshold: float = 0.5) -> list[dict[str, Any]]:
        if not self.is_available or self._model is None or self._kb_embeddings is None or len(self._kb_embeddings) == 0:
            return []

        try:
            query_vec = self._model.encode([query], convert_to_numpy=True, show_progress_bar=False)
            scores = np.dot(self._kb_embeddings, query_vec.T).flatten()
            norms = np.linalg.norm(self._kb_embeddings, axis=1) * np.linalg.norm(query_vec)
            similarities = scores / (norms + 1e-8)

            results: list[dict[str, Any]] = []
            indices = np.argsort(similarities)[::-1]
            for idx in indices:
                score = float(similarities[idx])
                if score < threshold:
                    break
                if len(results) >= top_k:
                    break
                results.append({**self._knowledge_base.get(self._kb_keys[idx], {}), "score": score})
            return results
        except Exception as e:
            logger.error(f"KB search failed: {e}")
            return []

    def _semantic_search(self, query: str, top_k: int) -> list[RetrievalResult]:
        try:
            query_vec = self._model.encode([query], convert_to_numpy=True, show_progress_bar=False)
            scores = np.dot(self._embeddings, query_vec.T).flatten()
            norms = np.linalg.norm(self._embeddings, axis=1) * np.linalg.norm(query_vec)
            similarities = scores / (norms + 1e-8)
        except Exception as e:
            logger.error(f"Semantic search failed: {e}")
            return self._fallback_bm25_search(query, top_k)

        seen_ids: set[str] = set()
        results: list[RetrievalResult] = []
        indices = np.argsort(similarities)[::-1]

        for idx in indices:
            score = float(similarities[idx])
            if score < 0.15:
                break
            chunk = self._chunks[int(idx)]
            if chunk.evidence_id not in seen_ids:
                seen_ids.add(chunk.evidence_id)
                results.append(RetrievalResult(chunk=chunk, score=score, rank=len(results) + 1))
            if len(results) >= top_k:
                break

        return results

    def _fallback_bm25_search(self, query: str, top_k: int) -> list[RetrievalResult]:
        from app.core.engine import EvidenceSnippet, compute_idf, expand_terms, tokenize, FIELDS, freshness_status

        if not self._chunks:
            return []

        snippets = [
            EvidenceSnippet(
                evidence_id=c.evidence_id,
                title=c.title,
                evidence_type=c.evidence_type,
                frameworks=c.frameworks,
                control_ids=c.control_ids,
                last_reviewed=c.last_reviewed or date.today(),
                owner=c.owner,
                snippet=c.snippet,
                summary=c.summary,
            )
            for c in self._chunks
        ]

        idf, avgdl = compute_idf(snippets)
        query_terms = expand_terms(tokenize(query))
        scores: list[tuple[float, EvidenceChunk]] = []

        for chunk, snippet in zip(self._chunks, snippets):
            score = 0.0
            for field_name, field_weight in FIELDS:
                field_text = getattr(snippet, field_name, "")
                if isinstance(field_text, list):
                    field_text = " ".join(field_text)
                field_tokens = tokenize(str(field_text))
                doc_len = len(field_tokens)

                for term, qtf in query_terms.items():
                    tf = field_tokens.count(term)
                    if tf == 0:
                        continue
                    idf_val = idf.get(term, 0.5)
                    tf_norm = (tf * 1.5) / (tf + 1.5 * (1 - 0.75 + 0.75 * doc_len / max(avgdl, 1)))
                    score += qtf * idf_val * tf_norm * field_weight

                phrase = " ".join(field_tokens)
                if len(query_terms) >= 2 and all(str(t) in phrase for t in list(query_terms.keys())[:3]):
                    score += 2.0

            status, age_days = freshness_status(snippet.last_reviewed, date.today())
            if status == "stale":
                score *= 0.9
            elif status == "outdated":
                score *= 0.7

            scores.append((score, chunk))

        scores.sort(key=lambda x: x[0], reverse=True)

        if not scores or scores[0][0] <= 0:
            return []

        cutoff = min(0.6, scores[0][0] * 0.4)
        seen_ids: set[str] = set()
        results: list[RetrievalResult] = []

        for score, chunk in scores:
            if score < cutoff:
                break
            if chunk.evidence_id not in seen_ids:
                seen_ids.add(chunk.evidence_id)
                results.append(RetrievalResult(chunk=chunk, score=score, rank=len(results) + 1))
            if len(results) >= top_k:
                break

        return results

    def compute_confidence(self, results: list[RetrievalResult], use_ai: bool = False) -> tuple[str, float, str]:
        if not results:
            return "low", 0.0, "No matching evidence found for this question."

        top_score = results[0].score
        count = len(results)

        if use_ai:
            if top_score >= 0.7 and count >= 2:
                return "high", top_score, "Strong semantic match across multiple evidence sources."
            elif top_score >= 0.5:
                return "medium", top_score, "Good semantic match, but limited evidence depth."
            elif top_score >= 0.3:
                return "low", top_score, "Weak semantic match. Human review strongly recommended."
            return "low", top_score, "No strong semantic match found."

        if top_score >= 10.0 and count >= 2:
            return "high", top_score, "Strongly matching evidence from {count} sources.".format(count=count)
        elif top_score >= 5.0:
            return "medium", top_score, "Moderate evidence match. Review before sending."
        return "low", top_score, "Weak match. Human review required."

    def build_citations(self, results: list[RetrievalResult]) -> list[dict[str, Any]]:
        citations = []
        for r in results:
            citations.append(
                {
                    "source_id": r.chunk.evidence_id,
                    "title": r.chunk.title,
                    "citation": f"[S{r.rank}:{r.chunk.evidence_id}]",
                    "snippet": r.chunk.snippet[:200],
                    "score": round(r.score, 4),
                    "last_reviewed": r.chunk.last_reviewed.isoformat() if r.chunk.last_reviewed else None,
                }
            )
        return citations

    def build_freshness(self, results: list[RetrievalResult]) -> list[dict[str, Any]]:
        from app.core.engine import freshness_status

        freshness = []
        for r in results:
            status, age_days = freshness_status(r.chunk.last_reviewed or date.today(), date.today())
            freshness.append(
                {
                    "source": r.chunk.title,
                    "status": status,
                    "last_reviewed": r.chunk.last_reviewed.isoformat() if r.chunk.last_reviewed else None,
                    "age_days": age_days,
                }
            )
        return freshness

    def build_evidence_context(self, results: list[RetrievalResult]) -> list[dict[str, Any]]:
        return [
            {
                "title": r.chunk.title,
                "type": r.chunk.evidence_type,
                "frameworks": r.chunk.frameworks,
                "summary": r.chunk.summary,
                "snippets": [r.chunk.snippet],
            }
            for r in results
        ]

    def generate_synthetic_answer(self, question: str, results: list[RetrievalResult]) -> str:
        if not results:
            return "No evidence available to answer this question. Please upload relevant evidence or mark for human completion."

        top = results[0]
        if len(results) == 1:
            return f"Based on our {top.chunk.title}, {top.chunk.snippet.strip()} [S1:{top.chunk.evidence_id}]"

        parts = []
        for i, r in enumerate(results):
            parts.append(f"{r.chunk.snippet.strip()} [S{i + 1}:{r.chunk.evidence_id}]")

        answer = "Based on our approved evidence:\n\n" + "\n\n".join(parts)
        return answer


_engine_instance: AIEngine | None = None


def get_ai_engine() -> AIEngine:
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = AIEngine()
        _engine_instance.initialize()
    return _engine_instance


def reset_ai_engine() -> None:
    global _engine_instance
    _engine_instance = None
