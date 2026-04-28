from __future__ import annotations

from collections.abc import Callable
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
from src.echo_engine import generate_echo_items, run_echo_simulation
from src.framing import generate_framings
from src.llm_client import build_llm_client
from src.llm_pipeline import (
    estimate_llm_cost,
    generate_hybrid_frames,
    generate_hybrid_response_artifacts,
)
from src.media_ecosystem import default_media_actors
from src.population import generate_population
from src.reaction_engine import run_initial_reactions
from src.report import (
    agents_to_dataframe,
    dataframe_to_csv_export,
    echo_items_to_dataframe,
    echo_reactions_to_dataframe,
    reactions_to_dataframe,
    simulation_summary_json,
)
from src.scenarios import demo_scenarios
from src.schemas import LLMProvider, NewsEvent, PopulationConfig
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
    settings = get_settings()
    with st.sidebar:
        st.header("Setup")
        scenario_name = st.selectbox("Scenario", list(scenarios) + ["Custom event"])
        if scenario_name == "Custom event":
            event = _custom_event_form()
        else:
            event = scenarios[scenario_name]

        population_size = st.slider("Population size", 50, 1000, 300, step=50)
        seed = st.number_input("Random seed", value=42, min_value=0, step=1)
        run_mode_label = st.selectbox(
            "Run mode",
            ["Mock", "Hybrid"],
            help="Hybrid uses LLM calls only for framings, echo items, and representative comments.",
        )
        run_mode = "mock" if run_mode_label == "Mock" else "hybrid"
        provider_options = (
            [LLMProvider.MOCK]
            if run_mode == "mock"
            else [LLMProvider.ANTHROPIC, LLMProvider.OPENAI, LLMProvider.GEMINI]
        )
        provider = st.selectbox(
            "Provider",
            provider_options,
            format_func=lambda value: value.value,
            help="Claude and ChatGPT/OpenAI routes use the Trinity gateway. Gemini uses its direct API key.",
        )
        model_preset = st.selectbox(
            "Model preset",
            _model_preset_options(provider, run_mode),
            disabled=run_mode == "mock",
        )
        model_name = _model_for_preset(settings, provider, model_preset)
        if model_name:
            st.caption(f"Model: {model_name}")

        all_frames = generate_framings(event, n=6)
        selected_frame_ids = st.multiselect(
            "Framings" if run_mode == "mock" else "Fallback framings",
            [frame.frame_id for frame in all_frames],
            default=[frame.frame_id for frame in all_frames[:4]],
            help="In Hybrid mode this count guides LLM frame generation and these frames are used if the LLM call fails.",
        )
        echo_enabled = st.toggle("Echo simulation", value=True)
        echo_rounds = st.number_input("Echo rounds", value=1, min_value=1, max_value=1)
        frame_count = max(1, len(selected_frame_ids))
        estimate = estimate_llm_cost(
            run_mode=run_mode,
            provider=provider,
            population_size=population_size,
            frame_count=frame_count,
            echo_enabled=echo_enabled,
        )
        st.caption(
            f"Estimated LLM calls: {estimate.estimated_calls}; "
            f"rough cost: ${estimate.estimated_usd_low:.4f}-${estimate.estimated_usd_high:.4f}. "
            f"{estimate.notes}"
        )
        provider_ready, provider_message = _provider_ready(settings, provider, run_mode)
        if provider_message:
            (st.info if provider_ready else st.warning)(provider_message)

        if st.button(
            "Run simulation",
            type="primary",
            use_container_width=True,
            disabled=not provider_ready,
        ):
            frames = [
                frame for frame in all_frames if frame.frame_id in set(selected_frame_ids)
            ] or all_frames[:1]
            with st.status("Running EchoGrid simulation...", expanded=True) as status:
                def progress(message: str) -> None:
                    status.write(message)

                simulation = _run_simulation(
                    event=event,
                    frames=frames,
                    population_size=population_size,
                    seed=int(seed),
                    echo_enabled=echo_enabled,
                    echo_rounds=int(echo_rounds),
                    run_mode=run_mode,
                    provider=provider,
                    model_name=model_name,
                    progress_callback=progress,
                )
                status.update(label="Simulation ready", state="complete")
                return simulation
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


