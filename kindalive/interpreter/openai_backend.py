"""OpenAICompatBackend — LLM backend for any OpenAI-compatible server.

Covers both local and cloud deployments with one code path: Ollama
(``http://localhost:11434/v1``), LM Studio (``http://localhost:1234/v1``),
vLLM, llama.cpp's server, or OpenAI itself (``https://api.openai.com/v1``).
Anything that speaks the ``/chat/completions`` protocol works.

Configuration comes from constructor args or environment variables:

    KINDALIVE_LLM_BASE_URL   e.g. http://localhost:11434/v1
                                  https://openrouter.ai/api/v1
    KINDALIVE_LLM_MODEL      e.g. llama3.1 / gpt-4o-mini / qwen/qwen3-...
    KINDALIVE_LLM_KEY        bearer token (or OPENAI_API_KEY); optional
                             for local servers, required for cloud ones
    KINDALIVE_LLM_REFERER    optional HTTP-Referer (OpenRouter attribution)
    KINDALIVE_LLM_TITLE      optional X-Title (defaults to "Kindalive")

Works with OpenRouter out of the box — it's an OpenAI-compatible
endpoint. No SDK dependency — a single httpx POST.
"""

from __future__ import annotations

import os

try:
    import httpx
except ImportError as exc:  # pragma: no cover - exercised only without the extra
    raise ImportError(
        "The OpenAI-compatible backend needs the 'httpx' package. "
        'Install it with: pip install "kindalive[openai]"'
    ) from exc

DEFAULT_BASE_URL = "http://localhost:11434/v1"  # Ollama's default
DEFAULT_MODEL = "llama3.1"


class OpenAICompatBackend:
    """Calls any OpenAI-compatible chat-completions endpoint.

    Args:
        base_url: Server base URL ending in ``/v1``. Falls back to
            ``KINDALIVE_LLM_BASE_URL``, then Ollama's default.
        model: Model name as the server knows it. Falls back to
            ``KINDALIVE_LLM_MODEL``, then ``llama3.1``.
        api_key: Bearer token. Falls back to ``OPENAI_API_KEY``. Local
            servers usually need none.
        max_tokens: Max response tokens.
        temperature: Sampling temperature (0 = deterministic).
        timeout: Request timeout in seconds — generous because local
            models can be slow to first token.
    """

    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
        api_key: str | None = None,
        max_tokens: int = 1024,
        temperature: float = 0.0,
        timeout: float = 120.0,
        referer: str | None = None,
        title: str | None = None,
    ) -> None:
        self._base_url = (
            base_url
            or os.environ.get("KINDALIVE_LLM_BASE_URL", "")
            or DEFAULT_BASE_URL
        ).rstrip("/")
        self._model = (
            model
            or os.environ.get("KINDALIVE_LLM_MODEL", "")
            or DEFAULT_MODEL
        )
        # KINDALIVE_LLM_KEY is the preferred name (so an OpenRouter key
        # doesn't have to masquerade as OPENAI_API_KEY); OPENAI_API_KEY
        # still works as a fallback.
        self._api_key = (
            api_key
            or os.environ.get("KINDALIVE_LLM_KEY")
            or os.environ.get("OPENAI_API_KEY", "")
        )
        # Optional OpenRouter attribution headers (ignored by other
        # servers). Title defaults to "Kindalive"; referer only if set.
        self._referer = referer or os.environ.get("KINDALIVE_LLM_REFERER", "")
        self._title = (
            title
            if title is not None
            else os.environ.get("KINDALIVE_LLM_TITLE", "Kindalive")
        )
        self._max_tokens = max_tokens
        self._temperature = temperature
        self._timeout = timeout
        self._call_count = 0

    @property
    def call_count(self) -> int:
        return self._call_count

    @property
    def model(self) -> str:
        return self._model

    @property
    def base_url(self) -> str:
        return self._base_url

    async def call(
        self,
        system_prompt: str,
        user_prompt: str,
        history: list[dict[str, str]] | None = None,
        max_tokens: int | None = None,
    ) -> str:
        """POST to /chat/completions, return the assistant text.

        Args:
            history: Prior conversation turns ({"role", "content"} dicts,
                oldest first) inserted between the system prompt and the
                new user message so the robot keeps conversational context.
        """
        headers = {"Content-Type": "application/json"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"
        # OpenRouter uses these for app attribution/rankings; harmless
        # elsewhere (unknown headers are ignored).
        if self._referer:
            headers["HTTP-Referer"] = self._referer
        if self._title:
            headers["X-Title"] = self._title
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(history or [])
        messages.append({"role": "user", "content": user_prompt})
        payload = {
            "model": self._model,
            "max_tokens": max_tokens or self._max_tokens,
            "temperature": self._temperature,
            "messages": messages,
        }
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.post(
                f"{self._base_url}/chat/completions",
                json=payload,
                headers=headers,
            )
            response.raise_for_status()
        self._call_count += 1
        data = response.json()
        return str(data["choices"][0]["message"]["content"])
