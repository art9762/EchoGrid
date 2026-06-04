# Simulation pipeline

Part of the EchoGrid docs. EchoGrid is an LLM-assisted synthetic-society simulator for media-dynamics, echo-effect, and communication-risk analysis. **All outputs are SYNTHETIC — they are model-generated reactions, not real polls or measurements of real people.**

Related: [Data model](data-model.md) · [Analytics & metrics](analytics-metrics.md) · [Run modes](run-modes.md)

This document describes the end-to-end runtime flow of a single simulation, grounded in `src/simulation.py` and the domain modules it orchestrates. For the layered system design, see `architecture.md` — this page focuses only on what happens when `run_simulation(...)` is called.

---

## 1. Entry point: `run_simulation(...)`

The orchestrator lives in `src/simulation.py`. It keeps the Streamlit UI thin: callers supply an event, frames, run settings, and a persistence target; the service coordinates the domain generators, the echo layer, storage, and progress notifications, then returns a dashboard dict.

### Parameters

| Parameter | Type | Default | Meaning |
|-----------|------|---------|---------|
| `event` | `NewsEvent` | *(required)* | The news event being simulated (title, topic, country, original text). Drives framing text, relevance scoring, and seed derivation. |
| `frames` | `list[NewsFrame]` | *(required)* | Media framings to apply. Used directly in mock; treated as fallback when an LLM regenerates frames. |
| `population_size` | `int` | *(required)* | Number of synthetic agents to generate. **Capped at 100 when `run_mode` is full/full_llm_sample** (raises `ValueError` otherwise). |
| `seed` | `int` | *(required)* | Master seed. Flows into every stochastic stage to make runs reproducible (see §5). |
| `echo_enabled` | `bool` | *(required)* | If true (and `echo_rounds` truthy), runs the multi-round echo-chamber simulation. |
| `echo_rounds` | `int` | *(required)* | Number of echo amplification rounds. `run_echo_simulation` clamps to `max(1, echo_rounds)`. |
| `run_mode` | `str` | `"mock"` | Execution mode: `mock`, `hybrid`, or `full`/`full_llm_sample`. Normalized via `.strip().lower()`. |
| `provider` | `LLMProvider \| str` | `LLMProvider.MOCK` | LLM provider; coerced to the `LLMProvider` enum. |
| `model_name` | `str \| None` | `None` | Optional model override applied per-provider via `_settings_for_provider`. |
| `db_path` | `str \| Path \| None` | `None` | SQLite target. Falls back to `settings.database_path` when `None`. |
| `progress_callback` | `Callable \| None` | `None` | Receives `(message, percent)` or `(message)` (arity auto-detected by `_accepts_two_positional_args`). |
| `llm_client_factory` | `Callable[[Any], Any]` | `build_llm_client` | Builds the LLM client from provider-specific settings. |
| `max_workers` | `int \| None` | `None` | Parallelism for full-sample LLM reactions. Falls back to `settings.llm_max_workers`. |
| `request_timeout_seconds` | `int \| None` | `None` | Per-request LLM timeout. Falls back to `settings.llm_request_timeout_seconds`. |
| `media_preset` | `str` | `"balanced"` | Media-actor preset (see §2.4). |
| `included_actor_types` | `set \| None` | `None` | Optional allowlist of `ActorType`s; non-matching actors are filtered out. |
| `echo_items_per_actor` | `int \| tuple[int, int]` | `1` | Echo items each media actor emits per round. Tuple = randomized range; influencer/grassroots actors get at least 2. |

**Returned dashboard dict** includes: `simulation_id`, `event`, `frames`, `agents`, `reactions`/`initial_reactions`, `media_actors`, `bubbles`, `assignments`/`bubble_assignments`, `echo_result`, `run_mode`, `provider`, `representative_comments`, `llm_errors`, `llm_cost_estimate`, and a `metadata` block (provider, runtime_mode, population_size, seed, echo flags, worker/timeout settings, media_preset).

---

## 2. Stage-by-stage flow

```
NewsEvent + frames + settings
        │
        ▼
(hybrid/full only) LLM connect → regenerate frames ........ 8–18%
        │
        ▼
[1] Population generation (deterministic, seeded) ......... 10%
        │
        ▼
[2] Media framings (6 builtin frames, or LLM frames)
        │
        ▼
[3] Initial reactions (mock baseline; full=LLM sample) .... 35–42%
        │
        ▼
[4] Media ecosystem (11 actors + preset) ................. 55%
[5] Social bubbles (7 bubbles + agent assignment)
        │
        ▼
[6] Echo item generation  ┐
[7] Multi-round echo       ├ if echo_enabled ............... 68–75%
    reactions in bubbles  ┘
        │
        ▼
[8] Final metrics → persist → dashboard dict ............. 92–100%
```

