# LLM Providers

> Part of the EchoGrid docs. See also [Configuration](configuration.md), [Run modes](run-modes.md), and the [Cost guide](cost-guide.md).

EchoGrid is an LLM-assisted **synthetic-society simulator**. Every artifact it produces is **SYNTHETIC** — never a real poll or evidence of actual public opinion. This document describes how EchoGrid talks to language models: the client abstraction, the four concrete clients, the factory, the orchestration pipeline, the prompt templates, and the ethical guardrail that sits in front of request handling.

Source files:
- `src/llm_client.py` — `LLMClient` ABC, concrete clients, factory, JSON helpers
- `src/llm_pipeline.py` — orchestration (cost estimate, hybrid + full-sample generation)
- `src/prompts/` — the five prompt templates and `load_prompt`
- `src/guardrails.py` — `classify_request` ethical gate

---

## 1. The `LLMClient` ABC

`LLMClient` (in `src/llm_client.py`) is an abstract base class. Subclasses implement exactly one abstract method, `complete_text(prompt, max_tokens=1500) -> str`; everything else (JSON parsing, validation, retry, typed helpers) is provided by the base class.

Constructor stores `model` and `timeout_seconds` (both optional).

### Text and JSON completion

| Method | Returns | Notes |
|--------|---------|-------|
| `complete_text(prompt, max_tokens=1500)` | `str` | Abstract — the only thing subclasses must implement. |
| `complete_json(prompt, max_tokens=1500)` | `dict[str, Any]` | Calls `complete_text`, then `parse_json_response` (requires a JSON object). |
| `complete_model(prompt, model_type, max_tokens=1500, retries=1)` | `EchoGridModel` | Validates the response against a Pydantic `model_type` via `_complete_validated_adapter`. |

### Typed JSON validation + retry

The core of typed generation is `_complete_validated_adapter`:

```python
def _complete_validated_adapter(self, prompt, adapter, max_tokens, retries=1) -> T:
    retry_prompt = prompt
    for attempt in range(retries + 1):
        try:
            payload = parse_json_value(self.complete_text(retry_prompt, max_tokens=max_tokens))
            return adapter.validate_python(payload)
        except (json.JSONDecodeError, ValidationError, ValueError) as exc:
            if attempt == retries:
                break
            retry_prompt = build_json_retry_prompt(prompt, exc)
    raise ValueError("LLM returned invalid JSON after retry") from last_error
```

- Runs the call, strips code fences, parses JSON, and validates against a Pydantic `TypeAdapter`.
- On `JSONDecodeError` / `ValidationError` / `ValueError`, it rebuilds the prompt with `build_json_retry_prompt` (appending the error and a "JSON only" instruction) and retries.
- `retries` defaults to **1**, i.e. up to **2 total attempts**. After the last attempt it raises `ValueError("LLM returned invalid JSON after retry")`, chaining the last underlying exception.
- `_complete_validated_model` is a thin wrapper that builds a `TypeAdapter(model_type)` and delegates here.

### `generate_*` typed helpers

These wrap `_complete_validated_adapter` with a concrete schema and a sensible `max_tokens` default. Their return types come from `src/schemas.py`.

| Helper | Schema (validated as) | Default `max_tokens` |
|--------|-----------------------|----------------------|
| `generate_reaction_json` | `AgentReaction` | 1500 |
| `generate_echo_items_json` | `list[EchoItem]` | 3000 |
| `generate_echo_reaction_json` | `EchoReaction` | 1500 |
| `generate_framings_json` | `list[NewsFrame]` | 2500 |
| `generate_representative_comments_json` | `list[RepresentativeComment]` | 2500 |

### Module-level JSON helpers

- **`parse_json_value(text)`** — strips surrounding whitespace, then strips a leading/trailing triple-backtick (` ``` `) fence if present (handles ` ```json ` blocks by dropping the first fence line and a trailing fence line), then `json.loads` the remainder. Returns any JSON value.
- **`parse_json_response(text)`** — calls `parse_json_value` and raises `ValueError("Expected a JSON object from LLM response")` if the parsed value is not a `dict`.
- **`build_json_retry_prompt(original_prompt, error)`** — returns the original prompt plus a note that the previous response failed to parse/validate, the error text, and an instruction to "Return JSON only, with no markdown, comments, or extra fields."

