"""Aggregation and metric helpers for EchoGrid simulations."""

from __future__ import annotations

from collections import Counter
from statistics import mean, median

import pandas as pd

from src.schemas import (
    AgentProfile,
    AgentReaction,
    EchoItem,
    EchoReaction,
    FinalAgentState,
    SocialBubble,
    Stance,
)
from src.utils import clamp

STANCE_ORDER = [Stance.SUPPORT, Stance.OPPOSE, Stance.NEUTRAL, Stance.CONFUSED]
STANCE_SIGN = {
    Stance.SUPPORT: 1,
    Stance.OPPOSE: -1,
    Stance.NEUTRAL: 0,
    Stance.CONFUSED: 0,
}


def age_group(age: int) -> str:
    if age <= 24:
        return "18-24"
    if age <= 34:
        return "25-34"
    if age <= 49:
        return "35-49"
    if age <= 64:
        return "50-64"
    return "65+"


def institutional_trust_bucket(trust: int) -> str:
    if trust < 34:
        return "low"
    if trust < 67:
        return "medium"
    return "high"


def segment_value(agent: AgentProfile, by_field: str) -> object:
    if by_field == "age_group":
        return age_group(agent.age)
    if by_field == "institutional_trust_bucket":
        return institutional_trust_bucket(agent.institutional_trust)
    return getattr(agent, by_field)


def stance_distribution(reactions: list[AgentReaction]) -> dict[str, float]:
    total = len(reactions)
    if total == 0:
        return {stance.value: 0.0 for stance in STANCE_ORDER}
    return {
        stance.value: round(
            sum(1 for reaction in reactions if reaction.stance == stance) * 100 / total,
            2,
        )
        for stance in STANCE_ORDER
    }


def emotion_averages(reactions: list[AgentReaction]) -> dict[str, float]:
    if not reactions:
        return {
            "anger": 0.0,
            "fear": 0.0,
            "hope": 0.0,
            "distrust": 0.0,
            "indifference": 0.0,
            "emotional_intensity": 0.0,
        }
    values = {
        "anger": mean(reaction.emotions.anger for reaction in reactions),
        "fear": mean(reaction.emotions.fear for reaction in reactions),
        "hope": mean(reaction.emotions.hope for reaction in reactions),
        "distrust": mean(reaction.emotions.distrust for reaction in reactions),
        "indifference": mean(reaction.emotions.indifference for reaction in reactions),
        "emotional_intensity": mean(reaction.emotional_intensity for reaction in reactions),
    }
    return {key: round(value, 2) for key, value in values.items()}


def trust_average(reactions: list[AgentReaction]) -> float:
    if not reactions:
        return 0.0
    return round(mean(reaction.trust_in_source for reaction in reactions), 2)


def share_likelihood_distribution(reactions: list[AgentReaction]) -> dict[str, float]:
    if not reactions:
        return {
            "average": 0.0,
            "median": 0.0,
            "p75": 0.0,
            "high_share_percent": 0.0,
        }
    shares = sorted(reaction.share_likelihood for reaction in reactions)
    p75_index = min(len(shares) - 1, int(len(shares) * 0.75))
    return {
        "average": round(mean(shares), 2),
        "median": round(median(shares), 2),
        "p75": round(shares[p75_index], 2),
        "high_share_percent": round(sum(1 for value in shares if value >= 65) * 100 / len(shares), 2),
    }


def segment_breakdown(
    reactions: list[AgentReaction], agents: list[AgentProfile], by_field: str
) -> list[dict[str, object]]:
    agent_lookup = {agent.id: agent for agent in agents}
    rows: list[dict[str, object]] = []
    for reaction in reactions:
        agent = agent_lookup.get(reaction.agent_id)
        if not agent:
            continue
        segment = segment_value(agent, by_field)
        rows.append(
            {
                "segment": segment,
                "stance": reaction.stance.value,
                "share_likelihood": reaction.share_likelihood,
                "anger": reaction.emotions.anger,
                "distrust": reaction.emotions.distrust,
                "trust": reaction.trust_in_source,
            }
        )
    if not rows:
        return []

    frame = pd.DataFrame(rows)
    grouped = []
    for segment, group in frame.groupby("segment", sort=True):
        grouped.append(
            {
                "segment": segment,
                "count": int(len(group)),
                "support_percent": round((group["stance"] == Stance.SUPPORT.value).mean() * 100, 2),
                "oppose_percent": round((group["stance"] == Stance.OPPOSE.value).mean() * 100, 2),
                "average_share_likelihood": round(float(group["share_likelihood"].mean()), 2),
                "average_anger": round(float(group["anger"].mean()), 2),
                "average_distrust": round(float(group["distrust"].mean()), 2),
                "average_trust": round(float(group["trust"].mean()), 2),
            }
        )
    return grouped


