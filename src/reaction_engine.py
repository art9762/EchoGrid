"""Initial agent reaction generation."""

from __future__ import annotations

from src.schemas import AgentProfile, AgentReaction, Emotions, NewsEvent, NewsFrame, Stance
from src.utils import clamp, seeded_rng

FRAME_EFFECTS = {
    "neutral": {"support": 0, "anger": -6, "trust": 8},
    "technocratic": {"support": 5, "anger": -10, "trust": 6},
    "progressive": {"support": 8, "anger": 2, "trust": 0},
    "populist": {"support": -8, "anger": 13, "trust": -8},
    "skeptical": {"support": -6, "anger": 6, "trust": -7},
    "tabloid_outrage": {"support": -12, "anger": 22, "trust": -18},
}


def run_initial_reactions(
    agents: list[AgentProfile],
    event: NewsEvent,
    frames: list[NewsFrame],
    mode: str = "mock",
    seed: int = 42,
) -> list[AgentReaction]:
    return [
        run_agent_reaction(agent, event, frame, mode=mode, seed=seed)
        for frame in frames
        for agent in agents
    ]


def run_agent_reaction(
    agent: AgentProfile,
    event: NewsEvent,
    frame: NewsFrame,
    mode: str = "mock",
    seed: int = 42,
) -> AgentReaction:
    if mode != "mock":
        raise NotImplementedError("LLM reaction mode will be added after mock mode.")
    return _mock_agent_reaction(agent, event, frame, seed)


def _mock_agent_reaction(
    agent: AgentProfile, event: NewsEvent, frame: NewsFrame, seed: int
) -> AgentReaction:
    rng = seeded_rng(seed, agent.id, event.title, frame.frame_id)
    effects = FRAME_EFFECTS.get(frame.frame_id, FRAME_EFFECTS["neutral"])
    event_relevance = _event_relevance(agent, event)

    support_score = 50 + effects["support"]
    support_score += (agent.institutional_trust - 50) * 0.18
    support_score += (agent.openness_to_change - 50) * 0.14
    support_score -= (agent.risk_aversion - 50) * 0.12
    support_score += event_relevance * 0.08

    if "fairness" in agent.values and frame.frame_id == "progressive":
        support_score += 9
    if "freedom" in agent.values and frame.frame_id in {"populist", "tabloid_outrage"}:
        support_score -= 8
    if "stability" in agent.values and frame.frame_id == "technocratic":
        support_score += 5
    if event.topic in {"taxes", "housing"} and agent.income_level in {"low", "lower_middle"}:
        support_score -= 4

    support_score += rng.gauss(0, 8)
    stance = _stance_from_score(support_score, agent, frame, rng.random())
    stance_strength = clamp(35 + abs(support_score - 50) * 1.15 + rng.gauss(0, 7))

    trust_in_source = clamp(
        agent.institutional_trust
        + effects["trust"]
        + _source_trust_adjustment(agent, frame)
        + rng.gauss(0, 8)
    )

    anger = clamp(
        agent.anger_proneness * 0.45
        + effects["anger"]
        + (18 if stance == Stance.OPPOSE else 0)
        + rng.gauss(0, 8)
    )
    fear = clamp(
        agent.risk_aversion * 0.38
        + event_relevance * 0.16
        + (10 if frame.frame_id in {"skeptical", "tabloid_outrage"} else 0)
        + rng.gauss(0, 8)
    )
    hope = clamp(
        agent.openness_to_change * 0.35
        + (22 if stance == Stance.SUPPORT else 4)
        - (8 if frame.frame_id == "tabloid_outrage" else 0)
        + rng.gauss(0, 8)
    )
    distrust = clamp(
        (100 - agent.institutional_trust) * 0.42
        + (100 - trust_in_source) * 0.26
        + (12 if frame.frame_id in {"populist", "skeptical", "tabloid_outrage"} else 0)
        + rng.gauss(0, 8)
    )
    indifference = clamp(
        48
        - event_relevance * 0.25
        - max(anger, fear, hope, distrust) * 0.18
        + (10 if agent.political_engagement == "low" else 0)
        + rng.gauss(0, 6)
    )
    emotions = Emotions(
        anger=anger,
        fear=fear,
        hope=hope,
        distrust=distrust,
        indifference=indifference,
    )

    personal_impact = clamp(event_relevance + _income_impact(agent, event) + rng.gauss(0, 8))
    group_impact = clamp(event_relevance + (100 - agent.institutional_trust) * 0.18 + rng.gauss(0, 8))
    share_likelihood = clamp(
        emotions.average * 0.48
        + (12 if agent.political_engagement == "high" else 0)
        + (10 if {"social_media", "influencers", "tabloid"} & set(agent.media_diet) else 0)
        + rng.gauss(0, 7)
    )
    comment_likelihood = clamp(share_likelihood * 0.72 + agent.anger_proneness * 0.18 + rng.gauss(0, 6))
    discussion_likelihood = clamp(
        share_likelihood * 0.42
        + (18 if agent.political_engagement in {"moderate", "high"} else 4)
        + rng.gauss(0, 7)
    )

    return AgentReaction(
        agent_id=agent.id,
        frame_id=frame.frame_id,
        stance=stance,
        stance_strength=stance_strength,
        emotions=emotions,
        trust_in_source=trust_in_source,
        perceived_personal_impact=personal_impact,
        perceived_group_impact=group_impact,
        share_likelihood=share_likelihood,
        comment_likelihood=comment_likelihood,
        discussion_likelihood=discussion_likelihood,
        triggered_values=_triggered_values(agent, frame),
        main_reason=_main_reason(agent, event, frame, stance),
        likely_comment=_likely_comment(agent, event, frame, stance),
        what_could_change_mind=_change_mind(stance),
    )