---

## 2. Concrete clients

| Client | Transport / SDK | Auth | Base URL | Cost | Used for |
|--------|-----------------|------|----------|------|----------|
| `MockLLMClient` | none (local string) | none | none | $0 | Deterministic default, offline/dev/tests |
| `TrinityLLMClient` | `openai` SDK (`OpenAI`) | `api_key` | `base_url` (Trinity gateway) | paid | **OpenAI/ChatGPT** models only |
| `AnthropicLLMClient` | **native** `anthropic` SDK (`Anthropic`) | `auth_token` | default `https://gate.trinity.tg/aurora` | paid | **Claude** models |
| `GeminiLLMClient` | `google.genai` SDK | `api_key` | SDK default (Google) | paid | **Gemini** models |

### `MockLLMClient`

`complete_text` always returns the same literal string:

```json
{"provider": "mock", "note": "deterministic mock mode is active"}
```

Deterministic and free ($0). It makes **no** network calls. The pipeline's deterministic fallbacks (see §3) mean Mock runs still produce a complete, valid sample without any LLM.

### `TrinityLLMClient` (OpenAI-compatible gateway)

- Imports `OpenAI` lazily inside `complete_text` and builds a client with `api_key`, `base_url`, and `timeout`.
- Calls `chat.completions.create` with `model`, `max_tokens`, `temperature=0.2`, and a single user message.
- Normalizes the response content: returns the string directly, joins a list of content parts (`item["text"]`) when the SDK returns structured content, or `"{}"` as a fallback.
- Carries a `provider_label` (e.g. `"openai"`) used only for error messages.
- This is the gateway used for **OpenAI/ChatGPT** models. It is OpenAI-compatible, so it points at the **Trinity** base URL with the Trinity API key.

### `AnthropicLLMClient` (DIRECT Anthropic client)

- Imports `Anthropic` lazily and constructs it with `auth_token`, `base_url`, and `timeout`. The default `base_url` is **`https://gate.trinity.tg/aurora`** (set in `config.py` / `.env.example`).
- Calls `messages.create` with the active model, `max_tokens`, `temperature=0.2`, and one user message; joins all `text` content blocks, falling back to `"{}"`.
- **Two-model swapping.** The client holds two models:
  - `reaction_model` — used for per-agent reactions (cheaper, e.g. Haiku)
  - `artifact_model` — used for run-level artifacts (frames, echo items, representative comments; e.g. Sonnet). This is also the base-class `self.model` and the initial `_active_model`.
  - `generate_reaction_json` temporarily sets `_active_model = reaction_model`, runs the call, and **always restores** `artifact_model` in a `finally` block.
  - `generate_framings_json`, `generate_echo_items_json`, and `generate_representative_comments_json` each explicitly set `_active_model = artifact_model` before delegating to the base class.

> **Key nuance:** Claude routes through the **native Anthropic client** (`anthropic` SDK), *not* the OpenAI-compatible Trinity gateway. Even though the default Anthropic base URL points at the Trinity host (`gate.trinity.tg/aurora`), the request uses the Anthropic Messages API, not OpenAI chat completions. OpenAI/ChatGPT models route through `TrinityLLMClient` (the OpenAI SDK against `TRINITY_BASE_URL`).

### `GeminiLLMClient` (direct)

- Imports `google.genai` lazily and builds `genai.Client(api_key=...)`.
- Calls `models.generate_content` with `model`, `contents=prompt`, and a `GenerateContentConfig` setting `max_output_tokens`, `temperature=0.2`, and **`response_mime_type="application/json"`** (asks Gemini for JSON directly).
- Returns `response.text` or `"{}"`. Note: this client does not take a `base_url`; it uses the Google SDK default endpoint.

---

## 3. The factory: `build_llm_client(settings)`

`build_llm_client(settings: AppSettings) -> LLMClient` maps the configured provider to a concrete client and validates required credentials. Provider enum values come from `LLMProvider` in `src/schemas.py`.

