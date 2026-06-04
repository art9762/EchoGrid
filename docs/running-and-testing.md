# Running and Testing EchoGrid

> Part of the [EchoGrid](../README.md) documentation. Siblings: [modules-reference.md](modules-reference.md) ·
> [architecture.md](architecture.md) · [layers.md](layers.md) · [data-model.md](data-model.md) ·
> [cost-guide.md](cost-guide.md) · [ethics.md](ethics.md) · [limitations.md](limitations.md).

EchoGrid is a Python, LLM-assisted synthetic-society simulator. It produces **synthetic
simulation outputs, not real polls or predictions** — every screen and export carries that
disclaimer. This guide covers installing, running, testing, linting, and the Streamlit UI.

---

## 1. Install

EchoGrid targets Python 3.10+ (`pyproject.toml` sets `target-version = "py310"`).

### With Make (recommended)

```bash
make install        # creates .venv and installs requirements.txt into it
```

`make install` runs:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

### Manual venv + pip

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

If your Python certificate setup blocks PyPI, add trusted-host flags:

```bash
.venv/bin/pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org -r requirements.txt
```

### Configuration (optional)

Mock mode is fully local and needs no API keys. For LLM modes:

```bash
cp .env.example .env
```

Then set any of these in `.env`:

```bash
TRINITY_API_KEY=
TRINITY_BASE_URL=
GEMINI_API_KEY=
```

Anthropic/Claude and OpenAI/ChatGPT routes go through the **Trinity** gateway; Gemini uses
`GEMINI_API_KEY` directly. See [modules-reference.md](modules-reference.md) (`config.py`,
`llm_client.py`) for the full settings surface.

---

## 2. Run

```bash
make run            # → .venv/bin/streamlit run app.py
```

or directly:

```bash
.venv/bin/streamlit run app.py
```

`app.py` is a thin entrypoint: it sets the Streamlit page config, injects the theme, shows the
disclaimers, renders the setup panel, and renders the dashboard or empty state. All rendering
lives in `src/ui/`; all simulation logic lives in `src/simulation.py` and the domain modules.

---

## 3. Test

```bash
make test           # → .venv/bin/python -m pytest -q   (whole suite)
make smoke          # → pytest tests/test_app_smoke.py -q  (fast end-to-end)
```

or directly:

```bash
.venv/bin/python -m pytest -q
```

Pytest is configured in `pyproject.toml`:

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["."]
addopts = "-q"
```

`pythonpath = ["."]` lets tests import `app` and `src.*` without installing the package.

---

## 4. Lint and Format

EchoGrid uses **ruff** for both linting and formatting.

```bash
make lint           # → .venv/bin/python -m ruff check .
make format         # → .venv/bin/python -m ruff format .
```

Ruff config (`pyproject.toml`):

| Setting | Value |
|---------|-------|
| `line-length` | `100` |
| `target-version` | `py310` |
| lint `select` | `E`, `F`, `I`, `UP`, `B` (pycodestyle errors, pyflakes, import sort, pyupgrade, bugbear) |
| lint `ignore` | `E501` (line-length handled by the formatter) |
| format `quote-style` | `double` |
| `exclude` | `.git`, `.venv`, `__pycache__`, `.pytest_cache` |

---

## 5. Clean and Reindex

```bash
make clean          # removes .pytest_cache, .ruff_cache, .mypy_cache, htmlcov,
                    # .coverage, and all __pycache__ directories
