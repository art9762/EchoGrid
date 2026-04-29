from __future__ import annotations

from collections.abc import Callable
from typing import Any

import streamlit as st

from src.config import ETHICAL_USE_DISCLAIMER, SYNTHETIC_SIMULATION_DISCLAIMER, get_settings
from src.llm_client import build_llm_client
from src.schemas import LLMProvider, NewsEvent
from src.simulation import run_simulation as run_simulation_service
from src.ui.dashboard import render_dashboard, render_empty_state
from src.ui.setup import render_setup_panel


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
    progress_callback: Callable[..., None] | None = None,
    max_workers: int | None = None,
    request_timeout_seconds: int | None = None,
    media_preset: str = "balanced",
    included_actor_types: set | None = None,
    echo_items_per_actor: int | tuple[int, int] = 1,
) -> dict[str, Any]:
    return run_simulation_service(
        event=event,
        frames=frames,
        population_size=population_size,
        seed=seed,
        echo_enabled=echo_enabled,
        echo_rounds=echo_rounds,
        run_mode=run_mode,
        provider=provider,
        model_name=model_name,
        db_path=get_settings().database_path,
        progress_callback=progress_callback,
        llm_client_factory=build_llm_client,
        max_workers=max_workers,
        request_timeout_seconds=request_timeout_seconds,
        media_preset=media_preset,
        included_actor_types=included_actor_types,
        echo_items_per_actor=echo_items_per_actor,
    )


def main() -> None:
    st.set_page_config(page_title="EchoGrid", layout="wide")
    st.title("EchoGrid")
    st.caption(
        "Synthetic society simulator for media dynamics, echo effects, and communication-risk analysis."
    )
    st.warning(SYNTHETIC_SIMULATION_DISCLAIMER)
    st.info(ETHICAL_USE_DISCLAIMER)

    settings = get_settings()
    simulation = render_setup_panel(settings=settings, run_simulation=_run_simulation)
    if simulation:
        st.session_state["simulation"] = simulation

    current = st.session_state.get("simulation")
    if not current:
        render_empty_state()
        return

    render_dashboard(current)


if __name__ == "__main__":
    main()
