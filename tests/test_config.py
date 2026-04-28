from src.config import AppSettings, get_settings
from src.schemas import LLMProvider


def test_settings_default_to_mock_provider(monkeypatch) -> None:
    monkeypatch.delenv("ECHOGRID_LLM_PROVIDER", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    settings = AppSettings.from_env()

    assert settings.llm_provider == LLMProvider.MOCK
    assert settings.anthropic_reaction_model == "claude-haiku-4-5-20251001"
    assert settings.gemini_reaction_model == "gemini-2.5-flash-lite"
    assert settings.openai_reaction_model == "gpt-5.4-nano"


def test_settings_read_available_api_keys(monkeypatch) -> None:
    monkeypatch.setenv("ECHOGRID_LLM_PROVIDER", "anthropic")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "anthropic-test-key")
    monkeypatch.setenv("GEMINI_API_KEY", "gemini-test-key")
    monkeypatch.setenv("OPENAI_API_KEY", "openai-test-key")

    settings = get_settings()

    assert settings.llm_provider == LLMProvider.ANTHROPIC
    assert settings.anthropic_api_key == "anthropic-test-key"
    assert settings.gemini_api_key == "gemini-test-key"
    assert settings.openai_api_key == "openai-test-key"
