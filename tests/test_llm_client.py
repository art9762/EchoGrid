import json

import pytest

import src.llm_client as llm_client
from src.config import AppSettings
from src.llm_client import (
    GeminiLLMClient,
    MockLLMClient,
    build_llm_client,
    parse_json_response,
)
from src.schemas import LLMProvider


class QueueLLMClient(llm_client.LLMClient):
    def __init__(self, responses: list[str]) -> None:
        super().__init__(model="test-model")
        self.responses = responses
        self.prompts: list[str] = []

    def complete_text(self, prompt: str, max_tokens: int = 1500) -> str:
        self.prompts.append(prompt)
        return self.responses.pop(0)


REACTION_JSON = {
    "agent_id": "agent-1",
    "frame_id": "frame-1",
    "stance": "support",
    "stance_strength": 68,
    "emotions": {
        "anger": 10,
        "fear": 20,
        "hope": 60,
        "distrust": 15,
        "indifference": 5,
    },
    "trust_in_source": 72,
    "perceived_personal_impact": 40,
    "perceived_group_impact": 55,
    "share_likelihood": 30,
    "comment_likelihood": 25,
    "discussion_likelihood": 45,
    "triggered_values": ["fairness"],
    "main_reason": "The framing feels practical.",
    "likely_comment": "This could work if it is implemented carefully.",
    "what_could_change_mind": "Evidence that costs fall unfairly on workers.",
}

ECHO_ITEM_JSON = {
    "id": "echo-1",
    "round_number": 1,
    "echo_type": "expert_correction",
    "text": "An expert explains which claims are and are not supported.",
    "origin_actor_id": "expert-1",
    "source_frame_id": "frame-1",
    "target_bubbles": ["policy-watchers"],
    "emotion": "reassurance",
    "distortion_level": 5,
    "sensationalism_level": 10,
    "estimated_reach": 45,
    "created_from_reaction_ids": ["agent-1:frame-1"],
}

ECHO_REACTION_JSON = {
    "agent_id": "agent-1",
    "echo_item_id": "echo-1",
    "bubble_id": "policy-watchers",
    "previous_stance": "support",
    "updated_stance": "neutral",
    "stance_shift": -10,
    "emotion_shift": {
        "anger": -2,
        "fear": -5,
        "hope": -8,
        "distrust": 2,
        "indifference": 3,
    },
    "trust_shift": 4,
    "share_likelihood_shift": -6,
    "reason": "The correction reduces certainty without fully reversing the stance.",
}

FRAME_JSON = {
    "frame_id": "llm-neutral",
    "label": "Neutral public-service frame",
    "text": "Officials describe the proposal and its expected scope.",
    "tone": "neutral",
    "implied_values": ["public_information", "stability"],
    "source_type": "public_broadcaster",
}

COMMENT_JSON = {
    "segment_id": "support:neutral",
    "segment_label": "Supporters reacting to the neutral frame",
    "stance": "support",
    "frame_id": "neutral",
    "bubble_id": "policy-watchers",
    "comment": "This sounds reasonable if the rollout is transparent.",
    "source_reaction_ids": ["agent-1:neutral"],
}


def test_build_llm_client_returns_mock_by_default() -> None:
    settings = AppSettings()

    client = build_llm_client(settings)

    assert isinstance(client, MockLLMClient)


def test_build_llm_client_supports_available_providers() -> None:
    anthropic_client = build_llm_client(
        AppSettings(
            llm_provider=LLMProvider.ANTHROPIC,
            trinity_api_key="trinity-key",
            trinity_base_url="https://trinity.example/v1",
        )
    )
    assert isinstance(anthropic_client, llm_client.TrinityLLMClient)
    assert anthropic_client.provider_label == "anthropic"
    assert anthropic_client.model == "claude-sonnet-4-6"

    assert isinstance(
        build_llm_client(AppSettings(llm_provider=LLMProvider.GEMINI, gemini_api_key="key")),
        GeminiLLMClient,
    )

    openai_client = build_llm_client(
        AppSettings(
            llm_provider=LLMProvider.OPENAI,
            trinity_api_key="trinity-key",
            trinity_base_url="https://trinity.example/v1",
        )
    )
    assert isinstance(openai_client, llm_client.TrinityLLMClient)
    assert openai_client.provider_label == "openai"
    assert openai_client.model == "gpt-5.4-mini"


def test_build_llm_client_rejects_missing_trinity_settings_for_gateway_providers() -> None:
    with pytest.raises(ValueError, match="TRINITY_API_KEY"):
        build_llm_client(AppSettings(llm_provider=LLMProvider.ANTHROPIC))

    with pytest.raises(ValueError, match="TRINITY_BASE_URL"):
        build_llm_client(
            AppSettings(llm_provider=LLMProvider.OPENAI, trinity_api_key="trinity-key")
        )


def test_parse_json_response_accepts_plain_or_fenced_json() -> None:
    assert parse_json_response('{"ok": true}') == {"ok": True}
    assert parse_json_response('```json\n{"ok": true}\n```') == {"ok": True}


def test_generate_reaction_json_returns_validated_agent_reaction() -> None:
    client = QueueLLMClient([json.dumps(REACTION_JSON)])

    reaction = client.generate_reaction_json("Generate reaction")

    assert reaction.agent_id == "agent-1"
    assert reaction.emotions.hope == 60


def test_generate_echo_items_json_returns_validated_echo_items() -> None:
    client = QueueLLMClient([json.dumps([ECHO_ITEM_JSON])])

    echo_items = client.generate_echo_items_json("Generate echo items")

    assert len(echo_items) == 1
    assert echo_items[0].id == "echo-1"


def test_generate_echo_reaction_json_returns_validated_echo_reaction() -> None:
    client = QueueLLMClient([json.dumps(ECHO_REACTION_JSON)])

    echo_reaction = client.generate_echo_reaction_json("Generate echo reaction")

    assert echo_reaction.echo_item_id == "echo-1"
    assert echo_reaction.trust_shift == 4


def test_generate_framings_json_returns_validated_news_frames() -> None:
    client = QueueLLMClient([json.dumps([FRAME_JSON])])

    frames = client.generate_framings_json("Generate frames")

    assert len(frames) == 1
    assert frames[0].frame_id == "llm-neutral"


def test_generate_representative_comments_json_returns_validated_comments() -> None:
    client = QueueLLMClient([json.dumps([COMMENT_JSON])])

    comments = client.generate_representative_comments_json("Generate comments")

    assert len(comments) == 1
    assert comments[0].segment_id == "support:neutral"


def test_generate_reaction_json_retries_once_after_invalid_json() -> None:
    client = QueueLLMClient(["not json", json.dumps(REACTION_JSON)])

    reaction = client.generate_reaction_json("Generate reaction")

    assert reaction.agent_id == "agent-1"
    assert len(client.prompts) == 2
    assert "Return JSON only" in client.prompts[1]
