"""Aggregation and metric helpers for EchoGrid simulations."""

from __future__ import annotations

from statistics import mean, median

import pandas as pd

from src.schemas import AgentProfile, AgentReaction, EchoItem, EchoReaction, SocialBubble, Stance
from src.utils import clamp


STANCE_ORDER = [Stance.SUPPORT, Stance.OPPOSE, Stance.NEUTRAL, Stance.CONFUSED]
STANCE_SIGN = {
    Stance.SUPPORT: 1,
    Stance.OPPOSE: -1,
    Stance.NEUTRAL: 0,
    Stance.CONFUSED: 0,
}


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
        segment = getattr(agent, by_field)
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


def unexpected_segments(
    reactions: list[AgentReaction], agents: list[AgentProfile]
) -> list[dict[str, object]]:
    rows = segment_breakdown(reactions, agents, by_field="income_level")
    return [
        row
        for row in rows
        if row["count"] >= 5
        and (row["average_anger"] >= 60 or row["average_share_likelihood"] >= 60)
    ]


def echo_amplification_index(
    initial_reactions: list[AgentReaction],
    echo_reactions: list[EchoReaction],
    echo_items: list[EchoItem],
) -> float:
    if not initial_reactions or not echo_reactions:
        return 0.0
    anger = max(0.0, anger_delta(echo_reactions))
    trust_loss = max(0.0, -trust_delta(echo_reactions))
    share_growth = max(0.0, virality_growth(echo_reactions))
    stance_motion = mean(abs(reaction.stance_shift) for reaction in echo_reactions)
    distortion = distortion_drift(echo_items)
    score = anger * 0.22 + trust_loss * 0.2 + share_growth * 0.22 + stance_motion * 0.18 + distortion * 0.18
    return round(clamp(score), 2)


def distortion_drift(echo_items: list[EchoItem]) -> float:
    if not echo_items:
        return 0.0
    total_reach = sum(max(item.estimated_reach, 1) for item in echo_items)
    weighted = sum(item.distortion_level * max(item.estimated_reach, 1) for item in echo_items)
    return round(weighted / total_reach, 2)


def polarization_delta(
    initial_reactions: list[AgentReaction], echo_reactions: list[EchoReaction]
) -> float:
    if not echo_reactions:
        return 0.0
    return round(mean(abs(reaction.stance_shift) for reaction in echo_reactions), 2)


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
