from __future__ import annotations

from types import SimpleNamespace
from time import perf_counter

import app
from src.framing import generate_framings
from src.schemas import (
    EchoItem,
    EchoType,
    EmotionLabel,
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
