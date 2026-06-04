# EchoGrid Module Reference

> Part of the [EchoGrid documentation](index.md). Siblings: [running-and-testing.md](running-and-testing.md) ·
> [architecture.md](architecture.md) · [layers.md](layers.md) · [data-model.md](data-model.md) ·
> [simulation-pipeline.md](simulation-pipeline.md) · [analytics-metrics.md](analytics-metrics.md) ·
> [llm-providers.md](llm-providers.md) · [configuration.md](configuration.md) ·
> [storage-and-export.md](storage-and-export.md) · [run-modes.md](run-modes.md) ·
> [cost-guide.md](cost-guide.md) · [ethics.md](ethics.md) · [limitations.md](limitations.md).

A one-stop responsibility map for every module under `src/` plus `app.py` and `src/ui/*`.
EchoGrid is a Python, LLM-assisted synthetic-society simulator whose outputs are **synthetic
simulation artifacts, not real polls**. The architecture is layered: a thin Streamlit
entrypoint, a UI layer, a UI-independent service layer, domain engines, an LLM gateway,
analytics, reporting, and persistence. See [architecture.md](architecture.md) and
[layers.md](layers.md) for the prose overview.

## Pipeline at a glance

```text
NewsEvent
  → synthetic population        (population.py)
  → media framings              (framing.py)
  → initial reactions           (reaction_engine.py)
  → media/social echo items     (echo_engine.py, media_ecosystem.py, social_bubbles.py)
  → echo reactions in bubbles   (echo_engine.py)
  → metrics, storage, export    (analytics.py, storage.py, report.py)
```

The whole pipeline is sequenced by `simulation.py`; LLM modes layer `llm_pipeline.py` +
`llm_client.py` on top of the deterministic mock path.

## Entrypoint and service layer

| Module | Responsibility | Deeper doc |
|--------|----------------|------------|
| `app.py` | Thin Streamlit entrypoint. Sets page config, injects theme, shows disclaimers, renders setup panel and dashboard/empty state. Wraps the service layer in `_run_simulation`, wiring in settings, the LLM client factory, and a progress callback. | [running-and-testing.md](running-and-testing.md) |
| `src/simulation.py` | UI-independent application-service layer. `run_simulation(...)` orchestrates population → framings → reactions → echo → metrics → persistence, selects mock/hybrid/full-sample paths, enforces the 100-agent full-sample cap, and emits progress. Returns the simulation result dict the UI consumes. | [simulation-pipeline.md](simulation-pipeline.md), [run-modes.md](run-modes.md) |

## Domain and data model

| Module | Responsibility | Deeper doc |
|--------|----------------|------------|
| `src/schemas.py` | Pydantic models and enums for the whole system: `NewsEvent`, `NewsFrame`, `AgentProfile`, `PopulationConfig`, `AgentReaction`/`Emotions`, `MediaActor`/`ActorType`, `SocialBubble`, `EchoItem`/`EchoType`/`EmotionLabel`, `EchoReaction`/`EmotionShift`, `EchoSimulationResult`, `RepresentativeComment`, `LLMGenerationError`, `LLMProvider`, `Stance`. Enforces value ranges (0–100 scores). | [data-model.md](data-model.md) |
| `src/config.py` | App settings and constants. `AppSettings`/`get_settings()`/`from_env()` load provider, Trinity/Gemini credentials, per-provider model presets, worker/timeout defaults, and the SQLite `database_path`. Defines `DATA_DIR`, `PROMPTS_DIR`, and the `SYNTHETIC_SIMULATION_DISCLAIMER` / `ETHICAL_USE_DISCLAIMER` strings. | [configuration.md](configuration.md) |
| `src/utils.py` | Shared deterministic-randomness and normalization helpers: `clamp`, `stable_seed`, `seeded_rng`. Underpins reproducible mock generation. | — |
| `src/population.py` | Synthetic population generation. Builds diverse, internally coherent `AgentProfile`s (demographics, economics, psychology, media diet, values) deterministically from a seed. | [simulation-pipeline.md](simulation-pipeline.md) |
| `src/framing.py` | News framing generation. `generate_framings` returns built-in frames (neutral, technocratic, progressive, populist, skeptical, tabloid_outrage) tailored to the event. | [simulation-pipeline.md](simulation-pipeline.md) |
| `src/reaction_engine.py` | Initial agent reactions. `run_agent_reaction` / `run_initial_reactions` produce deterministic mock `AgentReaction`s per agent×frame, deriving stance, emotions, trust (from media diet + frame source), and likely comments. | [simulation-pipeline.md](simulation-pipeline.md) |
| `src/echo_engine.py` | Echo/amplification simulation. Generates `EchoItem`s from actors/frames/reactions, runs bubble-scoped echo reactions over one or more rounds, and computes amplification metrics + round summaries (`EchoSimulationResult`). Accepts echo-item overrides for LLM modes. | [simulation-pipeline.md](simulation-pipeline.md), [analytics-metrics.md](analytics-metrics.md) |
| `src/social_bubbles.py` | Social-bubble definitions and assignment. `default_social_bubbles` plus `assign_agents_to_bubbles` partition the population into echo communities. | [simulation-pipeline.md](simulation-pipeline.md) |
| `src/media_ecosystem.py` | Default media actors and presets. `default_media_actors` builds the actor mix (broadcaster, tabloid, partisan, influencer, expert, government, grassroots) with preset reshaping and actor-type filtering. | [simulation-pipeline.md](simulation-pipeline.md) |
| `src/scenarios.py` | The seven built-in demo `NewsEvent`s (`demo_scenarios()`), e.g. emissions car tax, AI surveillance, four-day week, digital ID, housing reform, classroom phone ban, short-term rentals. | [simulation-pipeline.md](simulation-pipeline.md) |

