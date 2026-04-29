# EchoGrid Cost Guide

EchoGrid is synthetic-first. Mock mode is the default demo path and makes no LLM calls.

## Mock

- Calls: 0.
- Cost: $0.
- Best for: local demos, tests, offline exploration, and repeatable seed traces.

## Hybrid

- Calls: usually 2-3 per run.
- Scope: LLM framings, echo items, and representative comments only.
- Agent reactions: deterministic local mock reactions.
- Best for: improved narrative artifacts without per-agent cost.

Hybrid mode samples high-signal reactions and sends artifact-level prompts, so a 1000-agent run still uses a small fixed number of provider calls.

## Full LLM Sample

- Calls: `population_size * frame_count + artifact calls`.
- Cap: 100 agents in the app.
- Scope: per-agent/frame initial reactions plus the Hybrid artifact calls.
- Best for: small qualitative samples where provider-generated reactions are useful.

The app displays estimated calls, token bands, and rough USD ranges before each LLM run. Errors are captured per generation step and the simulation continues with deterministic fallback artifacts when possible.

## Provider Notes

- Anthropic and OpenAI routes use the Trinity OpenAI-compatible gateway.
- Gemini uses the direct `GEMINI_API_KEY` path.
- `ECHOGRID_LLM_MAX_WORKERS` and `ECHOGRID_LLM_REQUEST_TIMEOUT_SECONDS` control concurrency and request limits.

All outputs remain synthetic and must not be treated as polling evidence.