def polarization_score(reactions: list[AgentReaction]) -> float:
    if len(reactions) < 2:
        return 0.0
    signed_scores = [
        STANCE_SIGN[reaction.stance] * reaction.stance_strength for reaction in reactions
    ]
    series = pd.Series(signed_scores)
    stance_spread = min(100.0, float(series.std(ddof=0)))
    intensity = emotion_averages(reactions)["emotional_intensity"]
    return round(clamp(stance_spread * (0.72 + intensity / 180)), 2)


def virality_risk_score(reactions: list[AgentReaction]) -> float:
    if not reactions:
        return 0.0
    emotional_intensity = emotion_averages(reactions)["emotional_intensity"]
    average_share = mean(reaction.share_likelihood for reaction in reactions)
    average_comment = mean(reaction.comment_likelihood for reaction in reactions)
    return round(clamp(emotional_intensity * average_share * average_comment / 10000), 2)


def _spread(values: list[float]) -> float:
    if not values:
        return 0.0
    return float(max(values) - min(values))


def frame_comparison(reactions: list[AgentReaction]) -> dict[str, dict[str, object]]:
    grouped: dict[str, list[AgentReaction]] = {}
    for reaction in reactions:
        grouped.setdefault(reaction.frame_id, []).append(reaction)

    return {
        frame_id: {
            "stance_distribution": stance_distribution(frame_reactions),
            "emotion_averages": emotion_averages(frame_reactions),
            "average_trust": trust_average(frame_reactions),
            "average_share_likelihood": share_likelihood_distribution(frame_reactions)[
                "average"
            ],
            "polarization_score": polarization_score(frame_reactions),
            "virality_risk_score": virality_risk_score(frame_reactions),
        }
        for frame_id, frame_reactions in grouped.items()
    }


def frame_sensitivity_score(reactions: list[AgentReaction]) -> dict[str, object]:
    comparison = frame_comparison(reactions)
    if not comparison:
        return {
            "score": 0.0,
            "stance_spread": 0.0,
            "trust_spread": 0.0,
            "share_spread": 0.0,
            "highest_share_frame": None,
            "lowest_trust_frame": None,
        }

    support_values = [
        data["stance_distribution"][Stance.SUPPORT.value]
        for data in comparison.values()
    ]
    oppose_values = [
        data["stance_distribution"][Stance.OPPOSE.value]
        for data in comparison.values()
    ]
    trust_values = [float(data["average_trust"]) for data in comparison.values()]
    share_values = [
        float(data["average_share_likelihood"]) for data in comparison.values()
    ]
    stance_spread = max(
        _spread(support_values),
        _spread(oppose_values),
    )
    trust_spread = _spread(trust_values)
    share_spread = _spread(share_values)
    score = clamp(stance_spread * 0.45 + trust_spread * 0.25 + share_spread * 0.3)
    highest_share_frame = max(
        comparison, key=lambda frame_id: comparison[frame_id]["average_share_likelihood"]
    )
    lowest_trust_frame = min(
        comparison, key=lambda frame_id: comparison[frame_id]["average_trust"]
    )
    return {
        "score": round(score, 2),
        "stance_spread": round(stance_spread, 2),
        "trust_spread": round(trust_spread, 2),
        "share_spread": round(share_spread, 2),
        "highest_share_frame": highest_share_frame,
        "lowest_trust_frame": lowest_trust_frame,
    }


def unexpected_segments(
    reactions: list[AgentReaction], agents: list[AgentProfile]
) -> list[dict[str, object]]:
    candidates = []
    for field in ["income_level", "age_group", "institutional_trust_bucket"]:
        for row in segment_breakdown(reactions, agents, by_field=field):
            if row["count"] < 5:
                continue
            risk_score = (
                float(row["average_anger"]) * 0.38
                + float(row["average_distrust"]) * 0.27
                + float(row["average_share_likelihood"]) * 0.35
            )
            if risk_score < 45:
                continue
            enriched = dict(row)
            enriched["field"] = field
            enriched["risk_score"] = round(risk_score, 2)
            candidates.append(enriched)
    return sorted(candidates, key=lambda row: row["risk_score"], reverse=True)[:8]


