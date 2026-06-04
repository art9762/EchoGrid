# Analytics Metrics

Part of the EchoGrid docs. EchoGrid is a Python LLM-assisted synthetic-society simulator.

Related: [Simulation pipeline](simulation-pipeline.md) · [Data model](data-model.md)

> **Synthetic indicators, not real opinion.** Every number on this page is computed
> from model-generated agent reactions inside a simulation. These are **synthetic
> indicators**, not measurements of real public opinion. They describe how a fictional
> population of LLM-driven agents responded to fictional content. Do **not** read any
> value as a poll, forecast, or estimate of what real people think.

This document describes the metric and aggregation helpers in
[`src/analytics.py`](../src/analytics.py). All computation uses Python's `statistics`
(`mean`, `median`), `collections.Counter`, and **pandas** (`pd.DataFrame`,
`pd.Series`, `groupby`, population standard deviation via `std(ddof=0)`). Values are
constrained with `clamp` from `src.utils` (default range `0–100` unless other bounds
are passed). Most outputs are rounded to 2 decimals.

---

## Metric summary

| Metric | Measures | Output shape | Range |
|--------|----------|--------------|-------|
| `stance_distribution` | % of reactions per stance | dict stance→% | 0–100 each |
| `emotion_averages` | mean emotion + intensity | dict of 6 floats | source-bound |
| `polarization_score` | stance spread × intensity | float | 0–100 |
| `virality_risk_score` | intensity × share × comment | float | 0–100 |
| `frame_comparison` | per-frame metric bundle | dict frame→bundle | mixed |
| `echo_amplification_index` | weighted echo amplification | float | 0–100 |
| `echo_amplification_breakdown` | component breakdown of index | dict comp→{raw,weight,contrib} | mixed |
| `distortion_drift` | reach-weighted distortion | float | 0–distortion scale |
| `trust_delta` / `anger_delta` / `virality_growth` | mean post-echo shifts | float | shift-bound |
| `final_state_metrics` | after-echo aggregate state | dict | mixed |
| `narrative_risk_summary` | top risk highlights | dict | mixed |

---

## Helper functions (bucketing)

These prepare segment keys; they are not headline metrics.

- `age_group(age)` → `"18-24"` (≤24), `"25-34"` (≤34), `"35-49"` (≤49), `"50-64"` (≤64), else `"65+"`.
- `institutional_trust_bucket(trust)` → `"low"` (<34), `"medium"` (<67), else `"high"`.
- `segment_value(agent, by_field)` → dispatches to the two helpers above for
  `"age_group"` / `"institutional_trust_bucket"`, otherwise `getattr(agent, by_field)`.

Shared constants:

- `STANCE_ORDER = [SUPPORT, OPPOSE, NEUTRAL, CONFUSED]`
- `STANCE_SIGN = {SUPPORT: 1, OPPOSE: -1, NEUTRAL: 0, CONFUSED: 0}`

---

## `stance_distribution(reactions)`

- **Measures:** percentage of agent reactions falling into each stance.
- **Input:** `list[AgentReaction]`.
- **Output:** `dict[str, float]` keyed by stance value, in `STANCE_ORDER`.
- **Formula:** for each stance, `round(count(stance) * 100 / total, 2)`. Empty input
  returns `0.0` for every stance.
- **Range:** 0–100 per stance (sums to ~100 modulo rounding).

## `emotion_averages(reactions)`

- **Measures:** mean of each emotion channel plus mean emotional intensity.
- **Input:** `list[AgentReaction]`.
- **Output:** `dict[str, float]` with keys `anger`, `fear`, `hope`, `distrust`,
  `indifference`, `emotional_intensity`. Empty input → all `0.0`.
- **Formula:** plain `mean(...)` over `reaction.emotions.<channel>` and
  `reaction.emotional_intensity`, each rounded to 2 dp.

## `trust_average(reactions)`

- **Measures:** mean `trust_in_source` across reactions.
- **Output:** float, `0.0` if empty.

## `share_likelihood_distribution(reactions)`

- **Measures:** distribution of share likelihood.
- **Output:** dict `average`, `median`, `p75`, `high_share_percent`.
- **Formula:** sorts shares; `p75` index = `min(len-1, int(len*0.75))`;
  `high_share_percent` = `% of shares ≥ 65`.

## `segment_breakdown(reactions, agents, by_field)`

