# EchoGrid Promo Landing — Handoff

**Date:** 2026-06-03
**Status:** Built and visually verified. **One blocking bug** (scroll-reveal
leaves most of the page invisible). Everything else works.

---

## What was built

A static, bilingual (EN/RU), dark-tech one-page promo landing ("site visit
card") for EchoGrid. No build step — plain files, hostable on GitHub Pages.

```
site/
  index.html   (379 lines)  — markup, all copy via data-i18n attributes
  styles.css   (786 lines)  — dark OLED theme, glass cards, responsive
  main.js      (604 lines)  — i18n, hero canvas, Motion reveals
```

**Design system** (from the `ui-ux-pro-max` skill):
- Style: Dark Mode (OLED). Background `#050510`, panels `#0A0E27`,
  glass `rgba(255,255,255,0.04)` with `0.08` borders.
- Accents: cyan `#38BDF8`, violet `#8B5CF6`, CTA orange `#F97316`.
  Text `#E6EAF5` / muted `#94A3B8`.
- Fonts: Exo (headings) + Roboto Mono (labels/metrics), Google Fonts @import.

**Spec:** `docs/superpowers/specs/2026-06-03-promo-landing-design.md`

**Sections (in order):** floating glass navbar (wordmark · What/How/Features/
Ethics anchors · EN|RU toggle · GitHub button) → hero with animated canvas →
What it IS vs IS NOT (two glass panels) → 6-step pipeline → features bento grid
with count-up stats (1000 / 7 / 3 / 5) → 7 demo-scenario mono chips → ethics
(allowed vs disallowed) → "Run it locally" CTA with copyable
`streamlit run app.py` → footer (MIT + synthetic-output disclaimer).

---

## What works (verified in headless Chromium / Playwright)

- ✅ **i18n EN↔RU**: toggle flips `<html lang>`, swaps all `data-i18n` text,
  persists to `localStorage["echogrid-lang"]`, no reload. RU copy is
  hand-written and fluent (not machine-literal).
- ✅ **Hero**: canvas node-grid with echo ripples renders, neon gradient
  headline, dual CTAs. No console errors.
- ✅ **Layout/colors/typography**: matches the spec exactly (confirmed via
  `prefers-reduced-motion` render, which bypasses the bug — see below).
- ✅ **Responsive**: 375px shows no horizontal scroll
  (`scrollWidth == clientWidth == 375`).
- ✅ **Copy-to-clipboard** on the run command, with `execCommand` fallback.
- ✅ **Accessibility**: skip-link, focus rings, aria-labels on icon buttons,
  44px mobile toggle.

Reference screenshots from verification (regenerate if needed): the
reduced-motion renders (`rm-what.png`, `ru-what.png`) show the intended
result — full sections, glass cards, correct RU translation.

---

## ⚠️ Blocking bug: most of the page is invisible on a normal visit

**Symptom:** With default settings (motion enabled), the hero renders but
**everything below it is blank**. On load, 22 of 27 `.reveal` blocks are stuck
at `opacity:0`. Natural wheel-scrolling does NOT reveal them.

**Why it happens (root cause):**

`main.js` → `initMotion()` (around lines 496–552):

1. Line 504: `import("https://cdn.jsdelivr.net/npm/motion@latest/+esm")` —
   **succeeds** (confirmed: `data-anim="on"` only gets set *after* a successful
   import, and it WAS set).
2. Line 514: `document.documentElement.setAttribute("data-anim", "on")`.
   CSS then forces `[data-anim="on"] .reveal { opacity: 0 }` — i.e. it
   *hides* every reveal block, expecting the animation to bring them back.
3. Lines 528–531: `inView(".reveal...", info => animate(info.target,
   { opacity:[0,1], transform:[...] }, { duration:.55, easing:"ease-out" }))`
   — this animation **does not commit its final opacity**, so blocks fall
   back to the CSS `opacity:0` and stay invisible.

**Most likely cause:** Motion API/version mismatch from pinning `@latest`.
In current Motion (v11/12+):
- the option is **`ease`**, not **`easing`** (line 525, 530, 524) — an
  unknown option can make the keyframe animation a no-op;
- WAAPI animations don't persist final styles unless filled/committed —
  Motion normally handles this, but only when the call is valid.

So the page hides content (step 2) but the un-hide animation (step 3) silently
fails → permanent `opacity:0`.

**Note:** an earlier test of mine logged `__motionLoaded=false` — ignore that;
that variable doesn't exist in the code, so the reading was meaningless. The
reliable signal is `data-anim="on"` + 22 reveals at `opacity:0`.

---

## Suggested fixes (pick one)

**Option A — make reveal failure-proof (recommended).** Never hide content
unless you can guarantee it gets un-hidden. Set `data-anim="on"` only
*per-element as you animate it*, or after confirming the animation committed.
Simplest robust version: drop the global hide; instead set each element's
inline `opacity:0` immediately before animating it inside the `inView`
callback, so any failure leaves it at the CSS default (visible).

**Option B — fix the Motion call.** Pin a known version instead of `@latest`
(e.g. `motion@11.11.13`), rename `easing` → `ease` (lines 524, 525, 530), and
verify `animate(...)` commits final opacity (Motion's `animate` returns a
promise/controls; ensure keyframes are valid). Then re-test that reveals
actually reach `opacity:1`.

**Belt-and-suspenders:** in CSS, consider gating the hide behind a class only
added once Motion is confirmed working, and add a `<noscript>`/timeout
fallback that sets `data-anim` back to off after, say, 1.5s if reveals are
still hidden.

---

## Also worth knowing

- **`file://` does NOT work.** `main.js` is an ES module (`import` from CDN),
  so opening `index.html` directly is blocked by CORS
  (`blocked by CORS policy ... only supported for protocol schemes http(s)`).
  The whole page is `opacity:0` and the toggle is dead over `file://`.
  → Must be served over HTTP. GitHub Pages is fine. Locally:
  `cd site && python3 -m http.server 8765` then open
  `http://localhost:8765/`.
- `prefers-reduced-motion: reduce` renders everything correctly (it skips the
  hide-then-animate path entirely) — that's the proof the markup/CSS are
  sound and the bug is isolated to the Motion reveal logic.
- GitHub/Docs links in the navbar/footer use `#` placeholders — swap in real
  URLs.

---

## How to re-verify after fixing

```bash
cd /Users/artem/Dev/echogrid/site
python3 -m http.server 8765        # serve (file:// won't work)
# open http://localhost:8765/ in a browser, scroll down:
#   every section below the hero must become visible
#   toggle EN|RU — all text swaps, lang persists on reload
#   check prefers-reduced-motion still shows everything
```

Quick headless check that reveals reach full opacity (needs `npx playwright
install chromium` once):

```js
// served at :8765, then in a Playwright script:
// load, wheel-scroll through the page, assert no .reveal stays opacity<0.05
```
