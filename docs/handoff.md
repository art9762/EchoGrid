# EchoGrid Handoff

Date: 2026-06-02
Status: ready for presentation

## What Was Done Today

1. **Project restructuring.** The GitHub version (art9762/EchoGrid) became the main codebase at project root. The previous local-only version was moved to `_old/` for reference.

2. **Пояснительная записка (ГОСТ 7.32-2017).** A complete academic report was written from scratch for the current codebase — `docs/zapiska.md` (531 lines, 6 sections, 13 references). Covers architecture, all three run modes, LLM pipeline, guardrails, testing, analytics. The docx was generated via `docs/generate_docx.py` → `docs/Пояснительная_записка.docx` (57 KB, Times New Roman 14pt, 1.5 spacing, ГОСТ margins).

3. **Verification.** All 85 tests pass. Full mock pipeline runs end-to-end. Docx generation succeeds.

4. **Contrastive metrics analysis.** Ran all 7 scenarios and isolated per-frame runs to produce presentation-ready numbers showing the dual-path-to-polarization thesis (aggressive framing = instant shift; neutral + echo chamber = gradual radicalization).

## Current Project State

### Architecture

```
app.py                 → Thin Streamlit entrypoint
src/simulation.py      → Service-layer orchestration (UI-independent)
src/schemas.py         → 28+ Pydantic v2 models, extra="forbid"
src/population.py      → Synthetic population generation
src/framing.py         → Frame construction
src/media_ecosystem.py → Media actor presets
src/social_bubbles.py  → Bubble assignment
src/reaction_engine.py → First-round reactions (mock deterministic)
src/echo_engine.py     → Multi-round echo simulation (configurable rounds)
src/llm_client.py      → LLMClient ABC + Mock/Trinity/Gemini implementations
src/llm_pipeline.py    → Bounded Hybrid/Full LLM orchestration, cost estimation
src/analytics.py       → 15+ pure aggregation functions
src/storage.py         → SQLite persistence, load/delete previous runs
src/report.py          → DataFrame export (CSV/JSON/ZIP)
src/guardrails.py      → Ethical request classification
src/scenarios.py       → 7 demo scenarios
src/config.py          → AppSettings from .env
src/ui/                → setup.py, dashboard.py (14 tabs), charts.py
```

### Run Modes

| Mode | API calls | Population cap | Description |
|------|-----------|----------------|-------------|
| Mock | 0 | unlimited | Fully deterministic, seed-based |
| Hybrid | 3-5 fixed | unlimited | LLM for framings + echo items + comments; reactions stay mock |
| Full LLM sample | N×F per-agent | 100 max | LLM per agent/frame reaction; bounded with timeout/fallback |

### Provider Routing

- Anthropic / OpenAI → Trinity gateway (OpenAI-compatible chat completions)
- Gemini → direct via `GEMINI_API_KEY`
- Mock → no network, deterministic

### Key Metrics (output of simulation)

- amplification — share-likelihood ratio after/before echo
- distortion — mean factual deviation of echo items
- polarization — normalized stance std dev
- anger_delta, trust_delta — mean shift per agent
- radicalized_fraction — agents shifted to extreme stance

### Testing

- 85 tests, <1s runtime
- Covers: schemas, config, population, framings, media, bubbles, reactions, echo, analytics, storage/export, LLM client, LLM pipeline, simulation service, guardrails, app smoke, Streamlit UI
- CI: GitHub Actions (ruff lint + pytest)
- `make test` / `make smoke` / `make lint`

### Documentation

| File | Purpose |
|------|---------|
| `README.md` | User-facing setup, run modes, architecture, limitations |
| `docs/zapiska.md` | ГОСТ 7.32-2017 academic report (Russian) |
| `docs/Пояснительная_записка.docx` | Generated docx version |
| `docs/architecture.md` | Module responsibilities |
| `docs/layers.md` | Layer boundaries |
| `docs/ethics.md` | Allowed/disallowed uses |
| `docs/demo-script.md` | Conference demo walkthrough |
| `docs/cost-guide.md` | Mock vs Hybrid vs Full cost behavior |
| `docs/limitations.md` | Modeling and safety caveats |
| `docs/AI_HANDOFF.md` | AI/developer continuation notes |

## Quick Commands

```bash
make install          # create venv + install deps
make run              # start Streamlit app
make test             # full test suite
make smoke            # app smoke test only
make lint             # ruff check
make format           # ruff format
```

## Regenerate Academic Report

```bash
.venv/bin/python docs/generate_docx.py
# outputs docs/Пояснительная_записка.docx
```

## Known Limitations

- Hybrid/Full LLM modes use mock echo reactions (intentional: avoids unbounded per-round calls).
- Cost estimates are planning approximations, not billing truth.
- LLM artifacts stored as JSON in simulation payload, not normalized tables.
- Mock metrics are deterministic and plausible but not empirically calibrated.

## Files in `_old/`

Previous local-only version with simpler architecture (no service layer, no hybrid/full LLM, no guardrails, 5-stance scale, 42 tests). Kept for reference — the zapiska format and docx generator were originally developed there.