def _provider_ready(
    settings: Any, provider: LLMProvider, run_mode: str
) -> tuple[bool, str]:
    if run_mode == "mock":
        return True, "Mock mode is local and does not require API keys."
    if provider in {LLMProvider.ANTHROPIC, LLMProvider.OPENAI}:
        missing = []
        if not getattr(settings, "trinity_api_key", None):
            missing.append("TRINITY_API_KEY")
        if not getattr(settings, "trinity_base_url", None):
            missing.append("TRINITY_BASE_URL")
        if missing:
            return False, f"Set {', '.join(missing)} in .env before running {provider.value} via Trinity."
        return True, f"{provider.value} will be routed through the Trinity gateway."
    if provider == LLMProvider.GEMINI:
        if not getattr(settings, "gemini_api_key", None):
            return False, "Set GEMINI_API_KEY in .env before running Gemini Hybrid mode."
        return True, "Gemini Hybrid mode will use the direct Gemini API key."
    return False, f"Unsupported provider for {run_mode}: {provider.value}"


def _run_simulation(
    event: NewsEvent,
    frames,
    population_size: int,
    seed: int,
    echo_enabled: bool,
    echo_rounds: int,
    run_mode: str = "mock",
    provider: LLMProvider = LLMProvider.MOCK,
    model_name: str | None = None,
    progress_callback: Callable[[str], None] | None = None,
) -> dict[str, Any]:
    provider = provider if isinstance(provider, LLMProvider) else LLMProvider(provider)
    run_mode = run_mode.strip().lower()
    settings = get_settings()
    frames_for_run = list(frames)
    llm_errors = []
    representative_comments = []
    llm_client = None

    if run_mode == "hybrid":
        _notify(progress_callback, "Connecting to LLM provider")
        llm_client = build_llm_client(
            _settings_for_provider(settings, provider, model_name)
        )
        _notify(progress_callback, "Generating LLM framings")
        frames_for_run, frame_errors = generate_hybrid_frames(
            client=llm_client,
            event=event,
            fallback_frames=frames_for_run,
            frame_count=len(frames_for_run),
        )
        llm_errors.extend(frame_errors)

    _notify(progress_callback, "Generating synthetic population")
    agents = generate_population(
        PopulationConfig(country=event.country, population_size=population_size, seed=seed)
    )
    _notify(progress_callback, "Running initial synthetic reactions")
    initial_reactions = run_initial_reactions(
        agents, event, frames_for_run, mode="mock", seed=seed
    )
    _notify(progress_callback, "Preparing media actors and social bubbles")
    media_actors = default_media_actors()
    bubbles = default_social_bubbles()
    assignments = assign_agents_to_bubbles(agents, bubbles)
    echo_result = None
    echo_items_override = None

    if echo_enabled and echo_rounds:
        if run_mode == "hybrid" and llm_client is not None:
            _notify(progress_callback, "Generating LLM echo items and representative comments")
            fallback_echo_items = generate_echo_items(
                event=event,
                frames=frames_for_run,
                reactions=initial_reactions,
                media_actors=media_actors,
                bubbles=bubbles,
                mode="mock",
                seed=seed,
            )
            artifacts = generate_hybrid_response_artifacts(
                client=llm_client,
                event=event,
                frames=frames_for_run,
                initial_reactions=initial_reactions,
                media_actors=media_actors,
                bubbles=bubbles,
                fallback_echo_items=fallback_echo_items,
                echo_enabled=True,
            )
            echo_items_override = artifacts.echo_items
            representative_comments = artifacts.representative_comments
            llm_errors.extend(artifacts.errors)

        _notify(progress_callback, "Running echo reactions")
        echo_result = run_echo_simulation(
            agents=agents,
            event=event,
            frames=frames_for_run,
            initial_reactions=initial_reactions,
            media_actors=media_actors,
            bubbles=bubbles,
            bubble_assignments=assignments,
            mode="mock",
            seed=seed,
            echo_items_override=echo_items_override,
        )
    elif run_mode == "hybrid" and llm_client is not None:
        _notify(progress_callback, "Generating representative comments")
        artifacts = generate_hybrid_response_artifacts(
            client=llm_client,
            event=event,
            frames=frames_for_run,
            initial_reactions=initial_reactions,
            media_actors=media_actors,
            bubbles=bubbles,
            fallback_echo_items=[],
            echo_enabled=False,
        )
        representative_comments = artifacts.representative_comments
        llm_errors.extend(artifacts.errors)

    _notify(progress_callback, "Saving simulation")
    simulation_id = save_simulation(
        db_path=settings.database_path,
        event=event,
        agents=agents,
        frames=frames_for_run,
        reactions=initial_reactions,
        media_actors=media_actors,
        bubbles=bubbles,
        bubble_assignments=assignments,
        echo_result=echo_result,
    )
    return {
        "simulation_id": simulation_id,
        "event": event,
        "frames": frames_for_run,
        "agents": agents,
        "reactions": initial_reactions,
        "initial_reactions": initial_reactions,
        "media_actors": media_actors,
        "bubbles": bubbles,
        "assignments": assignments,
        "echo_result": echo_result,
        "run_mode": run_mode,
        "provider": provider,
        "representative_comments": representative_comments,
        "llm_errors": llm_errors,
        "llm_cost_estimate": estimate_llm_cost(
            run_mode=run_mode,
            provider=provider,
            population_size=population_size,
            frame_count=len(frames_for_run),
            echo_enabled=echo_enabled,
        ),
    }

