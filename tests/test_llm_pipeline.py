import json

from src.echo_engine import generate_echo_items
from src.framing import generate_framings
from src.llm_pipeline import (
    estimate_llm_cost,
    generate_full_sample_reactions,
    generate_hybrid_artifacts,
)
from src.media_ecosystem import default_media_actors
from src.population import generate_population
from src.reaction_engine import run_initial_reactions
from src.schemas import LLMProvider, NewsEvent, PopulationConfig
from src.social_bubbles import default_social_bubbles


class QueueClient:
    def __init__(self, responses: list[object]) -> None:
        self.responses = responses
        self.prompts: list[str] = []

    def generate_framings_json(self, prompt: str):
        self.prompts.append(prompt)
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response

    def generate_echo_items_json(self, prompt: str):
        self.prompts.append(prompt)
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response

    def generate_representative_comments_json(self, prompt: str):
        self.prompts.append(prompt)
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response

    def generate_reaction_json(self, prompt: str):
        self.prompts.append(prompt)
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


def sample_context():
    event = NewsEvent(
        title="City restricts short-term rentals",
        description="A city council proposes limits on short-term rental listings.",
        country="United States",
        topic="housing",
        source_type="official_statement",
        original_text="The council announced a proposed cap on short-term rentals.",
    )
    agents = generate_population(PopulationConfig(population_size=40, seed=19))
    fallback_frames = generate_framings(event, n=3)
    reactions = run_initial_reactions(agents, event, fallback_frames, seed=19)
    media_actors = default_media_actors()
    bubbles = default_social_bubbles()
    mock_echo_items = generate_echo_items(
        event, fallback_frames, reactions, media_actors, bubbles, seed=19
    )
    return event, fallback_frames, reactions, media_actors, bubbles, mock_echo_items


def test_estimate_llm_cost_counts_hybrid_calls_without_agent_scale_calls() -> None:
    estimate = estimate_llm_cost(
        run_mode="hybrid",
        provider=LLMProvider.ANTHROPIC,
        population_size=1000,
        frame_count=4,
        echo_enabled=True,
    )

    assert estimate.estimated_calls == 3
    assert estimate.estimated_input_tokens > 0
    assert estimate.estimated_output_tokens > 0
    assert estimate.estimated_usd_low >= 0
    assert "No per-agent LLM calls" in estimate.notes


def test_estimate_llm_cost_counts_full_sample_reaction_calls() -> None:
    estimate = estimate_llm_cost(
        run_mode="full_llm_sample",
        provider=LLMProvider.OPENAI,
        population_size=25,
        frame_count=3,
        echo_enabled=True,
    )

    assert estimate.estimated_calls == 78
    assert estimate.estimated_input_tokens > 25 * 3 * 600
    assert estimate.estimated_output_tokens > 25 * 3 * 250
    assert "Full LLM sample" in estimate.notes


def test_generate_hybrid_artifacts_uses_llm_outputs() -> None:
    event, fallback_frames, reactions, media_actors, bubbles, _ = sample_context()
    llm_frames = [
        fallback_frames[0].model_copy(
            update={"frame_id": "llm-neutral", "label": "LLM Neutral"}
        )
    ]
    llm_echo_items = [
        {
            "id": "llm-echo-1",
            "round_number": 1,
            "echo_type": "official_clarification",
            "text": "Officials clarify what the rental cap would and would not cover.",
            "origin_actor_id": "official-city",
            "source_frame_id": "llm-neutral",
            "target_bubbles": ["policy_detail_seekers"],
            "emotion": "reassurance",
            "distortion_level": 4,
            "sensationalism_level": 8,
            "estimated_reach": 55,
            "created_from_reaction_ids": ["agent-0001:neutral"],
        }
    ]
    llm_comments = [
        {
            "segment_id": "support:llm-neutral",
            "segment_label": "Supporters of the LLM neutral frame",
            "stance": "support",
            "frame_id": "llm-neutral",
            "bubble_id": "policy_detail_seekers",
            "comment": "This seems workable if there are clear safeguards.",
            "source_reaction_ids": ["agent-0001:neutral"],
        }
    ]
    client = QueueClient([llm_frames, llm_echo_items, llm_comments])

    artifacts = generate_hybrid_artifacts(
        client=client,
        event=event,
        fallback_frames=fallback_frames,
        initial_reactions=reactions,
        media_actors=media_actors,
        bubbles=bubbles,
        frame_count=3,
    )

    assert artifacts.frames[0].frame_id == "llm-neutral"
    assert artifacts.echo_items[0].id == "llm-echo-1"
    assert artifacts.representative_comments[0].segment_id == "support:llm-neutral"
    assert artifacts.errors == []
    assert len(client.prompts) == 3
    assert json.loads(client.prompts[0].split("Event JSON:\n", 1)[1])["title"] == event.title


def test_generate_hybrid_artifacts_falls_back_and_records_errors() -> None:
    event, fallback_frames, reactions, media_actors, bubbles, mock_echo_items = sample_context()
    client = QueueClient(
        [
            ValueError("framing unavailable"),
            ValueError("echo unavailable"),
            [],
        ]
    )

    artifacts = generate_hybrid_artifacts(
        client=client,
        event=event,
        fallback_frames=fallback_frames,
        initial_reactions=reactions,
        media_actors=media_actors,
        bubbles=bubbles,
        fallback_echo_items=mock_echo_items,
        frame_count=3,
    )

    assert artifacts.frames == fallback_frames
    assert artifacts.echo_items == mock_echo_items
    assert [error.step for error in artifacts.errors] == ["framings", "echo_items"]


def test_generate_full_sample_reactions_falls_back_per_call_and_reports_progress() -> None:
    event, fallback_frames, reactions, _, _, _ = sample_context()
    agents = generate_population(PopulationConfig(population_size=2, seed=23))
    frames = fallback_frames[:1]
    fallback_reactions = run_initial_reactions(agents, event, frames, seed=23)
    llm_reaction = fallback_reactions[0].model_copy(
        update={
            "stance_strength": 88,
            "likely_comment": "LLM-generated reaction with stricter source reasoning.",
        }
    )
    client = QueueClient([llm_reaction, ValueError("provider timeout")])
    progress: list[tuple[str, int]] = []

    generated, errors = generate_full_sample_reactions(
        client=client,
        event=event,
        agents=agents,
        frames=frames,
        fallback_reactions=fallback_reactions,
        seed=23,
        max_workers=1,
        request_timeout_seconds=5,
        progress_callback=lambda message, percent: progress.append((message, percent)),
    )

    assert len(generated) == 2
    assert generated[0].stance_strength == 88
    assert generated[0].agent_id == agents[0].id
    assert generated[0].frame_id == frames[0].frame_id
    assert generated[1].model_dump() == fallback_reactions[1].model_dump()
    assert [error.step for error in errors] == [
        f"full_reaction:{agents[1].id}:{frames[0].frame_id}"
    ]
    assert progress[-1] == ("Generated 2/2 Full LLM sample reactions", 100)