- **Measures:** per-segment stance/emotion/trust aggregates.
- **Method:** builds a **pandas** `DataFrame`, `groupby("segment", sort=True)`.
- **Output:** list of dicts with `segment`, `count`, `support_percent`,
  `oppose_percent`, `average_share_likelihood`, `average_anger`, `average_distrust`,
  `average_trust`. Percentages via boolean `.mean() * 100`.

---

## `polarization_score(reactions)`

- **Measures:** how spread-out and intense stances are.
- **Input:** `list[AgentReaction]` (returns `0.0` if fewer than 2).
- **Output:** float, clamped to 0–100.
- **Formula:**

  ```
  signed = STANCE_SIGN[stance] * stance_strength          # per reaction
  stance_spread = min(100, pd.Series(signed).std(ddof=0)) # population std, capped
  intensity     = emotion_averages(reactions)["emotional_intensity"]
  score = clamp(stance_spread * (0.72 + intensity / 180))
  ```

  The intensity term scales the base `0.72` multiplier upward as emotional intensity rises.

## `virality_risk_score(reactions)`

- **Measures:** likelihood that content spreads, from intensity and engagement.
- **Output:** float, clamped 0–100. `0.0` if empty.
- **Formula:**

  ```
  score = clamp(emotional_intensity * avg_share_likelihood * avg_comment_likelihood / 10000)
  ```

  where the three factors are means over the reaction set. The `/ 10000` normalizes
  the product of three roughly-0–100 quantities back toward a 0–100 band.

---

## `frame_comparison(reactions)`

- **Measures:** runs the core metrics independently per `frame_id`.
- **Output:** `dict[frame_id, bundle]` where each bundle contains
  `stance_distribution`, `emotion_averages`, `average_trust`,
  `average_share_likelihood`, `polarization_score`, `virality_risk_score` — each
  computed on that frame's subset of reactions.

### Related: `frame_sensitivity_score(reactions)`

Builds on `frame_comparison` to quantify how much the frame mattered.

- **Output:** dict `score`, `stance_spread`, `trust_spread`, `share_spread`,
  `highest_share_frame`, `lowest_trust_frame`.
- **Formula:** `_spread(values) = max - min`; `stance_spread = max(support_spread, oppose_spread)`.

  ```
  score = clamp(stance_spread * 0.45 + trust_spread * 0.25 + share_spread * 0.30)
  ```

### Related: `unexpected_segments(reactions, agents)`

Scans `income_level`, `age_group`, `institutional_trust_bucket` segments (count ≥ 5),
scoring each:

```
risk_score = avg_anger * 0.38 + avg_distrust * 0.27 + avg_share_likelihood * 0.35
```

Keeps rows with `risk_score ≥ 45`, returns top 8 by risk.

---

## Echo amplification

These metrics compare initial reactions against post-echo reactions to measure how
much the "echo" (re-sharing/distortion) stage amplified the narrative.

### `_AMPLIFICATION_WEIGHTS`

| Component | Weight | Raw value source |
|-----------|--------|------------------|
| `anger_delta` | **0.22** | `max(0, anger_delta(echo_reactions))` |
| `trust_loss` | **0.20** | `max(0, -trust_delta(echo_reactions))` |
| `share_growth` | **0.22** | `max(0, virality_growth(echo_reactions))` |
| `stance_motion` | **0.18** | `mean(|stance_shift|)` over echo reactions |
| `distortion` | **0.18** | `distortion_drift(echo_items)` |

Weights sum to **1.00**.

### `echo_amplification_index(initial_reactions, echo_reactions, echo_items)`

- **Measures:** overall amplification from the echo stage.
- **Output:** float, clamped 0–100. `0.0` if either reaction list is empty.
- **Formula:** sums `weighted_contribution` across all breakdown components, then clamps:

  ```
  index = clamp( Σ (raw_value_i * weight_i) )
  ```

### `echo_amplification_breakdown(initial_reactions, echo_reactions, echo_items)`

- **Measures:** the per-component decomposition behind the index.
- **Output:** `dict[component, {raw_value, weight, weighted_contribution}]` where
  `weighted_contribution = round(raw_value * weight, 2)`. Empty input → all components
  zeroed (weights preserved). Note `trust_loss` uses the **negated** trust delta (only
  trust *decreases* contribute), and `anger_delta` / `share_growth` are floored at 0.

### `distortion_drift(echo_items)`

