import json
import sqlite3

from src.echo_engine import run_echo_simulation
from src.framing import generate_framings
from src.media_ecosystem import default_media_actors
from src.population import generate_population
from src.reaction_engine import run_initial_reactions
from src.report import (
    agents_to_dataframe,
    echo_items_to_dataframe,
    reactions_to_dataframe,
    simulation_summary_json,
)
from src.schemas import NewsEvent, PopulationConfig
from src.social_bubbles import assign_agents_to_bubbles, default_social_bubbles
from src.storage import init_database, save_simulation


def sample_run():
    event = NewsEvent(
        title="Housing policy reform",
        description="A reform package would change zoning and rental protections.",
        country="United States",
        topic="housing",
        source_type="legislative_package",
        original_text="Lawmakers introduced housing reforms covering zoning and rentals.",
    )
    agents = generate_population(PopulationConfig(population_size=20, seed=22))
    frames = generate_framings(event, n=2)
    reactions = run_initial_reactions(agents, event, frames, seed=22)
    actors = default_media_actors()
    bubbles = default_social_bubbles()
    assignments = assign_agents_to_bubbles(agents, bubbles)
    echo_result = run_echo_simulation(
        agents=agents,
        event=event,
        frames=frames,
        initial_reactions=reactions,
        media_actors=actors,
        bubbles=bubbles,
        bubble_assignments=assignments,
        seed=22,
    )
    return event, agents, frames, reactions, actors, bubbles, assignments, echo_result


def test_storage_initializes_and_saves_simulation(tmp_path) -> None:
    db_path = tmp_path / "echogrid.sqlite3"
    event, agents, frames, reactions, actors, bubbles, assignments, echo_result = sample_run()

    init_database(db_path)
    simulation_id = save_simulation(
        db_path=db_path,
        event=event,
        agents=agents,
        frames=frames,
        reactions=reactions,
        media_actors=actors,
        bubbles=bubbles,
        bubble_assignments=assignments,
        echo_result=echo_result,
    )

    with sqlite3.connect(db_path) as connection:
        simulation_count = connection.execute("select count(*) from simulations").fetchone()[0]
        agent_count = connection.execute("select count(*) from agents").fetchone()[0]
        echo_count = connection.execute("select count(*) from echo_items").fetchone()[0]

    assert simulation_id == echo_result.simulation_id
    assert simulation_count == 1
    assert agent_count == len(agents)
    assert echo_count == len(echo_result.echo_items)


def test_report_helpers_return_exportable_data() -> None:
    event, agents, frames, reactions, _, _, _, echo_result = sample_run()

    assert len(agents_to_dataframe(agents)) == len(agents)
    assert len(reactions_to_dataframe(reactions)) == len(reactions)
    assert len(echo_items_to_dataframe(echo_result.echo_items)) == len(echo_result.echo_items)
    payload = json.loads(
        simulation_summary_json(
            event=event,
            frames=frames,
            reactions=reactions,
            echo_result=echo_result,
        )
    )
    assert payload["event"]["title"] == "Housing policy reform"
    assert "amplification_metrics" in payload
