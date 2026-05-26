"""LLM service for AI-powered answer synthesis. Supports 10+ LLM providers."""

from typing import Any

import httpx

from app.config import settings
from app.services.llm_providers import get_provider_config

SYSTEM_PROMPT = """You are a security compliance assistant. Draft a concise answer to the customer's security question using ONLY the evidence snippets provided below.

Rules:
- Only use facts from the evidence. If evidence doesn't cover the question, say so honestly.
- Cite the evidence source by title in brackets, e.g., [ISO 27001 Certificate].
- Keep answers under 250 words.
- Be specific, not generic. Use concrete details from the evidence.
- If the evidence is insufficient to answer fully, note what IS covered and what requires additional documentation.
- Never fabricate certifications, controls, or capabilities."""


def _resolve_config() -> tuple[str, str, str, dict[str, str]]:
    provider_info = get_provider_config(settings.LLM_PROVIDER) or get_provider_config("custom") or {}
    api_type = provider_info.get("api_type", "openai")
    base_url = str(
        provider_info.get("base_url", settings.LLM_API_BASE)
        if settings.LLM_PROVIDER != "custom"
        else settings.LLM_API_BASE
    )

    from app.services.llm_providers import get_model_for_provider

    model = get_model_for_provider(
        settings.LLM_PROVIDER, settings.LLM_MODEL if settings.LLM_PROVIDER != "ollama" else None
    )

    if settings.LLM_PROVIDER == "ollama" and not model:
        model = str(settings.OLLAMA_MODEL)

    if not model:
        model = str(settings.LLM_MODEL)

    model = str(model)

    if provider_info.get("no_auth"):
        headers = {"Content-Type": "application/json"}
    elif api_type == "anthropic":
        headers = {
            "x-api-key": settings.LLM_API_KEY,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }
    else:
        headers = {
            "Authorization": f"Bearer {settings.LLM_API_KEY}",
            "Content-Type": "application/json",
        }

    return api_type, base_url, model, headers


async def generate_llm_answer(
    question: str,
    evidence_context: list[dict[str, Any]],
    custom_instructions: str = "",
) -> dict[str, Any]:
    if not settings.llm_configured:
        return {"error": "LLM is not configured. Set LLM_API_KEY and LLM_PROVIDER in environment."}

    context_text = ""
    for i, ev in enumerate(evidence_context, 1):
        context_text += f"\n[Evidence {i}: {ev.get('title', 'Untitled')}]\n"
        context_text += f"Type: {ev.get('type', 'N/A')}\n"
        context_text += f"Frameworks: {', '.join(ev.get('frameworks', []))}\n"
        context_text += f"Summary: {ev.get('summary', '')}\n"
        context_text += "Snippets:\n"
        for snippet in ev.get("snippets", []):
            context_text += f"  - {snippet}\n"

    user_prompt = f"Question:\n{question}\n\nAvailable Evidence:\n{context_text}\n\nDraft an answer:"
    if custom_instructions:
        user_prompt += f"\n\nAdditional instructions: {custom_instructions}"

    api_type, base_url, model, headers = _resolve_config()

    if api_type == "anthropic":
        return await _call_anthropic(base_url, model, headers, user_prompt)
    elif api_type == "google":
        return await _call_google(base_url, model, headers, user_prompt)
    else:
        return await _call_openai_compatible(base_url, model, headers, user_prompt)


async def _call_openai_compatible(
    base_url: str, model: str, headers: dict[str, str], user_prompt: str
) -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{base_url}/chat/completions",
            headers=headers,
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                "max_tokens": settings.LLM_MAX_TOKENS,
                "temperature": 0.3,
            },
        )

    if response.status_code != 200:
        return {"error": f"LLM API error: {response.status_code}", "detail": response.text[:500]}

    data = response.json()
    content = data["choices"][0]["message"]["content"]
    usage = data.get("usage", {})

    return {
        "answer_text": content,
        "model": data.get("model", model),
        "usage": {
            "prompt_tokens": usage.get("prompt_tokens", 0),
            "completion_tokens": usage.get("completion_tokens", 0),
        },
    }


async def _call_anthropic(base_url: str, model: str, headers: dict[str, str], user_prompt: str) -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{base_url}/messages",
            headers=headers,
            json={
                "model": model,
                "max_tokens": settings.LLM_MAX_TOKENS,
                "temperature": 0.3,
                "system": SYSTEM_PROMPT,
                "messages": [{"role": "user", "content": user_prompt}],
            },
        )

    if response.status_code != 200:
        return {"error": f"Anthropic API error: {response.status_code}", "detail": response.text[:500]}

    data = response.json()
    content = data["content"][0]["text"]
    usage = data.get("usage", {})

    return {
        "answer_text": content,
        "model": data.get("model", model),
        "usage": {
            "prompt_tokens": usage.get("input_tokens", 0),
            "completion_tokens": usage.get("output_tokens", 0),
        },
    }


async def _call_google(base_url: str, model: str, headers: dict[str, str], user_prompt: str) -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{base_url}/models/{model}:generateContent",
            params={"key": settings.LLM_API_KEY},
            headers={"Content-Type": "application/json"},
            json={
                "systemInstruction": {"parts": [{"text": SYSTEM_PROMPT}]},
                "contents": [{"parts": [{"text": user_prompt}]}],
                "generationConfig": {
                    "maxOutputTokens": settings.LLM_MAX_TOKENS,
                    "temperature": 0.3,
                },
            },
        )

    if response.status_code != 200:
        return {"error": f"Gemini API error: {response.status_code}", "detail": response.text[:500]}

    data = response.json()
    content = data["candidates"][0]["content"]["parts"][0]["text"]
    usage = data.get("usageMetadata", {})

    return {
        "answer_text": content,
        "model": model,
        "usage": {
            "prompt_tokens": usage.get("promptTokenCount", 0),
            "completion_tokens": usage.get("candidatesTokenCount", 0),
        },
    }


async def generate_batch_answers(
    questions: list[str],
    evidence_context: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for question in questions:
        results.append(await generate_llm_answer(question, evidence_context))
    return results
