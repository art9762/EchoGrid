# EchoGrid — Promo Landing (Site Visit Card)

**Date:** 2026-06-03
**Type:** Static bilingual (EN/RU) dark-tech promotional landing page

## Goal

A beautiful, dynamic one-page "site visit card" for EchoGrid — an LLM-assisted
synthetic society simulator. The site explains what the project is (and is NOT),
how it works, and its key features, with strong dark-tech visuals and motion. It
does NOT run the simulation; it is pure promo/static.

## Stack

- Plain `index.html` + `styles.css` + `main.js` in `site/`.
- No build step. Opens directly in a browser, hostable on GitHub Pages.
- **Motion** (motion.dev) via ESM CDN for scroll-reveal, stagger, and count-up.
- A `<canvas>` for the hero "echo grid" background animation (vanilla JS).

## Visual System (from ui-ux-pro-max)

- **Base style:** Dark Mode (OLED). Deep background `#050510` / midnight `#0A0E27`.
  Minimal neon glow (text-shadow / box-shadow), NOT heavy cyberpunk glitch — keep
  readability and WCAG AA contrast.
- **Colors:**
  - Background: `#050510` (deep), panels `#0A0E27` / glass `rgba(255,255,255,0.04)`
  - Primary accent: cyan `#38BDF8`
  - Secondary accent: violet `#8B5CF6`
  - CTA: warm orange `#F97316`
  - Text: `#E6EAF5` primary, `#94A3B8` muted
- **Typography:** Exo (headings, weights 300–700) / Roboto Mono (labels, metrics,
  code-ish detail). Google Fonts import.
- **Effects:** subtle radial glows behind sections, glass cards with
  `border: 1px solid rgba(255,255,255,0.08)`, hover = color/shadow transition
  (no layout-shifting scale on cards), accent underglow on CTA.

## Internationalization (EN / RU)

- Toggle in the navbar (EN | RU). Default EN.
- All copy stored in a JS dictionary `i18n = { en: {...}, ru: {...} }`.
- DOM elements carry `data-i18n="key"`; a `setLang(lang)` function swaps
  `textContent`. Choice persisted to `localStorage` (`echogrid-lang`).
- `<html lang>` updated on switch. No page reload.

## Sections (one-page, scroll-reveal)

1. **Navbar (sticky/floating)** — wordmark "EchoGrid", anchor links (What / How /
   Features / Ethics), language toggle, GitHub CTA. Spacing from edges (top-4).
2. **Hero** — headline + tagline, two CTAs (View on GitHub / See how it works
   scroll). Background: animated `<canvas>` grid of nodes where "events" flash and
   echo waves ripple outward (product metaphor). Respects `prefers-reduced-motion`
   (falls back to a static gradient + faint grid).
3. **What it is / is NOT** — two contrasting glass panels. "Is": synthetic agents,
   media framings, echo reactions, metrics. "Is NOT": not a polling tool, not
   prediction, not for manipulation/targeting. (Ethical framing from README.)
4. **How it works** — animated 6-step pipeline:
   NewsEvent → Synthetic population → Media framings → Initial reactions →
   Echo cascade → Final metrics. Steps reveal/highlight in sequence on scroll.
5. **Features** — bento/card grid: Synthetic population profiles, Media ecosystem,
   Multi-round echo cascades, Before/after metrics (amplification, trust, anger,
   distortion, polarization), Storage & export (CSV/JSON/ZIP), Three run modes
   (Mock / Hybrid / Full LLM sample). SVG icons (Lucide-style), no emojis.
6. **Demo scenarios** — the 7 built-in scenarios as mono-font chips/marquee.
7. **Ethics** — highlighted block: allowed uses (research, education,
   communication-risk analysis) vs disallowed (manipulation, political targeting,
   harassment, radicalization, targeting vulnerable groups).
8. **Footer / CTA** — final call ("Run it locally"), code snippet
   (`streamlit run app.py`), links (GitHub, docs), MIT license, synthetic-output
   disclaimer.

## Animation Plan (Motion)

- Section content: `inView` + stagger fade/translate-up (150–300ms, ease-out).
- Metrics: count-up numbers when scrolled into view.
- Pipeline: sequential highlight of the 6 steps.
- Hero canvas: requestAnimationFrame node-grid with periodic echo ripples.
- All gated by `prefers-reduced-motion`.

## Accessibility / Quality Gates

- Contrast ≥ 4.5:1 (dark base supports 7:1 for primary text).
- Visible focus rings; keyboard-navigable nav + toggle.
- `cursor-pointer` on all interactive elements; 44px touch targets.
- SVG icons only (no emoji). `alt`/`aria-label` on icon-only controls.
- Responsive at 375 / 768 / 1024 / 1440px; no horizontal scroll.
- `viewport` meta; body text ≥ 16px.

## Out of Scope (YAGNI)

- No backend, no real simulation execution from the browser.
- No forms, no analytics, no auth.
- No framework/build tooling (React/Astro/Vite).

## Build Approach

A frontend subagent builds the full `site/` directory per this spec (to conserve
main-thread context). Then verify in-browser via screenshot and check the quality
gates above.
