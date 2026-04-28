# EchoGrid Handoff

Date: 2026-04-28
Branch: `codex/trinity-llm-routing`

## Current State

EchoGrid has a working deterministic mock MVP plus a first usable Hybrid LLM mode.

Hybrid mode keeps population generation and initial reactions local/mock, then makes bounded LLM calls for:

- media framings
- echo items
- representative comments

Claude/Anthropic and ChatGPT/OpenAI providers are routed through Trinity using the OpenAI-compatible chat completions client. Gemini remains a direct route through `GEMINI_API_KEY`.

## Main Files Changed

- `src/config.py`: added `TRINITY_API_KEY` and `TRINITY_BASE_URL`; removed direct Claude/OpenAI key usage.
- `src/llm_client.py`: added `TrinityLLMClient`, typed generation helpers, JSON parsing for objects/arrays, one retry after invalid JSON or schema validation failure.
- `src/llm_pipeline.py`: new bounded Hybrid orchestration, prompt builders, cost estimator, fallback/error capture.
- `src/schemas.py`: added `RepresentativeComment`, `LLMGenerationError`, `LLMCostEstimate`, `HybridArtifacts`.
- `app.py`: added Mock/Hybrid run mode selector, provider/model preset controls, rough cost preview, status messages, Hybrid runtime integration, representative comments display, LLM fallback error display.
- `src/prompts/representative_comments_prompt.txt`: new strict JSON prompt.
- `.env.example`, `README.md`, `requirements.txt`: updated for Trinity routing.

## How To Run

Mock mode:

```bash
.venv/bin/streamlit run app.py
```

Hybrid Anthropic/OpenAI via Trinity:

```bash
cp .env.example .env
# set TRINITY_API_KEY and TRINITY_BASE_URL
.venv/bin/streamlit run app.py
```

Run tests:

```bash
.venv/bin/python -m pytest -q
```

## Known Gaps

- Full per-agent LLM small-sample mode is not implemented.
- LLM artifacts are visible in the current dashboard session and summary export, but representative comments and LLM errors are not persisted in dedicated SQLite tables.
- Hybrid mode uses mock echo reactions over LLM echo items; this is intentional to avoid many per-agent calls.
- Cost estimates are rough planning numbers, not provider billing truth.
- The app still has a large `app.py`; the backlog item to split dashboard helpers remains useful.

## Suggested Next Steps

1. Run a manual Streamlit smoke test for Mock and Hybrid modes.
2. Add SQLite persistence for `representative_comments`, `llm_errors`, and run metadata.
3. Add ZIP export containing CSVs plus `summary.json`.
4. Refactor dashboard code out of `app.py`.
5. Add previous-simulation loading in the sidebar.
6. Decide whether Full LLM small-sample mode should call per-agent reactions or only stratified segment representatives.
