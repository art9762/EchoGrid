"""Export and report helpers for simulation results."""

from __future__ import annotations

import json

import pandas as pd

from src.analytics import (
    age_group,
    emotion_averages,
    institutional_trust_bucket,
    share_likelihood_distribution,
    stance_distribution,
    trust_average,
)
from src.config import ETHICAL_USE_DISCLAIMER, SYNTHETIC_SIMULATION_DISCLAIMER
from src.schemas import AgentProfile, AgentReaction, EchoItem, EchoReaction, EchoSimulationResult, NewsEvent, NewsFrame


def agents_to_dataframe(agents: list[AgentProfile]) -> pd.DataFrame:
    rows = []
    for agent in agents:
        row = agent.model_dump(mode="json")
        row["age_group"] = age_group(agent.age)
        row["institutional_trust_bucket"] = institutional_trust_bucket(
            agent.institutional_trust
        )
        rows.append(row)
    return pd.DataFrame(rows)


def reactions_to_dataframe(
    reactions: list[AgentReaction],
    bubble_assignments: dict[str, list[str]] | None = None,
) -> pd.DataFrame:
    bubble_by_agent = _bubble_by_agent(bubble_assignments or {})
    rows = []
    for reaction in reactions:
        row = reaction.model_dump(mode="json")
        emotions = row.pop("emotions")
        row.update({f"emotion_{key}": value for key, value in emotions.items()})
        row["emotional_intensity"] = reaction.emotional_intensity
        if bubble_assignments is not None:
            row["social_bubble"] = bubble_by_agent.get(reaction.agent_id)
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
        "export_metadata": export_metadata("summary"),
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


def dataframe_to_csv_export(frame: pd.DataFrame, export_name: str) -> str:
    metadata = export_metadata(export_name)
    header = "\n".join(
        [
            f"# EchoGrid export: {metadata['export_name']}",
            f"# {metadata['synthetic_simulation_disclaimer']}",
            f"# {metadata['ethical_use_disclaimer']}",
        ]
    )
    return f"{header}\n{frame.to_csv(index=False)}"


def export_metadata(export_name: str) -> dict[str, str]:
    return {
        "export_name": export_name,
        "synthetic_simulation_disclaimer": SYNTHETIC_SIMULATION_DISCLAIMER,
        "ethical_use_disclaimer": ETHICAL_USE_DISCLAIMER,
    }


def _bubble_by_agent(assignments: dict[str, list[str]]) -> dict[str, str]:
    return {
        agent_id: bubble_id
        for bubble_id, agent_ids in assignments.items()
        for agent_id in agent_ids
    }
