> Part of the [EchoGrid documentation](index.md). See also [LLM providers](llm-providers.md), [Configuration](configuration.md), [Cost guide](cost-guide.md), and [Simulation pipeline](simulation-pipeline.md).

# Run Modes

EchoGrid runs the **same deterministic pipeline** in three modes. The mode only
changes *which artifacts are produced by an LLM* versus computed locally by the
deterministic mock engine. Every mode produces synthetic output — none of them
measure or predict real public opinion.

The mode is selected by the `run_mode` argument to
`src.simulation.run_simulation` (and the matching control in the Streamlit setup
panel): `"mock"`, `"hybrid"`, or `"full_sample"`.

| | Mock | Hybrid | Full LLM sample |
|---|---|---|---|
| `run_mode` | `"mock"` | `"hybrid"` | `"full_sample"` |
| LLM calls per run | **0** | ~**2–3** (fixed) | `agents × frames` + artifacts |
| Cost | **$0** | low, bounded | scales with sample size |
| Agent reactions | deterministic | deterministic | **LLM-generated** |
| Framings | builtin (6) | **LLM** | **LLM** |
| Echo items | deterministic | **LLM** | **LLM** |
| Representative comments | deterministic | **LLM** | **LLM** |
| Provider required | no | yes | yes |
| Agent cap | none | none | **100** |
| Reproducible from seed | fully | artifacts vary; structure stable | reactions vary |

---

## Mock — deterministic, offline, $0

The default and the demo path. **No provider, no network, no key.** The entire
run — population, framings, reactions, echo items, multi-round echo reactions,
and metrics — is computed locally by the deterministic mock engine.

- Same inputs (event + `population_size` + `seed` + echo settings) always yield
  **byte-identical** output. Re-running a seed reproduces it exactly.
- Best for: local demos, the automated test suite, offline exploration, and
  repeatable seed traces.
- `provider` is `LLMProvider.MOCK`; `build_llm_client` returns `MockLLMClient`,
  whose `complete_text` returns a fixed stub and is never on the result path.

This is the mode every test runs in — the suite needs no API keys.

---

## Hybrid — bounded artifact-level LLM calls

Hybrid keeps **all per-agent reactions deterministic** (the same mock engine as
Mock) but replaces the *narrative artifacts* with LLM output. Only three
artifact-level prompts are issued, regardless of population size:

1. **Framings** — `generate_hybrid_frames` (replaces the 6 builtin frames).
2. **Echo items** — bounded LLM generation per media actor.
3. **Representative comments** — a small set of illustrative synthetic quotes.

Because reactions stay deterministic, a **1,000-agent** Hybrid run still issues a
small fixed number of provider calls (~2–3). This is the sweet spot: richer,
model-written narrative text without per-agent cost.

- Each artifact step has **per-step error capture**: if a generation call fails
  or returns invalid JSON (after the typed validate-and-retry in
  `LLMClient._complete_validated_adapter`), the run falls back to the
  deterministic artifact and continues.
- Requires a configured provider (see [Configuration](configuration.md)).

---

## Full LLM sample — per-agent reactions, capped

Full sample issues an LLM call for **each agent × each frame** initial reaction
(`generate_full_sample_reactions`, run concurrently via a `ThreadPoolExecutor`
bounded by `ECHOGRID_LLM_MAX_WORKERS`) **plus** the Hybrid artifact calls.

- **Hard cap: 100 agents.** `run_simulation` truncates the sample to 100 in
  `full_sample` mode to keep cost and latency bounded — this is a small
  qualitative sample, not a population.
- Call volume ≈ `min(population_size, 100) × frame_count + artifact_calls`.
- Each per-agent call has its **own fallback**: a failed reaction falls back to
  the deterministic mock reaction for that agent, so a few provider errors never
  abort the run.
- Echo reactions remain deterministic even here — only the *initial* reactions
  are LLM-generated.
- Best for: small qualitative samples where provider-written reactions add value
  to a demo or discussion.

---

## Cost preview & guardrails

Before any LLM run the app shows an **estimate** — projected call count, a token
band, and a rough USD range — from `estimate_llm_cost` /
`_rough_price_band` (Gemini band ≈ 0.05–3.5, other providers ≈ 0.1–15.0, Mock 0).
See the [Cost guide](cost-guide.md) for the per-mode cost breakdown and the
[LLM providers](llm-providers.md) doc for the pricing-band internals.

All three modes route requests through `src.guardrails.classify_request`, which
refuses manipulative-targeting, election-targeting, and harassment/radicalization
prompts. See [ethics.md](ethics.md) and [limitations.md](limitations.md).

> **Synthetic output, every mode.** Switching to Hybrid or Full sample makes the
> text more model-written — it does **not** make it real. EchoGrid output is
> never polling evidence or a prediction about actual people.
