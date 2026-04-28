from __future__ import annotations

import json
from typing import Any

import pandas as pd
import plotly.express as px
import streamlit as st

from src.analytics import (
    bubble_susceptibility,
    emotion_averages,
    frame_comparison,
    segment_breakdown,
    share_likelihood_distribution,
    stance_distribution,
    trust_average,
)
from src.config import ETHICAL_USE_DISCLAIMER, SYNTHETIC_SIMULATION_DISCLAIMER, get_settings
from src.echo_engine import run_echo_simulation
from src.framing import generate_framings
from src.media_ecosystem import default_media_actors
from src.population import generate_population
from src.reaction_engine import run_initial_reactions
from src.scenarios import demo_scenarios
from src.schemas import NewsEvent, PopulationConfig
from src.social_bubbles import assign_agents_to_bubbles, default_social_bubbles
from src.storage import save_simulation


def main() -> None:
    st.set_page_config(page_title="EchoGrid", layout="wide")
    st.title("EchoGrid")
    st.caption(
        "Synthetic society simulator for media dynamics, echo effects, and communication-risk analysis."
    )

    st.warning(SYNTHETIC_SIMULATION_DISCLAIMER)
    st.info(ETHICAL_USE_DISCLAIMER)

    simulation = _setup_panel()
    if simulation:
        st.session_state["simulation"] = simulation

    current = st.session_state.get("simulation")
    if not current:
        st.write("Configure a scenario in the setup panel and run the simulation.")
        return

    _dashboard(current)


def _setup_panel() -> dict[str, Any] | None:
    scenarios = demo_scenarios()
    with st.sidebar:
        st.header("Setup")
        scenario_name = st.selectbox("Scenario", list(scenarios) + ["Custom event"])
        if scenario_name == "Custom event":
            event = _custom_event_form()
        else:
            event = scenarios[scenario_name]

        population_size = st.slider("Population size", 50, 1000, 300, step=50)
        seed = st.number_input("Random seed", value=42, min_value=0, step=1)
        provider = st.selectbox(
            "Provider",
            ["mock", "anthropic", "gemini", "openai"],
            help="MVP v1 runs the full simulation in deterministic mock mode. API providers are configured for the upcoming LLM mode.",
        )
        st.caption(f"Configured provider: {provider}. Current run mode: mock.")

        all_frames = generate_framings(event, n=6)
        selected_frame_ids = st.multiselect(
            "Framings",
            [frame.frame_id for frame in all_frames],
            default=[frame.frame_id for frame in all_frames[:4]],
        )
        echo_enabled = st.toggle("Echo simulation", value=True)
        echo_rounds = st.number_input("Echo rounds", value=1, min_value=1, max_value=1)

        if st.button("Run simulation", type="primary", use_container_width=True):
            frames = [
                frame for frame in all_frames if frame.frame_id in set(selected_frame_ids)
            ] or all_frames[:1]
            with st.spinner("Generating synthetic population and echo dynamics..."):
                return _run_simulation(
                    event=event,
                    frames=frames,
                    population_size=population_size,
                    seed=int(seed),
                    echo_enabled=echo_enabled,
                    echo_rounds=int(echo_rounds),
                )
    return None


def _custom_event_form() -> NewsEvent:
    title = st.text_input("Title", "Custom public message")
    topic = st.text_input("Topic", "policy")
    country = st.text_input("Country", "United States")
    source_type = st.text_input("Source type", "public_message")
    description = st.text_area(
        "Description", "Describe the event, proposal, statement, or post."
    )
    original_text = st.text_area("Original text", description)
    return NewsEvent(
        title=title,
        description=description,
        country=country,
        topic=topic,
        source_type=source_type,
        original_text=original_text,
    )


