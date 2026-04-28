# EchoGrid TODO

Текущий статус: локальный MVP уже запускается в mock mode, имеет модульную структуру, Streamlit dashboard, SQLite storage, exports, базовую аналитику, echo simulation и provider scaffolding для Anthropic, Gemini и OpenAI. Этот файл описывает, что нужно доделать до уверенного conference-grade MVP.

## P0 - стабилизировать текущий MVP

- [ ] Пройти полный ручной smoke-test в Streamlit:
  - открыть `http://localhost:8501`
  - запустить каждый из 7 demo scenarios
  - проверить population sizes `50`, `300`, `1000`
  - проверить выбор 1, 3, 6 framings
  - проверить включенный и выключенный echo simulation
  - проверить все tabs без runtime errors
  - проверить CSV/JSON downloads

- [ ] Исправить найденные UI/runtime ошибки после smoke-test.

- [ ] Вынести dashboard helper-функции из `app.py` в отдельные модули:
  - `src/dashboard.py` или `src/ui/dashboard.py`
  - `src/ui/tables.py`
  - `src/ui/charts.py`

- [x] Заменить дублирующиеся dataframe helpers в `app.py` на функции из `src/report.py`.

- [x] Добавить базовый app smoke test:
  - импорт `app.py`
  - вызов `_run_simulation(...)` на маленькой популяции
  - проверка, что возвращаются agents, reactions, echo_result, simulation_id

- [x] Добавить performance check для mock mode:
  - `1000` agents
  - `4` frames
  - `1` echo round
  - целевой runtime: комфортно для локального демо

- [x] Проверить, что SQLite-файл не коммитится и создается в `data/echogrid.sqlite3`.

## P0 - привести интерфейс к demo-grade качеству

- [ ] Уплотнить первый экран:
  - четкий setup в sidebar
  - в main area сразу видны статус, scenario summary и ключевые метрики последнего run

- [ ] Улучшить visual hierarchy:
  - меньше длинных таблиц в первых tabs
  - ключевые метрики выше таблиц
  - таблицы ниже как inspectable detail

- [ ] Добавить consistent chart styling:
  - единая палитра для stance
  - единая палитра для emotions
  - читаемые labels
  - не перегружать графики цветом

- [ ] Добавить табличные фильтры:
  - reactions by frame
  - reactions by stance
  - echo items by echo_type
  - echo items by target_bubble
  - comments by stance/frame/bubble

- [x] Добавить progress/status messages при запуске симуляции:
  - generating population
  - generating frames
  - running reactions
  - generating echo items
  - running echo reactions
  - saving/exporting

- [ ] Добавить clear empty states:
  - echo disabled
  - no filtered rows
  - no previous simulation loaded

## P1 - Hybrid LLM mode

- [x] Добавить prompt loader:
  - файл: `src/prompts.py` или `src/utils.py`
  - функция: `load_prompt(name: str) -> str`
  - тест: prompt exists and contains JSON instruction

- [x] Расширить `src/llm_client.py`:
  - отдельные методы для `generate_reaction_json`
  - `generate_echo_items_json`
  - `generate_echo_reaction_json`
  - retry once on invalid JSON
  - structured validation through Pydantic schemas

- [x] Добавить provider routing:
  - `mock`
  - `anthropic` через Trinity
  - `gemini`
  - `openai` через Trinity

- [x] Добавить UI mode selector:
  - `Mock`
  - `Hybrid`

- [x] Реализовать Hybrid mode:
  - population остается mock
  - initial reactions остаются mock для всех agents
  - LLM генерирует improved framings
  - LLM генерирует echo items
  - LLM генерирует representative comments для selected segments

- [ ] Реализовать Full LLM small sample mode:
  - ограничить population до безопасного лимита, например `25-100`
  - показывать предупреждение о стоимости
  - не запускать тысячи вызовов без явного подтверждения

- [x] Добавить cost estimator перед запуском LLM:
  - estimated input tokens
  - estimated output tokens
  - estimated calls
  - rough USD estimate by provider/model

- [x] Добавить model presets:
  - Anthropic cheap: `claude-haiku-4-5-20251001`
  - Anthropic balanced: `claude-sonnet-4-6`
  - Gemini cheap: `gemini-2.5-flash-lite`
  - Gemini balanced: `gemini-2.5-flash`
  - OpenAI cheap: `gpt-5.4-nano`
  - OpenAI balanced: `gpt-5.4-mini`

