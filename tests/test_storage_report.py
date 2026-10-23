import json
import sqlite3
import zipfile
from html import escape
from html.parser import HTMLParser
from io import BytesIO

import pytest

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
    simulation_export_zip,
    simulation_report_html,
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
from src.simulation import run_simulation
from src.social_bubbles import assign_agents_to_bubbles, default_social_bubbles
from src.storage import (
    delete_simulation,
    init_database,
    list_simulations,
    load_simulation,
    save_simulation,
)


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


def test_load_simulation_restores_llm_artifacts_and_runtime_metadata(tmp_path) -> None:
    db_path = tmp_path / "echogrid.sqlite3"
    event, agents, frames, reactions, actors, bubbles, assignments, echo_result = sample_run()
    representative_comment = RepresentativeComment(
        segment_id="support:neutral",
        segment_label="Supporters of the neutral frame",
        stance=Stance.SUPPORT,
        frame_id="neutral",
        bubble_id="high_trust_institutionalists",
        comment="This is acceptable if safeguards stay visible.",
        source_reaction_ids=["agent-00001:neutral"],
    )
    llm_error = LLMGenerationError(
        step="full_reaction:agent-00002:neutral",
        message="TimeoutError: request timed out",
    )
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
        seed=22,
        provider="openai",
        run_mode="full_llm_sample",
        representative_comments=[representative_comment],
        llm_errors=[llm_error],
    )

    loaded = load_simulation(db_path, simulation_id)

    assert loaded["run_mode"] == "full_llm_sample"
    assert loaded["provider"] == LLMProvider.OPENAI
    assert loaded["metadata"]["seed"] == 22
    assert loaded["representative_comments"][0].comment == representative_comment.comment
    assert loaded["llm_errors"][0].step == llm_error.step


def test_list_simulations_returns_metadata_and_delete_removes_run(tmp_path) -> None:
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
        seed=22,
        provider="mock",
    )

    summaries = list_simulations(db_path)

    assert len(summaries) == 1
    assert summaries[0]["simulation_id"] == simulation_id
    assert summaries[0]["event_title"] == "Housing policy reform"
    assert summaries[0]["country"] == "United States"
    assert summaries[0]["topic"] == "housing"
    assert summaries[0]["population_size"] == len(agents)
    assert summaries[0]["seed"] == 22
    assert summaries[0]["provider"] == "mock"
    assert delete_simulation(db_path, simulation_id) is True
    assert list_simulations(db_path) == []
    with pytest.raises(KeyError):
        load_simulation(db_path, simulation_id)


def test_report_helpers_return_exportable_data() -> None:
    event, agents, frames, reactions, _, bubbles, assignments, echo_result = sample_run()

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
            bubbles=bubbles,
        )
    )
    assert payload["event"]["title"] == "Housing policy reform"
    assert "amplification_metrics" in payload
    assert "amplification_breakdown" in payload
    assert "final_state_metrics" in payload
    assert "narrative_risk_summary" in payload
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


def test_simulation_export_zip_contains_release_artifacts() -> None:
    event, agents, frames, reactions, actors, bubbles, assignments, echo_result = sample_run()
    archive = simulation_export_zip(
        {
            "event": event,
            "frames": frames,
            "agents": agents,
            "initial_reactions": reactions,
            "media_actors": actors,
            "bubbles": bubbles,
            "bubble_assignments": assignments,
            "echo_result": echo_result,
        }
    )

    with zipfile.ZipFile(BytesIO(archive)) as zf:
        names = set(zf.namelist())
        summary = json.loads(zf.read("summary.json"))
        agents_csv = zf.read("agents.csv").decode("utf-8")
        readme = zf.read("README.txt").decode("utf-8")

    assert {
        "README.txt",
        "summary.json",
        "report.html",
        "agents.csv",
        "reactions.csv",
        "echo_items.csv",
        "echo_reactions.csv",
    } <= names
    assert summary["event"]["title"] == "Housing policy reform"
    assert agents_csv.startswith("# EchoGrid export: agents")
    assert "not a real poll" in readme


