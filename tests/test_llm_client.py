import pytest

from src.config import AppSettings
from src.llm_client import (
    AnthropicLLMClient,
    GeminiLLMClient,
    MockLLMClient,
    OpenAILLMClient,
    build_llm_client,
    parse_json_response,
)
from src.schemas import LLMProvider


def test_build_llm_client_returns_mock_by_default() -> None:
    settings = AppSettings()

    client = build_llm_client(settings)

    assert isinstance(client, MockLLMClient)


def test_build_llm_client_supports_available_providers() -> None:
    assert isinstance(
        build_llm_client(
            AppSettings(llm_provider=LLMProvider.ANTHROPIC, anthropic_api_key="key")
        ),
        AnthropicLLMClient,
    )
    assert isinstance(
        build_llm_client(AppSettings(llm_provider=LLMProvider.GEMINI, gemini_api_key="key")),
        GeminiLLMClient,
    )
    assert isinstance(
        build_llm_client(AppSettings(llm_provider=LLMProvider.OPENAI, openai_api_key="key")),
        OpenAILLMClient,
    )


def test_build_llm_client_rejects_missing_api_key() -> None:
    with pytest.raises(ValueError):
        build_llm_client(AppSettings(llm_provider=LLMProvider.ANTHROPIC))


def test_parse_json_response_accepts_plain_or_fenced_json() -> None:
    assert parse_json_response('{"ok": true}') == {"ok": True}
    assert parse_json_response('```json\n{"ok": true}\n```') == {"ok": True}
