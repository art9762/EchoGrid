from __future__ import annotations

from time import perf_counter
from types import SimpleNamespace

import app
from src.framing import generate_framings
from src.schemas import (
    AgentReaction,
    EchoItem,
    EchoType,
    EmotionLabel,
    Emotions,
    LLMProvider,
    NewsEvent,
    NewsFrame,
    RepresentativeComment,
    Stance,
)


def _event() -> NewsEvent:
    return NewsEvent(
        title="Transit safety update",
        description="A city announces a safety update for the public transit network.",
        country="United States",
        topic="transportation",
        source_type="public_announcement",
        original_text="The transit agency announced new safety measures and reporting channels.",
    )


def _use_temp_database(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(
        app,
        "get_settings",
        lambda: SimpleNamespace(database_path=tmp_path / "echogrid.sqlite3"),
    )


class FakeHybridClient:
    def generate_framings_json(self, prompt: str):
        return [
            NewsFrame(
                frame_id="llm-neutral",
                label="LLM Neutral",
                text="A balanced frame generated through the configured gateway.",
                tone="neutral",
                implied_values=["stability"],
                source_type="public_broadcaster",
            )
        ]

    def generate_echo_items_json(self, prompt: str):
        return [
            EchoItem(
                id="llm-echo-1",
                round_number=1,
                echo_type=EchoType.OFFICIAL_CLARIFICATION,
                text="Officials clarify the scope of the update.",
                origin_actor_id="official-source",
                source_frame_id="llm-neutral",
                target_bubbles=["policy_detail_seekers"],
                emotion=EmotionLabel.REASSURANCE,
                distortion_level=3,
                sensationalism_level=5,
                estimated_reach=50,
                created_from_reaction_ids=[],
            )
        ]

    def generate_representative_comments_json(self, prompt: str):
        return [
            RepresentativeComment(
                segment_id="support:llm-neutral",
                segment_label="Supporters of the LLM neutral frame",
                stance=Stance.SUPPORT,
                frame_id="llm-neutral",
                bubble_id="policy_detail_seekers",
                comment="This sounds reasonable if the details are transparent.",
                source_reaction_ids=["agent-0001:llm-neutral"],
            )
        ]

    def generate_reaction_json(self, prompt: str):
        frame_id = "llm-neutral"
        agent_id = "agent-00001"
        if "agent-00002" in prompt:
            agent_id = "agent-00002"
        return AgentReaction(
            agent_id=agent_id,
            frame_id=frame_id,
            stance=Stance.SUPPORT,
            stance_strength=82,
            emotions=Emotions(anger=8, fear=12, hope=68, distrust=10, indifference=14),
            trust_in_source=74,
            perceived_personal_impact=41,
            perceived_group_impact=45,
            share_likelihood=39,
            comment_likelihood=31,
            discussion_likelihood=33,
            triggered_values=["stability"],
            main_reason="The LLM sample sees the update as guarded but useful.",
            likely_comment="This seems reasonable if the details are transparent.",
            what_could_change_mind="Evidence of poor implementation.",
        )


def test_run_simulation_returns_core_outputs(tmp_path, monkeypatch) -> None:
    _use_temp_database(monkeypatch, tmp_path)
    event = _event()
    frames = generate_framings(event, n=2)

    simulation = app._run_simulation(
        event=event,
        frames=frames,
        population_size=12,
        seed=7,
        echo_enabled=True,
        echo_rounds=1,
    )

    assert simulation["simulation_id"]
    assert len(simulation["agents"]) == 12
    assert len(simulation["reactions"]) == 12 * len(frames)
    assert simulation["echo_result"] is not None


def test_run_simulation_hybrid_uses_gateway_artifacts(tmp_path, monkeypatch) -> None:
    _use_temp_database(monkeypatch, tmp_path)
    monkeypatch.setattr(app, "build_llm_client", lambda settings: FakeHybridClient())
    event = _event()
    fallback_frames = generate_framings(event, n=2)

    simulation = app._run_simulation(
        event=event,
        frames=fallback_frames,
        population_size=12,
        seed=7,
        echo_enabled=True,
        echo_rounds=1,
        run_mode="hybrid",
        provider=LLMProvider.ANTHROPIC,
    )

    assert simulation["run_mode"] == "hybrid"
    assert simulation["provider"] == LLMProvider.ANTHROPIC
    assert [frame.frame_id for frame in simulation["frames"]] == ["llm-neutral"]
    assert len(simulation["initial_reactions"]) == 12
    assert simulation["representative_comments"][0].segment_id == "support:llm-neutral"
    assert simulation["llm_errors"] == []
    assert simulation["echo_result"].echo_items[0].id == "llm-echo-1"


def test_run_simulation_full_llm_sample_uses_per_agent_reactions(tmp_path, monkeypatch) -> None:
    _use_temp_database(monkeypatch, tmp_path)
    monkeypatch.setattr(app, "build_llm_client", lambda settings: FakeHybridClient())
    event = _event()
    fallback_frames = generate_framings(event, n=1)

    simulation = app._run_simulation(
        event=event,
        frames=fallback_frames,
        population_size=2,
        seed=7,
        echo_enabled=True,
        echo_rounds=1,
        run_mode="full_llm_sample",
        provider=LLMProvider.OPENAI,
        max_workers=1,
        request_timeout_seconds=5,
    )

    assert simulation["run_mode"] == "full_llm_sample"
    assert [frame.frame_id for frame in simulation["frames"]] == ["llm-neutral"]
    assert len(simulation["initial_reactions"]) == 2
    assert {reaction.stance_strength for reaction in simulation["initial_reactions"]} == {82}
    assert simulation["llm_errors"] == []
    assert simulation["metadata"]["max_workers"] == 1


def test_run_simulation_full_llm_sample_rejects_large_population(tmp_path, monkeypatch) -> None:
    _use_temp_database(monkeypatch, tmp_path)
    event = _event()
    fallback_frames = generate_framings(event, n=1)

    try:
        app._run_simulation(
            event=event,
            frames=fallback_frames,
            population_size=101,
            seed=7,
            echo_enabled=False,
            echo_rounds=0,
            run_mode="full_llm_sample",
            provider=LLMProvider.OPENAI,
        )
    except ValueError as exc:
        assert "Full LLM sample mode is capped at 100 agents" in str(exc)
    else:
        raise AssertionError("Expected full sample population cap to raise ValueError")


def test_mock_mode_performance_check_completes_comfortably(tmp_path, monkeypatch) -> None:
    _use_temp_database(monkeypatch, tmp_path)
    event = _event()
    frames = generate_framings(event, n=4)

    started_at = perf_counter()
    simulation = app._run_simulation(
        event=event,
        frames=frames,
        population_size=1000,
        seed=11,
        echo_enabled=True,
        echo_rounds=1,
    )
    elapsed = perf_counter() - started_at

    assert len(simulation["agents"]) == 1000
    assert len(simulation["initial_reactions"]) == 1000 * 4
    assert simulation["echo_result"] is not None
    assert elapsed < 5
