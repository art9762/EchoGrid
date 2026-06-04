"""EchoGrid Streamlit theme — OLED dark design system.

Mirrors the promo site tokens from site/styles.css for cross-surface consistency.
Injects a single <style> block via st.markdown; no JavaScript required.
Motion uses CSS keyframes only, guarded by prefers-reduced-motion.
"""

from __future__ import annotations

import streamlit as st

_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Exo:wght@300;400;500;600;700&family=Roboto+Mono:wght@400;500;600&display=swap');

/* ── OLED tokens ─────────────────────────────────────────────────── */
:root {
  --bg-deep:       #050510;
  --bg-midnight:   #0A0E27;
  --glass:         rgba(255, 255, 255, 0.04);
  --glass-strong:  rgba(255, 255, 255, 0.06);
  --border:        rgba(255, 255, 255, 0.08);
  --border-strong: rgba(255, 255, 255, 0.14);
  --cyan:    #38BDF8;
  --violet:  #8B5CF6;
  --orange:  #F97316;
  --green:   #34D399;
  --red:     #FB7185;
  --text:    #E6EAF5;
  --muted:   #94A3B8;
  --font-head: 'Exo', system-ui, sans-serif;
  --font-mono: 'Roboto Mono', ui-monospace, monospace;
}

/* ── App surfaces ────────────────────────────────────────────────── */
.stApp,
[data-testid="stAppViewContainer"] {
  background-color: var(--bg-deep) !important;
  color: var(--text) !important;
  font-family: var(--font-head) !important;
}

[data-testid="stSidebar"],
[data-testid="stSidebarContent"] {
  background-color: var(--bg-midnight) !important;
  border-right: 1px solid var(--border) !important;
}

[data-testid="stHeader"] {
  background-color: var(--bg-deep) !important;
}

.block-container {
  background-color: var(--bg-deep) !important;
  padding-top: 2rem !important;
}

/* ── Typography ──────────────────────────────────────────────────── */
h1, h2, h3, h4, h5, h6,
.stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
  font-family: var(--font-head) !important;
  color: var(--text) !important;
  letter-spacing: -0.01em;
}

h1, .stApp h1 { font-weight: 700 !important; }
h2, .stApp h2 { font-weight: 600 !important; }
h3, .stApp h3 { font-weight: 500 !important; }

p, .stMarkdown p, label, .stWidgetLabel {
  font-family: var(--font-head) !important;
  color: var(--text) !important;
}

.stCaption, [data-testid="stCaptionContainer"] {
  color: var(--muted) !important;
  font-family: var(--font-head) !important;
}

/* ── Metric glass cards ──────────────────────────────────────────── */
[data-testid="stMetric"] {
  background: var(--glass) !important;
  border: 1px solid var(--border) !important;
  border-radius: 14px !important;
  padding: 14px 18px !important;
  backdrop-filter: blur(8px) !important;
}

[data-testid="stMetricValue"] {
  font-family: var(--font-mono) !important;
  font-size: 1.6rem !important;
  font-weight: 600 !important;
  color: var(--cyan) !important;
}

[data-testid="stMetricLabel"] {
  font-family: var(--font-head) !important;
  font-size: 0.78rem !important;
  font-weight: 500 !important;
  letter-spacing: 0.06em !important;
  text-transform: uppercase !important;
  color: var(--muted) !important;
}

[data-testid="stMetricDelta"] {
  font-family: var(--font-mono) !important;
  font-size: 0.8rem !important;
}

/* ── Tabs ────────────────────────────────────────────────────────── */
[data-baseweb="tab-list"] {
  background: var(--bg-midnight) !important;
  border-bottom: 1px solid var(--border) !important;
  gap: 0 !important;
}

[data-baseweb="tab"] {
  background: transparent !important;
  color: var(--muted) !important;
  font-family: var(--font-head) !important;
  font-size: 0.85rem !important;
  font-weight: 500 !important;
  border-bottom: 2px solid transparent !important;
  transition: color 150ms ease, border-color 150ms ease !important;
  padding: 10px 16px !important;
}

[data-baseweb="tab"]:hover {
  color: var(--text) !important;
  border-bottom-color: rgba(56, 189, 248, 0.4) !important;
}

[aria-selected="true"][data-baseweb="tab"] {
  color: var(--cyan) !important;
  border-bottom-color: var(--cyan) !important;
  background: transparent !important;
}

[data-baseweb="tab-panel"] {
  background: var(--bg-deep) !important;
  padding-top: 1.5rem !important;
}

/* ── Buttons ─────────────────────────────────────────────────────── */
[data-testid="stBaseButton-primary"],
[data-testid="baseButton-primary"],
.stButton > button[kind="primary"] {
  background: var(--orange) !important;
  color: #fff !important;
  border: none !important;
  border-radius: 8px !important;
  font-family: var(--font-head) !important;
  font-weight: 600 !important;
  letter-spacing: 0.02em !important;
  transition: background 200ms ease, transform 200ms ease, box-shadow 200ms ease !important;
}

