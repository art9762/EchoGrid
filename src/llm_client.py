from __future__ import annotations

import json
from abc import ABC, abstractmethod
from typing import Any, TypeVar

from pydantic import TypeAdapter, ValidationError

from src.config import AppSettings
from src.schemas import (
    AgentReaction,
    EchoGridModel,
    EchoItem,
    EchoReaction,
    LLMProvider,
    NewsFrame,
    RepresentativeComment,
)

T = TypeVar("T")


class LLMClient(ABC):
    def __init__(self, model: str | None = None, timeout_seconds: int | None = None) -> None:
        self.model = model
        self.timeout_seconds = timeout_seconds

    def complete_json(self, prompt: str, max_tokens: int = 1500) -> dict[str, Any]:
        return parse_json_response(self.complete_text(prompt, max_tokens=max_tokens))

    def complete_model(
        self,
        prompt: str,
        model_type: type[EchoGridModel],
        max_tokens: int = 1500,
        retries: int = 1,
    ) -> EchoGridModel:
        return self._complete_validated_adapter(
            prompt, TypeAdapter(model_type), max_tokens=max_tokens, retries=retries
        )

    def generate_reaction_json(self, prompt: str, max_tokens: int = 1500) -> AgentReaction:
        return self._complete_validated_model(prompt, AgentReaction, max_tokens=max_tokens)

    def generate_echo_items_json(self, prompt: str, max_tokens: int = 3000) -> list[EchoItem]:
        return self._complete_validated_adapter(
            prompt, TypeAdapter(list[EchoItem]), max_tokens=max_tokens
        )

    def generate_echo_reaction_json(self, prompt: str, max_tokens: int = 1500) -> EchoReaction:
        return self._complete_validated_model(prompt, EchoReaction, max_tokens=max_tokens)

    def generate_framings_json(self, prompt: str, max_tokens: int = 2500) -> list[NewsFrame]:
        return self._complete_validated_adapter(
            prompt, TypeAdapter(list[NewsFrame]), max_tokens=max_tokens
        )

    def generate_representative_comments_json(
        self, prompt: str, max_tokens: int = 2500
    ) -> list[RepresentativeComment]:
        return self._complete_validated_adapter(
            prompt, TypeAdapter(list[RepresentativeComment]), max_tokens=max_tokens
        )

    def _complete_validated_model(
        self, prompt: str, model_type: type[EchoGridModel], max_tokens: int
    ) -> Any:
        return self._complete_validated_adapter(
            prompt, TypeAdapter(model_type), max_tokens=max_tokens
        )

    def _complete_validated_adapter(
        self,
        prompt: str,
        adapter: TypeAdapter[T],
        max_tokens: int,
        retries: int = 1,
    ) -> T:
        retry_prompt = prompt
        last_error: Exception | None = None
        for attempt in range(retries + 1):
            try:
                payload = parse_json_value(self.complete_text(retry_prompt, max_tokens=max_tokens))
                return adapter.validate_python(payload)
            except (json.JSONDecodeError, ValidationError, ValueError) as exc:
                last_error = exc
                if attempt == retries:
                    break
                retry_prompt = build_json_retry_prompt(prompt, exc)
        raise ValueError("LLM returned invalid JSON after retry") from last_error

    @abstractmethod
    def complete_text(self, prompt: str, max_tokens: int = 1500) -> str:
        raise NotImplementedError


class MockLLMClient(LLMClient):
    def complete_text(self, prompt: str, max_tokens: int = 1500) -> str:
        return '{"provider": "mock", "note": "deterministic mock mode is active"}'


class TrinityLLMClient(LLMClient):
    def __init__(
        self,
        api_key: str,
        base_url: str,
        model: str,
        provider_label: str,
        timeout_seconds: int | None = None,
    ) -> None:
        super().__init__(model=model, timeout_seconds=timeout_seconds)
        self.api_key = api_key
        self.base_url = base_url
        self.provider_label = provider_label

    def complete_text(self, prompt: str, max_tokens: int = 1500) -> str:
        from openai import OpenAI

        client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            timeout=self.timeout_seconds,
        )
        response = client.chat.completions.create(
            model=self.model or "",
            max_tokens=max_tokens,
            temperature=0.2,
            messages=[{"role": "user", "content": prompt}],
        )
        content = response.choices[0].message.content
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            return "".join(
                item.get("text", "") if isinstance(item, dict) else str(item) for item in content
            )
        return "{}"