## Analytics and reporting

| Module | Responsibility | Deeper doc |
|--------|----------------|------------|
| `src/analytics.py` | Pure metric functions over reactions and echo results: stance/emotion distributions, trust/share aggregates, polarization and virality scores, segment breakdowns, frame comparison/sensitivity, final-state metrics, amplification breakdown, narrative-risk and bubble-susceptibility summaries, correction effectiveness. | [analytics-metrics.md](analytics-metrics.md) |
| `src/report.py` | Export and report builders. Converts agents/reactions/echo items/echo reactions to DataFrames, builds disclaimer-stamped CSV, the `summary.json` payload (`simulation_summary_json`), `export_metadata`, and the full ZIP bundle (`simulation_export_zip`). | [storage-and-export.md](storage-and-export.md) |

## Persistence

| Module | Responsibility | Deeper doc |
|--------|----------------|------------|
| `src/storage.py` | Local SQLite persistence. `init_database`, `save_simulation`, `load_simulation`, `list_simulations`, `delete_simulation`. Stores runs (agents, frames, reactions, actors, bubbles, assignments, echo results, plus run mode/provider/seed, representative comments, and LLM errors) as JSON-backed rows; restores them for previous-run loading. | [storage-and-export.md](storage-and-export.md) |

## LLM gateway and safety

| Module | Responsibility | Deeper doc |
|--------|----------------|------------|
| `src/llm_client.py` | Provider abstraction. `build_llm_client` selects `MockLLMClient`, `AnthropicLLMClient`, `TrinityLLMClient` (OpenAI-compatible), or `GeminiLLMClient`; validates credentials. Clients expose `complete_text` plus typed `generate_*_json` helpers (reactions, echo items, echo reactions, framings, comments) with JSON parsing, retry-once, and per-task model routing (e.g. haiku for reactions, sonnet for artifacts). | [llm-providers.md](llm-providers.md) |
| `src/llm_pipeline.py` | Bounded LLM orchestration. `estimate_llm_cost` projects calls/tokens/USD per run mode; `generate_hybrid_artifacts` produces LLM framings/echo items/representative comments with fallback + error capture; `generate_full_sample_reactions` runs capped per-agent reactions with workers, timeouts, fallback, and progress. | [llm-providers.md](llm-providers.md), [run-modes.md](run-modes.md) |
| `src/guardrails.py` | Central ethical guardrails. `classify_request` allows research/framing analysis and refuses manipulation, political targeting, harassment, and vulnerable-group targeting with a fixed refusal message. | [llm-providers.md](llm-providers.md), [ethics.md](ethics.md) |
| `src/prompts/` | Prompt templates (`framing_prompt.txt`, `reaction_prompt.txt`, `echo_generation_prompt.txt`, `echo_reaction_prompt.txt`, `representative_comments_prompt.txt`) plus `load_prompt(name)`. Each template requests JSON-only output, mirrors its schema fields, and embeds guardrail language. | [llm-providers.md](llm-providers.md), [ethics.md](ethics.md) |

## UI layer (`src/ui/`)

| Module | Responsibility | Deeper doc |
|--------|----------------|------------|
| `src/ui/setup.py` | `render_setup_panel`: the sidebar controls — previous-run load/delete, demo button, scenario/custom event, run-mode and provider selection, model preset, population/seed sliders, framing multiselect, echo toggle/rounds, media preset, actor toggles, worker/timeout sliders, cost panel, provider-readiness gating, and run dispatch with live status. | [running-and-testing.md](running-and-testing.md), [cost-guide.md](cost-guide.md) |
| `src/ui/dashboard.py` | `render_dashboard` (summary strip + 14 tabs: Overview, Narrative, Population, Media, Bubbles, Initial Reaction, Echo Timeline, Echo Items, Amplification, Bubble Impact, Frame Comparison, Segment Explorer, Comments, Export) and `render_empty_state`. Pulls metrics from `analytics.py`, exports from `report.py`, charts from `ui/charts.py`. | [running-and-testing.md](running-and-testing.md), [data-model.md](data-model.md) |
| `src/ui/charts.py` | Plotly chart helpers and the design-system palettes (stance/emotion/echo colors). `apply_chart_layout` applies the OLED dark theme; `stance_bar`, `echo_type_bar`, `histogram`, `scatter` build themed figures. | [running-and-testing.md](running-and-testing.md) |
| `src/ui/theme.py` | `inject_theme`: emits one CSS `<style>` block mirroring the promo-site tokens (OLED surfaces, Exo/Roboto Mono fonts, glass metric cards, themed widgets, CSS-only animations guarded by `prefers-reduced-motion`). No JavaScript. | [running-and-testing.md](running-and-testing.md) |

> `src/ui/__init__.py` is a package marker (docstring only).

For how these modules are exercised and tested, see
[running-and-testing.md](running-and-testing.md).
