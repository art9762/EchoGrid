from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic import Field

from src.schemas import EchoGridModel, LLMProvider


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
SIMULATIONS_DIR = DATA_DIR / "simulations"
EXPORTS_DIR = DATA_DIR / "exports"
PROMPTS_DIR = PROJECT_ROOT / "src" / "prompts"

SYNTHETIC_SIMULATION_DISCLAIMER = (
    "EchoGrid generates synthetic reactions. It is not a real poll and should "
    "not be used as evidence of actual public opinion."
)

ETHICAL_USE_DISCLAIMER = (
    "Echo simulation is intended for research, education, and communication "
    "risk analysis. It must not be used to optimize manipulative persuasion, "
    "political targeting, harassment, radicalization, or targeting vulnerable "
    "groups."
)


class AppSettings(EchoGridModel):
    llm_provider: LLMProvider = LLMProvider.MOCK
    trinity_api_key: str | None = None
    trinity_base_url: str | None = None
    gemini_api_key: str | None = None
    anthropic_reaction_model: str = "claude-haiku-4-5-20251001"
    anthropic_echo_model: str = "claude-sonnet-4-6"
    anthropic_report_model: str = "claude-sonnet-4-6"
    anthropic_premium_model: str = "claude-opus-4-7"
    gemini_reaction_model: str = "gemini-2.5-flash-lite"
    gemini_echo_model: str = "gemini-2.5-flash"
    gemini_report_model: str = "gemini-2.5-flash"
    openai_reaction_model: str = "gpt-5.4-nano"
    openai_echo_model: str = "gpt-5.4-mini"
    openai_report_model: str = "gpt-5.4-mini"
    database_path: Path = Field(default=DATA_DIR / "echogrid.sqlite3")

    @classmethod
    def from_env(cls) -> "AppSettings":
        load_dotenv(PROJECT_ROOT / ".env")
        return cls(
            llm_provider=LLMProvider(os.getenv("ECHOGRID_LLM_PROVIDER", "mock")),
            trinity_api_key=os.getenv("TRINITY_API_KEY") or None,
            trinity_base_url=os.getenv("TRINITY_BASE_URL") or None,
            gemini_api_key=os.getenv("GEMINI_API_KEY") or None,
            anthropic_reaction_model=os.getenv(
                "ECHOGRID_ANTHROPIC_REACTION_MODEL",
                "claude-haiku-4-5-20251001",
            ),
            anthropic_echo_model=os.getenv(
                "ECHOGRID_ANTHROPIC_ECHO_MODEL", "claude-sonnet-4-6"
            ),
            anthropic_report_model=os.getenv(
                "ECHOGRID_ANTHROPIC_REPORT_MODEL", "claude-sonnet-4-6"
            ),
            anthropic_premium_model=os.getenv(
                "ECHOGRID_ANTHROPIC_PREMIUM_MODEL", "claude-opus-4-7"
            ),
            gemini_reaction_model=os.getenv(
                "ECHOGRID_GEMINI_REACTION_MODEL", "gemini-2.5-flash-lite"
            ),
            gemini_echo_model=os.getenv(
                "ECHOGRID_GEMINI_ECHO_MODEL", "gemini-2.5-flash"
            ),
            gemini_report_model=os.getenv(
                "ECHOGRID_GEMINI_REPORT_MODEL", "gemini-2.5-flash"
            ),
            openai_reaction_model=os.getenv(
                "ECHOGRID_OPENAI_REACTION_MODEL", "gpt-5.4-nano"
            ),
            openai_echo_model=os.getenv(
                "ECHOGRID_OPENAI_ECHO_MODEL", "gpt-5.4-mini"
            ),
            openai_report_model=os.getenv(
                "ECHOGRID_OPENAI_REPORT_MODEL", "gpt-5.4-mini"
            ),
            database_path=Path(
                os.getenv("ECHOGRID_DATABASE_PATH", str(DATA_DIR / "echogrid.sqlite3"))
            ),
        )


def get_settings() -> AppSettings:
    return AppSettings.from_env()
