# Configuration

> Part of the EchoGrid docs. See also [LLM providers](llm-providers.md), [Run modes](run-modes.md), and the [Cost guide](cost-guide.md).

EchoGrid is an LLM-assisted **synthetic-society simulator**; all outputs are **SYNTHETIC**. This document describes runtime configuration: the `AppSettings` model, every environment variable from `.env.example`, the fixed paths and disclaimer strings, and copy-pasteable setups for each provider mode.

Source: `src/config.py` and `.env.example`.

---

## 1. `AppSettings` and `from_env()`

`AppSettings` (a Pydantic `EchoGridModel`) holds all runtime settings. `AppSettings.from_env()` loads `<PROJECT_ROOT>/.env` (via `python-dotenv`) and reads environment variables, applying the defaults below. `get_settings()` is a thin wrapper that returns `AppSettings.from_env()`.

Two things to note about `from_env()`:
- Credential fields (`TRINITY_API_KEY`, `TRINITY_BASE_URL`, `GEMINI_API_KEY`, `ANTHROPIC_AUTH_TOKEN`) use `os.getenv(...) or None`, so an empty string becomes `None` (treated as unset).
- `ANTHROPIC_BASE_URL` falls back to `https://gate.trinity.tg/aurora` when unset.
- Note an asymmetry: the model field for the Anthropic reaction model defaults statically to `claude-haiku-4-5-20251001`, while `from_env()` reads it from `ECHOGRID_ANTHROPIC_REACTION_MODEL` (same default).

### Provider selection

| Env var | Field | Default | Meaning |
|---------|-------|---------|---------|
| `ECHOGRID_LLM_PROVIDER` | `llm_provider` (`LLMProvider`) | `mock` | Which provider to use: `mock`, `anthropic`, `gemini`, or `openai`. Drives `build_llm_client`. |

### Trinity gateway (OpenAI/ChatGPT models only)

| Env var | Field | Default | Meaning |
|---------|-------|---------|---------|
| `TRINITY_API_KEY` | `trinity_api_key` | `None` | API key for the OpenAI-compatible Trinity gateway. Required for `openai` mode. |
| `TRINITY_BASE_URL` | `trinity_base_url` | `None` | Base URL of the Trinity gateway. Required for `openai` mode. |

### Gemini (direct Google client)

| Env var | Field | Default | Meaning |
|---------|-------|---------|---------|
| `GEMINI_API_KEY` | `gemini_api_key` | `None` | Google Gemini API key. Required for `gemini` mode. |
| `ECHOGRID_GEMINI_REACTION_MODEL` | `gemini_reaction_model` | `gemini-2.5-flash-lite` | Model for per-agent reactions (Full sample). |
| `ECHOGRID_GEMINI_ECHO_MODEL` | `gemini_echo_model` | `gemini-2.5-flash` | Model for artifact generation (the one passed to `GeminiLLMClient`). |
| `ECHOGRID_GEMINI_REPORT_MODEL` | `gemini_report_model` | `gemini-2.5-flash` | Model for report generation. |

### Anthropic / Claude (NATIVE Anthropic client)

Claude routes through the **direct Anthropic client**, not the OpenAI Trinity gateway (see [LLM providers](llm-providers.md)).

| Env var | Field | Default | Meaning |
|---------|-------|---------|---------|
| `ANTHROPIC_AUTH_TOKEN` | `anthropic_auth_token` | `None` | Anthropic auth token. Required for `anthropic` mode. |
| `ANTHROPIC_BASE_URL` | `anthropic_base_url` | `https://gate.trinity.tg/aurora` | Base URL for the Anthropic client. Required for `anthropic` mode (default supplied). |
| `ECHOGRID_ANTHROPIC_REACTION_MODEL` | `anthropic_reaction_model` | `claude-haiku-4-5-20251001` | Cheaper model used for per-agent reactions; swapped in via `_active_model`. |
| `ECHOGRID_ANTHROPIC_ECHO_MODEL` | `anthropic_echo_model` | `claude-sonnet-4-6` | Artifact model (frames, echo items, comments); also the client's base `model`. |
| `ECHOGRID_ANTHROPIC_REPORT_MODEL` | `anthropic_report_model` | `claude-sonnet-4-6` | Model for report generation. |
| `ECHOGRID_ANTHROPIC_PREMIUM_MODEL` | `anthropic_premium_model` | `claude-opus-4-7` | Premium/high-end model option. |

### OpenAI / ChatGPT (via Trinity)

These name the models sent to the Trinity gateway; credentials come from `TRINITY_*` above.

| Env var | Field | Default | Meaning |
|---------|-------|---------|---------|
| `ECHOGRID_OPENAI_REACTION_MODEL` | `openai_reaction_model` | `gpt-5.4-nano` | Model for per-agent reactions. |
| `ECHOGRID_OPENAI_ECHO_MODEL` | `openai_echo_model` | `gpt-5.4-mini` | Artifact model (passed to `TrinityLLMClient` in `openai` mode). |
| `ECHOGRID_OPENAI_REPORT_MODEL` | `openai_report_model` | `gpt-5.4-mini` | Model for report generation. |