| `settings.llm_provider` | Client built | Required settings | Model passed |
|-------------------------|--------------|-------------------|--------------|
| `MOCK` | `MockLLMClient()` | none | — |
| `ANTHROPIC` | `AnthropicLLMClient` | `anthropic_auth_token`, `anthropic_base_url` | `reaction_model=anthropic_reaction_model`, `artifact_model=anthropic_echo_model` |
| `GEMINI` | `GeminiLLMClient` | `gemini_api_key` | `gemini_echo_model` |
| `OPENAI` | `TrinityLLMClient` (via `_build_trinity_client`) | `trinity_api_key`, `trinity_base_url` | `openai_echo_model` |
| anything else | — | — | raises `ValueError(f"Unsupported LLM provider: ...")` |

Each branch raises a clear `ValueError` if a required credential/URL is missing (e.g. `"ANTHROPIC_AUTH_TOKEN is required for Anthropic mode"`). All clients receive `timeout_seconds=settings.llm_request_timeout_seconds`.

**`_build_trinity_client(settings, provider_label, model, timeout_seconds)`** — shared helper that checks `trinity_api_key` and `trinity_base_url` (raising `"TRINITY_API_KEY is required for {provider_label} mode"` etc. if missing) and constructs a `TrinityLLMClient`. Currently used by the `OPENAI` branch with `provider_label="openai"`.

---

## 4. The orchestration layer (`src/llm_pipeline.py`)

This module coordinates bounded LLM use. It defines a `HybridLLMClient` `Protocol` (the four `generate_*` methods the pipeline needs) so any client satisfying that shape works.

### `estimate_llm_cost(...)`

`estimate_llm_cost(run_mode, provider, population_size, frame_count, echo_enabled) -> LLMCostEstimate` returns a token/call/USD estimate. Behaviour by normalized `run_mode`:

- **`mock`** — 0 calls, 0 tokens, $0; note that mock makes no LLM calls.
- **`full_llm_sample` / `full`** — `reaction_calls = population_size * max(frame_count, 1)` plus artifact calls (`1 + 1 + (1 if echo_enabled else 0)`). Input ~700 tokens/reaction, output ~320/reaction, plus frame and echo overhead. Notes that full mode calls the provider once per agent/frame and is **capped at 100 agents** by the app.
- **default (Hybrid)** — `calls = 1 (framing) + 1 (representative comments) + (1 if echo_enabled)`. It samples up to **24** reactions for context tokens only; there are **no per-agent calls**.

USD is computed as `(input + output) / 1e6 * rate` for both a low and high `_rough_price_band(provider)` rate.

### `_rough_price_band(provider)`

| Provider | Low rate ($/M tokens) | High rate ($/M tokens) |
|----------|----------------------|------------------------|
| `MOCK` | 0 | 0 |
| `GEMINI` | 0.05 | 3.5 |
| everything else (Anthropic, OpenAI) | 0.1 | 15.0 |

### `generate_hybrid_frames(...)`

Picks `fallback_frames[:frame_count]` as a baseline, then tries `client.generate_framings_json(build_framing_prompt(event, frame_count))`. On success, `_normalize_frames` validates, truncates to `frame_count`, and slugifies/deduplicates `frame_id`s. Any exception is captured as an `LLMGenerationError` (step `"framings"`) and the deterministic fallback frames are kept. Returns `(frames, errors)`.

### `generate_hybrid_response_artifacts(...)`

Generates the two response artifacts, each guarded independently:
- **Echo items** (only if `echo_enabled`): `generate_echo_items_json` over `build_echo_items_prompt` (event, frames, sampled reactions, media actors, bubbles). On failure → `LLMGenerationError("echo_items", ...)` and `fallback_echo_items` are used.
- **Representative comments**: `generate_representative_comments_json` over `build_representative_comments_prompt`. On failure → `LLMGenerationError("representative_comments", ...)`.

Returns a `HybridArtifacts` with frames, echo items, representative comments, and the accumulated errors. (`generate_hybrid_artifacts` is the convenience wrapper that runs frames then artifacts and merges results/errors.)

Reaction context is bounded by `_reaction_samples`, which ranks reactions by `emotional_intensity + share_likelihood` and keeps the top `limit` (default 24) as compact dicts.

### `generate_full_sample_reactions(...)`