make reindex        # → .venv/bin/python scripts/reindex_memory.py
```

`clean` removes build/cache artifacts only — it does not touch the SQLite database or exports
under `data/`. `reindex` runs the memory reindex helper script.

---

## 6. Requirements and Tooling

Runtime and dev dependencies (`requirements.txt`):

| Package | Constraint | Role |
|---------|-----------|------|
| `anthropic` | `>=0.40.0` | Anthropic/Claude SDK surface |
| `google-genai` | `>=1.0.0` | Gemini direct provider |
| `openai` | `>=2.0.0` | OpenAI-compatible client (also used for Trinity routing) |
| `pandas` | `>=2.2.0` | DataFrames for analytics, tables, and CSV export |
| `plotly` | `>=5.24.0` | Dashboard charts |
| `pydantic` | `>=2.8.0` | Schema validation for all domain models |
| `python-dotenv` | `>=1.0.1` | Loads `.env` settings |
| `streamlit` | `>=1.39.0` | Web UI |
| `pytest` | `>=8.3.0` | Test runner |
| `ruff` | `>=0.8.0` | Lint + format |

---

## 7. Streamlit UI Walkthrough

The UI is grounded in `src/ui/` (`theme.py`, `setup.py`, `dashboard.py`, `charts.py`) and
orchestrated by `app.py`.

### Page chrome, theme, and disclaimers (`app.py` + `theme.py`)

On load, `main()` sets a wide layout, then `inject_theme()` (`src/ui/theme.py`) emits one
`<style>` block: an OLED dark design system (Exo + Roboto Mono fonts, glass metric cards,
themed tabs/buttons/sliders/inputs, CSS-only entrance animations guarded by
`prefers-reduced-motion`). The header shows the EchoGrid logo and tagline, then two persistent
notices are rendered as Streamlit alerts:

- `st.warning(SYNTHETIC_SIMULATION_DISCLAIMER)` — outputs are synthetic, not a real poll.
- `st.info(ETHICAL_USE_DISCLAIMER)` — disallowed uses (no manipulation, targeting, etc.).

Both strings come from `src/config.py`. The dashboard also repeats the synthetic notice at the
bottom of every run.

### Setup panel (`render_setup_panel`, `src/ui/setup.py`)

Rendered in the sidebar. What the user sees and does, top to bottom:

- **Previous runs** — if saved simulations exist, an expander lists them (timestamp, title,
  population, topic, run mode) with **Load** and **Delete** buttons backed by `src/storage.py`.
- **Run demo mode** — one-click primary button: runs the "City restricts short-term rentals"
  scenario with 300 mock agents, seed 42, echo on (2 rounds), balanced media preset.
- **Scenario** select — one of the seven demo scenarios from `src/scenarios.py`, or
  **Custom event** which opens a form (title, topic, country, source type, description,
  original text) producing a `NewsEvent`.
- **Run mode** — `Mock`, `Hybrid`, or `Full LLM sample`. Full LLM sample shows a cost/safety
  warning and is capped at 100 agents.
- **Population size** slider — 50–1000 (step 50) in mock/hybrid; 25–100 (step 25) for full
  sample.
- **Random seed** number input (default 42) for deterministic runs.
- **Provider** select — `MOCK` for mock mode; `ANTHROPIC` / `OPENAI` / `GEMINI` for LLM modes.
- **Model preset** — `balanced` / `cheap` / `premium` (Anthropic) or `balanced` / `cheap`
  (others); disabled in mock mode. Resolves to a concrete model name from settings.
- **Framings** multiselect — chooses which of six generated frames to use (or guide LLM frame
  generation in LLM modes).
- **Echo simulation** toggle + **Echo rounds** (1–3).
- **Media preset** — `balanced`, `low_trust`, `high_institutional_trust`, `highly_partisan`,
  `expert_heavy`.
- **Media actor toggles** — expander of per-`ActorType` checkboxes to include/exclude actor
  types.
- **Echo items per actor** select-slider (1–3) for timeline density.
- **LLM max workers** and **LLM request timeout** sliders (disabled in mock mode).
- **Cost panel** — a caption with estimated LLM calls and rough USD range via
  `estimate_llm_cost` (`src/llm_pipeline.py`); see [cost-guide.md](cost-guide.md).
- **Provider readiness** notice — checks `.env` keys; the **Run simulation** primary button is
  disabled until the provider is ready.

Running shows a live `st.status` panel that streams progress messages from the simulation
service via a `progress_callback`. The result is stored in `st.session_state["simulation"]`.

### Dashboard (`render_dashboard`, `src/ui/dashboard.py`)

When a simulation exists, a five-metric summary strip (agents, frames, initial trust, share
likelihood, echo items) sits above 14 tabs:

| Tab | Shows |
|-----|-------|
| Overview | IDs, run mode/provider, cost estimate, LLM-fallback panel, event text, final metrics |
| Narrative | Plain-language amplification summary, top echo type/bubble, correction effectiveness |
| Population | Histograms (age, trust, income, location) + agent table |
| Media | Media-actor table + credibility/sensationalism bubble plot + amplification-pressure bars |
| Bubbles | Social-bubble table + agent-count bars colored by outrage sensitivity |
| Initial Reaction | Trust/share/intensity metrics, stance bar, filterable reactions table |
| Echo Timeline | Round-by-round cards (original → frames → reactions → echo rounds) + echo items |
| Echo Items | Filterable echo items by type/target bubble + reach bars |
| Amplification | Amplification metrics, breakdown table, correction effectiveness |
| Bubble Impact | Per-bubble share/anger shift table and bars |
| Frame Comparison | Frame sensitivity score + per-frame stance/trust/share/polarization table |
| Segment Explorer | Group-by segment breakdown + unexpected high-risk segments |
| Comments | Representative comments + filterable synthetic comment stream |
| Export | Download buttons (see below) |

Charts come from `src/ui/charts.py` (shared dark Plotly layout + stance/emotion/echo palettes);
analytics from `src/analytics.py`; export builders from `src/report.py`. The **Export** tab
offers agents CSV, reactions CSV, echo items/reactions CSV (when echo ran), summary JSON, and a
full ZIP bundle. See [data-model.md](data-model.md) and [layers.md](layers.md).

### Empty state (`render_empty_state`, `src/ui/dashboard.py`)

Before the first run, the page shows three metrics (Default mode: Mock; Demo scenarios: 7;
Storage: SQLite) and a prompt to configure the sidebar or launch demo mode.

---

## 8. Test Suite

All tests live in `tests/` and run under pytest. What each file broadly verifies:

| Test file | Verifies |
|-----------|----------|
| `test_app_smoke.py` | End-to-end `app._run_simulation` for mock, hybrid (fake gateway client), and full-LLM-sample runs; the 100-agent cap raises `ValueError`; a 1000-agent mock run completes well under 5s |
| `test_streamlit_ui.py` | Drives the real app with `streamlit.testing.v1.AppTest`: demo-mode click renders the dashboard with no exceptions and the expected 14 tab labels (no widget-key collisions) |
| `test_simulation_service.py` | `src.simulation.run_simulation` orchestrates a mock run, persists it, emits ordered progress callbacks, and can skip the echo layer |
| `test_project_structure.py` | Core modules import; prompt templates exist and request JSON; `app.py`/`.env.example`/`LICENSE`/`README`/`Makefile`/`pyproject.toml`/release docs exist |
| `test_prompts.py` | `load_prompt` resolves by name and `.txt` suffix, rejects unknown names, and each template covers its schema fields plus guardrail language ("Return JSON only", "Do not", "targeting") |
| `test_guardrails.py` | `classify_request` refuses manipulation/targeting/harassment requests, allows research framing; export metadata carries both disclaimers |
| `test_analytics.py` | Reaction metrics, bounded polarization/virality scores, segment breakdown, frame comparison/sensitivity, final-state metrics, amplification breakdown, narrative risk, polarization delta |
| `test_config.py` | Settings default to mock provider with expected model names; read API keys from env; default SQLite path is git-ignored |
| `test_echo.py` | Deterministic echo-item generation, single echo reactions, full echo simulation metrics, multi-round support, multiple items per actor, and echo-item override |
| `test_framing_media_bubbles.py` | The six built-in frame IDs, the media-actor ecosystem coverage, and full social-bubble assignment of all agents |
| `test_llm_client.py` | `build_llm_client` provider selection (mock/Anthropic/Gemini/Trinity-OpenAI), missing-credential errors, JSON parsing (plain + fenced), validated reaction/echo/frame/comment generation, retry-once on bad JSON, Anthropic model routing (haiku for reactions, sonnet for artifacts) |
| `test_llm_pipeline.py` | Cost estimation for hybrid vs full sample, hybrid artifacts use LLM output, fallback-and-record-errors behavior, full-sample per-call fallback with progress reporting |
| `test_media_ecosystem.py` | Media presets reshape the environment (expert_heavy vs low_trust) and actor-type include filters |
| `test_population.py` | Population size, seed determinism, demographic diversity, and life-stage/status coherence |
| `test_reaction_engine.py` | Deterministic mock reactions, full agent×frame coverage, source-trust from media diet/frame source, and comment variety by topic/profile |
| `test_scenarios.py` | Seven demo scenarios, all `NewsEvent`s, expected titles present |
| `test_schemas.py` | Pydantic validation for agent profiles, events/frames, nested reactions/emotions, echo items/reactions, and out-of-range rejection |
| `test_storage_report.py` | SQLite init/save/load/list/delete, restored LLM artifacts + runtime metadata, report DataFrames, summary JSON contents, CSV metadata header, and ZIP export artifacts |

Run the fast end-to-end check alone with `make smoke`; run everything with `make test`.
