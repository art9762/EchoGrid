# Release Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Bring EchoGrid from a working synthetic MVP to a release-ready local demo with tested storage, exports, dashboard polish, and developer handoff documentation.

**Architecture:** Keep the deterministic mock pipeline intact and harden the release surface around it. Add persistence affordances in `src.storage`, export bundling in `src.report`, small Streamlit UX improvements in `app.py`, and developer-facing docs without changing the core synthetic simulation model.

**Tech Stack:** Python, Streamlit, Pandas, Plotly, Pydantic, SQLite, Pytest.

---

### Task 1: Storage Release Utilities

**Files:**
- Modify: `src/storage.py`
- Modify: `tests/test_storage_report.py`

- [x] **Step 1: Write failing tests**

Add a test that saves a synthetic run, verifies `list_simulations` returns title, country, topic, population size, seed, and provider, then deletes the run and confirms `load_simulation` raises `KeyError`.

- [x] **Step 2: Run red test**

Run: `.venv/bin/python -m pytest tests/test_storage_report.py -q`

Expected red result: import error for missing `list_simulations` or `delete_simulation`.

- [x] **Step 3: Implement storage functions**

Add metadata to `save_simulation`, add `list_simulations(db_path, limit=25)`, and add `delete_simulation(db_path, simulation_id)`.

- [x] **Step 4: Run green test**

Run: `.venv/bin/python -m pytest tests/test_storage_report.py -q`

Expected green result: storage tests pass.

### Task 2: ZIP Export Bundle

**Files:**
- Modify: `src/report.py`
- Modify: `tests/test_storage_report.py`
- Modify: `app.py`

- [x] **Step 1: Write failing tests**

Add a test that calls `simulation_export_zip` with a synthetic simulation dict and verifies the archive contains `README.txt`, `summary.json`, `agents.csv`, `reactions.csv`, `echo_items.csv`, and `echo_reactions.csv`.

- [x] **Step 2: Run red test**

Run: `.venv/bin/python -m pytest tests/test_storage_report.py -q`

Expected red result: import error for missing `simulation_export_zip`.

- [x] **Step 3: Implement report helper**

Build the archive with `zipfile.ZipFile`, existing dataframe helpers, and export disclaimers.

- [x] **Step 4: Wire Streamlit download**

Add `Export full ZIP` in the export tab.

- [x] **Step 5: Run green test**

Run: `.venv/bin/python -m pytest tests/test_storage_report.py tests/test_app_smoke.py -q`

Expected green result: storage/report and app smoke tests pass.

### Task 3: Dashboard Release Polish

**Files:**
- Modify: `app.py`
- Modify: `tests/test_app_smoke.py`

- [x] **Step 1: Preserve smoke coverage**

Keep `_run_simulation` compatible with existing tests while adding optional provider metadata and progress callbacks.

- [x] **Step 2: Add previous-run controls**

Use `list_simulations`, `load_simulation`, and `delete_simulation` inside the sidebar.

- [x] **Step 3: Add filters and clearer empty states**

Add frame/stance filters for initial reactions, echo type and target-bubble filters for echo items, and stance/frame/bubble filters for comments.

- [x] **Step 4: Run smoke tests**

Run: `.venv/bin/python -m pytest tests/test_app_smoke.py tests/test_storage_report.py -q`

Expected green result: app smoke and release export tests pass.

### Task 4: Developer Experience And Documentation

**Files:**
- Create: `Makefile`
- Create: `pyproject.toml`
- Create: `docs/architecture.md`
- Create: `docs/ethics.md`
- Create: `docs/demo-script.md`
- Create: `docs/AI_HANDOFF.md`
- Modify: `tests/test_project_structure.py`
- Modify: `README.md`
- Modify: `todo.md`

- [x] **Step 1: Write failing structure tests**

Add tests that require Makefile, pyproject, and the release docs.

- [x] **Step 2: Run red test**

Run: `.venv/bin/python -m pytest tests/test_project_structure.py -q`

Expected red result: missing release developer files and docs.

- [x] **Step 3: Add files**

Create command targets, pytest config, architecture notes, ethics notes, demo script, and handoff notes. Keep all wording clear that EchoGrid is synthetic.

- [x] **Step 4: Update README and todo**

Document make commands, previous-run loading, ZIP export, and completed release items.

### Task 5: Final Verification

**Files:**
- No production edits expected.

- [x] **Step 1: Run full tests**

Run: `.venv/bin/python -m pytest -q`

Observed green result: `55 passed`.

- [x] **Step 2: Run a local Streamlit smoke check**

Run: `.venv/bin/streamlit run app.py --server.headless true`

Observed result: port `8501` was already in use, the app started on `8502`, and `curl -I http://localhost:8502` returned `HTTP/1.1 200 OK`.

- [x] **Step 3: Review git diff**

Run: `git status --short` and inspect changed files for unrelated edits.

Observed result: changed files are scoped to release hardening, docs, tests, and developer tooling.
