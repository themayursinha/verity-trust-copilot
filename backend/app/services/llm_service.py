"""LLM service for generating answer suggestions when BM25 confidence is low."""
from typing import Any

import httpx

from app.config import settings

SYSTEM_PROMPT = """You are a security compliance assistant. Draft a concise answer to the customer's security question using ONLY the evidence snippets provided below. 

Rules:
- Only use facts from the evidence. If evidence doesn't cover the question, say so honestly.
- Cite the evidence source by title in brackets, e.g., [ISO 27001 Certificate].
- Keep answers under 250 words.
- Be specific, not generic. Use concrete details from the evidence.
- If the evidence is insufficient to answer fully, note what IS covered and what requires additional documentation.
- Never fabricate certifications, controls, or capabilities."""


async def generate_llm_answer(
    question: str,
    evidence_context: list[dict[str, Any]],
) -> dict[str, Any]:
    """Generate an LLM-powered answer suggestion using available evidence."""
    if not settings.llm_configured:
        return {"error": "LLM is not configured. Set LLM_API_KEY."}

    context_text = ""
    for i, ev in enumerate(evidence_context, 1):
        context_text += f"\n[Evidence {i}: {ev.get('title', 'Untitled')}]\n"
        context_text += f"Type: {ev.get('type', 'N/A')}\n"
        context_text += f"Frameworks: {', '.join(ev.get('frameworks', []))}\n"
        context_text += f"Summary: {ev.get('summary', '')}\n"
        context_text += f"Snippets:\n"
        for snippet in ev.get("snippets", []):
            context_text += f"  - {snippet}\n"

    user_prompt = f"Question:\n{question}\n\nAvailable Evidence:\n{context_text}\n\nDraft an answer:"

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{settings.LLM_API_BASE}/chat/completions",
            headers={
                "Authorization": f"Bearer {settings.LLM_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": settings.LLM_MODEL,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                "max_tokens": settings.LLM_MAX_TOKENS,
                "temperature": 0.3,
            },
        )

    if response.status_code != 200:
        return {
            "error": f"LLM API error: {response.status_code}",
            "detail": response.text[:500],
        }

    data = response.json()
    content = data["choices"][0]["message"]["content"]
    usage = data.get("usage", {})

    return {
        "answer_text": content,
        "model": data.get("model", settings.LLM_MODEL),
        "usage": {
            "prompt_tokens": usage.get("prompt_tokens", 0),
            "completion_tokens": usage.get("completion_tokens", 0),
        },
    }
