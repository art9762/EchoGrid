from __future__ import annotations

import json
from typing import Any

import pandas as pd
import plotly.express as px
import streamlit as st

from src.analytics import (
    bubble_susceptibility,
    correction_effectiveness,
    emotion_averages,
    final_state_metrics,
    frame_comparison,
    frame_sensitivity_score,
    narrative_risk_summary,
    segment_breakdown,
    share_likelihood_distribution,
    stance_distribution,
    trust_average,
    unexpected_segments,
)
from src.config import SYNTHETIC_SIMULATION_DISCLAIMER
from src.report import (
    agents_to_dataframe,
    dataframe_to_csv_export,
    echo_items_to_dataframe,
    echo_reactions_to_dataframe,
    reactions_to_dataframe,
    simulation_export_zip,
    simulation_summary_json,
)
from src.schemas import LLMProvider, NewsEvent
from src.ui.charts import (
    STANCE_COLORS,
    apply_chart_layout,
    echo_type_bar,
    histogram,
    scatter,
    stance_bar,
)


def render_dashboard(simulation: dict[str, Any]) -> None:
    _summary_strip(simulation)
    tabs = st.tabs(
        [
            "Overview",
            "Narrative",
            "Population",
            "Media",
            "Bubbles",
            "Initial Reaction",
            "Echo Timeline",
            "Echo Items",
            "Amplification",
            "Bubble Impact",
            "Frame Comparison",
            "Segment Explorer",
            "Comments",
            "Export",
        ]
    )
    with tabs[0]:
        _overview_tab(simulation)
    with tabs[1]:
        _narrative_tab(simulation)
    with tabs[2]:
        _population_tab(simulation)
    with tabs[3]:
        _media_tab(simulation)
    with tabs[4]:
        _bubbles_tab(simulation)
    with tabs[5]:
        _initial_reaction_tab(simulation)
    with tabs[6]:
        _timeline_tab(simulation)
    with tabs[7]:
        _echo_items_tab(simulation)
    with tabs[8]:
        _amplification_tab(simulation)
    with tabs[9]:
        _bubble_impact_tab(simulation)
    with tabs[10]:
        _frame_comparison_tab(simulation)
    with tabs[11]:
        _segment_tab(simulation)
    with tabs[12]:
        _comments_tab(simulation)
    with tabs[13]:
        _export_tab(simulation)
    st.caption(f"Persistent notice: {SYNTHETIC_SIMULATION_DISCLAIMER}")


def render_empty_state() -> None:
    st.subheader("Ready for a synthetic run")
    c1, c2, c3 = st.columns(3)
    c1.metric("Default mode", "Mock")
    c2.metric("Demo scenarios", "7")
    c3.metric("Storage", "SQLite")
    st.write(
        "Configure the sidebar or launch Demo mode. EchoGrid will keep the run "
        "synthetic, persist it locally, and make CSV/JSON/ZIP exports available."
    )


def _summary_strip(simulation: dict[str, Any]) -> None:
    echo_result = simulation["echo_result"]
    reactions = simulation["initial_reactions"]
    cols = st.columns(5)
    cols[0].metric("Agents", len(simulation["agents"]))
    cols[1].metric("Frames", len(simulation["frames"]))
    cols[2].metric("Initial trust", trust_average(reactions))
    cols[3].metric(
        "Share likelihood", share_likelihood_distribution(reactions)["average"]
    )
    cols[4].metric("Echo items", len(echo_result.echo_items) if echo_result else 0)