Generates **per-agent** LLM reactions, one task per `(agent, frame)` pair, using a `ThreadPoolExecutor`:
- Worker count = `max(1, min(max_workers, total))`.
- Builds a per-key deterministic fallback up front (existing fallback reaction, or `run_agent_reaction(..., mode="mock", seed=seed)`).
- Each future is read with `future.result(timeout=request_timeout_seconds)`. On `TimeoutError` **or any exception**, it records an `LLMGenerationError` (`full_reaction:{agent.id}:{frame.frame_id}`) and substitutes the deterministic fallback for that single call — so one failed/slow call never sinks the run.
- Reports progress via the optional `progress_callback(message, percent)`.
- Returns `(reactions, errors)`; reactions are returned in task order, with the generated reaction's `agent_id`/`frame_id` re-stamped from the source agent/frame.

### HYBRID vs FULL SAMPLE — the practical difference

- **HYBRID (default):** Agent reactions are computed **deterministically** (no LLM). The LLM is used **only for artifact-level calls** — roughly **2–3 calls per run**: framings, optionally echo items, and representative comments. Reaction samples are passed as context, not generated per agent. Cheap and bounded.
- **FULL SAMPLE:** Adds **one LLM call per agent per frame** for reactions on top of the artifact calls. The app **caps this at 100 agents**, and every per-agent call has an individual deterministic fallback on timeout/error.

See [Run modes](run-modes.md) and the [Cost guide](cost-guide.md) for how to choose and budget these.

---

## 5. Prompt templates (`src/prompts/`)

`load_prompt(name)` reads a template by logical name or filename. Naming rules (`_prompt_path`): a `.txt` name is used as-is; a `*_prompt` name gets `.txt` appended; any other name gets `_prompt.txt` appended. Path-traversal names are rejected.

| Template file | `load_prompt` name | Purpose |
|---------------|--------------------|---------|
| `framing_prompt.txt` | `framing` | Generate realistic alternative `NewsFrame` framings of an event (neutral, technocratic, progressive, populist, skeptical, tabloid). |
| `reaction_prompt.txt` | `reaction` | Simulate one synthetic respondent's `AgentReaction` to an event+frame (stance, emotions, trust, share/comment likelihood). |
| `echo_generation_prompt.txt` | `echo_generation` | Generate media/social `EchoItem` artifacts (tabloid headlines, influencer posts, expert corrections, memes, etc.) with distortion/sensationalism levels. |
| `echo_reaction_prompt.txt` | `echo_reaction` | Simulate how one synthetic person updates/reinforces/resists their stance after seeing an echo item (`EchoReaction`). |
| `representative_comments_prompt.txt` | `representative_comments` | Write short `RepresentativeComment` artifacts summarizing visible response segments for research/demo inspection. |

Every template ends with "Return JSON only" and explicitly forbids persuasion optimization, manipulative/election/vulnerable-group targeting, harassment, and radicalization, reinforcing the guardrail in §6.

---

## 6. Ethical guardrail: `guardrails.classify_request()`

`src/guardrails.py` is the central ethical gate that sits **in front of request handling** (before a simulation request is accepted/processed). `classify_request(request_text) -> GuardrailDecision` normalizes the text (lowercase, whitespace-collapsed) and matches it against disallowed phrase patterns grouped into three categories:

| Category | Example blocked phrases |
|----------|-------------------------|
| **manipulative targeting** | "manipulate group/voters", "best message to manipulate", "persuade vulnerable", "target vulnerable", "optimize persuasion", "psychographic targeting" |
| **election targeting** | "election targeting", "target voters", "swing voters", "suppress turnout" |
| **harassment or radicalization** | "harass", "radicalize", "incite", "intimidate" |

If any pattern matches, it returns `GuardrailDecision(allowed=False, reason=<category>, refusal_message=...)` where the refusal offers to reframe the request as synthetic risk analysis, safety evaluation, or educational comparison. Otherwise it returns `allowed=True, reason="allowed research or analysis"`. `is_disallowed_request(text)` is the boolean convenience wrapper (`not classify_request(text).allowed`).

The module also exports `PROHIBITED_USE_TEXT`, the human-readable prohibited-use statement, complementing the disclaimers in `config.py` (see [Configuration](configuration.md)).
