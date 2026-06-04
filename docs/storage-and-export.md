# Storage and Export

Part of the EchoGrid docs. EchoGrid produces **SYNTHETIC** output; the synthetic-simulation disclaimer is embedded in every export artifact (see [Disclaimers in exports](#disclaimers-in-exports)). See also [Data model](data-model.md) and [Configuration](configuration.md).

This document covers two source modules:

- `src/storage.py` — SQLite persistence for completed simulation runs.
- `src/report.py` — DataFrame conversion, JSON summary, and ZIP export.

---

## Where data lives on disk

Paths are defined in `src/config.py`:

| Constant | Path | Purpose |
|----------|------|---------|
| `DATA_DIR` | `data/` | Root for all run data. |
| `database_path` (`AppSettings`) | `data/echogrid.sqlite3` | SQLite database holding all persisted runs. Overridable via the `ECHOGRID_DATABASE_PATH` environment variable. |
| `SIMULATIONS_DIR` | `data/simulations/` | Per-run simulation files. |
| `EXPORTS_DIR` | `data/exports/` | Generated export bundles. |

`init_database()` creates the parent directory of the database path (`path.parent.mkdir(parents=True, exist_ok=True)`) before connecting, so the `data/` tree is created on first save.

---

## SQLite persistence (`storage.py`)

All persistence is JSON-payload based: every domain object is serialized to a `payload_json` column via `model_dump(mode="json")` and rehydrated with the matching Pydantic model's `model_validate_json`. Helper `_json(model)` does the dump; `_load_one` / `_load_many` do the load.

### Schema

The database has one parent table, `simulations`, plus 9 child tables. Every child table is keyed on `simulation_id` (FK conceptually back to `simulations`).

| Table | Columns | Primary key | JSON payload (`payload_json`) holds |
|-------|---------|-------------|-------------------------------------|
| `simulations` | `simulation_id`, `created_at`, `payload_json` | `simulation_id` | Run-level metadata dict (see below) — **not** a single domain model. |
| `events` | `simulation_id`, `payload_json` | `simulation_id` | One `NewsEvent`. |
| `agents` | `simulation_id`, `agent_id`, `payload_json` | (`simulation_id`, `agent_id`) | One `AgentProfile` per row. |
| `frames` | `simulation_id`, `frame_id`, `payload_json` | (`simulation_id`, `frame_id`) | One `NewsFrame` per row. |
| `reactions` | `simulation_id`, `agent_id`, `frame_id`, `payload_json` | none | One `AgentReaction` (initial reaction) per row. |
| `media_actors` | `simulation_id`, `actor_id`, `payload_json` | (`simulation_id`, `actor_id`) | One `MediaActor` per row. |
| `social_bubbles` | `simulation_id`, `bubble_id`, `payload_json` | (`simulation_id`, `bubble_id`) | One `SocialBubble` per row. |
| `echo_items` | `simulation_id`, `echo_item_id`, `payload_json` | (`simulation_id`, `echo_item_id`) | One `EchoItem` per row (echo phase only). |
| `echo_reactions` | `simulation_id`, `agent_id`, `echo_item_id`, `payload_json` | none | One `EchoReaction` (second-round) per row. |
| `echo_round_summaries` | `simulation_id`, `round_number`, `payload_json` | none | One `RoundSummary` per row. |

The 9 child tables are enumerated in `CHILD_TABLES`; `save_simulation` and `delete_simulation` iterate this list when clearing rows for a `simulation_id`.

#### `simulations.payload_json` metadata

This is the run header, not a domain model. Built in `save_simulation`, it contains:

- Identity / timing: `simulation_id`, `created_at`.
- Event fields: `event_title`, `country`, `topic`, `source_type`.
- Counts: `population_size`, `agent_count`, `frame_count`, `reaction_count`, `echo_item_count`.
- Run config: `seed`, `provider`, `run_mode`.
- `bubble_assignments` — `dict[bubble_id, list[agent_id]]`.
- `amplification_metrics` — from the echo result (empty `{}` when no echo run).
- `final_reaction_state_by_agent` — per-agent final reaction state, JSON-dumped (empty when no echo run).
- `representative_comments` — list of `RepresentativeComment` dumps.
- `llm_errors` — list of `LLMGenerationError` dumps.

### Functions

- **`init_database(db_path)`** — creates the parent dir, then runs every statement in `TABLE_DEFINITIONS` (`create table if not exists ...`). Idempotent.
- **`save_simulation(...)`** — the main write path. Calls `init_database`, derives the `simulation_id` (uses `echo_result.simulation_id` if present, otherwise `sim-{stable_seed(...) % 1_000_000:06d}`), builds the metadata payload, then in one connection: deletes any existing rows for that id across all `CHILD_TABLES`, `insert or replace` into `simulations` and `events`, and `executemany` inserts for `agents`, `frames`, `reactions`, `media_actors`, `social_bubbles`. When an `EchoSimulationResult` is supplied it also inserts `echo_items`, `echo_reactions`, and `echo_round_summaries`. Returns the `simulation_id`.
- **`list_simulations(db_path, limit=25)`** — returns `[]` if the DB file is absent; otherwise reads `simulations` ordered by `created_at desc` (limited), and projects each metadata payload into a compact summary dict (id, created_at, event_title, country, topic, source_type, population_size, seed, provider, run_mode, frame/reaction/echo counts). Reads only the parent table — no child rows.
- **`delete_simulation(db_path, simulation_id)`** — returns `False` if the DB is absent; otherwise deletes the id's rows from all child tables and from `simulations`. Returns `True` if a `simulations` row was removed (`cursor.rowcount > 0`).
- **`load_simulation(db_path, simulation_id)`** — full rehydration. Reads the metadata payload (raises `KeyError` if missing), loads the single `events` row plus the many-rows tables back into their Pydantic models, and reconstructs an `EchoSimulationResult` only when any of `echo_items` / `echo_reactions` / `round_summaries` exist (pulling `final_reaction_state_by_agent` and `amplification_metrics` from metadata). Returns a dict with the event, agents, frames, reactions (also aliased as `initial_reactions`), media_actors, bubbles, `bubble_assignments`, `echo_result`, `run_mode`, `provider` (coerced to `LLMProvider` when valid, else the raw string), `representative_comments`, `llm_errors`, and the raw `metadata`.

### Round-trip

A run round-trips as: domain objects → `_json(model)` (`model_dump(mode="json")` + `json.dumps`) → `payload_json` columns via `save_simulation`, then `payload_json` → `model_validate_json` → domain objects via `load_simulation`. Echo-phase data is conditional in both directions — present only when the run included an echo simulation. Run-level aggregates (`bubble_assignments`, `amplification_metrics`, `final_reaction_state_by_agent`, comments, errors) live only in the `simulations` metadata payload, not in child tables.

---

## Reporting and export (`report.py`)

### DataFrame converters

| Function | Input | Output / notable transforms |
|----------|-------|-----------------------------|
| `agents_to_dataframe(agents)` | `list[AgentProfile]` | Adds derived `age_group` and `institutional_trust_bucket` columns. |
| `reactions_to_dataframe(reactions, bubble_assignments=None)` | `list[AgentReaction]` | Explodes the `emotions` dict into `emotion_<key>` columns, adds `emotional_intensity`, and (when assignments given) a `social_bubble` column resolved per agent. |
| `echo_items_to_dataframe(echo_items)` | `list[EchoItem]` | Direct model dump to rows. |
| `echo_reactions_to_dataframe(echo_reactions)` | `list[EchoReaction]` | Explodes `emotion_shift` into `<key>_shift` columns. |

### `simulation_summary_json(...)`

Returns an indented JSON string. Payload includes `export_metadata("summary")` (which carries the disclaimers), `run_mode`, `provider`, the dumped `event` and `frames`, `initial_metrics` (stance distribution, emotion averages, trust average, share-likelihood distribution — from `src/analytics`), and — only when an echo result is present — `amplification_metrics`, `amplification_breakdown`, `final_state_metrics`, and `narrative_risk_summary`. It also reports `echo_item_count`, `echo_reaction_count`, `representative_comments`, and `llm_errors`.

### `dataframe_to_csv_export(frame, export_name)`

Prepends a 3-line comment header before `frame.to_csv(index=False)`:

```
# EchoGrid export: <export_name>
# <synthetic_simulation_disclaimer>
# <ethical_use_disclaimer>
```

So every CSV a user receives is self-labeling: the export name plus both disclaimers from `src/config.py`. `export_metadata(export_name)` is the source of these strings.

### `simulation_export_zip(simulation)`

Builds an in-memory `ZIP_DEFLATED` archive (via `BytesIO`) and returns its bytes. Contents:

| Artifact | Source | Always present? |
|----------|--------|-----------------|
| `README.txt` | `_archive_readme()` — bundle description + both disclaimers + per-file legend | Yes |
| `summary.json` | `simulation_summary_json(...)` | Yes |
| `agents.csv` | `agents_to_dataframe(agents)` | Yes |
| `reactions.csv` | `reactions_to_dataframe(initial_reactions, bubble_assignments)` | Yes |
| `media_actors.csv` | DataFrame of `MediaActor` dumps | Yes |
| `social_bubbles.csv` | DataFrame of `SocialBubble` dumps | Yes |
| `echo_items.csv` | `echo_items_to_dataframe(...)` | Only when `echo_result` present |
| `echo_reactions.csv` | `echo_reactions_to_dataframe(...)` | Only when `echo_result` present |

`bubble_assignments` is read from `simulation["bubble_assignments"]` (falling back to `simulation["assignments"]`, then `{}`). All CSVs pass through `dataframe_to_csv_export`, so each carries the disclaimer header.

### Export file structure a user receives

A downloaded bundle (a single `.zip`) unpacks to:

```
README.txt          synthetic + ethical disclaimers, file legend
summary.json        event, frames, initial + echo metrics, comments, errors
agents.csv          synthetic agent profiles (+ age_group, trust bucket)
reactions.csv       initial synthetic reactions (emotion_* cols, social_bubble)
media_actors.csv    media ecosystem actors used in the run
social_bubbles.csv  social bubble definitions used in the run
echo_items.csv      generated echo items        (echo runs only)
echo_reactions.csv  second-round reactions      (echo runs only)
```

---

## Disclaimers in exports

`SYNTHETIC_SIMULATION_DISCLAIMER` and `ETHICAL_USE_DISCLAIMER` (defined in `src/config.py`) are surfaced in **every** export path: the `summary.json` `export_metadata`, the header of every CSV, and `README.txt`. EchoGrid output is synthetic — not a real poll — and exports state this on their face. See [Configuration](configuration.md) for the disclaimer text.
