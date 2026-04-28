from __future__ import annotations

from types import SimpleNamespace
from time import perf_counter

import app
from src.framing import generate_framings
from src.schemas import NewsEvent


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
