from __future__ import annotations

import pytest

from src.schemas import AgentReaction, EchoItem, EchoReaction, EmotionShift, Emotions, NewsFrame


PROMPT_FIELD_EXPECTATIONS = {
    "reaction": set(AgentReaction.model_fields) | set(Emotions.model_fields),
    "echo_generation": set(EchoItem.model_fields),
    "echo_reaction": set(EchoReaction.model_fields) | set(EmotionShift.model_fields),
    "framing": set(NewsFrame.model_fields),
}


def test_load_prompt_reads_templates_by_name() -> None:
    from src.prompts import load_prompt

    prompt = load_prompt("reaction")

    assert "AgentReaction" in prompt
    assert "Return JSON only" in prompt


def test_load_prompt_accepts_txt_suffix() -> None:
    from src.prompts import load_prompt

    assert load_prompt("framing") == load_prompt("framing_prompt.txt")


def test_load_prompt_rejects_unknown_prompt() -> None:
    from src.prompts import load_prompt

    with pytest.raises(FileNotFoundError):
        load_prompt("missing_prompt")


@pytest.mark.parametrize("prompt_name, field_names", PROMPT_FIELD_EXPECTATIONS.items())
def test_prompt_templates_cover_schema_fields_and_guardrails(
    prompt_name: str, field_names: set[str]
) -> None:
    from src.prompts import load_prompt

    prompt = load_prompt(prompt_name)
    missing_fields = sorted(field for field in field_names if field not in prompt)

    assert missing_fields == []
    assert "Return JSON only" in prompt
    assert "Do not" in prompt
    assert "targeting" in prompt.lower()