def _overview_tab(simulation: dict[str, Any]) -> None:
    event: NewsEvent = simulation["event"]
    st.caption(f"Simulation ID: {simulation['simulation_id']}")
    st.caption(
        f"Run mode: {simulation.get('run_mode', 'mock')} | "
        f"Provider: {_provider_label(simulation.get('provider'))}"
    )
    cost = simulation.get("llm_cost_estimate")
    if cost:
        st.caption(
            f"Estimated LLM calls: {cost.estimated_calls}; "
            f"tokens: {cost.estimated_input_tokens}/{cost.estimated_output_tokens}; "
            f"rough cost: ${cost.estimated_usd_low:.4f}-${cost.estimated_usd_high:.4f}"
        )
    _llm_error_panel(simulation)
    st.subheader(event.title)
    st.write(event.description)
    st.code(event.original_text, language="text")
    if simulation["echo_result"]:
        metrics = final_state_metrics(
            simulation["echo_result"].final_reaction_state_by_agent,
            simulation["echo_result"].echo_reactions,
        )
        c1, c2, c3 = st.columns(3)
        c1.metric("Final trust", metrics["final_trust_average"])
        c2.metric("Final share", metrics["final_share_likelihood_average"])
        c3.metric("Average anger shift", metrics["average_anger_shift"])


def _narrative_tab(simulation: dict[str, Any]) -> None:
    event: NewsEvent = simulation["event"]
    echo_result = simulation["echo_result"]
    st.subheader("What happened")
    st.write(
        f"{event.title} was shown through {len(simulation['frames'])} frame(s) to "
        f"{len(simulation['agents'])} synthetic agents."
    )
    st.subheader("Where amplification appeared")
    if not echo_result:
        st.write("Echo simulation was disabled.")
        return
    risk = narrative_risk_summary(
        echo_result.echo_items, echo_result.echo_reactions, simulation["bubbles"]
    )
    highest = risk.get("highest_distortion_item") or {}
    top_bubble = risk.get("top_bubble") or {}
    c1, c2, c3 = st.columns(3)
    c1.metric("Top echo type", str(risk.get("top_echo_type") or "none"))
    c2.metric("Top affected bubble", str(top_bubble.get("label") or "none"))
    c3.metric("Highest distortion", highest.get("distortion_level", 0))
    if highest:
        st.write(highest["text"])
    st.subheader("Which corrections helped")
    st.write(correction_effectiveness(echo_result.echo_items, echo_result.echo_reactions))


def _population_tab(simulation: dict[str, Any]) -> None:
    agents_df = agents_to_dataframe(simulation["agents"])
    c1, c2 = st.columns(2)
    c1.plotly_chart(histogram(agents_df, x="age", nbins=20), width="stretch")
    c2.plotly_chart(
        histogram(agents_df, x="institutional_trust", nbins=20),
        width="stretch",
    )
    c3, c4 = st.columns(2)
    c3.plotly_chart(histogram(agents_df, x="income_level"), width="stretch")
    c4.plotly_chart(histogram(agents_df, x="location_type"), width="stretch")
    st.dataframe(agents_df.head(100), width="stretch", hide_index=True)


def _media_tab(simulation: dict[str, Any]) -> None:
    actors_df = pd.DataFrame(
        [actor.model_dump(mode="json") for actor in simulation["media_actors"]]
    )
    st.dataframe(actors_df, width="stretch", hide_index=True)
    st.plotly_chart(
        scatter(
            actors_df,
            x="credibility",
            y="sensationalism",
            size="reach",
            color="actor_type",
            hover_name="name",
        ),
        width="stretch",
    )
    contribution = actors_df[["name", "actor_type", "reach", "sensationalism"]].copy()
    contribution["amplification_pressure"] = (
        contribution["reach"] * contribution["sensationalism"] / 100
    ).round(2)
    st.plotly_chart(
        apply_chart_layout(
            px.bar(
                contribution,
                x="name",
                y="amplification_pressure",
                color="actor_type",
            )
        ),
        width="stretch",
    )


def _bubbles_tab(simulation: dict[str, Any]) -> None:
    rows = []
    assignments = _bubble_assignments(simulation)
    for bubble in simulation["bubbles"]:
        data = bubble.model_dump(mode="json")
        data["agent_count"] = len(assignments.get(bubble.id, []))
        rows.append(data)
    bubbles_df = pd.DataFrame(rows)
    st.dataframe(bubbles_df, width="stretch", hide_index=True)
    st.plotly_chart(
        apply_chart_layout(
            px.bar(
                bubbles_df,
                x="label",
                y="agent_count",
                color="outrage_sensitivity",
                color_continuous_scale="Tealrose",
            )
        ),
        width="stretch",
    )


