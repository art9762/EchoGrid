"""Export and report helpers for simulation results."""

from __future__ import annotations

import json

import pandas as pd

from src.analytics import (
    emotion_averages,
    share_likelihood_distribution,
    stance_distribution,
    trust_average,
)
from src.schemas import AgentProfile, AgentReaction, EchoItem, EchoReaction, EchoSimulationResult, NewsEvent, NewsFrame


def agents_to_dataframe(agents: list[AgentProfile]) -> pd.DataFrame:
    return pd.DataFrame([agent.model_dump(mode="json") for agent in agents])


def reactions_to_dataframe(reactions: list[AgentReaction]) -> pd.DataFrame:
    rows = []
    for reaction in reactions:
        row = reaction.model_dump(mode="json")
        emotions = row.pop("emotions")
        row.update({f"emotion_{key}": value for key, value in emotions.items()})
        row["emotional_intensity"] = reaction.emotional_intensity
        rows.append(row)
    return pd.DataFrame(rows)


def echo_items_to_dataframe(echo_items: list[EchoItem]) -> pd.DataFrame:
    return pd.DataFrame([item.model_dump(mode="json") for item in echo_items])


def echo_reactions_to_dataframe(echo_reactions: list[EchoReaction]) -> pd.DataFrame:
    rows = []
    for reaction in echo_reactions:
        row = reaction.model_dump(mode="json")
        shifts = row.pop("emotion_shift")
        row.update({f"{key}_shift": value for key, value in shifts.items()})
        rows.append(row)
    return pd.DataFrame(rows)


def simulation_summary_json(
    event: NewsEvent,
    frames: list[NewsFrame],
    reactions: list[AgentReaction],
    echo_result: EchoSimulationResult | None = None,
) -> str:
    payload = {
        "event": event.model_dump(mode="json"),
        "frames": [frame.model_dump(mode="json") for frame in frames],
        "initial_metrics": {
            "stance_distribution": stance_distribution(reactions),
            "emotion_averages": emotion_averages(reactions),
            "trust_average": trust_average(reactions),
            "share_likelihood_distribution": share_likelihood_distribution(reactions),
        },
        "amplification_metrics": (
            echo_result.amplification_metrics if echo_result else {}
        ),
        "echo_item_count": len(echo_result.echo_items) if echo_result else 0,
        "echo_reaction_count": len(echo_result.echo_reactions) if echo_result else 0,
    }
    return json.dumps(payload, indent=2)