- [ ] Добавить concurrency controls:
  - `max_workers`
  - request timeout
  - graceful per-call failure
  - progress counter

- [ ] Добавить LLM error storage:
  - invalid JSON
  - provider timeout
  - missing API key
  - rate limit
  - partial simulation continues

## P1 - сделать prompt-и сильнее

- [x] Переписать `reaction_prompt.txt` под strict schema:
  - перечислить все поля
  - указать допустимые enum values
  - указать диапазоны `0-100`
  - запретить markdown
  - запретить persuasion targeting

- [x] Переписать `echo_generation_prompt.txt`:
  - request array of echo items
  - require 1-3 items per media actor
  - require realistic distortions
  - require distortion_level to match claim strength

- [x] Переписать `echo_reaction_prompt.txt`:
  - require stance_shift range
  - require trust_shift range
  - include bubble correction_resistance
  - include source credibility

- [x] Добавить `framing_prompt.txt` schema contract.

- [x] Добавить tests для prompt coverage:
  - каждое поле целевой схемы упомянуто в prompt
  - prompt содержит ethical limitations
  - prompt содержит `Return JSON only`

## P1 - расширить analytics

- [ ] Добавить final-state analytics:
  - final stance distribution
  - final trust average
  - final share likelihood average
  - final emotional intensity estimate

- [ ] Улучшить `polarization_delta`:
  - сравнивать signed stance distribution before/after
  - учитывать emotional intensity

- [ ] Улучшить `echo_amplification_index`:
  - нормализовать компоненты
  - явно показывать contribution breakdown

- [ ] Добавить `frame_sensitivity_score`:
  - насколько разные framings меняют stance/emotions/share

- [ ] Добавить `narrative_risk_summary`:
  - top risky echo types
  - top affected bubbles
  - top distortion sources

- [ ] Добавить `correction_effectiveness` в UI:
  - expert corrections vs official clarifications
  - trust_shift
  - anger_shift
  - share_likelihood_shift

- [ ] Добавить `unexpected_segments` в UI:
  - сегменты с неожиданно высокой anger/share/distrust

## P1 - storage и загрузка прошлых прогонов

- [ ] Добавить список прошлых simulations в sidebar.

- [x] Добавить `load_simulation(db_path, simulation_id)`.

- [x] Добавить tests для загрузки:
  - save simulation
  - load simulation
  - loaded counts match saved counts

- [ ] Добавить metadata в `simulations` table:
  - event title
  - country
  - topic
  - population_size
  - seed
  - provider
  - created_at

- [ ] Добавить кнопку delete previous simulation.

- [ ] Добавить export ZIP:
  - agents.csv
  - reactions.csv
  - echo_items.csv
  - echo_reactions.csv
  - summary.json

## P1 - ethical guardrails

- [x] Добавить central guardrails module:
  - `src/guardrails.py`
  - prohibited use text
  - disallowed request classifier helpers

- [ ] Добавить UI warning перед LLM mode:
  - synthetic simulation only
  - not polling
  - not targeting
  - not persuasion optimization

- [x] Добавить refusal behavior для опасных запросов:
  - "find best message to manipulate group X"
  - election targeting
  - vulnerable group targeting
  - harassment or radicalization

- [x] Добавить tests для guardrails:
  - manipulative targeting blocked
  - research framing allowed
  - export still contains disclaimer

- [x] Вшить disclaimer в summary JSON.

- [x] Вшить disclaimer в CSV/JSON export metadata.

## P1 - качество mock mode

- [ ] Улучшить population coherence:
  - occupation vs age
  - family_status vs age
  - income vs education
  - media_diet vs trust

- [x] Добавить age groups для Segment Explorer:
  - `18-24`
  - `25-34`
  - `35-49`
  - `50-64`
  - `65+`

- [x] Добавить institutional trust buckets:
  - low
  - medium
  - high

- [x] Добавить social_bubble в reactions dataframe.

- [ ] Улучшить `run_agent_reaction`:
  - topic-specific effects
  - source-specific trust
  - media-diet-specific framing sensitivity
  - more varied comments