def _initial_reaction_tab(simulation: dict[str, Any]) -> None:
    reactions = simulation["initial_reactions"]
    c1, c2, c3 = st.columns(3)
    c1.metric("Average trust", trust_average(reactions))
    c2.metric(
        "Average share likelihood", share_likelihood_distribution(reactions)["average"]
    )
    c3.metric("Emotional intensity", emotion_averages(reactions)["emotional_intensity"])
    stance_df = pd.DataFrame(
        [
            {"stance": key, "percent": value}
            for key, value in stance_distribution(reactions).items()
        ]
    )
    st.plotly_chart(stance_bar(stance_df), width="stretch")
    df = reactions_to_dataframe(reactions, _bubble_assignments(simulation))
    frame_ids = sorted(df["frame_id"].unique())
    stances = sorted(df["stance"].unique())
    c4, c5 = st.columns(2)
    selected_frames = c4.multiselect(
        "Frame", frame_ids, default=frame_ids, key="initial_frame_filter"
    )
    selected_stances = c5.multiselect(
        "Stance", stances, default=stances, key="initial_stance_filter"
    )
    filtered = df[df["frame_id"].isin(selected_frames) & df["stance"].isin(selected_stances)]
    if filtered.empty:
        st.info("No reactions match the selected filters.")
    else:
        st.dataframe(filtered.head(150), width="stretch", hide_index=True)


def _timeline_tab(simulation: dict[str, Any]) -> None:
    event: NewsEvent = simulation["event"]
    _timeline_card("Round 0", "Original event", event.original_text)
    for frame in simulation["frames"]:
        _timeline_card("Round 1", frame.label, frame.text)
    _timeline_card(
        "Round 2",
        "Initial reactions",
        str(stance_distribution(simulation["initial_reactions"])),
    )
    echo_result = simulation["echo_result"]
    if not echo_result:
        st.write("Echo simulation was disabled.")
        return
    for summary in echo_result.round_summaries:
        if summary.round_number <= 2:
            continue
        _timeline_card(
            f"Round {summary.round_number}",
            summary.label,
            ", ".join(f"{key}: {value}" for key, value in summary.metrics.items()),
        )
    st.dataframe(
        echo_items_to_dataframe(echo_result.echo_items),
        width="stretch",
        hide_index=True,
    )


def _echo_items_tab(simulation: dict[str, Any]) -> None:
    echo_result = simulation["echo_result"]
    if not echo_result:
        st.write("Echo simulation was disabled.")
        return
    df = echo_items_to_dataframe(echo_result.echo_items)
    echo_types = sorted(df["echo_type"].unique())
    bubble_values = sorted({bubble for values in df["target_bubbles"] for bubble in values})
    c1, c2 = st.columns(2)
    selected_types = c1.multiselect(
        "Echo type", echo_types, default=echo_types, key="echo_type_filter"
    )
    selected_bubbles = c2.multiselect(
        "Target bubble",
        bubble_values,
        default=bubble_values,
        key="echo_target_bubble_filter",
    )
    filtered = df[
        df["echo_type"].isin(selected_types)
        & df["target_bubbles"].apply(
            lambda values: bool(set(values) & set(selected_bubbles))
        )
    ]
    if filtered.empty:
        st.info("No echo items match the selected filters.")
    else:
        st.plotly_chart(
            echo_type_bar(
                filtered.groupby("echo_type", as_index=False)["estimated_reach"].sum(),
                x="echo_type",
                y="estimated_reach",
            ),
            width="stretch",
        )
        st.dataframe(filtered, width="stretch", hide_index=True)


