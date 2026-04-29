# EchoGrid AI Handoff

This document is for future models and developers continuing EchoGrid.

## Current Release State

EchoGrid is a working synthetic Streamlit MVP. It supports deterministic mock-mode simulation, bounded Hybrid mode, capped Full LLM sample mode, SQLite persistence, previous-run loading and deletion, CSV/JSON/ZIP exports, guardrail disclaimers, CI/lint configuration, and automated tests.

## Fast Commands

```bash
make install
make test
make smoke
make lint
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
- Added `src.simulation.run_simulation` as the UI-independent application-service layer.
- Added typed `LLMClient.complete_model` validation/retry support for future hybrid mode.
- Added amplification breakdown, final-state metrics, and narrative-risk summary helpers.
- Added `docs/layers.md` to document current layer boundaries.
- Added capped Full LLM sample mode with per-agent/frame calls, concurrency controls, timeouts, deterministic fallback, and persisted LLM diagnostics.
- Split Streamlit setup/dashboard/chart helpers into `src/ui/`.
- Added bounded multi-round echo simulation, media presets, actor toggles, narrative summary, and demo mode.

## Important Constraints

- Keep outputs framed as synthetic. Do not remove export disclaimers.
- Do not treat mock metrics as calibrated research findings.
- Do not implement demographic persuadability ranking or targeting-copy optimization.
- Preserve deterministic behavior for seed-based mock tests.
- Use tests first for behavior changes.

## High-Value Next Work

1. Add a previous-run comparison view using existing loaded simulations.
2. Add scenario-comparison workflows.
3. Add exportable HTML/PDF reports.
4. Add screenshots after a manual Streamlit pass.
5. Add optional graph-based diffusion as a research extension.

## Files To Read First

- `README.md` for user-facing setup and limitations.
- `todo.md` for backlog priorities.
- `docs/architecture.md` and `docs/layers.md` for module responsibilities and layer boundaries.
- `docs/ethics.md` for safety boundaries.
- `tests/test_app_smoke.py` and `tests/test_storage_report.py` for release-critical behavior.