@pytest.mark.parametrize("echo_enabled", [False, True])
def test_html_report_from_mock_run_survives_storage_and_zip(tmp_path, echo_enabled) -> None:
    event = NewsEvent(
        title="Transit safety update — Город",
        description="The city proposes a safety update to its public transit network.",
        country="United States",
        topic="transportation",
        source_type="public_announcement",
        original_text="New reporting channels and passenger safeguards are proposed.",
    )

    def no_llm_calls(_settings):
        pytest.fail("Mock report workflow must not create an LLM client")

    db = tmp_path / "report.sqlite3"
    current = run_simulation(
        event=event,
        frames=generate_framings(event, n=2),
        population_size=12,
        seed=71,
        echo_enabled=echo_enabled,
        echo_rounds=2 if echo_enabled else 0,
        db_path=db,
        llm_client_factory=no_llm_calls,
    )
    loaded = load_simulation(db, current["simulation_id"])
    html = simulation_report_html(loaded)
    initial_metrics = json.loads(
        simulation_summary_json(event, loaded["frames"], loaded["initial_reactions"])
    )["initial_metrics"]
    assert "<!doctype html>" in html
    assert event.title in html
    assert current["simulation_id"] in html
    assert "<dt>seed</dt><dd>71</dd>" in html
    assert "<dt>run mode</dt><dd>mock</dd>" in html
    assert "<dt>provider</dt><dd>mock</dd>" in html
    assert f"<dt>trust average</dt><dd>{initial_metrics['trust_average']}</dd>" in html
    assert "Synthetic simulation — not a real poll" in html
    assert "not be used as evidence of actual public opinion" in html
    assert "political targeting" in html
    if echo_enabled:
        assert "<h2>Final state metrics</h2>" in html
        assert "<h2>Echo rounds</h2>" in html
        for item in loaded["echo_result"].echo_items:
            assert escape(item.text) in html
    else:
        assert "No echo results were recorded" in html
        assert "<h2>Final state metrics</h2>" not in html
    with zipfile.ZipFile(BytesIO(simulation_export_zip(loaded))) as archive:
        assert archive.read("report.html").decode("utf-8") == html
        assert "report.html" in archive.read("README.txt").decode("utf-8")
        assert json.loads(archive.read("summary.json"))["initial_metrics"] == initial_metrics


def test_html_report_escapes_all_run_content_and_has_no_external_resources() -> None:
    event, agents, frames, reactions, actors, bubbles, assignments, echo_result = sample_run()
    injected = (
        '</title><script>alert("unsafe")</script><img src="https://bad.test/x" onerror="x"> & Город'
    )
    event.title = event.description = event.original_text = injected
    frames[0].text = frames[0].label = frames[0].tone = injected
    echo_result.echo_items[0].text = injected
    echo_result.round_summaries[0].metrics = {injected: {injected: [injected]}}
    html = simulation_report_html(
        {
            "simulation_id": injected,
            "event": event,
            "frames": frames,
            "agents": agents,
            "initial_reactions": reactions,
            "bubbles": bubbles,
            "echo_result": echo_result,
            "provider": injected,
            "run_mode": injected,
            "metadata": {"created_at": injected, "seed": injected},
            "representative_comments": [
                RepresentativeComment(
                    segment_id="test",
                    segment_label=injected,
                    stance=Stance.NEUTRAL,
                    comment=injected,
                    source_reaction_ids=[injected],
                )
            ],
            "llm_errors": [LLMGenerationError(step=injected, message=injected)],
        }
    )
    assert injected not in html
    assert escape(injected) in html

    class Elements(HTMLParser):
        def handle_starttag(self, tag, attrs):
            assert tag not in {"script", "img", "link", "iframe", "object", "embed", "a"}
            assert not any(key.startswith("on") or key in {"src", "href"} for key, _ in attrs)

    Elements().feed(html)
    assert "default-src 'none'" in html


def test_html_report_does_not_invent_missing_metadata() -> None:
    event, agents, frames, reactions, _, bubbles, _, _ = sample_run()
    html = simulation_report_html(
        {
            "event": event,
            "agents": agents,
            "frames": frames,
            "initial_reactions": reactions,
            "bubbles": bubbles,
        }
    )
    assert "<dt>created at</dt><dd>Not recorded</dd>" in html
    assert "<dt>seed</dt><dd>Not recorded</dd>" in html