### Execution and storage

| Env var | Field | Default | Bounds | Meaning |
|---------|-------|---------|--------|---------|
| `ECHOGRID_LLM_MAX_WORKERS` | `llm_max_workers` | `4` | 1–16 | Thread-pool size for Full sample per-agent reactions. |
| `ECHOGRID_LLM_REQUEST_TIMEOUT_SECONDS` | `llm_request_timeout_seconds` | `30` | 5–300 | Per-request timeout (seconds); applied to all clients and to `future.result(timeout=...)` in Full sample. |
| `ECHOGRID_DATABASE_PATH` | `database_path` (`Path`) | `data/echogrid.sqlite3` | — | SQLite database path. Resolves under `DATA_DIR` by default. |

> `from_env()` casts `ECHOGRID_LLM_MAX_WORKERS` and `ECHOGRID_LLM_REQUEST_TIMEOUT_SECONDS` with `int(...)`, and Pydantic enforces the bounds above; an out-of-range value will raise a validation error.

---

## 2. Constants, paths, and disclaimers

Defined at module level in `src/config.py`:

| Constant | Value | Purpose |
|----------|-------|---------|
| `PROJECT_ROOT` | `Path(__file__).resolve().parents[1]` | Repository root (parent of `src/`). |
| `DATA_DIR` | `PROJECT_ROOT / "data"` | Root data directory. |
| `SIMULATIONS_DIR` | `DATA_DIR / "simulations"` | Stored simulation runs. |
| `EXPORTS_DIR` | `DATA_DIR / "exports"` | Exported artifacts. |
| `PROMPTS_DIR` | `PROJECT_ROOT / "src" / "prompts"` | Prompt-template directory used by `load_prompt`. |

### Disclaimer strings

Two canonical disclaimer strings live in `config.py`:

- **`SYNTHETIC_SIMULATION_DISCLAIMER`** — "EchoGrid generates synthetic reactions. It is not a real poll and should not be used as evidence of actual public opinion."
- **`ETHICAL_USE_DISCLAIMER`** — "Echo simulation is intended for research, education, and communication risk analysis. It must not be used to optimize manipulative persuasion, political targeting, harassment, radicalization, or targeting vulnerable groups."

(See also `PROHIBITED_USE_TEXT` and the `classify_request` guardrail in [LLM providers](llm-providers.md).)

---

## 3. Provider mode examples

Each block is a copy-pasteable `.env` for one provider. Start from `.env.example`.

### Mock (default, $0, no network)

```env
ECHOGRID_LLM_PROVIDER=mock
```

Deterministic local generation; no keys needed. Ideal for development, CI, and tests.

### Anthropic / Claude (native client)

```env
ECHOGRID_LLM_PROVIDER=anthropic
ANTHROPIC_AUTH_TOKEN=your-anthropic-auth-token
ANTHROPIC_BASE_URL=https://gate.trinity.tg/aurora
ECHOGRID_ANTHROPIC_REACTION_MODEL=claude-haiku-4-5-20251001
ECHOGRID_ANTHROPIC_ECHO_MODEL=claude-sonnet-4-6
ECHOGRID_ANTHROPIC_REPORT_MODEL=claude-sonnet-4-6
ECHOGRID_ANTHROPIC_PREMIUM_MODEL=claude-opus-4-7
```

Requires `ANTHROPIC_AUTH_TOKEN` and `ANTHROPIC_BASE_URL` (default supplied). Reactions use the Haiku reaction model; artifacts use the Sonnet echo model.

### Gemini (direct Google client)

```env
ECHOGRID_LLM_PROVIDER=gemini
GEMINI_API_KEY=your-gemini-api-key
ECHOGRID_GEMINI_REACTION_MODEL=gemini-2.5-flash-lite
ECHOGRID_GEMINI_ECHO_MODEL=gemini-2.5-flash
ECHOGRID_GEMINI_REPORT_MODEL=gemini-2.5-flash
```

Requires `GEMINI_API_KEY`. The client requests JSON directly (`response_mime_type="application/json"`).

### OpenAI / ChatGPT (via Trinity gateway)

```env
ECHOGRID_LLM_PROVIDER=openai
TRINITY_API_KEY=your-trinity-api-key
TRINITY_BASE_URL=https://your-trinity-gateway/v1
ECHOGRID_OPENAI_REACTION_MODEL=gpt-5.4-nano
ECHOGRID_OPENAI_ECHO_MODEL=gpt-5.4-mini
ECHOGRID_OPENAI_REPORT_MODEL=gpt-5.4-mini
```

Requires `TRINITY_API_KEY` and `TRINITY_BASE_URL`. OpenAI/ChatGPT models route through the OpenAI-compatible Trinity gateway (not the Anthropic client).

### Shared execution/storage settings (optional, any mode)

```env
ECHOGRID_LLM_MAX_WORKERS=4
ECHOGRID_LLM_REQUEST_TIMEOUT_SECONDS=30
ECHOGRID_DATABASE_PATH=data/echogrid.sqlite3
```