### 2.1 Population generation — `src/population.py`

`generate_population(PopulationConfig(country, population_size, seed))` builds one `AgentProfile` per index from a single `random.Random(seed)`. Each agent draws from deterministic **weighted distributions** via `weighted_choice`:

- Age group (5 bands), gender, location type, education, income, political engagement.
- Derived attributes conditioned on the above: occupation (age/education-aware), family status (age-aware), economic position (income-aware), social position, media diet, values, concerns.
- Psychometric scores (`institutional_trust`, `risk_aversion`, `openness_to_change`, `anger_proneness`, `empathy_level`, `need_for_stability`, `status_anxiety`) computed from a base adjusted by attributes plus `rng.gauss(...)` jitter, then `clamp`ed to 0–100. Examples: college/graduate add +8 trust; tabloid/partisan diet subtracts 12; low income subtracts 8.

Agent IDs are zero-padded (`agent-00001`).

### 2.2 Media framings — `src/framing.py`

`generate_framings(event, n=5)` returns the first `n` of **6 builtin frames**, each constructed from the event title/topic. Frames carry tone, implied values, and a `source_type` (which later affects source-trust adjustments).

| frame_id | Label | Tone | Implied values | source_type |
|----------|-------|------|----------------|-------------|
| `neutral` | Neutral | neutral | balance, public_information | public_broadcaster |
| `technocratic` | Technocratic | technocratic | competence, evidence, stability | policy_outlet |
| `progressive` | Progressive | values_oriented | fairness, care, accountability | progressive_outlet |
| `populist` | Populist | populist | local_control, freedom, accountability | populist_outlet |
| `skeptical` | Skeptical | skeptical | caution, accountability, stability | independent_commentary |
| `tabloid_outrage` | Tabloid / Outrage | outrage | security, freedom, status_protection | tabloid |

In `hybrid`/`full_llm_sample` modes, `run_simulation` first calls `generate_hybrid_frames(...)` to regenerate frames from the LLM, keeping the passed-in frames as fallback; in `mock` mode the supplied frames are used as-is.

### 2.3 Initial reactions — `src/reaction_engine.py`

`run_initial_reactions(agents, event, frames, mode="mock", seed)` produces one `AgentReaction` per **(frame × agent)** pair. In the orchestrator this always runs first as `mode="mock"` to form `fallback_initial_reactions`; in `full_llm_sample` mode it is then replaced by `generate_full_sample_reactions(...)` (parallel LLM calls, falling back per-agent on error).

The mock reaction (`_mock_agent_reaction`):
- Seeds a per-reaction RNG: `seeded_rng(seed, agent.id, event.title, frame.frame_id)`.
- Looks up **`FRAME_EFFECTS`** deltas (support/anger/trust) by frame:

  | frame | support | anger | trust |
  |-------|--------:|------:|------:|
  | neutral | 0 | −6 | +8 |
  | technocratic | +5 | −10 | +6 |
  | progressive | +8 | +2 | 0 |
  | populist | −8 | +13 | −8 |
  | skeptical | −6 | +6 | −7 |
  | tabloid_outrage | −12 | +22 | −18 |

- Computes a `support_score` starting at `50 + effects["support"]`, adjusted by trust, openness, risk-aversion, event relevance, value/frame interactions, and income/topic interactions, plus Gaussian noise.
- **5-point stance logic** (`_stance_from_score`): `SUPPORT` if score ≥ 59, `OPPOSE` if ≤ 41, otherwise `NEUTRAL`; with probabilistic `CONFUSED` branches for low-engagement mid-score agents and for secondary-education agents on the technocratic frame.
- Derives `Emotions` (anger, fear, hope, distrust, indifference), `trust_in_source` (including `_source_trust_adjustment` based on whether the frame's source is in the agent's media diet), perceived personal/group impact, and share/comment/discussion likelihoods — all `clamp`ed. Non-mock modes raise `NotImplementedError` here.

### 2.4 Media ecosystem — `src/media_ecosystem.py`

`default_media_actors(preset, include_actor_types)` returns **11 actors**, each with `actor_type`, `political_bias`, `tone`, `sensationalism`, `credibility`, `reach`, and `audience_affinity` (bubble IDs).

