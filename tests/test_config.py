from pathlib import Path

from src.config import DATA_DIR, AppSettings, get_settings
from src.schemas import LLMProvider


def test_settings_default_to_mock_provider(monkeypatch) -> None:
    monkeypatch.delenv("ECHOGRID_LLM_PROVIDER", raising=False)
    monkeypatch.delenv("TRINITY_API_KEY", raising=False)
    monkeypatch.delenv("TRINITY_BASE_URL", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    settings = AppSettings.from_env()

    assert settings.llm_provider == LLMProvider.MOCK
    assert settings.llm_max_workers == 4
    assert settings.llm_request_timeout_seconds == 30
    assert settings.trinity_api_key is None
    assert settings.trinity_base_url is None
    assert settings.anthropic_reaction_model == "claude-haiku-4-5-20251001"
    assert settings.gemini_reaction_model == "gemini-2.5-flash-lite"
    assert settings.openai_reaction_model == "gpt-5.4-nano"


def test_settings_read_available_api_keys(monkeypatch) -> None:
    monkeypatch.setenv("ECHOGRID_LLM_PROVIDER", "anthropic")
    monkeypatch.setenv("TRINITY_API_KEY", "trinity-test-key")
    monkeypatch.setenv("TRINITY_BASE_URL", "https://trinity.example/v1")
    monkeypatch.setenv("GEMINI_API_KEY", "gemini-test-key")

    settings = get_settings()

    assert settings.llm_provider == LLMProvider.ANTHROPIC
    assert settings.trinity_api_key == "trinity-test-key"
    assert settings.trinity_base_url == "https://trinity.example/v1"
    assert settings.gemini_api_key == "gemini-test-key"


def test_default_sqlite_database_path_is_not_committed() -> None:
    settings = AppSettings()
    gitignore = Path(".gitignore").read_text(encoding="utf-8")

    assert settings.database_path == DATA_DIR / "echogrid.sqlite3"
    assert "data/*.sqlite3" in gitignore