def _amplification_tab(simulation: dict[str, Any]) -> None:
    echo_result = simulation["echo_result"]
    if not echo_result:
        st.write("Echo simulation was disabled.")
        return
    metrics = echo_result.amplification_metrics
    cols = st.columns(max(1, len(metrics)))
    for col, (key, value) in zip(cols, metrics.items(), strict=False):
        col.metric(key.replace("_", " ").title(), value)
    metric_df = pd.DataFrame(
        [{"metric": key, "value": value} for key, value in metrics.items()]
    )
    st.plotly_chart(
        apply_chart_layout(px.bar(metric_df, x="metric", y="value")),
        width="stretch",
    )
    breakdown = simulation_summary_json(
        event=simulation["event"],
        frames=simulation["frames"],
        reactions=simulation["initial_reactions"],
        echo_result=echo_result,
        bubbles=simulation["bubbles"],
    )
    summary = json.loads(breakdown)["amplification_breakdown"]
    if summary:
        rows = [
            {"component": component, **values}
            for component, values in summary.items()
        ]
        st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)
    st.subheader("Correction effectiveness")
    st.write(correction_effectiveness(echo_result.echo_items, echo_result.echo_reactions))


def _bubble_impact_tab(simulation: dict[str, Any]) -> None:
    echo_result = simulation["echo_result"]
    if not echo_result:
        st.write("Echo simulation was disabled.")
        return
    rows = bubble_susceptibility(echo_result.echo_reactions, simulation["bubbles"])
    df = pd.DataFrame(rows)
    st.dataframe(df, width="stretch", hide_index=True)
    if not df.empty:
        st.plotly_chart(
            apply_chart_layout(
                px.bar(
                    df,
                    x="label",
                    y="average_share_likelihood_shift",
                    color="average_anger_shift",
                    color_continuous_scale="Tealrose",
                )
            ),
            width="stretch",
        )


def _frame_comparison_tab(simulation: dict[str, Any]) -> None:
    comparison = frame_comparison(simulation["initial_reactions"])
    rows = []
    for frame_id, data in comparison.items():
        rows.append(
            {
                "frame_id": frame_id,
                "average_trust": data["average_trust"],
                "average_share_likelihood": data["average_share_likelihood"],
                "polarization_score": data["polarization_score"],
                "virality_risk_score": data["virality_risk_score"],
                **data["stance_distribution"],
            }
        )
    df = pd.DataFrame(rows)
    st.write(frame_sensitivity_score(simulation["initial_reactions"]))
    st.dataframe(df, width="stretch", hide_index=True)
    st.plotly_chart(
        apply_chart_layout(
            px.bar(
                df,
                x="frame_id",
                y=["support", "oppose", "neutral", "confused"],
                color_discrete_map=STANCE_COLORS,
            )
        ),
        width="stretch",
    )


def _segment_tab(simulation: dict[str, Any]) -> None:
    field = st.selectbox(
        "Group by",
        [
            "income_level",
            "age_group",
            "institutional_trust_bucket",
            "education_level",
            "location_type",
            "economic_position",
            "social_position",
            "political_engagement",
        ],
    )
    rows = segment_breakdown(
        simulation["initial_reactions"], simulation["agents"], by_field=field
    )
    df = pd.DataFrame(rows)
    st.dataframe(df, width="stretch", hide_index=True)
    if not df.empty:
        st.plotly_chart(
            apply_chart_layout(px.bar(df, x="segment", y="average_share_likelihood")),
            width="stretch",
        )
    st.subheader("Unexpected high-risk segments")
    unexpected = pd.DataFrame(
        unexpected_segments(simulation["initial_reactions"], simulation["agents"])
    )
    if unexpected.empty:
        st.info("No high-risk synthetic segments crossed the review threshold.")
    else:
        st.dataframe(unexpected, width="stretch", hide_index=True)