- [ ] Улучшить `generate_echo_items`:
  - 1-3 items per actor option
  - meme captions
  - official clarifications
  - partisan interpretations
  - expert corrections tied to distortion

- [ ] Сделать deterministic seed trace:
  - same seed => exact same result
  - different seed => plausible variation

## P2 - multi-round echo simulation

- [ ] Обобщить `run_echo_simulation` на `echo_rounds > 1`.

- [ ] Добавить `RoundSummary` generation.

- [ ] Добавить timeline по rounds:
  - round 0 original event
  - round 1 frames
  - round 2 initial reactions
  - round 3 echo items
  - round 4 echo reactions
  - round 5 new echo items
  - etc.

- [ ] Добавить decay/saturation:
  - repeated outrage has diminishing returns
  - corrections can reduce distortion but may not persuade resistant bubbles

- [ ] Добавить tests:
  - two echo rounds produce two sets of echo items
  - round numbers are correct
  - final states update across rounds

## P2 - richer media ecosystem

- [ ] Добавить actor toggles в UI:
  - include/exclude tabloids
  - include/exclude experts
  - include/exclude government source
  - include/exclude influencers

- [ ] Добавить media actor presets:
  - low-trust environment
  - high-institutional-trust environment
  - highly partisan environment
  - expert-heavy environment

- [ ] Добавить actor audience matching:
  - echo items reach bubbles based on affinity
  - credibility interacts with trust profile

- [ ] Добавить charts:
  - credibility vs reach
  - sensationalism vs distortion
  - actor contribution to virality

## P2 - UI polish for conference demo

- [ ] Сделать demo script:
  - one recommended scenario
  - one recommended population size
  - one recommended talking path through tabs

- [ ] Добавить "Demo mode" button:
  - auto-select scenario
  - auto-run 300 agents
  - auto-select 4 frames
  - echo enabled

- [ ] Добавить narrative summary tab:
  - "What happened"
  - "Where amplification appeared"
  - "Which bubbles shifted"
  - "Which corrections helped"

- [ ] Добавить visual timeline cards вместо только таблиц.

- [ ] Добавить readable representative comments:
  - support
  - oppose
  - neutral
  - confused
  - high anger
  - high distrust

- [ ] Добавить persistent "Synthetic, not polling" footer.

- [ ] Проверить mobile/tablet layout.

## P2 - docs and presentation material

- [ ] Добавить `docs/architecture.md`.

- [ ] Добавить `docs/ethics.md`.

- [ ] Добавить `docs/demo-script.md`.

- [ ] Добавить screenshots в README.

- [ ] Добавить cost guide:
  - mock
  - hybrid
  - full LLM small sample
  - provider comparison

- [ ] Добавить limitations подробнее:
  - no prediction
  - no calibration
  - synthetic personas
  - model bias
  - prompt sensitivity
  - stochastic outputs

## P2 - developer experience

- [ ] Добавить `Makefile`:
  - `make install`
  - `make test`
  - `make run`
  - `make clean`

- [ ] Добавить `pyproject.toml` для pytest config и tool settings.

- [ ] Добавить formatting/linting:
  - ruff
  - black или ruff format

- [ ] Добавить CI позже:
  - install
  - pytest
  - basic import check

- [ ] Добавить type checking позже:
  - mypy или pyright

## P3 - research-grade extensions later

- [ ] Graph-based diffusion вместо simple bubbles.

- [ ] Calibration hooks для внешних datasets без claims of prediction.

- [ ] Scenario comparison:
  - same event, different framing
  - same framing, different media ecosystem
  - same event, different country preset

- [ ] Synthetic panel memory:
  - agents retain prior exposure
  - repeated source trust changes over time

- [ ] Export full report as HTML/PDF.

- [ ] Cloud deployment option.

- [ ] Multi-user project workspace.

## Suggested next execution order

1. P0 smoke-test dashboard manually.
2. Fix visible/runtime issues from Streamlit.
3. Refactor `app.py` into UI modules.
4. Add Hybrid LLM mode for frames, echo items, and representative comments.
5. Add cost estimator and provider/model selector.
6. Add load previous simulation.
7. Polish dashboard visuals for conference demo.
8. Add guardrails module and tests.
9. Add demo script and screenshots.