def echo_amplification_index(
    initial_reactions: list[AgentReaction],
    echo_reactions: list[EchoReaction],
    echo_items: list[EchoItem],
) -> float:
    if not initial_reactions or not echo_reactions:
        return 0.0
    breakdown = echo_amplification_breakdown(
        initial_reactions, echo_reactions, echo_items
    )
    score = sum(row["weighted_contribution"] for row in breakdown.values())
    return round(clamp(score), 2)


def echo_amplification_breakdown(
    initial_reactions: list[AgentReaction],
    echo_reactions: list[EchoReaction],
    echo_items: list[EchoItem],
) -> dict[str, dict[str, float]]:
    """Explain the weighted components behind the amplification index."""
    if not initial_reactions or not echo_reactions:
        return {
            key: {"raw_value": 0.0, "weight": weight, "weighted_contribution": 0.0}
            for key, weight in _AMPLIFICATION_WEIGHTS.items()
        }

    raw_values = {
        "anger_delta": max(0.0, anger_delta(echo_reactions)),
        "trust_loss": max(0.0, -trust_delta(echo_reactions)),
        "share_growth": max(0.0, virality_growth(echo_reactions)),
        "stance_motion": round(
            mean(abs(reaction.stance_shift) for reaction in echo_reactions), 2
        ),
        "distortion": distortion_drift(echo_items),
    }
    return {
        key: {
            "raw_value": value,
            "weight": _AMPLIFICATION_WEIGHTS[key],
            "weighted_contribution": round(value * _AMPLIFICATION_WEIGHTS[key], 2),
        }
        for key, value in raw_values.items()
    }


_AMPLIFICATION_WEIGHTS = {
    "anger_delta": 0.22,
    "trust_loss": 0.2,
    "share_growth": 0.22,
    "stance_motion": 0.18,
    "distortion": 0.18,
}


def distortion_drift(echo_items: list[EchoItem]) -> float:
    if not echo_items:
        return 0.0
    total_reach = sum(max(item.estimated_reach, 1) for item in echo_items)
    weighted = sum(item.distortion_level * max(item.estimated_reach, 1) for item in echo_items)
    return round(weighted / total_reach, 2)


def polarization_delta(
    initial_reactions: list[AgentReaction], echo_reactions: list[EchoReaction]
) -> float:
    if not initial_reactions or not echo_reactions:
        return 0.0
    initial_by_agent: dict[str, AgentReaction] = {}
    for reaction in initial_reactions:
        initial_by_agent.setdefault(reaction.agent_id, reaction)
    final_by_agent: dict[str, EchoReaction] = {}
    for reaction in echo_reactions:
        final_by_agent[reaction.agent_id] = reaction

    initial_scores = [
        STANCE_SIGN[reaction.stance] * reaction.stance_strength
        for reaction in initial_by_agent.values()
    ]
    final_scores = []
    for agent_id, initial in initial_by_agent.items():
        final = final_by_agent.get(agent_id)
        if final is None:
            final_scores.append(STANCE_SIGN[initial.stance] * initial.stance_strength)
            continue
        final_scores.append(
            STANCE_SIGN[final.updated_stance]
            * clamp(initial.stance_strength + abs(final.stance_shift) * 0.5)
        )
    if len(initial_scores) < 2 or len(final_scores) < 2:
        return 0.0
    initial_spread = float(pd.Series(initial_scores).std(ddof=0))
    final_spread = float(pd.Series(final_scores).std(ddof=0))
    emotion_pressure = mean(
        max(0, reaction.emotion_shift.anger) + max(0, reaction.emotion_shift.distrust)
        for reaction in echo_reactions
    )
    return round(clamp(final_spread - initial_spread + emotion_pressure * 0.08, -100, 100), 2)


def trust_delta(echo_reactions: list[EchoReaction]) -> float:
    if not echo_reactions:
        return 0.0
    return round(mean(reaction.trust_shift for reaction in echo_reactions), 2)


def anger_delta(echo_reactions: list[EchoReaction]) -> float:
    if not echo_reactions:
        return 0.0
    return round(mean(reaction.emotion_shift.anger for reaction in echo_reactions), 2)


def virality_growth(echo_reactions: list[EchoReaction]) -> float:
    if not echo_reactions:
        return 0.0
    return round(mean(reaction.share_likelihood_shift for reaction in echo_reactions), 2)


