from __future__ import annotations

from collections.abc import Callable
from typing import Any

import streamlit as st

from src.config import AppSettings
from src.framing import generate_framings
from src.llm_pipeline import estimate_llm_cost
from src.scenarios import demo_scenarios
from src.schemas import ActorType, LLMProvider, NewsEvent
from src.storage import delete_simulation, list_simulations, load_simulation

RunSimulation = Callable[..., dict[str, Any]]


def render_setup_panel(
    settings: AppSettings, run_simulation: RunSimulation
) -> dict[str, Any] | None:
    scenarios = demo_scenarios()
    with st.sidebar:
        st.header("Setup")
        loaded = _previous_runs_panel(settings.database_path)
        if loaded:
            return loaded

        if st.button("Run demo mode", type="primary", width="stretch"):
            event = scenarios["City restricts short-term rentals"]
            frames = generate_framings(event, n=4)
            return _run_with_status(
                run_simulation=run_simulation,
                event=event,
                frames=frames,
                population_size=300,
                seed=42,
                echo_enabled=True,
                echo_rounds=2,
                run_mode="mock",
                provider=LLMProvider.MOCK,
                model_name=None,
                media_preset="balanced",
                included_actor_types=None,
                echo_items_per_actor=(1, 2),
                max_workers=settings.llm_max_workers,
                request_timeout_seconds=settings.llm_request_timeout_seconds,
            )

        scenario_name = st.selectbox("Scenario", list(scenarios) + ["Custom event"])
        event = _custom_event_form() if scenario_name == "Custom event" else scenarios[scenario_name]

        run_mode_label = st.selectbox(
            "Run mode",
            ["Mock", "Hybrid", "Full LLM sample"],
            help=(
                "Hybrid uses bounded artifact-level LLM calls. Full LLM sample "
                "adds one provider call per selected agent/frame and is capped at 100 agents."
            ),
        )
        run_mode = _run_mode_value(run_mode_label)
        if run_mode == "full_llm_sample":
            st.warning(
                "Full LLM sample is synthetic, cost-bearing, and capped at 100 agents. "
                "Do not use it for persuasion targeting or polling claims."
            )

        population_size = _population_control(run_mode)
        seed = st.number_input("Random seed", value=42, min_value=0, step=1)
        provider = _provider_control(run_mode)
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
            help=(
                "In LLM modes this count guides LLM frame generation; selected "
                "frames are used if provider generation falls back."
            ),
        )
        echo_enabled = st.toggle("Echo simulation", value=True)
        echo_rounds = st.number_input(
            "Echo rounds", value=1, min_value=1, max_value=3, disabled=not echo_enabled
        )
        media_preset = st.selectbox(
            "Media preset",
            [
                "balanced",
                "low_trust",
                "high_institutional_trust",
                "highly_partisan",
                "expert_heavy",
            ],
        )
        included_actor_types = _actor_type_toggles()
        echo_items_per_actor = st.select_slider(
            "Echo items per actor",
            options=[1, 2, 3],
            value=1,
            help="Higher values create a denser timeline with more memes, corrections, and interpretations.",
        )
        max_workers = st.slider(
            "LLM max workers",
            min_value=1,
            max_value=16,
            value=settings.llm_max_workers,
            disabled=run_mode == "mock",
        )
        request_timeout_seconds = st.slider(
            "LLM request timeout",
            min_value=5,
            max_value=300,
            value=settings.llm_request_timeout_seconds,
            step=5,
            disabled=run_mode == "mock",
        )

        _cost_panel(
            run_mode=run_mode,
            provider=provider,
            population_size=population_size,
            frame_count=max(1, len(selected_frame_ids)),
            echo_enabled=echo_enabled,
        )
        provider_ready, provider_message = _provider_ready(settings, provider, run_mode)
        if provider_message:
            (st.info if provider_ready else st.warning)(provider_message)

        if st.button(
            "Run simulation",
            type="primary",
            width="stretch",
            disabled=not provider_ready,
        ):
            frames = [
                frame for frame in all_frames if frame.frame_id in set(selected_frame_ids)
            ] or all_frames[:1]
            return _run_with_status(
                run_simulation=run_simulation,
                event=event,
                frames=frames,
                population_size=population_size,
                seed=int(seed),
                echo_enabled=echo_enabled,
                echo_rounds=int(echo_rounds if echo_enabled else 0),
                run_mode=run_mode,
                provider=provider,
                model_name=model_name,
                media_preset=media_preset,
                included_actor_types=included_actor_types,
                echo_items_per_actor=(
                    (1, int(echo_items_per_actor))
                    if int(echo_items_per_actor) > 1
                    else 1
                ),
                max_workers=int(max_workers),
                request_timeout_seconds=int(request_timeout_seconds),
            )
    return None