| id | Name | Actor type | Bias | Tone | Sens. | Cred. | Reach |
|----|------|-----------|------|------|------:|------:|------:|
| public-broadcaster | Civic Public Broadcaster | PUBLIC_BROADCASTER | center | neutral | 12 | 82 | 76 |
| policy-brief | Policy Brief Daily | PARTISAN_OUTLET | center | technocratic | 18 | 74 | 42 |
| progressive-outlet | Forward City | PARTISAN_OUTLET | center_left | emotional | 46 | 58 | 59 |
| conservative-outlet | Homefront Review | PARTISAN_OUTLET | center_right | skeptical | 44 | 57 | 58 |
| right-populist-tabloid | The Daily Alarm | TABLOID | populist | outrage | 88 | 28 | 72 |
| left-activist-page | People First Network | GRASSROOTS_ACCOUNT | left | emotional | 64 | 43 | 51 |
| centrist-explainer | The Context Thread | INFLUENCER | center | explanatory | 22 | 68 | 64 |
| outrage-influencer | No Filter Civic | INFLUENCER | populist | outrage | 91 | 24 | 83 |
| expert-fact-checker | Evidence Desk | EXPERT | none | explanatory | 8 | 88 | 45 |
| government-source | Official Information Office | GOVERNMENT_SOURCE | none | technocratic | 5 | 62 | 54 |
| grassroots-viral-account | Neighborhood Pulse | GRASSROOTS_ACCOUNT | none | ironic | 58 | 38 | 67 |

**Presets** (`_apply_preset`) deterministically transform the base list:

| Preset | Effect |
|--------|--------|
| `balanced` / `default` | No change. |
| `low_trust` | All actors: credibility −18 (min 10), sensationalism +14, reach +5. |
| `high_institutional_trust` | All actors: credibility +12, sensationalism −8. |
| `highly_partisan` | Keep only PARTISAN_OUTLET / TABLOID / INFLUENCER; those get sensationalism +18, reach +8. |
| `expert_heavy` | EXPERT / GOVERNMENT_SOURCE / PUBLIC_BROADCASTER get credibility +10, reach +7 (placed first). |

`included_actor_types` then filters to the allowlisted `ActorType`s.

### 2.5 Social bubbles — `src/social_bubbles.py`

`default_social_bubbles()` returns **7 bubbles**, each with `internal_trust`, `external_trust`, `outrage_sensitivity`, and `correction_resistance` that govern echo-round responsiveness.

| id | Label | Outrage sens. | Correction resist. |
|----|-------|-------------:|------------------:|
| high_trust_institutionalists | High-trust institutionalists | 28 | 24 |
| low_trust_working_class | Low-trust working class | 72 | 68 |
| young_urban_progressives | Young urban progressives | 59 | 45 |
| conservative_suburban_families | Conservative suburban families | 55 | 52 |
| apolitical_cost_sensitive | Apolitical cost-sensitive | 45 | 43 |
| highly_online_outrage_users | Highly online outrage users | 88 | 74 |
| expert_oriented_professionals | Expert-oriented professionals | 24 | 21 |

`assign_agents_to_bubbles(agents, bubbles)` places each agent via `_best_bubble`, an **additive scoring** function: each matching trait (trust thresholds, income, age, location, family status, values, media diet, anger/status-anxiety thresholds, education, content style) adds points to candidate bubbles. The highest score wins (ties broken by bubble id); agents with no signal default to `apolitical_cost_sensitive`. `_ensure_nonempty_bubbles` then donates one agent from the largest bubble to any empty bubble so every bubble has at least one member.

### 2.6 Echo item generation — `src/echo_engine.py`

`generate_echo_items(event, frames, reactions, media_actors, bubbles, mode="mock", seed, items_per_actor, round_number)` builds `EchoItem`s:
- Reactions are sorted by `(emotional_intensity + share_likelihood, agent_id, frame_id)` descending to pick the most intense "source" reactions per item.
- Per actor, `_item_count_for_actor` decides how many items (int, or randomized tuple range; influencer/grassroots get ≥2).
- `_echo_type_for_actor` maps actor type → `EchoType` (tabloid→headline, expert→correction, government→clarification, influencer→post, grassroots→viral comment, partisan→attack, plus meme/partisan variants for extra items).
- `_emotion_for_echo`, `_distortion_for_actor` (corrections stay low-distortion), and per-actor sensationalism/reach jitter set the item's properties. Target bubbles come from the actor's `audience_affinity` (or a deterministic fallback). Each item id is `echo-r{round}-{NNN}`.

In `hybrid` mode the orchestrator first builds mock fallback items, then calls `generate_hybrid_response_artifacts(...)` to optionally override them with LLM-generated echo items and collect representative comments.

### 2.7 Multi-round echo reactions — `src/echo_engine.py`