def _event_relevance(agent: AgentProfile, event: NewsEvent) -> int:
    topic = event.topic.lower()
    score = 35
    if topic in agent.main_concerns:
        score += 35
    if topic == "taxes" and agent.income_level in {"low", "lower_middle", "middle"}:
        score += 20
    if topic == "housing" and "housing" in agent.main_concerns:
        score += 20
    if topic == "jobs" and agent.occupation_category not in {"retired", "student"}:
        score += 18
    return clamp(score)


def _source_trust_adjustment(agent: AgentProfile, frame: NewsFrame) -> int:
    source = frame.source_type or ""
    if source in agent.media_diet:
        return 14
    if source == "public_broadcaster" and "public_broadcaster" in agent.media_diet:
        return 12
    if source == "tabloid" and "tabloid" not in agent.media_diet:
        return -18
    if source == "policy_outlet" and "expert_analysis" in agent.media_diet:
        return 10
    return 0


def _income_impact(agent: AgentProfile, event: NewsEvent) -> int:
    if event.topic in {"taxes", "housing"} and agent.income_level in {"low", "lower_middle"}:
        return 18
    if agent.economic_position in {"precarious", "strained"}:
        return 10
    return 0


def _stance_from_score(
    score: float, agent: AgentProfile, frame: NewsFrame, chance: float
) -> Stance:
    if 43 <= score <= 57 and agent.political_engagement == "low" and chance < 0.16:
        return Stance.CONFUSED
    if score >= 59:
        return Stance.SUPPORT
    if score <= 41:
        return Stance.OPPOSE
    if frame.frame_id == "technocratic" and agent.education_level == "secondary" and chance < 0.12:
        return Stance.CONFUSED
    return Stance.NEUTRAL


def _triggered_values(agent: AgentProfile, frame: NewsFrame) -> list[str]:
    values = [value for value in agent.values if value in frame.implied_values]
    if values:
        return values
    return agent.values[:2]


def _main_reason(
    agent: AgentProfile, event: NewsEvent, frame: NewsFrame, stance: Stance
) -> str:
    concern = agent.main_concerns[0] if agent.main_concerns else event.topic
    if stance == Stance.SUPPORT:
        return f"The {frame.label.lower()} frame connects with concerns about {concern} and feels potentially useful."
    if stance == Stance.OPPOSE:
        return f"The {frame.label.lower()} frame raises doubts about costs, trust, or unintended effects."
    if stance == Stance.CONFUSED:
        return "The message does not provide enough concrete detail to form a clear view."
    return f"The message seems relevant to {concern}, but the personal consequences are still unclear."


def _likely_comment(
    agent: AgentProfile, event: NewsEvent, frame: NewsFrame, stance: Stance
) -> str:
    if stance == Stance.SUPPORT:
        return f"If this actually helps with {event.topic}, I could get behind it."
    if stance == Stance.OPPOSE:
        return "This sounds like another policy where ordinary people may pay the price."
    if stance == Stance.CONFUSED:
        return "I need a clearer explanation before I know what to think."
    if "expert_analysis" in agent.media_diet:
        return "I would want to see the details and evidence before reacting strongly."
    return "Could be good or bad depending on how it is done."


def _change_mind(stance: Stance) -> str:
    if stance == Stance.SUPPORT:
        return "Credible evidence of major unintended costs or unfair implementation."
    if stance == Stance.OPPOSE:
        return "Clear safeguards, transparent costs, and trusted independent evidence."
    return "Specific examples, independent analysis, and clearer practical details."
