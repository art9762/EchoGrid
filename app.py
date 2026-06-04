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
from src.ui.theme import inject_theme


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


_LOGO_SVG = """
<svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24"
     fill="none" stroke="#38BDF8" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"
     aria-hidden="true" style="display:inline;vertical-align:middle;margin-right:10px">
  <circle cx="12" cy="12" r="10"/>
  <path d="M12 8v4l3 3"/>
  <path d="M2 12h2M20 12h2M12 2v2M12 20v2"/>
</svg>"""

_INFO_SVG = """
<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24"
     fill="none" stroke="#94A3B8" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"
     aria-hidden="true" style="display:inline;vertical-align:middle;margin-right:6px">
  <circle cx="12" cy="12" r="10"/>
  <path d="M12 16v-4M12 8h.01"/>
</svg>"""


def main() -> None:
    st.set_page_config(page_title="EchoGrid", layout="wide", page_icon="")
    inject_theme()

    st.markdown(
        f"<h1 style=\"font-family:'Exo',sans-serif;font-weight:700;font-size:2rem;"
        f'color:#E6EAF5;margin-bottom:0.2rem">'
        f"{_LOGO_SVG}EchoGrid</h1>"
        f'<p style="color:#94A3B8;font-size:0.95rem;margin-top:0;margin-bottom:1.2rem">'
        f"Synthetic society simulator for media dynamics, echo effects, and communication-risk "
        f"analysis.</p>",
        unsafe_allow_html=True,
    )

    with st.container():
        st.warning(SYNTHETIC_SIMULATION_DISCLAIMER)
    with st.container():
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
