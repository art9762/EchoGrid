# EchoGrid Core Layers

EchoGrid now has an explicit first-pass layering model. The goal is not heavy
architecture for its own sake; the goal is to keep the synthetic simulation
pipeline easy to test, easy to explain, and safe to extend across mock, Hybrid,
and capped Full LLM sample modes.

## Layer Map

```text
app.py
  Thin Streamlit entrypoint and test-compatible run wrapper

src/ui/
  UI layer: Streamlit setup controls, tabs, charts, downloads, demo mode

src/simulation.py
  Application-service layer: one run orchestration, progress callbacks,
  persistence handoff, provider/runtime metadata

src/schemas.py
src/population.py
src/framing.py
src/reaction_engine.py
src/media_ecosystem.py
src/social_bubbles.py
src/echo_engine.py
  Domain and simulation layer: Pydantic contracts, deterministic synthetic
  population, framings, reactions, media actors, bubbles, echo items, and
  final agent states

src/llm_client.py
src/llm_pipeline.py
src/prompts/
  LLM gateway layer: provider clients, JSON parsing, typed Pydantic validation,
  retry-on-invalid-output support, prompt templates, Hybrid and Full LLM sample
  orchestration

src/analytics.py
src/report.py
  Analytics and reporting layer: aggregate metrics, amplification breakdown,
  final-state metrics, narrative-risk highlights, CSV/JSON/ZIP exports

src/storage.py
  Persistence layer: SQLite initialization, save/load/list/delete helpers

src/config.py
src/guardrails.py
  Configuration and safety layer: environment settings, disclaimers,
  prohibited-use helpers
```

## Current Run Flow

`src/ui/setup.py` gathers the scenario, frame selection, population size, seed,
echo controls, media preset, actor toggles, and provider label. It calls
`src.simulation.run_simulation`, which
owns the actual run:

1. Optionally generate LLM framings in Hybrid or Full LLM sample mode.
2. Generate synthetic agents with `src.population.generate_population`.
3. Run deterministic initial reactions with `src.reaction_engine`, or capped per-agent/frame LLM reactions in Full LLM sample mode.
4. Create the media ecosystem and social bubbles.
5. Optionally generate LLM echo artifacts and representative comments.
6. Optionally run bounded multi-round echo layers with `src.echo_engine`.
7. Persist the run through `src.storage.save_simulation`.
8. Return a dashboard-compatible simulation dictionary.

Provider and runtime mode are stored in metadata. LLM errors and representative comments are persisted in the simulation payload so previous-run loading can restore the demo surface.

## New Contracts

- `src.simulation.run_simulation(...)` is the UI-independent orchestration
  contract. Tests can run full simulations without importing Streamlit.
- `LLMClient.complete_model(...)` is the typed LLM output contract. It parses
  JSON, validates a Pydantic model, and retries malformed or schema-invalid
  output.
- `src.analytics.echo_amplification_breakdown(...)` explains the weighted
  components behind `echo_amplification_index`.
- `src.analytics.final_state_metrics(...)` aggregates post-echo stance, trust,
  sharing, and shift metrics.
- `src.analytics.narrative_risk_summary(...)` highlights the dominant echo type,
  highest-risk bubble, and highest-distortion item for review.
- `src.llm_pipeline.generate_full_sample_reactions(...)` performs capped per-agent/frame LLM calls with per-call fallback and progress reporting.

## Testing Surface

- `tests/test_simulation_service.py` covers the application-service layer,
  progress callbacks, persistence, and echo-disabled runs.
- `tests/test_llm_client.py` covers typed LLM validation and retry behavior.
- `tests/test_analytics.py` covers final-state metrics, amplification breakdown,
  and narrative-risk summaries.
- Existing storage, report, and app smoke tests continue to verify that saved
  runs, exports, and the Streamlit wrapper remain compatible.

## Extension Notes

Future extensions should keep the same safety shape: bounded calls, visible cost estimates, explicit provider readiness checks, partial-failure storage, and synthetic-use disclaimers in every export.
