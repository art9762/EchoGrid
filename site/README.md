# EchoGrid — Promo Site & Interactive Demo

A static, bilingual (EN/RU), dark-tech promo website for **EchoGrid**, an
LLM-assisted synthetic-society simulator. It is a "site visit card": a one-page
landing that explains what EchoGrid is (and is not), how its six-stage pipeline
works, its features and ethics — plus a fully client-side **interactive demo**
that runs a deterministic mock echo-simulation in the browser. No build step, no
framework, no backend — plain HTML/CSS/JS served over HTTP.

> See **[RUNNING.md](RUNNING.md)** for how to serve and deploy.

---

## File map

| File | Purpose | ~Lines |
|------|---------|-------:|
| `index.html` | Landing page: navbar (What/How/Features/Ethics anchors, EN\|RU toggle, GitHub) → hero `<canvas>` → "What it is / is not" → 6-step pipeline → features bento + count-up stats → 7 scenario chips → ethics → "Run it locally" CTA → footer. All copy via `data-i18n` attributes. | 380 |
| `styles.css` | Design tokens (`:root`) + all landing styles: OLED dark theme, glass cards, responsive layout, fonts via Google Fonts `@import`. | 796 |
| `main.js` | Landing logic (ES module): i18n, mobile nav, copy-to-clipboard, hero canvas animation, Motion-based scroll reveals (CDN), count-up stats. | 689 |
| `demo.html` | Interactive demo page: mirrors the navbar/footer, adds a setup panel (event input + scenario chips + sliders), cascade canvas, and results dashboard. Loads `styles.css` then `demo.css` then `demo.js`. | 190 |
| `demo.css` | Demo-specific styles extending the landing design system (setup panel, sliders, chips, metric cards, stance bars). | 503 |
| `demo.js` | Demo logic (ES module, **fully vanilla, zero CDN deps**): i18n, seeded PRNG, mock simulation, cascade canvas, results rendering. | 813 |
| `HANDOFF.md` | Original build/handoff notes. (Its "blocking bug" section is now stale — the reveal logic in `main.js` was rewritten to be failure-proof; see [Landing reveals](#landing-reveals).) | 153 |
| `RUNNING.md` | How to run locally & deploy. | — |
| `README.md` | This file. | — |

---

## Design system

Defined as CSS custom properties in the `:root` block of `styles.css`. The demo
inherits all of them (it loads `styles.css` first). Style is **Dark Mode (OLED)**
with cyan/violet accents and an orange CTA.

```css
:root {
  /* Surfaces */
  --bg-deep:      #050510;                      /* page background */
  --bg-midnight:  #0A0E27;                       /* panels */
  --glass:        rgba(255,255,255,0.04);        /* glass card fill */
  --glass-strong: rgba(255,255,255,0.06);
  --border:       rgba(255,255,255,0.08);
  --border-strong:rgba(255,255,255,0.14);

  /* Accents */
  --cyan:   #38BDF8;   --violet: #8B5CF6;   --orange: #F97316;   /* CTA */
  --green:  #34D399;   --red:    #FB7185;

  /* Text */
  --text:  #E6EAF5;    --muted:  #94A3B8;

  /* Type */
  --font-head: 'Exo', system-ui, sans-serif;          /* headings + body */
  --font-mono: 'Roboto Mono', ui-monospace, monospace; /* labels, metrics */

  --maxw: 1180px;  --radius: 18px;  --radius-sm: 12px;
}
```

- **Glass cards** — the `.glass` class: translucent `--glass` fill, `--border`
  hairline, blur. Used for the navbar, panels, pipeline steps, feature cards,
  ethics block, run card, and every demo panel.
- **Fonts** — Exo + Roboto Mono, loaded via a single Google Fonts `@import` at
  the top of `styles.css`. They fall back to `system-ui` / `ui-monospace` if
  blocked.

To **retheme**, edit the token values in `:root` — the cyan/violet canvas colors
are also hard-coded as RGB arrays in the JS (`COL_CYAN = [56,189,248]`,
`COL_VIOLET = [139,92,246]` in `main.js` and `demo.js`); update those too if you
change `--cyan` / `--violet`.

---

## Internationalization (i18n)

Both pages are fully bilingual (English + Russian) with no page reload.

**How it works:**

- Any translatable element carries a `data-i18n="key"` attribute; the JS sets
  its `textContent` from a dictionary. Inputs use `data-i18n-placeholder="key"`
  (demo only) for placeholder text.
- The dictionaries are plain JS objects in the scripts:
  - **Landing** — `const i18n = { en: {…}, ru: {…} }` in `main.js`.
  - **Demo** — `const demoI18n = { en: {…}, ru: {…} }` in `demo.js`, plus a
    separate `SCENARIOS = { en, ru }` map for the seven scenario labels. The
    demo dictionary also re-includes the shared `nav.*` and `footer.*` keys so
    the mirrored navbar/footer translate.
- The chosen language persists to `localStorage` under the key
  **`echogrid-lang`** — the *same key on both pages*, so a choice on the landing
  carries into the demo and back.
- The `EN|RU` buttons (`.lang-btn[data-lang]`) call `setLang()`, which swaps all
  text, sets `<html lang>`, updates `aria-pressed`, and (in the demo)
  re-renders any already-rendered results in the new language.

**Add a new string:** add the same `key` to both `en` and `ru` in the relevant
dictionary, then put `data-i18n="key"` on the element.

**Add a new language** (e.g. `de`): add a `de: {…}` block with every key to the
dictionary (and to `SCENARIOS` in the demo), then add a `<button data-lang="de"
class="lang-btn">DE</button>` to the `.lang-toggle` in both HTML files.

---

## The interactive demo

The demo (`demo.html` + `demo.js` + `demo.css`) runs **entirely in the browser**
— no server-side compute, no real opinions, no network calls. It is a
*deterministic mock*, not real EchoGrid.

**Flow:** setup panel (free-text event **or** one of 7 scenario chips +
population slider `100–1000` step 50 + echo-rounds slider `1–3`) → press **Run
simulation** → seeded synthetic population is simulated → animated echo-cascade
`<canvas>` plays one ripple per round → results dashboard renders.

**How the mock works (high level, all in `demo.js`):**

- **Seeded PRNG** — `xmur3()` hashes the string `event + "::" + population +
  "::" + rounds` into a seed for `mulberry32()`. So the *same* inputs always
  produce *identical* output (re-running an event reproduces it exactly).
- **Media frame model** — `FRAME_EFFECTS` defines six framings
  (`neutral`, `technocratic`, `progressive`, `populist`, `skeptical`,
  `tabloid_outrage`), each with `support` / `anger` / `trust` deltas. Each
  synthetic agent is assigned an event-tilted media diet over these frames.
- **Per-agent pass** — each agent gets a baseline disposition, reacts to its
  frame, then goes through `rounds` of bounded echo (diminishing per-round
  nudge along its lean). Final `support` buckets into a **5-point stance scale**
  (`ss` strongly support → `so` strongly oppose).
- **Metrics** — five before→after metrics are aggregated:
  **Amplification, Trust, Anger, Distortion, Polarization** (the `metrics`
  object; amplification & distortion derive from opinion *spread*, polarization
  from mass at the two extremes).
- **Output** — animated stance-distribution bars, before→after metric cards
  with count-up, and a handful of anodyne synthetic comment templates, all under
  a **"Synthetic — not real opinions"** tag. Nothing here measures or predicts
  real public opinion.

---

## Editing common things

| I want to… | Do this |
|------------|---------|
| **Add a nav link** | Add an `<a … data-i18n="nav.x">` inside `.nav-links` in **both** `index.html` and `demo.html`, then add the `nav.x` key to the `en`/`ru` dicts in `main.js` *and* `demo.js`. |
| **Add a scenario chip** | The demo allows 1–7 via `data-scenario`. To add an 8th: add `<li><button … data-scenario="8">…</button></li>` to `#demo-chips` in `demo.html`; add `scen.8` to `SCENARIO_KEYS` and `SCENARIOS` (en+ru) in `demo.js`; add the matching landing chip + `scen.8` to `i18n` in `main.js`/`index.html`. |
| **Change accent colors** | Edit `--cyan` / `--violet` / `--orange` in `:root` (`styles.css`). For the canvas glow, also update the `COL_CYAN` / `COL_VIOLET` RGB arrays in `main.js` and `demo.js`. |
| **Change the slider ranges** | Edit the `min` / `max` / `step` on `#demo-pop` (population) and `#demo-rounds` (echo rounds) in `demo.html`. |
| **Swap the GitHub / Docs links** | They are `href="#"` placeholders in `index.html` and `demo.html` — replace with the real URLs. |
| **Edit a metric formula** | See the `simulate()` function and the `metrics` object in `demo.js`. |

---

### Landing reveals (note)

`main.js`'s `initMotion()` dynamically imports `motion@11.18.0` from jsDelivr for
scroll-reveal animations. The logic is **failure-proof**: each element is hidden
inline *only the instant before* it animates, the final visible state is
explicitly committed, and a watchdog `setTimeout` force-shows content if the
animation never resolves. If the CDN is unreachable or Motion is unavailable,
the `import()` is caught and all content simply shows at full opacity. (This
supersedes the "blocking bug" described in `HANDOFF.md`, which predates the
rewrite.)

---

For serving and deployment instructions, see **[RUNNING.md](RUNNING.md)**.