def _run_with_status(
    run_simulation: RunSimulation,
    event: NewsEvent,
    frames,
    population_size: int,
    seed: int,
    echo_enabled: bool,
    echo_rounds: int,
    run_mode: str,
    provider: LLMProvider,
    model_name: str | None,
    media_preset: str,
    included_actor_types: set[ActorType] | None,
    echo_items_per_actor: int | tuple[int, int],
    max_workers: int,
    request_timeout_seconds: int,
) -> dict[str, Any]:
    with st.status("Running EchoGrid simulation...", expanded=True) as status:
        def progress(message: str, percent: int | None = None) -> None:
            suffix = f" ({percent}%)" if percent is not None else ""
            status.write(f"{message}{suffix}")

        simulation = run_simulation(
            event=event,
            frames=frames,
            population_size=population_size,
            seed=seed,
            echo_enabled=echo_enabled,
            echo_rounds=echo_rounds,
            run_mode=run_mode,
            provider=provider,
            model_name=model_name,
            progress_callback=progress,
            media_preset=media_preset,
            included_actor_types=included_actor_types,
            echo_items_per_actor=echo_items_per_actor,
            max_workers=max_workers,
            request_timeout_seconds=request_timeout_seconds,
        )
        status.update(label="Simulation ready", state="complete")
        return simulation


def _previous_runs_panel(database_path) -> dict[str, Any] | None:
    summaries = list_simulations(database_path)
    if not summaries:
        st.caption("No saved runs yet.")
        return None

    with st.expander("Previous runs", expanded=False):
        options = {
            _simulation_label(summary): summary["simulation_id"] for summary in summaries
        }
        selected_label = st.selectbox("Saved simulation", list(options))
        selected_id = options[selected_label]
        c1, c2 = st.columns(2)
        if c1.button("Load", width="stretch"):
            return load_simulation(database_path, selected_id)
        if c2.button("Delete", width="stretch"):
            delete_simulation(database_path, selected_id)
            st.rerun()
    return None


def _simulation_label(summary: dict[str, Any]) -> str:
    title = summary.get("event_title") or "Untitled event"
    created_at = str(summary.get("created_at") or "")[:19].replace("T", " ")
    population_size = summary.get("population_size", 0)
    topic = summary.get("topic") or "topic"
    run_mode = summary.get("run_mode", "mock")
    return f"{created_at} | {title} | {population_size} agents | {topic} | {run_mode}"


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


def _run_mode_value(label: str) -> str:
    if label == "Hybrid":
        return "hybrid"
    if label == "Full LLM sample":
        return "full_llm_sample"
    return "mock"


def _population_control(run_mode: str) -> int:
    if run_mode == "full_llm_sample":
        return st.slider("Population size", 25, 100, 25, step=25)
    return st.slider("Population size", 50, 1000, 300, step=50)


def _provider_control(run_mode: str) -> LLMProvider:
    provider_options = (
        [LLMProvider.MOCK]
        if run_mode == "mock"
        else [LLMProvider.ANTHROPIC, LLMProvider.OPENAI, LLMProvider.GEMINI]
    )
    return st.selectbox(
        "Provider",
        provider_options,
        format_func=lambda value: value.value,
        help="Claude and ChatGPT/OpenAI routes use Trinity. Gemini uses GEMINI_API_KEY.",
    )


def _actor_type_toggles() -> set[ActorType] | None:
    with st.expander("Media actor toggles", expanded=False):
        selected = {
            actor_type
            for actor_type in ActorType
            if st.checkbox(actor_type.value.replace("_", " ").title(), value=True)
        }
    if selected == set(ActorType):
        return None
    return selected


def _cost_panel(
    run_mode: str,
    provider: LLMProvider,
    population_size: int,
    frame_count: int,
    echo_enabled: bool,
) -> None:
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
            return (
                False,
                f"Set {', '.join(missing)} in .env before running {provider.value} via Trinity.",
            )
        return True, f"{provider.value} will be routed through the Trinity gateway."
    if provider == LLMProvider.GEMINI:
        if not getattr(settings, "gemini_api_key", None):
            return False, "Set GEMINI_API_KEY in .env before running Gemini LLM mode."
        return True, "Gemini LLM mode will use the direct Gemini API key."
    return False, f"Unsupported provider for {run_mode}: {provider.value}"


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
