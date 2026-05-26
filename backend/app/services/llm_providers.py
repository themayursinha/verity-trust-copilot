"""LLM provider registry — presets for popular LLM providers and inference services.

Supports OpenAI-compatible APIs, Anthropic, Google Gemini, and Ollama.
All cloud providers use the BYOK model — users bring their own API keys.
"""

from __future__ import annotations

from typing import Any

LLM_PROVIDERS: dict[str, dict[str, Any]] = {
    "openai": {
        "name": "OpenAI",
        "base_url": "https://api.openai.com/v1",
        "models": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"],
        "api_type": "openai",
        "docs": "https://platform.openai.com/api-keys",
        "pricing": "https://openai.com/pricing",
    },
    "anthropic": {
        "name": "Anthropic (Claude)",
        "base_url": "https://api.anthropic.com/v1",
        "models": ["claude-sonnet-4-20250514", "claude-3-5-sonnet-20241022", "claude-3-haiku-20240307"],
        "api_type": "anthropic",
        "docs": "https://console.anthropic.com/settings/keys",
        "pricing": "https://www.anthropic.com/pricing",
    },
    "google": {
        "name": "Google (Gemini)",
        "base_url": "https://generativelanguage.googleapis.com/v1beta",
        "models": ["gemini-2.5-flash", "gemini-2.5-pro", "gemini-2.0-flash"],
        "api_type": "google",
        "docs": "https://aistudio.google.com/apikey",
        "pricing": "https://ai.google.dev/pricing",
    },
    "groq": {
        "name": "Groq",
        "base_url": "https://api.groq.com/openai/v1",
        "models": ["llama-3.3-70b-versatile", "mixtral-8x7b-32768", "gemma2-9b-it", "deepseek-r1-distill-llama-70b"],
        "api_type": "openai",
        "docs": "https://console.groq.com/keys",
        "pricing": "https://groq.com/pricing",
    },
    "together": {
        "name": "Together AI",
        "base_url": "https://api.together.xyz/v1",
        "models": [
            "meta-llama/Llama-3.3-70B-Instruct-Turbo",
            "mistralai/Mixtral-8x7B-Instruct-v0.1",
            "deepseek-ai/DeepSeek-R1",
        ],
        "api_type": "openai",
        "docs": "https://api.together.xyz/settings/api-keys",
        "pricing": "https://www.together.ai/pricing",
    },
    "deepseek": {
        "name": "DeepSeek",
        "base_url": "https://api.deepseek.com/v1",
        "models": ["deepseek-chat", "deepseek-reasoner"],
        "api_type": "openai",
        "docs": "https://platform.deepseek.com/api_keys",
        "pricing": "https://api-docs.deepseek.com/quick_start/pricing",
    },
    "mistral": {
        "name": "Mistral AI",
        "base_url": "https://api.mistral.ai/v1",
        "models": ["mistral-large-latest", "mistral-medium-latest", "pixtral-large-latest", "codestral-latest"],
        "api_type": "openai",
        "docs": "https://console.mistral.ai/api-keys",
        "pricing": "https://mistral.ai/technology/#pricing",
    },
    "fireworks": {
        "name": "Fireworks AI",
        "base_url": "https://api.fireworks.ai/inference/v1",
        "models": [
            "accounts/fireworks/models/llama-v3p3-70b-instruct",
            "accounts/fireworks/models/mixtral-8x22b-instruct",
        ],
        "api_type": "openai",
        "docs": "https://fireworks.ai/api-keys",
        "pricing": "https://fireworks.ai/pricing",
    },
    "xai": {
        "name": "xAI (Grok)",
        "base_url": "https://api.x.ai/v1",
        "models": ["grok-3-beta", "grok-2-1212"],
        "api_type": "openai",
        "docs": "https://console.x.ai",
        "pricing": "https://x.ai/pricing",
    },
    "ollama": {
        "name": "Ollama (local)",
        "base_url": "http://localhost:11434/v1",
        "models": ["llama3.2", "llama3.1", "mistral", "gemma3", "qwen2.5", "deepseek-r1"],
        "api_type": "openai",
        "no_auth": True,
        "docs": "https://ollama.com/download",
        "pricing": None,
    },
    "custom": {
        "name": "Custom OpenAI-compatible",
        "base_url": "",
        "models": [],
        "api_type": "openai",
        "docs": None,
        "pricing": None,
    },
}


def get_provider_config(provider: str) -> dict[str, Any] | None:
    return LLM_PROVIDERS.get(provider)


def list_providers() -> list[dict[str, Any]]:
    return [
        {
            "id": pid,
            "name": info["name"],
            "api_type": info.get("api_type", "openai"),
            "models": info.get("models", []),
            "requires_auth": not info.get("no_auth", False),
            "docs": info.get("docs"),
        }
        for pid, info in LLM_PROVIDERS.items()
    ]


def get_model_for_provider(provider: str, model_override: str | None = None) -> str:
    provider_info = LLM_PROVIDERS.get(provider, {})
    if model_override:
        return model_override
    models = provider_info.get("models", [])
    return models[0] if models else ""