[data-testid="stBaseButton-primary"]:hover,
.stButton > button[kind="primary"]:hover {
  background: #ea6c0b !important;
  transform: translateY(-1px) !important;
  box-shadow: 0 4px 16px rgba(249, 115, 22, 0.35) !important;
}

[data-testid="stBaseButton-secondary"],
.stButton > button[kind="secondary"],
.stButton > button {
  background: var(--glass) !important;
  color: var(--text) !important;
  border: 1px solid var(--border-strong) !important;
  border-radius: 8px !important;
  font-family: var(--font-head) !important;
  font-weight: 500 !important;
  transition: background 200ms ease, border-color 200ms ease !important;
}

.stButton > button:hover {
  background: var(--glass-strong) !important;
  border-color: var(--cyan) !important;
}

button:focus-visible,
[data-testid="stBaseButton-primary"]:focus-visible,
[data-testid="stBaseButton-secondary"]:focus-visible,
.stButton > button:focus-visible {
  outline: 2px solid var(--cyan) !important;
  outline-offset: 3px !important;
  border-radius: 8px !important;
}

/* ── Inputs / selects / sliders ──────────────────────────────────── */
[data-testid="stTextInput"] input,
[data-testid="stTextArea"] textarea,
[data-testid="stNumberInput"] input {
  background: var(--bg-midnight) !important;
  color: var(--text) !important;
  border: 1px solid var(--border-strong) !important;
  border-radius: 8px !important;
  font-family: var(--font-head) !important;
  transition: border-color 150ms ease !important;
}

[data-testid="stTextInput"] input:focus,
[data-testid="stTextArea"] textarea:focus {
  border-color: var(--cyan) !important;
  outline: none !important;
  box-shadow: 0 0 0 2px rgba(56, 189, 248, 0.2) !important;
}

[data-testid="stSelectbox"] > div,
[data-testid="stMultiSelect"] > div {
  background: var(--bg-midnight) !important;
  border: 1px solid var(--border-strong) !important;
  border-radius: 8px !important;
  color: var(--text) !important;
}

/* Slider accent */
[data-testid="stSlider"] [role="slider"] {
  background: var(--cyan) !important;
  border-color: var(--cyan) !important;
}

[data-testid="stSlider"] [data-testid="stTickBar"] {
  color: var(--muted) !important;
}

/* ── Containers / expanders ──────────────────────────────────────── */
[data-testid="stExpander"],
.streamlit-expanderContent {
  background: var(--glass) !important;
  border: 1px solid var(--border) !important;
  border-radius: 12px !important;
}

[data-testid="stContainer"] {
  background: var(--glass) !important;
}

/* ── Dataframe header ────────────────────────────────────────────── */
[data-testid="stDataFrame"] th,
.dvn-scroller th {
  background: var(--bg-midnight) !important;
  color: var(--muted) !important;
  font-family: var(--font-mono) !important;
  font-size: 0.75rem !important;
  letter-spacing: 0.05em !important;
  border-bottom: 1px solid var(--border-strong) !important;
}

[data-testid="stDataFrame"] td {
  color: var(--text) !important;
  font-family: var(--font-mono) !important;
  font-size: 0.8rem !important;
  border-bottom: 1px solid var(--border) !important;
}

/* ── Status / alerts ─────────────────────────────────────────────── */
[data-testid="stAlert"] {
  border-radius: 10px !important;
  border-left-width: 3px !important;
  font-family: var(--font-head) !important;
}

/* ── Keyframe animations ─────────────────────────────────────────── */
@keyframes fadeSlideUp {
  from {
    opacity: 0;
    transform: translateY(8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes shimmer {
  0%   { background-position: -400px 0; }
  100% { background-position: 400px 0; }
}

/* Apply entrance animation to top-level block containers */
[data-testid="stVerticalBlock"] > div,
.block-container > div {
  animation: fadeSlideUp 400ms ease-out both;
}

/* Shimmer utility class for loading states */
.echogrid-shimmer {
  background: linear-gradient(
    90deg,
    var(--glass) 25%,
    var(--glass-strong) 50%,
    var(--glass) 75%
  );
  background-size: 400px 100%;
  animation: shimmer 1.5s infinite linear;
  border-radius: 8px;
}

/* ── Reduced motion guard (MUST be last to win specificity) ──────── */
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation: none !important;
    transition: none !important;
  }
}
"""


def inject_theme() -> None:
    """Inject the EchoGrid OLED dark theme into the Streamlit app.

    Emits a single <style> block with Google Fonts import, OLED surface tokens,
    glass metric cards, tab/button/slider/input styling, and CSS-only entrance
    animations. All motion is wrapped in a prefers-reduced-motion guard.
    """
    st.markdown(f"<style>{_CSS}</style>", unsafe_allow_html=True)
