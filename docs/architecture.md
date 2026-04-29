# EchoGrid Architecture

EchoGrid is a Streamlit application for synthetic media-dynamics simulation. It is designed as a deterministic mock-mode MVP with bounded LLM-assisted modes for framings, echo artifacts, representative comments, and capped small-sample reactions.

## Runtime Shape

`app.py` is a thin Streamlit entrypoint. `src/ui/` owns setup, dashboard, and chart rendering. `src.simulation.run_simulation` owns the UI-independent application-service orchestration for a run. The simulation
pipeline is:

1. `NewsEvent` from a demo scenario or custom form.
2. Synthetic population from `src.population.generate_population`.
3. Built-in media framings from `src.framing.generate_framings`.
4. Initial reactions from `src.reaction_engine.run_initial_reactions` or capped Full LLM sample generation.
5. Media actors and social bubbles from `src.media_ecosystem` and `src.social_bubbles`.
6. Optional bounded multi-round echo simulation from `src.echo_engine.run_echo_simulation`.
7. Persistence through `src.storage.save_simulation`.
8. Final-state, amplification, and narrative-risk analytics through `src.analytics`.
9. CSV, JSON, and ZIP exports through `src.report`.

## Module Map

- `src/schemas.py`: Pydantic contracts for agents, events, reactions, echo items, final states, and config.
- `src/config.py`: environment loading, default paths, and safety disclaimers.
- `src/population.py`: deterministic synthetic agent generation.
- `src/framing.py`: built-in framing variants for public messages.
- `src/reaction_engine.py`: deterministic mock reactions and future LLM reaction hook.
- `src/echo_engine.py`: echo item generation, bubble-specific reaction shifts, and amplification metrics.
- `src/analytics.py`: aggregate metrics for stance, emotions, trust, virality, bubbles, and frames.
- `src/simulation.py`: application-service layer that coordinates a full run outside Streamlit.
- `src/ui/`: Streamlit setup, dashboard, and chart helpers.
- `src/storage.py`: SQLite persistence, load/list/delete helpers, and simulation metadata.
- `src/report.py`: export dataframes, summary JSON, and full ZIP bundles.
- `src/guardrails.py`: prohibited-use classifier helpers and refusal text.
- `src/llm_client.py`: provider scaffolding for Anthropic, Gemini, OpenAI, and mock mode, plus typed JSON/Pydantic validation for Hybrid and Full LLM sample generation.

See `docs/layers.md` for the current layer boundaries and extension notes.

## Data And Storage

The default SQLite database is `data/echogrid.sqlite3`. It is ignored by git. The storage layer keeps payload JSON in normalized tables so the MVP can evolve schemas without early migration complexity. `list_simulations` reads summary metadata for the sidebar, `load_simulation` restores a previous run, and `delete_simulation` removes a run and all child rows.

## Testing

Run the full suite with:

```bash
make test
```

The suite covers schema validation, deterministic population generation, prompt contracts, guardrails, mock reactions, echo simulation, analytics, storage, exports, and app smoke behavior. All current tests operate on synthetic data and do not require API keys.
