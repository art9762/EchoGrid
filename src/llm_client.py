from __future__ import annotations

import json
from abc import ABC, abstractmethod
from typing import Any

from src.config import AppSettings
from src.schemas import LLMProvider


class LLMClient(ABC):
    def __init__(self, model: str | None = None) -> None:
        self.model = model

    def complete_json(self, prompt: str, max_tokens: int = 1500) -> dict[str, Any]:
        return parse_json_response(self.complete_text(prompt, max_tokens=max_tokens))

    @abstractmethod
    def complete_text(self, prompt: str, max_tokens: int = 1500) -> str:
        raise NotImplementedError


class MockLLMClient(LLMClient):
    def complete_text(self, prompt: str, max_tokens: int = 1500) -> str:
        return '{"provider": "mock", "note": "deterministic mock mode is active"}'


class AnthropicLLMClient(LLMClient):
    def __init__(self, api_key: str, model: str) -> None:
        super().__init__(model=model)
        self.api_key = api_key

    def complete_text(self, prompt: str, max_tokens: int = 1500) -> str:
        from anthropic import Anthropic

        client = Anthropic(api_key=self.api_key)
        response = client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            temperature=0.2,
            messages=[{"role": "user", "content": prompt}],
        )
        return "".join(
            block.text for block in response.content if getattr(block, "type", None) == "text"
        )


class GeminiLLMClient(LLMClient):
    def __init__(self, api_key: str, model: str) -> None:
        super().__init__(model=model)
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


class OpenAILLMClient(LLMClient):
    def __init__(self, api_key: str, model: str) -> None:
        super().__init__(model=model)
        self.api_key = api_key

    def complete_text(self, prompt: str, max_tokens: int = 1500) -> str:
        from openai import OpenAI

        client = OpenAI(api_key=self.api_key)
        response = client.responses.create(
            model=self.model,
            input=prompt,
            max_output_tokens=max_tokens,
            temperature=0.2,
        )
        return response.output_text


def build_llm_client(settings: AppSettings) -> LLMClient:
    if settings.llm_provider == LLMProvider.MOCK:
        return MockLLMClient()
    if settings.llm_provider == LLMProvider.ANTHROPIC:
        if not settings.anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY is required for Anthropic mode")
        return AnthropicLLMClient(
            api_key=settings.anthropic_api_key,
            model=settings.anthropic_echo_model,
        )
    if settings.llm_provider == LLMProvider.GEMINI:
        if not settings.gemini_api_key:
            raise ValueError("GEMINI_API_KEY is required for Gemini mode")
        return GeminiLLMClient(
            api_key=settings.gemini_api_key,
            model=settings.gemini_echo_model,
        )
    if settings.llm_provider == LLMProvider.OPENAI:
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required for OpenAI mode")
        return OpenAILLMClient(
            api_key=settings.openai_api_key,
            model=settings.openai_echo_model,
        )
    raise ValueError(f"Unsupported LLM provider: {settings.llm_provider}")


def parse_json_response(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()
    parsed = json.loads(cleaned)
    if not isinstance(parsed, dict):
        raise ValueError("Expected a JSON object from LLM response")
    return parsed