def _run_simulation(
    event: NewsEvent,
    frames,
    population_size: int,
    seed: int,
    echo_enabled: bool,
    echo_rounds: int,
) -> dict[str, Any]:
    agents = generate_population(
        PopulationConfig(country=event.country, population_size=population_size, seed=seed)
    )
    initial_reactions = run_initial_reactions(agents, event, frames, mode="mock", seed=seed)
    media_actors = default_media_actors()
    bubbles = default_social_bubbles()
    assignments = assign_agents_to_bubbles(agents, bubbles)
    echo_result = None
    if echo_enabled and echo_rounds:
        echo_result = run_echo_simulation(
            agents=agents,
            event=event,
            frames=frames,
            initial_reactions=initial_reactions,
            media_actors=media_actors,
            bubbles=bubbles,
            bubble_assignments=assignments,
            mode="mock",
            seed=seed,
        )
    simulation_id = save_simulation(
        db_path=get_settings().database_path,
        event=event,
        agents=agents,
        frames=frames,
        reactions=initial_reactions,
        media_actors=media_actors,
        bubbles=bubbles,
        bubble_assignments=assignments,
        echo_result=echo_result,
    )
    return {
        "simulation_id": simulation_id,
        "event": event,
        "frames": frames,
        "agents": agents,
        "initial_reactions": initial_reactions,
        "media_actors": media_actors,
        "bubbles": bubbles,
        "assignments": assignments,
        "echo_result": echo_result,
    }


def _dashboard(simulation: dict[str, Any]) -> None:
    tabs = st.tabs(
        [
            "Overview",
            "Population",
            "Media",
            "Bubbles",
            "Initial Reaction",
            "Echo Timeline",
            "Echo Items",
            "Amplification",
            "Bubble Impact",
            "Frame Comparison",
            "Segment Explorer",
            "Comments",
            "Export",
        ]
    )
    with tabs[0]:
        _overview_tab(simulation)
    with tabs[1]:
        _population_tab(simulation)
    with tabs[2]:
        _media_tab(simulation)
    with tabs[3]:
        _bubbles_tab(simulation)
    with tabs[4]:
        _initial_reaction_tab(simulation)
    with tabs[5]:
        _timeline_tab(simulation)
    with tabs[6]:
        _echo_items_tab(simulation)
    with tabs[7]:
        _amplification_tab(simulation)
    with tabs[8]:
        _bubble_impact_tab(simulation)
    with tabs[9]:
        _frame_comparison_tab(simulation)
    with tabs[10]:
        _segment_tab(simulation)
    with tabs[11]:
        _comments_tab(simulation)
    with tabs[12]:
        _export_tab(simulation)


def _overview_tab(simulation: dict[str, Any]) -> None:
    event: NewsEvent = simulation["event"]
    reactions = simulation["initial_reactions"]
    echo_result = simulation["echo_result"]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Agents", len(simulation["agents"]))
    c2.metric("Frames", len(simulation["frames"]))
    c3.metric("Initial reactions", len(reactions))
    c4.metric("Echo items", len(echo_result.echo_items) if echo_result else 0)
    st.caption(f"Simulation ID: {simulation['simulation_id']}")
    st.subheader(event.title)
    st.write(event.description)
    st.code(event.original_text, language="text")


def _population_tab(simulation: dict[str, Any]) -> None:
    agents_df = _agents_df(simulation["agents"])
    c1, c2 = st.columns(2)
    c1.plotly_chart(px.histogram(agents_df, x="age", nbins=20), use_container_width=True)
    c2.plotly_chart(px.histogram(agents_df, x="institutional_trust", nbins=20), use_container_width=True)
    c3, c4 = st.columns(2)
    c3.plotly_chart(px.histogram(agents_df, x="income_level"), use_container_width=True)
    c4.plotly_chart(px.histogram(agents_df, x="location_type"), use_container_width=True)
    st.dataframe(agents_df.head(100), use_container_width=True, hide_index=True)


def _media_tab(simulation: dict[str, Any]) -> None:
    actors_df = pd.DataFrame([actor.model_dump(mode="json") for actor in simulation["media_actors"]])
    st.dataframe(actors_df, use_container_width=True, hide_index=True)
    st.plotly_chart(
        px.scatter(
            actors_df,
            x="credibility",
            y="sensationalism",
            size="reach",
            color="actor_type",
            hover_name="name",
        ),
        use_container_width=True,
    )


