"""
Thin wrapper around an OpenAI-compatible chat completions API (Module 5.1/5.2).

Deliberately minimal: one method (`complete`) that takes a system prompt and
a user prompt and returns text, or `None` if the AI isn't configured or the
request fails. Every higher-level AI feature (log summarization, anomaly
detection, RCA, natural-language Q&A) builds its prompt in
insight_service.py and calls through this one chokepoint - keeping the
actual HTTP/auth/error-handling logic in exactly one place.

Provider is selected via settings.LLM_PROVIDER (groq | openai | ollama) and
resolved through Settings.resolve_llm_config() - see app/core/config.py.
All three speak the same OpenAI-compatible /chat/completions shape, so no
provider-specific branching is needed here.
"""
import httpx

from app.core.config import settings
from app.core.logging_config import get_logger

logger = get_logger("ai_service")


class AIService:
    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
        timeout: float = 30.0,
    ):
        resolved = settings.resolve_llm_config()
        self.api_key = api_key or resolved["api_key"]
        self.base_url = (base_url or resolved["base_url"]).rstrip("/")
        self.model = model or resolved["model"]
        self.timeout = timeout
        self.provider = settings.LLM_PROVIDER

    @property
    def configured(self) -> bool:
     print("=" * 60)
     print("AIService configured check")
     print("provider =", self.provider)
     print("api_key =", self.api_key[:10] if self.api_key else None)
     print("configured =", bool(self.api_key))
     print("=" * 60)
     return bool(self.api_key)

    async def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        temperature: float = 0.2,
        json_mode: bool = False,
    ) -> str | None:
        if not self.configured:
            logger.warning("ai_not_configured", provider=self.provider)
            return None

        body = {
            "model": self.model,
            "temperature": temperature,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }
        # Only OpenAI/Groq reliably support this; harmless to include since
        # both accept it, and we only set it when a caller explicitly asks
        # for structured JSON output (see insight_service.root_cause_analysis).
        if json_mode:
            body["response_format"] = {"type": "json_object"}

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json=body,
                )
                response.raise_for_status()
                data = response.json()
                return data["choices"][0]["message"]["content"].strip()
        except (httpx.HTTPError, KeyError, IndexError, ValueError) as exc:
            logger.error("ai_completion_failed", provider=self.provider, error=str(exc))
            return None