def _comments_tab(simulation: dict[str, Any]) -> None:
    representative_comments = simulation.get("representative_comments") or []
    if representative_comments:
        st.subheader("Representative comments")
        for comment in representative_comments:
            with st.container(border=True):
                st.markdown(f"**{comment.segment_label}**")
                st.write(comment.comment)
                st.caption(
                    f"stance: {comment.stance.value} | frame: {comment.frame_id or 'any'} | "
                    f"bubble: {comment.bubble_id or 'any'}"
                )
        st.divider()

    df = reactions_to_dataframe(
        simulation["initial_reactions"], _bubble_assignments(simulation)
    )
    stances = sorted(df["stance"].unique())
    frames = sorted(df["frame_id"].unique())
    bubbles = sorted(value for value in df["social_bubble"].dropna().unique())
    c1, c2, c3 = st.columns(3)
    stance = c1.multiselect(
        "Stance", stances, default=stances, key="comment_stance_filter"
    )
    frame = c2.multiselect("Frame", frames, default=frames, key="comment_frame_filter")
    bubble = c3.multiselect(
        "Bubble", bubbles, default=bubbles, key="comment_bubble_filter"
    )
    filtered = df[
        df["stance"].isin(stance)
        & df["frame_id"].isin(frame)
        & df["social_bubble"].isin(bubble)
    ]
    if filtered.empty:
        st.info("No comments match the selected filters.")
        return
    st.dataframe(
        filtered[
            [
                "agent_id",
                "frame_id",
                "social_bubble",
                "stance",
                "likely_comment",
                "main_reason",
            ]
        ].head(300),
        width="stretch",
        hide_index=True,
    )


def _export_tab(simulation: dict[str, Any]) -> None:
    agents_df = agents_to_dataframe(simulation["agents"])
    reactions_df = reactions_to_dataframe(
        simulation["initial_reactions"], _bubble_assignments(simulation)
    )
    st.download_button(
        "Export agents CSV",
        dataframe_to_csv_export(agents_df, "agents"),
        "agents.csv",
    )
    st.download_button(
        "Export reactions CSV",
        dataframe_to_csv_export(reactions_df, "reactions"),
        "reactions.csv",
    )

    echo_result = simulation["echo_result"]
    if echo_result:
        echo_items_df = echo_items_to_dataframe(echo_result.echo_items)
        echo_reactions_df = echo_reactions_to_dataframe(echo_result.echo_reactions)
        st.download_button(
            "Export echo items CSV",
            dataframe_to_csv_export(echo_items_df, "echo_items"),
            "echo_items.csv",
        )
        st.download_button(
            "Export echo reactions CSV",
            dataframe_to_csv_export(echo_reactions_df, "echo_reactions"),
            "echo_reactions.csv",
        )
    st.download_button(
        "Export summary JSON",
        simulation_summary_json(
            event=simulation["event"],
            frames=simulation["frames"],
            reactions=simulation["initial_reactions"],
            echo_result=echo_result,
            run_mode=simulation.get("run_mode", "mock"),
            provider=simulation.get("provider"),
            representative_comments=simulation.get("representative_comments"),
            llm_errors=simulation.get("llm_errors"),
            bubbles=simulation["bubbles"],
        ),
        "summary.json",
        mime="application/json",
    )
    st.download_button(
        "Export full ZIP",
        simulation_export_zip(simulation),
        f"{simulation['simulation_id']}.zip",
        mime="application/zip",
    )


def _llm_error_panel(simulation: dict[str, Any]) -> None:
    llm_errors = simulation.get("llm_errors") or []
    if not llm_errors:
        return
    st.warning("Some LLM generation steps fell back to deterministic artifacts.")
    st.dataframe(
        pd.DataFrame([error.model_dump(mode="json") for error in llm_errors]),
        width="stretch",
        hide_index=True,
    )


def _timeline_card(round_label: str, title: str, body: str) -> None:
    with st.container(border=True):
        st.caption(round_label)
        st.markdown(f"**{title}**")
        st.write(body)


def _provider_label(provider: Any) -> str:
    if isinstance(provider, LLMProvider):
        return provider.value
    return str(provider or "mock")


def _bubble_assignments(simulation: dict[str, Any]) -> dict[str, list[str]]:
    return simulation.get("assignments") or simulation.get("bubble_assignments") or {}