`run_echo_simulation(...)` runs `max(1, echo_rounds)` rounds. It seeds round 0–2 summaries (Original event / Media framings / Initial reactions), then per round:
1. Generate that round's items (round 1 may use the LLM override; later rounds regenerate with `seed + round_index - 1`).
2. For each agent: find its bubble, select a targeted echo item (`_select_echo_item_for_bubble`), and run `run_echo_reaction` (seeded `seed + round_index`).
3. Apply the resulting `EchoReaction` to the agent's running state and record a `FinalAgentState`.

`_mock_echo_reaction` branches by item type/emotion:

| Branch | Trigger | Behavior |
|--------|---------|----------|
| **Correction** | `EXPERT_CORRECTION` or `OFFICIAL_CLARIFICATION` | Acceptance from openness + institutional trust + `(100 − bubble.correction_resistance)`; pushes trust up, anger/distrust down. |
| **Outrage** | emotion in {anger, fear, distrust, mockery} | Susceptibility from bubble outrage-sensitivity + anger-proneness + item sensationalism/distortion; raises anger, distrust, sharing; stance pushed by direction (tabloid/partisan force −1). |
| **Mild** | otherwise | Small openness-driven stance drift and mildness-driven trust drift; low-magnitude shifts. |

**Per-round saturation** dampens later rounds: `saturation = max(0.55, 1 − (round_number − 1) * 0.18)`. For rounds > 1, all five shifts (stance, trust, anger, distrust, share) are multiplied by this factor — so amplification decays each round but never below 55%.

`_updated_stance` re-derives a discrete stance from a base value plus the stance shift (≥22 → SUPPORT, ≤−22 → OPPOSE, else NEUTRAL).

### 2.8 Final metrics, persistence, return

After echo rounds, `run_echo_simulation` computes amplification metrics (`echo_amplification_index`, `distortion_drift`, `trust_delta`, `anger_delta`, `virality_growth`) from `src/analytics.py` and returns an `EchoSimulationResult`. The orchestrator then calls `save_simulation(...)` (SQLite) and returns the dashboard dict described in §1. Progress notifications fire throughout (8 → 100%).

---

## 3. Demo scenarios — `src/scenarios.py`

`demo_scenarios()` returns **7 prebuilt `NewsEvent`s** keyed by title:

1. Emissions-based car tax — topic `taxes`
2. AI surveillance in public spaces — topic `civil_liberties`
3. Four-day work week proposal — topic `jobs`
4. Mandatory digital ID — topic `civil_liberties`
5. Housing policy reform — topic `housing`
6. University bans phones in classrooms — topic `education`
7. City restricts short-term rentals — topic `housing`

All use country `United States` and supply description + `original_text`.

---

## 4. Run modes (summary)

| Mode | Frames | Initial reactions | Echo items | LLM calls |
|------|--------|-------------------|------------|-----------|
| `mock` | supplied builtin frames | deterministic mock | mock | none |
| `hybrid` | LLM-regenerated (fallback to supplied) | mock | mock + LLM override + representative comments | framing + artifacts |
| `full` / `full_llm_sample` | LLM-regenerated | LLM per-agent (parallel, per-agent fallback) | mock | framing + per-reaction (**capped at 100 agents**) |

See [Run modes](run-modes.md) for full detail.

---

## 5. Determinism — how the seed flows

EchoGrid is reproducible because the **single master `seed`** threads through every stochastic stage, and each random draw uses a *content-derived* sub-seed (via `seeded_rng`/`stable_seed`) rather than ambient state:

| Stage | Seeding |
|-------|---------|
| Population | `random.Random(config.seed)` drives every weighted choice and Gaussian draw. |
| Initial reactions | per reaction: `seeded_rng(seed, agent.id, event.title, frame.frame_id)`. |
| Full-sample LLM reactions | `seed` passed through to `generate_full_sample_reactions`. |
| Echo item generation | per actor: `seeded_rng(seed, event.title, actor.id, actor_index)`; later rounds use `seed + round_index - 1`. |
| Echo item selection | `seeded_rng(seed + round_index, agent.id, bubble.id, "echo-selection")`. |
| Echo reactions | `seeded_rng(seed + round_index, agent.id, item.id, bubble.id)`. |
| Simulation id | `sim-{stable_seed(seed, event.title) % 1_000_000:06d}`. |

Because sub-seeds combine the master seed with stable identifiers (agent id, event title, frame/actor/item/bubble ids, round index), the same inputs always reproduce the same synthetic society, framings, reactions, and echo trajectory. Sorting tie-breakers (e.g. reactions sorted by intensity then `agent_id`, `frame_id`) and the deterministic bubble-tie rule keep ordering stable too. The only non-determinism enters in `hybrid`/`full` modes from the LLM provider itself; the mock fallbacks remain fully reproducible.
