from __future__ import annotations

import plotly.express as px
import plotly.graph_objects as go

# ── Design-system palette (mirrors site/styles.css tokens) ────────────────────
STANCE_COLORS: dict[str, str] = {
    "support": "#34D399",  # green
    "oppose": "#FB7185",  # red
    "neutral": "#94A3B8",  # muted
    "confused": "#F97316",  # orange
}

EMOTION_COLORS: dict[str, str] = {
    "anger": "#FB7185",
    "fear": "#8B5CF6",
    "hope": "#34D399",
    "distrust": "#94A3B8",
    "indifference": "#64748B",
    "reassurance": "#38BDF8",
    "mockery": "#F97316",
    "neutral": "#94A3B8",
}

ECHO_TYPE_COLORS: dict[str, str] = {
    "viral_comment": "#F97316",
    "repost_summary": "#94A3B8",
    "tabloid_headline": "#FB7185",
    "influencer_post": "#8B5CF6",
    "expert_correction": "#34D399",
    "meme_caption": "#38BDF8",
    "partisan_attack": "#FB7185",
    "official_clarification": "#34D399",
}

# Shared layout constants
_PAPER_BG = "rgba(0,0,0,0)"
_PLOT_BG = "rgba(0,0,0,0)"
_FONT_COLOR = "#E6EAF5"
_FONT_FAMILY = "Roboto Mono, ui-monospace, monospace"
_GRID_COLOR = "rgba(255,255,255,0.06)"
_AXIS_COLOR = "rgba(255,255,255,0.12)"


def apply_chart_layout(fig: go.Figure) -> go.Figure:
    """Apply EchoGrid OLED dark theme to any Plotly figure."""
    fig.update_layout(
        paper_bgcolor=_PAPER_BG,
        plot_bgcolor=_PLOT_BG,
        font={"family": _FONT_FAMILY, "color": _FONT_COLOR, "size": 12},
        margin={"l": 10, "r": 10, "t": 36, "b": 10},
        legend={
            "bgcolor": "rgba(10,14,39,0.8)",
            "bordercolor": "rgba(255,255,255,0.08)",
            "borderwidth": 1,
            "font": {"size": 11},
        },
        legend_title_text="",
        hoverlabel={
            "bgcolor": "#0A0E27",
            "bordercolor": "#38BDF8",
            "font": {"family": _FONT_FAMILY, "color": _FONT_COLOR, "size": 12},
        },
        hovermode="closest",
    )
    fig.update_xaxes(
        gridcolor=_GRID_COLOR,
        linecolor=_AXIS_COLOR,
        tickcolor=_AXIS_COLOR,
        title_font={"size": 11, "color": "#94A3B8"},
        tickfont={"size": 10, "color": "#94A3B8"},
        zerolinecolor=_GRID_COLOR,
    )
    fig.update_yaxes(
        gridcolor=_GRID_COLOR,
        linecolor=_AXIS_COLOR,
        tickcolor=_AXIS_COLOR,
        title_font={"size": 11, "color": "#94A3B8"},
        tickfont={"size": 10, "color": "#94A3B8"},
        zerolinecolor=_GRID_COLOR,
    )
    return fig


def stance_bar(frame, x: str = "stance", y: str = "percent") -> go.Figure:
    """Horizontal stance breakdown bar using the design-system palette."""
    fig = px.bar(frame, x=x, y=y, color=x, color_discrete_map=STANCE_COLORS)
    return apply_chart_layout(fig)


def echo_type_bar(frame, x: str, y: str) -> go.Figure:
    """Bar chart coloured by echo type."""
    fig = px.bar(frame, x=x, y=y, color=x, color_discrete_map=ECHO_TYPE_COLORS)
    return apply_chart_layout(fig)


def histogram(frame, x: str, color: str | None = None, nbins: int | None = None) -> go.Figure:
    """Distribution histogram with optional categorical colour split."""
    kwargs: dict = {}
    if color is not None:
        kwargs["color"] = color
    if nbins is not None:
        kwargs["nbins"] = nbins
    fig = px.histogram(frame, x=x, **kwargs)
    fig.update_traces(marker_line_width=0)
    return apply_chart_layout(fig)


def scatter(frame, x: str, y: str, **kwargs) -> go.Figure:
    """Scatter / bubble plot with dark tokens."""
    fig = px.scatter(frame, x=x, y=y, **kwargs)
    return apply_chart_layout(fig)
