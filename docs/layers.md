# EchoGrid Core Layers

EchoGrid now has an explicit first-pass layering model. The goal is not heavy
architecture for its own sake; the goal is to keep the synthetic simulation
pipeline easy to test, easy to explain, and safe to extend toward hybrid LLM
mode.

## Layer Map

```text
app.py
  UI layer: Streamlit controls, tabs, charts, downloads

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
src/prompts/
  LLM gateway layer: provider clients, JSON parsing, typed Pydantic validation,
  retry-on-invalid-output support, prompt templates

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

`app.py` gathers the scenario, frame selection, population size, seed, echo
toggle, and provider label. It calls `src.simulation.run_simulation`, which
owns the actual run:

1. Generate synthetic agents with `src.population.generate_population`.
2. Run deterministic initial reactions with `src.reaction_engine`.
3. Create the media ecosystem and social bubbles.
4. Optionally run the one-round echo layer with `src.echo_engine`.
5. Persist the run through `src.storage.save_simulation`.
6. Return a dashboard-compatible simulation dictionary.

The selected provider is stored in metadata, but the runtime mode is still
`mock`. This is deliberate: full provider execution should only be enabled with
cost estimation, explicit UI controls, API-key checks, JSON validation, and
clear partial-failure behavior.

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

## Testing Surface

- `tests/test_simulation_service.py` covers the application-service layer,
  progress callbacks, persistence, and echo-disabled runs.
- `tests/test_llm_client.py` covers typed LLM validation and retry behavior.
- `tests/test_analytics.py` covers final-state metrics, amplification breakdown,
  and narrative-risk summaries.
- Existing storage, report, and app smoke tests continue to verify that saved
  runs, exports, and the Streamlit wrapper remain compatible.

## Extension Notes

The next safe LLM slice is hybrid mode for selected generation tasks, not
full-scale per-agent calls. A conservative order is:

1. Add cost estimation before any non-mock provider call.
2. Add provider-specific generation methods that use `complete_model`.
3. Start with low-volume generation such as framings, echo items, or
   representative comments.
4. Store provider errors and partial outputs so the simulation can continue
   safely when one generation step fails.