def correction_effectiveness(
    echo_items: list[EchoItem], echo_reactions: list[EchoReaction]
) -> dict[str, float]:
    corrective_ids = {
        item.id
        for item in echo_items
        if item.echo_type.value in {"expert_correction", "official_clarification"}
    }
    relevant = [
        reaction for reaction in echo_reactions if reaction.echo_item_id in corrective_ids
    ]
    if not relevant:
        return {"average_trust_shift": 0.0, "average_anger_shift": 0.0}
    return {
        "average_trust_shift": round(mean(reaction.trust_shift for reaction in relevant), 2),
        "average_anger_shift": round(
            mean(reaction.emotion_shift.anger for reaction in relevant), 2
        ),
    }


def bubble_susceptibility(
    echo_reactions: list[EchoReaction], bubbles: list[SocialBubble]
) -> list[dict[str, object]]:
    labels = {bubble.id: bubble.label for bubble in bubbles}
    grouped: dict[str, list[EchoReaction]] = {}
    for reaction in echo_reactions:
        if reaction.bubble_id:
            grouped.setdefault(reaction.bubble_id, []).append(reaction)

    rows = []
    for bubble_id, reactions in sorted(grouped.items()):
        rows.append(
            {
                "bubble_id": bubble_id,
                "label": labels.get(bubble_id, bubble_id),
                "count": len(reactions),
                "average_stance_shift": round(
                    mean(reaction.stance_shift for reaction in reactions), 2
                ),
                "average_anger_shift": round(
                    mean(reaction.emotion_shift.anger for reaction in reactions), 2
                ),
                "average_distrust_shift": round(
                    mean(reaction.emotion_shift.distrust for reaction in reactions), 2
                ),
                "average_share_likelihood_shift": round(
                    mean(reaction.share_likelihood_shift for reaction in reactions), 2
                ),
            }
        )
    return rows


def final_state_metrics(
    final_states: dict[str, FinalAgentState],
    echo_reactions: list[EchoReaction],
) -> dict[str, object]:
    """Aggregate after-echo state metrics for dashboard and exports."""
    states = list(final_states.values())
    if not states:
        return {
            "final_stance_distribution": {stance.value: 0.0 for stance in STANCE_ORDER},
            "final_trust_average": 0.0,
            "final_share_likelihood_average": 0.0,
            "average_stance_shift": 0.0,
            "average_anger_shift": 0.0,
        }

    stance_counts = Counter(state.final_stance for state in states)
    total = len(states)
    return {
        "final_stance_distribution": {
            stance.value: round(stance_counts[stance] * 100 / total, 2)
            for stance in STANCE_ORDER
        },
        "final_trust_average": round(mean(state.final_trust for state in states), 2),
        "final_share_likelihood_average": round(
            mean(state.final_share_likelihood for state in states), 2
        ),
        "average_stance_shift": (
            round(mean(reaction.stance_shift for reaction in echo_reactions), 2)
            if echo_reactions
            else 0.0
        ),
        "average_anger_shift": anger_delta(echo_reactions),
    }


def narrative_risk_summary(
    echo_items: list[EchoItem],
    echo_reactions: list[EchoReaction],
    bubbles: list[SocialBubble],
) -> dict[str, object]:
    """Return inspectable narrative-risk highlights from an echo run."""
    if not echo_items:
        return {
            "top_echo_type": None,
            "top_bubble": None,
            "highest_distortion_item": None,
        }

    echo_type_counts = Counter(item.echo_type.value for item in echo_items)
    bubble_labels = {bubble.id: bubble.label for bubble in bubbles}
    bubble_scores: dict[str, float] = {}
    for reaction in echo_reactions:
        if reaction.bubble_id is None:
            continue
        bubble_scores.setdefault(reaction.bubble_id, 0.0)
        bubble_scores[reaction.bubble_id] += (
            abs(reaction.stance_shift)
            + max(0, reaction.emotion_shift.anger)
            + max(0, reaction.share_likelihood_shift)
        )

    top_bubble_id = max(bubble_scores, key=bubble_scores.get) if bubble_scores else None
    highest_distortion = max(
        echo_items,
        key=lambda item: (item.distortion_level, item.estimated_reach, item.id),
    )
    return {
        "top_echo_type": echo_type_counts.most_common(1)[0][0],
        "top_bubble": (
            {
                "bubble_id": top_bubble_id,
                "label": bubble_labels.get(top_bubble_id, top_bubble_id),
                "risk_score": round(bubble_scores[top_bubble_id], 2),
            }
            if top_bubble_id
            else None
        ),
        "highest_distortion_item": {
            "id": highest_distortion.id,
            "echo_type": highest_distortion.echo_type.value,
            "distortion_level": highest_distortion.distortion_level,
            "estimated_reach": highest_distortion.estimated_reach,
            "text": highest_distortion.text,
        },
    }