class AnthropicLLMClient(LLMClient):
    def __init__(
        self,
        auth_token: str,
        base_url: str,
        reaction_model: str,
        artifact_model: str,
        timeout_seconds: int | None = None,
    ) -> None:
        super().__init__(model=artifact_model, timeout_seconds=timeout_seconds)
        self.auth_token = auth_token
        self.base_url = base_url
        self.reaction_model = reaction_model
        self.artifact_model = artifact_model
        self._active_model = artifact_model

    def complete_text(self, prompt: str, max_tokens: int = 1500) -> str:
        from anthropic import Anthropic

        client = Anthropic(
            auth_token=self.auth_token,
            base_url=self.base_url,
            timeout=self.timeout_seconds,
        )
        resp = client.messages.create(
            model=self._active_model,
            max_tokens=max_tokens,
            temperature=0.2,
            messages=[{"role": "user", "content": prompt}],
        )
        text = "".join(
            block.text for block in resp.content if getattr(block, "type", None) == "text"
        )
        return text or "{}"

    def generate_reaction_json(self, prompt: str, max_tokens: int = 1500) -> AgentReaction:
        self._active_model = self.reaction_model
        try:
            return super().generate_reaction_json(prompt, max_tokens=max_tokens)
        finally:
            self._active_model = self.artifact_model

    def generate_framings_json(self, prompt: str, max_tokens: int = 2500) -> list[NewsFrame]:
        self._active_model = self.artifact_model
        return super().generate_framings_json(prompt, max_tokens=max_tokens)

    def generate_echo_items_json(self, prompt: str, max_tokens: int = 3000) -> list[EchoItem]:
        self._active_model = self.artifact_model
        return super().generate_echo_items_json(prompt, max_tokens=max_tokens)

    def generate_representative_comments_json(
        self, prompt: str, max_tokens: int = 2500
    ) -> list[RepresentativeComment]:
        self._active_model = self.artifact_model
        return super().generate_representative_comments_json(prompt, max_tokens=max_tokens)


class GeminiLLMClient(LLMClient):
    def __init__(self, api_key: str, model: str, timeout_seconds: int | None = None) -> None:
        super().__init__(model=model, timeout_seconds=timeout_seconds)
        self.api_key = api_key

    def complete_text(self, prompt: str, max_tokens: int = 1500) -> str:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=self.api_key)
        response = client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=types.GenerateContentConfig(
                max_output_tokens=max_tokens,
                temperature=0.2,
                response_mime_type="application/json",
            ),
        )
        return response.text or "{}"


def build_llm_client(settings: AppSettings) -> LLMClient:
    if settings.llm_provider == LLMProvider.MOCK:
        return MockLLMClient()
    if settings.llm_provider == LLMProvider.ANTHROPIC:
        if not settings.anthropic_auth_token:
            raise ValueError("ANTHROPIC_AUTH_TOKEN is required for Anthropic mode")
        if not settings.anthropic_base_url:
            raise ValueError("ANTHROPIC_BASE_URL is required for Anthropic mode")
        return AnthropicLLMClient(
            auth_token=settings.anthropic_auth_token,
            base_url=settings.anthropic_base_url,
            reaction_model=settings.anthropic_reaction_model,
            artifact_model=settings.anthropic_echo_model,
            timeout_seconds=settings.llm_request_timeout_seconds,
        )
    if settings.llm_provider == LLMProvider.GEMINI:
        if not settings.gemini_api_key:
            raise ValueError("GEMINI_API_KEY is required for Gemini mode")
        return GeminiLLMClient(
            api_key=settings.gemini_api_key,
            model=settings.gemini_echo_model,
            timeout_seconds=settings.llm_request_timeout_seconds,
        )
    if settings.llm_provider == LLMProvider.OPENAI:
        return _build_trinity_client(
            settings=settings,
            provider_label="openai",
            model=settings.openai_echo_model,
            timeout_seconds=settings.llm_request_timeout_seconds,
        )
    raise ValueError(f"Unsupported LLM provider: {settings.llm_provider}")


def _build_trinity_client(
    settings: AppSettings,
    provider_label: str,
    model: str,
    timeout_seconds: int | None = None,
) -> TrinityLLMClient:
    if not settings.trinity_api_key:
        raise ValueError(f"TRINITY_API_KEY is required for {provider_label} mode")
    if not settings.trinity_base_url:
        raise ValueError(f"TRINITY_BASE_URL is required for {provider_label} mode")
    return TrinityLLMClient(
        api_key=settings.trinity_api_key,
        base_url=settings.trinity_base_url,
        model=model,
        provider_label=provider_label,
        timeout_seconds=timeout_seconds,
    )


def parse_json_response(text: str) -> dict[str, Any]:
    parsed = parse_json_value(text)
    if not isinstance(parsed, dict):
        raise ValueError("Expected a JSON object from LLM response")
    return parsed


def parse_json_value(text: str) -> Any:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()
    return json.loads(cleaned)


def build_json_retry_prompt(original_prompt: str, error: Exception) -> str:
    return (
        f"{original_prompt}\n\n"
        "The previous response could not be parsed or validated as the required JSON "
        f"schema. Error: {error}. Return JSON only, with no markdown, comments, or "
        "extra fields."
    )