def _model_preset_options(provider: LLMProvider, run_mode: str) -> list[str]:
    if run_mode == "mock":
        return ["Local mock"]
    if provider == LLMProvider.ANTHROPIC:
        return ["balanced", "cheap", "premium"]
    return ["balanced", "cheap"]


def _model_for_preset(settings: Any, provider: LLMProvider, preset: str) -> str | None:
    if provider == LLMProvider.MOCK:
        return None
    if provider == LLMProvider.ANTHROPIC:
        return {
            "cheap": getattr(settings, "anthropic_reaction_model", None),
            "balanced": getattr(settings, "anthropic_echo_model", None),
            "premium": getattr(settings, "anthropic_premium_model", None),
        }.get(preset)
    if provider == LLMProvider.OPENAI:
        return {
            "cheap": getattr(settings, "openai_reaction_model", None),
            "balanced": getattr(settings, "openai_echo_model", None),
        }.get(preset)
    if provider == LLMProvider.GEMINI:
        return {
            "cheap": getattr(settings, "gemini_reaction_model", None),
            "balanced": getattr(settings, "gemini_echo_model", None),
        }.get(preset)
    return None


def _settings_for_provider(
    settings: Any, provider: LLMProvider, model_name: str | None = None
) -> Any:
    updates = {"llm_provider": provider}
    if model_name and provider == LLMProvider.ANTHROPIC:
        updates["anthropic_echo_model"] = model_name
    elif model_name and provider == LLMProvider.OPENAI:
        updates["openai_echo_model"] = model_name
    elif model_name and provider == LLMProvider.GEMINI:
        updates["gemini_echo_model"] = model_name
    if hasattr(settings, "model_copy"):
        return settings.model_copy(update=updates)
    for key, value in updates.items():
        setattr(settings, key, value)
    return settings


def _notify(callback: Callable[[str], None] | None, message: str) -> None:
    if callback is not None:
        callback(message)


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
    st.caption(
        f"Run mode: {simulation.get('run_mode', 'mock')} | "
        f"Provider: {_provider_label(simulation.get('provider'))}"
    )
    llm_errors = simulation.get("llm_errors") or []
    if llm_errors:
        st.warning("Some LLM generation steps fell back to deterministic artifacts.")
        st.dataframe(
            pd.DataFrame([error.model_dump(mode="json") for error in llm_errors]),
            use_container_width=True,
            hide_index=True,
        )
    st.subheader(event.title)
    st.write(event.description)
    st.code(event.original_text, language="text")


