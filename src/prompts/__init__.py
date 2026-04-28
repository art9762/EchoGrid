"""Prompt template loading helpers."""

from __future__ import annotations

from pathlib import Path

from src.config import PROMPTS_DIR


def load_prompt(name: str) -> str:
    """Load a prompt template by logical name or filename."""
    path = _prompt_path(name)
    if not path.is_file():
        raise FileNotFoundError(f"Prompt template not found: {name}")
    return path.read_text(encoding="utf-8")


def _prompt_path(name: str) -> Path:
    clean_name = name.strip()
    if not clean_name or Path(clean_name).name != clean_name:
        raise FileNotFoundError(f"Invalid prompt template name: {name}")
    if clean_name.endswith(".txt"):
        filename = clean_name
    elif clean_name.endswith("_prompt"):
        filename = f"{clean_name}.txt"
    else:
        filename = f"{clean_name}_prompt.txt"
    return PROMPTS_DIR / filename
