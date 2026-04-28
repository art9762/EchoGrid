# EchoGrid AI Handoff

This document is for future models and developers continuing EchoGrid.

## Current Release State

EchoGrid is a working synthetic Streamlit MVP. It supports deterministic mock-mode simulation, SQLite persistence, previous-run loading and deletion, CSV/JSON/ZIP exports, guardrail disclaimers, and automated tests. API provider clients are scaffolded, but full LLM simulation is not enabled in the release workflow.

## Fast Commands

```bash
make install
make test
make smoke
make run
```

The app entrypoint is `app.py`. The test suite does not require API keys.

## Recent Release-Hardening Changes

- Added SQLite metadata to saved simulations.
- Added `list_simulations` and `delete_simulation`.
- Added sidebar loading/deletion for previous runs.
- Added progress messages during simulation runs.
- Added filters for initial reactions, echo items, and comments.
- Added full ZIP export through `src.report.simulation_export_zip`.
- Added `Makefile`, `pyproject.toml`, architecture notes, ethics notes, and demo script.

## Important Constraints

- Keep outputs framed as synthetic. Do not remove export disclaimers.
- Do not treat mock metrics as calibrated research findings.
- Do not implement demographic persuadability ranking or targeting-copy optimization.
- Preserve deterministic behavior for seed-based mock tests.
- Use tests first for behavior changes.

## High-Value Next Work

1. Split `app.py` into focused UI modules once the dashboard grows further.
2. Add a previous-run comparison view using existing loaded simulations.
3. Add final-state analytics charts from `EchoSimulationResult.final_reaction_state_by_agent`.
4. Add a cost estimator before any LLM mode.
5. Add CI with `make test`.
6. Add screenshots after a manual Streamlit pass.

## Files To Read First

- `README.md` for user-facing setup and limitations.
- `todo.md` for backlog priorities.
- `docs/architecture.md` for module responsibilities.
- `docs/ethics.md` for safety boundaries.
- `tests/test_app_smoke.py` and `tests/test_storage_report.py` for release-critical behavior.
