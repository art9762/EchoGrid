# EchoGrid

EchoGrid is an LLM-assisted synthetic society simulator for exploring how public messages can trigger reactions, move through media ecosystems, and become amplified, distorted, or polarized by echo effects.

## What It Is

EchoGrid creates synthetic agents with demographic, economic, psychological, social, and media-consumption profiles. A user enters or selects a public information event, then the system simulates:

- media framings
- initial agent reactions
- social and media echo items
- second-round reactions inside social bubbles
- before/after amplification, trust, anger, distortion, and polarization metrics

## What It Is Not

EchoGrid is not a polling tool and does not predict actual public opinion.

Results are synthetic simulation outputs. They should be treated as hypothesis-generation artifacts for research, education, communication-risk analysis, and media-dynamics exploration.

EchoGrid must not be used to optimize manipulative persuasion, political targeting, harassment, radicalization, or targeting vulnerable groups.

## Release Status

The current release runs fully in deterministic mock mode without API keys. It also includes a provider abstraction for:

- Anthropic / Claude via Trinity
- Gemini
- OpenAI / ChatGPT via Trinity

The full agent-scale pipeline currently uses mock mode by default. LLM provider calls are scaffolded for later integration into selected generation steps. The local release includes SQLite persistence, previous-run loading/deletion, CSV/JSON/ZIP exports, automated tests, and developer handoff docs.

## Installation

```bash
python3 -m venv .venv
.venv/bin/pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org -r requirements.txt
```

If your Python certificate setup works normally, the trusted-host flags are not required.

## Configuration

```bash
cp .env.example .env
```

Optional API keys:

```bash
TRINITY_API_KEY=
TRINITY_BASE_URL=
GEMINI_API_KEY=
```

Default mock mode does not require any key.

When `ECHOGRID_LLM_PROVIDER` is `anthropic` or `openai`, EchoGrid uses the Trinity gateway through the OpenAI-compatible chat completions client. Gemini remains a direct provider route.

## Developer Commands

```bash
make install
make test
make smoke
make run
make clean
```

## Run

```bash
.venv/bin/streamlit run app.py
```

The app opens a Streamlit dashboard with setup controls, previous-run loading, synthetic population charts, media ecosystem tables, social bubbles, initial reactions, echo timeline, amplification metrics, comments, and exports.

## Run Modes

- `Mock`: fully local deterministic simulation, no API calls.
- `Hybrid`: local synthetic population and initial reactions, plus bounded LLM calls for improved framings, echo items, and representative comments. Claude and ChatGPT/OpenAI models are routed through Trinity; Gemini uses `GEMINI_API_KEY`.

Hybrid mode deliberately avoids per-agent LLM calls. It samples high-signal reactions and sends only artifact-level prompts, so a 1000-agent run still uses a small fixed number of LLM requests.

## Demo Scenarios

EchoGrid includes seven built-in demo scenarios:

- Emissions-based car tax
- AI surveillance in public spaces
- Four-day work week proposal
- Mandatory digital ID
- Housing policy reform
- University bans phones in classrooms
- City restricts short-term rentals

## Architecture

```text
app.py
src/
  analytics.py
  config.py
  echo_engine.py
  framing.py
  llm_client.py
  llm_pipeline.py
  media_ecosystem.py
  population.py
  reaction_engine.py
  report.py
  scenarios.py
  schemas.py
  social_bubbles.py
  storage.py
  utils.py
  prompts/
data/
  simulations/
  exports/
tests/
```

Core pipeline:

```text
NewsEvent
  -> synthetic population
  -> media framings
  -> initial reactions
  -> media/social echo items
  -> echo reactions inside social bubbles
  -> final metrics, storage, export
```

## Storage And Export

SQLite storage is initialized automatically when a simulation is run from the app. Results are stored as JSON payloads for MVP flexibility.

Dashboard export supports:

- agents CSV
- reactions CSV
- echo items CSV
- echo reactions CSV
- summary JSON
- full ZIP bundle with README, CSVs, and summary JSON

Saved simulations can be loaded or deleted from the sidebar. The SQLite file is local runtime data and is ignored by git.

## Tests

```bash
.venv/bin/python -m pytest -q
```

The test suite covers schemas, configuration, population generation, framings, media actors, social bubbles, mock reactions, analytics, echo simulation, hybrid LLM orchestration, storage, exports, scenarios, and provider scaffolding.

## Release Documentation

- `docs/architecture.md` explains module responsibilities and the synthetic simulation pipeline.
- `docs/ethics.md` documents allowed and disallowed uses.
- `docs/demo-script.md` gives a conference-style demo path.
- `docs/AI_HANDOFF.md` summarizes current state and next work for other models and developers.
- `docs/superpowers/plans/2026-04-28-release-hardening.md` records the release-hardening plan and verification flow.

## Limitations

- Mock mode is plausible and deterministic, not scientifically calibrated.
- Outputs should not be interpreted as survey evidence.
- Current echo simulation supports one echo round.
- Hybrid mode uses bounded artifact-level LLM calls; full per-agent LLM simulation is not implemented.
- Network diffusion is bubble-based, not graph-based.
- Previous-run storage uses JSON payloads for MVP flexibility rather than migration-managed analytical tables.

## License

MIT License. See [LICENSE](LICENSE).

## Roadmap

- Extend hybrid mode with richer reports and persisted LLM artifacts.
- Add full LLM mode for small stratified samples.
- Add multi-round echo cascades.
- Add previous-run loading from SQLite.
- Add richer communication-risk reports.
- Add calibration hooks for external research datasets without claiming prediction.
