from __future__ import annotations

from src.framing import generate_framings
from src.schemas import NewsEvent
from src.simulation import run_simulation
from src.storage import list_simulations, load_simulation


def _event() -> NewsEvent:
    return NewsEvent(
        title="Library funding vote",
        description="A city council vote would change local library funding.",
        country="United States",
        topic="public_services",
        source_type="council_vote",
        original_text="The council will vote on a library funding package next week.",
    )


def test_run_simulation_service_orchestrates_and_persists_a_mock_run(tmp_path) -> None:
    event = _event()
    frames = generate_framings(event, n=2)
    progress_updates: list[tuple[str, int]] = []

    simulation = run_simulation(
        event=event,
        frames=frames,
        population_size=15,
        seed=19,
        echo_enabled=True,
        echo_rounds=1,
        provider="mock",
        db_path=tmp_path / "echogrid.sqlite3",
        progress_callback=lambda message, progress: progress_updates.append(
            (message, progress)
        ),
    )

    assert simulation["simulation_id"]
    assert simulation["event"] == event
    assert len(simulation["agents"]) == 15
    assert len(simulation["initial_reactions"]) == 30
    assert simulation["echo_result"] is not None
    assert {
        key: simulation["metadata"][key]
        for key in [
            "provider",
            "runtime_mode",
            "population_size",
            "seed",
            "echo_enabled",
            "echo_rounds",
        ]
    } == {
        "provider": "mock",
        "runtime_mode": "mock",
        "population_size": 15,
        "seed": 19,
        "echo_enabled": True,
        "echo_rounds": 1,
    }
    assert simulation["metadata"]["media_preset"] == "balanced"
    assert progress_updates[0] == ("Generating synthetic population...", 10)
    assert progress_updates[-1] == ("Simulation saved.", 100)
    assert list_simulations(tmp_path / "echogrid.sqlite3")[0]["simulation_id"] == simulation[
        "simulation_id"
    ]
    assert load_simulation(
        tmp_path / "echogrid.sqlite3", simulation["simulation_id"]
    )["simulation_id"] == simulation["simulation_id"]


def test_run_simulation_service_can_skip_echo_layer(tmp_path) -> None:
    event = _event()
    frames = generate_framings(event, n=1)

    simulation = run_simulation(
        event=event,
        frames=frames,
        population_size=5,
        seed=23,
        echo_enabled=False,
        echo_rounds=0,
        db_path=tmp_path / "echogrid.sqlite3",
    )

    assert len(simulation["agents"]) == 5
    assert len(simulation["initial_reactions"]) == 5
    assert simulation["echo_result"] is None