def _population_tab(simulation: dict[str, Any]) -> None:
    agents_df = agents_to_dataframe(simulation["agents"])
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
    st.dataframe(
        reactions_to_dataframe(reactions, _bubble_assignments(simulation)).head(150),
        use_container_width=True,
        hide_index=True,
    )


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
        st.dataframe(echo_items_to_dataframe(echo_result.echo_items), use_container_width=True, hide_index=True)
        st.subheader("Round 4: Echo reactions")
        st.dataframe(echo_reactions_to_dataframe(echo_result.echo_reactions).head(150), use_container_width=True, hide_index=True)


def _echo_items_tab(simulation: dict[str, Any]) -> None:
    echo_result = simulation["echo_result"]
    if not echo_result:
        st.write("Echo simulation was disabled.")
        return
    df = echo_items_to_dataframe(echo_result.echo_items)
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
            "age_group",
            "institutional_trust_bucket",
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
    representative_comments = simulation.get("representative_comments") or []
    if representative_comments:
        st.subheader("Representative comments")
        st.dataframe(
            pd.DataFrame(
                [comment.model_dump(mode="json") for comment in representative_comments]
            ),
            use_container_width=True,
            hide_index=True,
        )
        st.divider()

    df = reactions_to_dataframe(
        simulation["initial_reactions"], _bubble_assignments(simulation)
    )
    stance = st.multiselect("Stance", sorted(df["stance"].unique()), default=sorted(df["stance"].unique()))
    filtered = df[df["stance"].isin(stance)]
    st.dataframe(
        filtered[
            [
                "agent_id",
                "frame_id",
                "social_bubble",
                "stance",
                "likely_comment",
                "main_reason",
            ]
        ].head(300),
        use_container_width=True,
        hide_index=True,
    )


def _export_tab(simulation: dict[str, Any]) -> None:
    agents_df = agents_to_dataframe(simulation["agents"])
    reactions_df = reactions_to_dataframe(
        simulation["initial_reactions"], _bubble_assignments(simulation)
    )
    st.download_button(
        "Export agents CSV",
        dataframe_to_csv_export(agents_df, "agents"),
        "agents.csv",
    )
    st.download_button(
        "Export reactions CSV",
        dataframe_to_csv_export(reactions_df, "reactions"),
        "reactions.csv",
    )

    echo_result = simulation["echo_result"]
    if echo_result:
        echo_items_df = echo_items_to_dataframe(echo_result.echo_items)
        echo_reactions_df = echo_reactions_to_dataframe(echo_result.echo_reactions)
        st.download_button(
            "Export echo items CSV",
            dataframe_to_csv_export(echo_items_df, "echo_items"),
            "echo_items.csv",
        )
        st.download_button(
            "Export echo reactions CSV",
            dataframe_to_csv_export(echo_reactions_df, "echo_reactions"),
            "echo_reactions.csv",
        )
    st.download_button(
        "Export summary JSON",
        simulation_summary_json(
            event=simulation["event"],
            frames=simulation["frames"],
            reactions=simulation["initial_reactions"],
            echo_result=echo_result,
            run_mode=simulation.get("run_mode", "mock"),
            provider=simulation.get("provider"),
            representative_comments=simulation.get("representative_comments"),
            llm_errors=simulation.get("llm_errors"),
        ),
        "summary.json",
        mime="application/json",
    )


def _provider_label(provider: Any) -> str:
    if isinstance(provider, LLMProvider):
        return provider.value
    return str(provider or "mock")


def _bubble_assignments(simulation: dict[str, Any]) -> dict[str, list[str]]:
    return simulation.get("assignments") or simulation.get("bubble_assignments") or {}


if __name__ == "__main__":
    main()
