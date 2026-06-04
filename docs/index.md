# EchoGrid Documentation

**EchoGrid** is an LLM-assisted **synthetic-society simulator** for media
dynamics, echo effects, and communication-risk analysis. It takes a news event,
generates a synthetic population, exposes it to media framings, and simulates
multi-round "echo" reactions inside social bubbles — then reports amplification,
distortion, trust, anger, virality, and polarization indicators.

> **EchoGrid is not a poll or a predictor.** All output is *synthetic* — plausible
> personas reacting to framings, not real people or measured opinion. It must not
> be used to optimize manipulative persuasion, political/election targeting,
> harassment, radicalization, or targeting vulnerable groups. See
> [Ethics & safety](ethics.md) and [Limitations](limitations.md).

It is a Streamlit app: `app.py` is a thin entrypoint, `src/ui/` owns rendering,
and `src.simulation.run_simulation` is the UI-independent service layer that runs
the whole pipeline. It runs fully offline in **Mock** mode ($0, deterministic),
with optional bounded **Hybrid** and capped **Full LLM sample** modes.

---

## Start here

| If you want to… | Read |
|---|---|
| Understand the system shape and module map | [Architecture](architecture.md) → [Layer boundaries](layers.md) |
| Install, run, test, and tour the UI | [Running & testing](running-and-testing.md) |
| Know what each module does | [Modules reference](modules-reference.md) |
| Pick Mock vs Hybrid vs Full sample | [Run modes](run-modes.md) → [Cost guide](cost-guide.md) |

## Reference docs

| Doc | Covers |
|---|---|
| [Data model](data-model.md) | Every Pydantic schema, enum, computed property, and the deterministic-randomness helpers (`stable_seed`, `seeded_rng`, …). |
| [Simulation pipeline](simulation-pipeline.md) | End-to-end flow of `run_simulation` — population → framings → reactions → media/bubbles → multi-round echo → metrics → dashboard. |
| [Analytics & metrics](analytics-metrics.md) | Every metric in `analytics.py` with its exact formula/weights and a high/low interpretation guide. |
| [LLM providers](llm-providers.md) | The `LLMClient` ABC, Mock/Trinity/Anthropic/Gemini clients, the `llm_pipeline` layer, prompt templates, and the guardrail classifier. |
| [Configuration](configuration.md) | `AppSettings`, every environment variable with defaults, paths, and per-provider `.env` examples. |
| [Storage & export](storage-and-export.md) | SQLite schema (parent + 9 child tables) and CSV/JSON/ZIP export bundles. |

## Safety & scope

| Doc | Covers |
|---|---|
| [Ethics & safety](ethics.md) | Allowed/disallowed uses, design guardrails, developer guidance. |
| [Limitations](limitations.md) | Not prediction, not calibration, model sensitivity, the bubble-based (non-graph) diffusion model. |

## Other materials

- [Cost guide](cost-guide.md) — per-mode call counts and USD bands.
- [Demo script](demo-script.md) — a walkthrough for presenting EchoGrid.
- `handoff.md`, `AI_HANDOFF.md`, `WORK_LOG.md`, `zapiska.md` — build/handoff notes
  and the long-form explanatory note (RU).

---

## Pipeline at a glance

```
NewsEvent
   │
   ▼
synthetic population ──► media framings ──► initial reactions
   │                                              │
   │                          media actors + social bubbles
   │                                              │
   └──────────────►  echo items ──► multi-round echo reactions (in bubbles)
                                              │
                                              ▼
                          final metrics ──► SQLite persistence ──► CSV / JSON / ZIP export
```

Determinism threads a single master `seed` through every stage via
`stable_seed(...)`, so a Mock run is fully reproducible. See
[Simulation pipeline](simulation-pipeline.md) for the seed-flow detail.
