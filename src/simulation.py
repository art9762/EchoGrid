"""Application-service layer for running EchoGrid simulations.

This module keeps the Streamlit UI thin: callers provide an event, selected
frames, run settings, and a persistence target; the service coordinates the
domain generators, echo layer, storage, and progress notifications.
"""

from __future__ import annotations

from collections.abc import Callable
from inspect import Parameter, signature
from pathlib import Path
from typing import Any

from src.config import get_settings
from src.echo_engine import generate_echo_items, run_echo_simulation
from src.llm_client import build_llm_client
from src.llm_pipeline import (
    estimate_llm_cost,
    generate_hybrid_frames,
    generate_hybrid_response_artifacts,
)
from src.media_ecosystem import default_media_actors
from src.population import generate_population
from src.reaction_engine import run_initial_reactions
from src.schemas import LLMProvider, NewsEvent, NewsFrame, PopulationConfig
from src.social_bubbles import assign_agents_to_bubbles, default_social_bubbles
from src.storage import save_simulation


ProgressCallback = Callable[..., None]
LLMClientFactory = Callable[[Any], Any]


def run_simulation(
    event: NewsEvent,
    frames: list[NewsFrame],
    population_size: int,
    seed: int,
    echo_enabled: bool,
    echo_rounds: int,
    run_mode: str = "mock",
    provider: LLMProvider | str = LLMProvider.MOCK,
    model_name: str | None = None,
    db_path: str | Path | None = None,
    progress_callback: ProgressCallback | None = None,
    llm_client_factory: LLMClientFactory = build_llm_client,
) -> dict[str, Any]:
    """Run one EchoGrid simulation and persist the result."""
    provider = provider if isinstance(provider, LLMProvider) else LLMProvider(provider)
    run_mode = run_mode.strip().lower()
    settings = get_settings()
    database_path = Path(db_path) if db_path is not None else settings.database_path
    frames_for_run = list(frames)
    llm_errors = []
    representative_comments = []
    llm_client = None

    if run_mode == "hybrid":
        _notify(progress_callback, "Connecting to LLM provider", 8)
        llm_client = llm_client_factory(
            _settings_for_provider(settings, provider, model_name)
        )
        _notify(progress_callback, "Generating LLM framings", 18)
        frames_for_run, frame_errors = generate_hybrid_frames(
            client=llm_client,
            event=event,
            fallback_frames=frames_for_run,
            frame_count=len(frames_for_run),
        )
        llm_errors.extend(frame_errors)

    _notify(progress_callback, "Generating synthetic population...", 10)
    agents = generate_population(
        PopulationConfig(country=event.country, population_size=population_size, seed=seed)
    )

    _notify(progress_callback, "Running initial reactions...", 35)
    initial_reactions = run_initial_reactions(
        agents, event, frames_for_run, mode="mock", seed=seed
    )

    _notify(progress_callback, "Preparing media ecosystem and bubbles...", 55)
    media_actors = default_media_actors()
    bubbles = default_social_bubbles()
    assignments = assign_agents_to_bubbles(agents, bubbles)

    echo_result = None
    echo_items_override = None
    if echo_enabled and echo_rounds:
        if run_mode == "hybrid" and llm_client is not None:
            _notify(
                progress_callback,
                "Generating LLM echo items and representative comments",
                68,
            )
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

        _notify(progress_callback, "Generating echo items and reactions...", 75)
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
        _notify(progress_callback, "Generating representative comments", 78)
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

    _notify(progress_callback, "Saving simulation and exports metadata...", 92)
    simulation_id = save_simulation(
        db_path=database_path,
        event=event,
        agents=agents,
        frames=frames_for_run,
        reactions=initial_reactions,
        media_actors=media_actors,
        bubbles=bubbles,
        bubble_assignments=assignments,
        echo_result=echo_result,
        seed=seed,
        provider=provider.value,
    )

    _notify(progress_callback, "Simulation saved.", 100)
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
        "bubble_assignments": assignments,
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
        "metadata": {
            "provider": provider.value,
            "runtime_mode": run_mode,
            "population_size": population_size,
            "seed": seed,
            "echo_enabled": echo_enabled,
            "echo_rounds": echo_rounds,
        },
    }


def _notify(
    progress_callback: ProgressCallback | None, message: str, progress: int
) -> None:
    if progress_callback is None:
        return
    if _accepts_two_positional_args(progress_callback):
        progress_callback(message, progress)
        return
    progress_callback(message)


def _accepts_two_positional_args(callback: ProgressCallback) -> bool:
    parameters = signature(callback).parameters.values()
    positional = [
        parameter
        for parameter in parameters
        if parameter.kind
        in {
            Parameter.POSITIONAL_ONLY,
            Parameter.POSITIONAL_OR_KEYWORD,
            Parameter.VAR_POSITIONAL,
        }
    ]
    return any(parameter.kind == Parameter.VAR_POSITIONAL for parameter in positional) or len(
        positional
    ) >= 2


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
