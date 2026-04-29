from __future__ import annotations

import plotly.express as px

STANCE_COLORS = {
    "support": "#2f7d57",
    "oppose": "#bd3f3f",
    "neutral": "#58728a",
    "confused": "#9a7b2f",
}

EMOTION_COLORS = {
    "anger": "#bd3f3f",
    "fear": "#7f5aa2",
    "hope": "#2f7d57",
    "distrust": "#6f6f6f",
    "indifference": "#7a98a8",
    "reassurance": "#3f8f8c",
    "mockery": "#b26f33",
    "neutral": "#58728a",
}

ECHO_TYPE_COLORS = {
    "viral_comment": "#9a7b2f",
    "repost_summary": "#58728a",
    "tabloid_headline": "#bd3f3f",
    "influencer_post": "#b26f33",
    "expert_correction": "#2f7d57",
    "meme_caption": "#7f5aa2",
    "partisan_attack": "#8f3232",
    "official_clarification": "#3f8f8c",
}


def apply_chart_layout(fig):
    fig.update_layout(
        margin={"l": 10, "r": 10, "t": 36, "b": 10},
        legend_title_text="",
        font={"size": 13},
    )
    fig.update_xaxes(title_font={"size": 12}, tickfont={"size": 11})
    fig.update_yaxes(title_font={"size": 12}, tickfont={"size": 11})
    return fig


def stance_bar(frame, x: str = "stance", y: str = "percent"):
    fig = px.bar(frame, x=x, y=y, color=x, color_discrete_map=STANCE_COLORS)
    return apply_chart_layout(fig)


def echo_type_bar(frame, x: str, y: str):
    fig = px.bar(frame, x=x, y=y, color=x, color_discrete_map=ECHO_TYPE_COLORS)
    return apply_chart_layout(fig)


def histogram(frame, x: str, color: str | None = None, nbins: int | None = None):
    fig = px.histogram(frame, x=x, color=color, nbins=nbins)
    return apply_chart_layout(fig)


def scatter(frame, x: str, y: str, **kwargs):
    fig = px.scatter(frame, x=x, y=y, **kwargs)
    return apply_chart_layout(fig)