- **Measures:** reach-weighted average distortion across echo items.
- **Output:** float (0–distortion scale). `0.0` if empty.
- **Formula:** each item's `estimated_reach` is floored at 1:

  ```
  drift = Σ(distortion_level_i * max(reach_i, 1)) / Σ max(reach_i, 1)
  ```

### Shift deltas

| Function | Measures | Formula | Notes |
|----------|----------|---------|-------|
| `trust_delta(echo_reactions)` | mean trust change | `mean(trust_shift)` | signed; `0.0` if empty |
| `anger_delta(echo_reactions)` | mean anger change | `mean(emotion_shift.anger)` | signed; `0.0` if empty |
| `virality_growth(echo_reactions)` | mean share-likelihood change | `mean(share_likelihood_shift)` | signed; `0.0` if empty |

### Related: `polarization_delta(initial_reactions, echo_reactions)`

Compares signed-stance spread before vs after, plus emotion pressure:

```
initial_spread = std(initial signed scores, ddof=0)
final_spread   = std(final signed scores, ddof=0)   # final stance/strength, |shift|*0.5 blended
emotion_pressure = mean( max(0, anger_shift) + max(0, distrust_shift) )
delta = clamp(final_spread - initial_spread + emotion_pressure * 0.08, -100, 100)
```

Returns `0.0` with fewer than 2 scored agents on either side.

### Related: `correction_effectiveness(echo_items, echo_reactions)`

Filters to echo items of type `expert_correction` or `official_clarification`, then
returns `average_trust_shift` and `average_anger_shift` over reactions to those items
(`0.0` each if none match).

### Related: `bubble_susceptibility(echo_reactions, bubbles)`

Groups echo reactions by `bubble_id`, returning per-bubble `count` and mean
`stance_shift`, `anger_shift`, `distrust_shift`, `share_likelihood_shift`.

---

## `final_state_metrics(final_states, echo_reactions)`

- **Measures:** the after-echo aggregate state for dashboards/exports.
- **Inputs:** `dict[str, FinalAgentState]`, `list[EchoReaction]`.
- **Output:** dict with:
  - `final_stance_distribution` — % per stance via `Counter` over `final_stance`
    (`count * 100 / total`).
  - `final_trust_average` — `mean(final_trust)`.
  - `final_share_likelihood_average` — `mean(final_share_likelihood)`.
  - `average_stance_shift` — `mean(stance_shift)` over echo reactions (0.0 if none).
  - `average_anger_shift` — delegates to `anger_delta(echo_reactions)`.
- Empty states → all fields zeroed.

## `narrative_risk_summary(echo_items, echo_reactions, bubbles)`

- **Measures:** inspectable highlights of where narrative risk concentrated.
- **Output:** dict with:
  - `top_echo_type` — most common `echo_type` (`Counter.most_common(1)`).
  - `top_bubble` — bubble with the highest accumulated risk, where per-reaction risk =
    `|stance_shift| + max(0, anger_shift) + max(0, share_likelihood_shift)`; returns
    `{bubble_id, label, risk_score}` or `None`.
  - `highest_distortion_item` — item maximizing
    `(distortion_level, estimated_reach, id)`; returns its `id`, `echo_type`,
    `distortion_level`, `estimated_reach`, `text`.
- Empty `echo_items` → all three fields `None`.

---

## Interpretation guide

| Metric | Low value means | High value means |
|--------|-----------------|------------------|
| `stance_distribution` | few agents in that stance | that stance dominates the synthetic population |
| `emotion_averages` | calm/muted reactions | strong simulated emotional response |
| `polarization_score` | stances cluster, low intensity | stances split far apart with high intensity |
| `virality_risk_score` | unlikely to spread | high simulated spread potential (intensity + engagement) |
| `frame_sensitivity_score` | framing barely changed outcomes | framing strongly swung stance/trust/share |
| `echo_amplification_index` | echo stage barely amplified | echo stage strongly amplified anger, distrust, sharing, distortion |
| `distortion_drift` | accurate, low-distortion echoes | distorted content reached large audiences |
| `trust_delta` | (negative) trust eroded | (positive) trust grew after echoes |
| `polarization_delta` | population converged | population split further apart |

Read these comparatively across simulation runs and frames, never as absolute
real-world quantities.

> **Reminder:** these are **synthetic indicators** produced by a simulator. They are
> not measurements of real opinion, real virality, or real public sentiment.