def _bubbles_tab(simulation: dict[str, Any]) -> None:
    rows = []
    assignments = simulation["assignments"]
    for bubble in simulation["bubbles"]:
        data = bubble.model_dump(mode="json")
        data["agent_count"] = len(assignments.get(bubble.id, []))
        rows.append(data)
    bubbles_df = pd.DataFrame(rows)
    st.dataframe(bubbles_df, use_container_width=True, hide_index=True)
    st.plotly_chart(
        px.bar(bubbles_df, x="label", y="agent_count", color="outrage_sensitivity"),
        use_container_width=True,
    )


def _initial_reaction_tab(simulation: dict[str, Any]) -> None:
    reactions = simulation["initial_reactions"]
    c1, c2, c3 = st.columns(3)
    c1.metric("Average trust", trust_average(reactions))
    c2.metric("Average share likelihood", share_likelihood_distribution(reactions)["average"])
    c3.metric("Emotional intensity", emotion_averages(reactions)["emotional_intensity"])
    stance_df = pd.DataFrame(
        [{"stance": key, "percent": value} for key, value in stance_distribution(reactions).items()]
    )
    st.plotly_chart(px.bar(stance_df, x="stance", y="percent"), use_container_width=True)
    st.dataframe(_reactions_df(reactions).head(150), use_container_width=True, hide_index=True)


def _timeline_tab(simulation: dict[str, Any]) -> None:
    event: NewsEvent = simulation["event"]
    st.subheader("Round 0: Original event")
    st.write(event.original_text)
    st.subheader("Round 1: Media framings")
    for frame in simulation["frames"]:
        st.markdown(f"**{frame.label}**")
        st.write(frame.text)
    st.subheader("Round 2: Initial reactions")
    st.write(stance_distribution(simulation["initial_reactions"]))
    echo_result = simulation["echo_result"]
    if echo_result:
        st.subheader("Round 3: Echo items")
        st.dataframe(_echo_items_df(echo_result.echo_items), use_container_width=True, hide_index=True)
        st.subheader("Round 4: Echo reactions")
        st.dataframe(_echo_reactions_df(echo_result.echo_reactions).head(150), use_container_width=True, hide_index=True)


def _echo_items_tab(simulation: dict[str, Any]) -> None:
    echo_result = simulation["echo_result"]
    if not echo_result:
        st.write("Echo simulation was disabled.")
        return
    df = _echo_items_df(echo_result.echo_items)
    echo_types = st.multiselect("Echo type", sorted(df["echo_type"].unique()), default=sorted(df["echo_type"].unique()))
    filtered = df[df["echo_type"].isin(echo_types)]
    st.dataframe(filtered, use_container_width=True, hide_index=True)


def _amplification_tab(simulation: dict[str, Any]) -> None:
    echo_result = simulation["echo_result"]
    if not echo_result:
        st.write("Echo simulation was disabled.")
        return
    metrics = echo_result.amplification_metrics
    cols = st.columns(len(metrics))
    for col, (key, value) in zip(cols, metrics.items(), strict=False):
        col.metric(key.replace("_", " ").title(), value)
    metric_df = pd.DataFrame(
        [{"metric": key, "value": value} for key, value in metrics.items()]
    )
    st.plotly_chart(px.bar(metric_df, x="metric", y="value"), use_container_width=True)


def _bubble_impact_tab(simulation: dict[str, Any]) -> None:
    echo_result = simulation["echo_result"]
    if not echo_result:
        st.write("Echo simulation was disabled.")
        return
    rows = bubble_susceptibility(echo_result.echo_reactions, simulation["bubbles"])
    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)
    if not df.empty:
        st.plotly_chart(
            px.bar(df, x="label", y="average_share_likelihood_shift", color="average_anger_shift"),
            use_container_width=True,
        )


