import json
import sqlite3

from src.echo_engine import run_echo_simulation
from src.framing import generate_framings
from src.media_ecosystem import default_media_actors
from src.population import generate_population
from src.reaction_engine import run_initial_reactions
from src.report import (
    agents_to_dataframe,
    dataframe_to_csv_export,
    echo_items_to_dataframe,
    reactions_to_dataframe,
    simulation_summary_json,
)
from src.schemas import (
    LLMGenerationError,
    LLMProvider,
    NewsEvent,
    PopulationConfig,
    RepresentativeComment,
    Stance,
)
from src.social_bubbles import assign_agents_to_bubbles, default_social_bubbles
from src.storage import init_database, load_simulation, save_simulation


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


def test_load_simulation_restores_saved_run_counts(tmp_path) -> None:
    db_path = tmp_path / "echogrid.sqlite3"
    event, agents, frames, reactions, actors, bubbles, assignments, echo_result = sample_run()
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

    loaded = load_simulation(db_path, simulation_id)

    assert loaded["simulation_id"] == simulation_id
    assert loaded["event"].title == event.title
    assert len(loaded["agents"]) == len(agents)
    assert len(loaded["frames"]) == len(frames)
    assert len(loaded["reactions"]) == len(reactions)
    assert len(loaded["media_actors"]) == len(actors)
    assert len(loaded["bubbles"]) == len(bubbles)
    assert loaded["bubble_assignments"] == assignments
    assert len(loaded["echo_result"].echo_items) == len(echo_result.echo_items)
    assert len(loaded["echo_result"].echo_reactions) == len(echo_result.echo_reactions)


def test_report_helpers_return_exportable_data() -> None:
    event, agents, frames, reactions, _, _, assignments, echo_result = sample_run()

    agents_df = agents_to_dataframe(agents)
    reactions_df = reactions_to_dataframe(reactions, bubble_assignments=assignments)

    assert len(agents_df) == len(agents)
    assert {"age_group", "institutional_trust_bucket"} <= set(agents_df.columns)
    assert len(reactions_df) == len(reactions)
    assert "social_bubble" in reactions_df.columns
    assert reactions_df["social_bubble"].notna().all()
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
    assert "export_metadata" in payload
    assert "not a real poll" in payload["export_metadata"]["synthetic_simulation_disclaimer"]


def test_summary_export_includes_llm_artifacts_when_available() -> None:
    event, _, frames, reactions, _, _, _, echo_result = sample_run()
    representative_comment = RepresentativeComment(
        segment_id="support:neutral",
        segment_label="Supporters of the neutral frame",
        stance=Stance.SUPPORT,
        frame_id="neutral",
        bubble_id="policy_detail_seekers",
        comment="This sounds practical if safeguards are clear.",
        source_reaction_ids=["agent-0001:neutral"],
    )
    llm_error = LLMGenerationError(step="echo_items", message="ValueError: fallback used")

    payload = json.loads(
        simulation_summary_json(
            event=event,
            frames=frames,
            reactions=reactions,
            echo_result=echo_result,
            run_mode="hybrid",
            provider=LLMProvider.ANTHROPIC,
            representative_comments=[representative_comment],
            llm_errors=[llm_error],
        )
    )

    assert payload["run_mode"] == "hybrid"
    assert payload["provider"] == "anthropic"
    assert payload["representative_comments"][0]["segment_id"] == "support:neutral"
    assert payload["llm_errors"][0]["step"] == "echo_items"


def test_csv_export_includes_metadata_comments() -> None:
    _, agents, _, _, _, _, _, _ = sample_run()

    csv_text = dataframe_to_csv_export(agents_to_dataframe(agents), export_name="agents")

    assert csv_text.startswith("# EchoGrid export: agents")
    assert "not a real poll" in csv_text.splitlines()[1]
    assert "agent_id" in csv_text or "id" in csv_text