def _frame_comparison_tab(simulation: dict[str, Any]) -> None:
    comparison = frame_comparison(simulation["initial_reactions"])
    rows = []
    for frame_id, data in comparison.items():
        rows.append(
            {
                "frame_id": frame_id,
                "average_trust": data["average_trust"],
                "average_share_likelihood": data["average_share_likelihood"],
                "polarization_score": data["polarization_score"],
                "virality_risk_score": data["virality_risk_score"],
                **data["stance_distribution"],
            }
        )
    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)
    st.plotly_chart(px.bar(df, x="frame_id", y=["support", "oppose", "neutral", "confused"]), use_container_width=True)


def _segment_tab(simulation: dict[str, Any]) -> None:
    field = st.selectbox(
        "Group by",
        [
            "income_level",
            "education_level",
            "location_type",
            "economic_position",
            "social_position",
            "political_engagement",
        ],
    )
    rows = segment_breakdown(
        simulation["initial_reactions"], simulation["agents"], by_field=field
    )
    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)
    if not df.empty:
        st.plotly_chart(px.bar(df, x="segment", y="average_share_likelihood"), use_container_width=True)


def _comments_tab(simulation: dict[str, Any]) -> None:
    df = _reactions_df(simulation["initial_reactions"])
    stance = st.multiselect("Stance", sorted(df["stance"].unique()), default=sorted(df["stance"].unique()))
    filtered = df[df["stance"].isin(stance)]
    st.dataframe(
        filtered[["agent_id", "frame_id", "stance", "likely_comment", "main_reason"]].head(300),
        use_container_width=True,
        hide_index=True,
    )


def _export_tab(simulation: dict[str, Any]) -> None:
    agents_df = _agents_df(simulation["agents"])
    reactions_df = _reactions_df(simulation["initial_reactions"])
    st.download_button("Export agents CSV", agents_df.to_csv(index=False), "agents.csv")
    st.download_button("Export reactions CSV", reactions_df.to_csv(index=False), "reactions.csv")

    echo_result = simulation["echo_result"]
    if echo_result:
        echo_items_df = _echo_items_df(echo_result.echo_items)
        echo_reactions_df = _echo_reactions_df(echo_result.echo_reactions)
        st.download_button("Export echo items CSV", echo_items_df.to_csv(index=False), "echo_items.csv")
        st.download_button("Export echo reactions CSV", echo_reactions_df.to_csv(index=False), "echo_reactions.csv")
    st.download_button(
        "Export summary JSON",
        json.dumps(_summary_payload(simulation), indent=2),
        "summary.json",
        mime="application/json",
    )


def _agents_df(agents) -> pd.DataFrame:
    return pd.DataFrame([agent.model_dump(mode="json") for agent in agents])


def _reactions_df(reactions) -> pd.DataFrame:
    rows = []
    for reaction in reactions:
        row = reaction.model_dump(mode="json")
        emotions = row.pop("emotions")
        row.update({f"emotion_{key}": value for key, value in emotions.items()})
        row["emotional_intensity"] = reaction.emotional_intensity
        rows.append(row)
    return pd.DataFrame(rows)


def _echo_items_df(items) -> pd.DataFrame:
    return pd.DataFrame([item.model_dump(mode="json") for item in items])


def _echo_reactions_df(reactions) -> pd.DataFrame:
    rows = []
    for reaction in reactions:
        row = reaction.model_dump(mode="json")
        shifts = row.pop("emotion_shift")
        row.update({f"{key}_shift": value for key, value in shifts.items()})
        rows.append(row)
    return pd.DataFrame(rows)


def _summary_payload(simulation: dict[str, Any]) -> dict[str, Any]:
    echo_result = simulation["echo_result"]
    return {
        "event": simulation["event"].model_dump(mode="json"),
        "frames": [frame.model_dump(mode="json") for frame in simulation["frames"]],
        "initial_metrics": {
            "stance_distribution": stance_distribution(simulation["initial_reactions"]),
            "emotion_averages": emotion_averages(simulation["initial_reactions"]),
            "trust_average": trust_average(simulation["initial_reactions"]),
            "share_likelihood_distribution": share_likelihood_distribution(simulation["initial_reactions"]),
        },
        "amplification_metrics": echo_result.amplification_metrics if echo_result else {},
    }


if __name__ == "__main__":
    main()
