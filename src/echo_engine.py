"""Echo item generation and echo-round reaction orchestration."""

from __future__ import annotations

from src.analytics import (
    anger_delta,
    distortion_drift,
    echo_amplification_index,
    trust_delta,
    virality_growth,
)
from src.schemas import (
    ActorType,
    AgentProfile,
    AgentReaction,
    EchoItem,
    EchoReaction,
    EchoSimulationResult,
    EchoType,
    EmotionLabel,
    EmotionShift,
    FinalAgentState,
    MediaActor,
    NewsEvent,
    NewsFrame,
    SocialBubble,
    Stance,
)
from src.utils import clamp, stable_seed, seeded_rng


def generate_echo_items(
    event: NewsEvent,
    frames: list[NewsFrame],
    reactions: list[AgentReaction],
    media_actors: list[MediaActor],
    bubbles: list[SocialBubble],
    mode: str = "mock",
    seed: int = 42,
) -> list[EchoItem]:
    if mode != "mock":
        raise NotImplementedError("LLM echo item generation will be added later.")

    intense_reactions = sorted(
        reactions,
        key=lambda reaction: (
            reaction.emotional_intensity + reaction.share_likelihood,
            reaction.agent_id,
            reaction.frame_id,
        ),
        reverse=True,
    )
    bubble_ids = {bubble.id for bubble in bubbles}
    frame_ids = [frame.frame_id for frame in frames] or [None]

    items: list[EchoItem] = []
    for index, actor in enumerate(media_actors):
        rng = seeded_rng(seed, event.title, actor.id, index)
        source_reactions = intense_reactions[index : index + 3] or intense_reactions[:1]
        echo_type = _echo_type_for_actor(actor)
        emotion = _emotion_for_echo(actor, echo_type)
        distortion = _distortion_for_actor(actor, echo_type, rng.random())
        sensationalism = clamp(actor.sensationalism + rng.gauss(0, 6))
        target_bubbles = [
            affinity for affinity in actor.audience_affinity if affinity in bubble_ids
        ]
        if not target_bubbles:
            target_bubbles = [sorted(bubble_ids)[index % len(bubble_ids)]]

        items.append(
            EchoItem(
                id=f"echo-{index + 1:03d}",
                round_number=1,
                echo_type=echo_type,
                text=_echo_text(event, actor, echo_type, emotion),
                origin_actor_id=actor.id,
                source_frame_id=frame_ids[index % len(frame_ids)],
                target_bubbles=target_bubbles,
                emotion=emotion,
                distortion_level=distortion,
                sensationalism_level=sensationalism,
                estimated_reach=clamp(actor.reach + rng.gauss(0, 7)),
                created_from_reaction_ids=[
                    f"{reaction.agent_id}:{reaction.frame_id}"
                    for reaction in source_reactions
                ],
            )
        )
    return items


def run_echo_reaction(
    agent: AgentProfile,
    original_reaction: AgentReaction,
    echo_item: EchoItem,
    bubble: SocialBubble,
    mode: str = "mock",
    seed: int = 42,
) -> EchoReaction:
    if mode != "mock":
        raise NotImplementedError("LLM echo reaction mode will be added later.")
    return _mock_echo_reaction(agent, original_reaction, echo_item, bubble, seed)


def run_echo_simulation(
    agents: list[AgentProfile],
    event: NewsEvent,
    frames: list[NewsFrame],
    initial_reactions: list[AgentReaction],
    media_actors: list[MediaActor],
    bubbles: list[SocialBubble],
    bubble_assignments: dict[str, list[str]],
    mode: str = "mock",
    seed: int = 42,
    echo_items_override: list[EchoItem] | None = None,
) -> EchoSimulationResult:
    echo_items = echo_items_override or generate_echo_items(
        event, frames, initial_reactions, media_actors, bubbles, mode=mode, seed=seed
    )
    agent_lookup = {agent.id: agent for agent in agents}
    bubble_lookup = {bubble.id: bubble for bubble in bubbles}
    bubble_by_agent = {
        agent_id: bubble_id
        for bubble_id, agent_ids in bubble_assignments.items()
        for agent_id in agent_ids
    }
    original_by_agent: dict[str, AgentReaction] = {}
    for reaction in initial_reactions:
        original_by_agent.setdefault(reaction.agent_id, reaction)

    echo_reactions: list[EchoReaction] = []
    final_states: dict[str, FinalAgentState] = {}
    for agent_id, original in original_by_agent.items():
        agent = agent_lookup[agent_id]
        bubble_id = bubble_by_agent.get(agent_id, "apolitical_cost_sensitive")
        bubble = bubble_lookup[bubble_id]
        item = _select_echo_item_for_bubble(agent, bubble, echo_items, seed)
        echo_reaction = run_echo_reaction(
            agent, original, item, bubble, mode=mode, seed=seed
        )
        echo_reactions.append(echo_reaction)
        final_states[agent_id] = _final_state(agent_id, original, echo_reaction, bubble_id)

    metrics = {
        "echo_amplification_index": echo_amplification_index(
            initial_reactions, echo_reactions, echo_items
        ),
        "distortion_drift": distortion_drift(echo_items),
        "trust_delta": trust_delta(echo_reactions),
        "anger_delta": anger_delta(echo_reactions),
        "virality_growth": virality_growth(echo_reactions),
    }

    return EchoSimulationResult(
        simulation_id=f"sim-{stable_seed(seed, event.title) % 1_000_000:06d}",
        echo_items=echo_items,
        echo_reactions=echo_reactions,
        final_reaction_state_by_agent=final_states,
        amplification_metrics=metrics,
    )


def _mock_echo_reaction(
    agent: AgentProfile,
    original: AgentReaction,
    item: EchoItem,
    bubble: SocialBubble,
    seed: int,
) -> EchoReaction:
    rng = seeded_rng(seed, agent.id, item.id, bubble.id)
    correction = item.echo_type in {
        EchoType.EXPERT_CORRECTION,
        EchoType.OFFICIAL_CLARIFICATION,
    }
    outrage = item.emotion in {
        EmotionLabel.ANGER,
        EmotionLabel.FEAR,
        EmotionLabel.DISTRUST,
        EmotionLabel.MOCKERY,
    }

    if correction:
        correction_acceptance = (
            agent.openness_to_change * 0.35
            + agent.institutional_trust * 0.35
            + (100 - bubble.correction_resistance) * 0.3
        )
        stance_shift = clamp((correction_acceptance - 50) * 0.35 + rng.gauss(0, 5), -30, 30)
        trust_shift = clamp(8 + correction_acceptance * 0.12 + rng.gauss(0, 4), -20, 28)
        anger_shift = clamp(-8 - correction_acceptance * 0.08 + rng.gauss(0, 4), -28, 8)
        distrust_shift = clamp(-6 - correction_acceptance * 0.08 + rng.gauss(0, 4), -28, 8)
        share_shift = clamp(-4 + (100 - correction_acceptance) * 0.08 + rng.gauss(0, 4), -20, 18)
    elif outrage:
        susceptibility = (
            bubble.outrage_sensitivity * 0.34
            + agent.anger_proneness * 0.26
            + item.sensationalism_level * 0.2
            + item.distortion_level * 0.2
        )
        direction = -1 if original.stance != Stance.SUPPORT else 1
        if item.echo_type in {EchoType.TABLOID_HEADLINE, EchoType.PARTISAN_ATTACK}:
            direction = -1
        stance_shift = clamp(direction * (susceptibility - 35) * 0.38 + rng.gauss(0, 7), -45, 45)
        trust_shift = clamp(-item.distortion_level * 0.18 - item.sensationalism_level * 0.1 + rng.gauss(0, 5), -40, 12)
        anger_shift = clamp(5 + susceptibility * 0.18 + rng.gauss(0, 5), -8, 38)
        distrust_shift = clamp(4 + item.distortion_level * 0.16 + rng.gauss(0, 5), -8, 36)
        share_shift = clamp(6 + susceptibility * 0.2 + rng.gauss(0, 7), -8, 45)
    else:
        mildness = 100 - item.sensationalism_level
        stance_shift = clamp((agent.openness_to_change - 50) * 0.12 + rng.gauss(0, 5), -18, 18)
        trust_shift = clamp((mildness - 50) * 0.1 + rng.gauss(0, 4), -16, 16)
        anger_shift = clamp(rng.gauss(0, 5), -12, 12)
        distrust_shift = clamp((item.distortion_level - 30) * 0.08 + rng.gauss(0, 4), -12, 16)
        share_shift = clamp((item.estimated_reach - 50) * 0.1 + rng.gauss(0, 5), -12, 20)

    return EchoReaction(
        agent_id=agent.id,
        echo_item_id=item.id,
        bubble_id=bubble.id,
        previous_stance=original.stance,
        updated_stance=_updated_stance(original.stance, stance_shift),
        stance_shift=stance_shift,
        emotion_shift=EmotionShift(
            anger=anger_shift,
            fear=clamp((anger_shift + distrust_shift) * 0.35 + rng.gauss(0, 3), -20, 28),
            hope=clamp((-anger_shift * 0.25 if outrage else 4) + rng.gauss(0, 4), -25, 20),
            distrust=distrust_shift,
            indifference=clamp(-abs(share_shift) * 0.2 + rng.gauss(0, 3), -18, 12),
        ),
        trust_shift=trust_shift,
        share_likelihood_shift=share_shift,
        reason=_echo_reaction_reason(item, correction, outrage),
    )


def _echo_type_for_actor(actor: MediaActor) -> EchoType:
    if actor.actor_type == ActorType.TABLOID:
        return EchoType.TABLOID_HEADLINE
    if actor.actor_type == ActorType.EXPERT:
        return EchoType.EXPERT_CORRECTION
    if actor.actor_type == ActorType.GOVERNMENT_SOURCE:
        return EchoType.OFFICIAL_CLARIFICATION
    if actor.actor_type == ActorType.INFLUENCER:
        return EchoType.INFLUENCER_POST
    if actor.actor_type == ActorType.GRASSROOTS_ACCOUNT:
        return EchoType.VIRAL_COMMENT
    if actor.actor_type == ActorType.PARTISAN_OUTLET and actor.political_bias.value != "center":
        return EchoType.PARTISAN_ATTACK
    return EchoType.REPOST_SUMMARY


def _emotion_for_echo(actor: MediaActor, echo_type: EchoType) -> EmotionLabel:
    if echo_type in {EchoType.EXPERT_CORRECTION, EchoType.OFFICIAL_CLARIFICATION}:
        return EmotionLabel.REASSURANCE
    if actor.tone.value == "outrage" or echo_type == EchoType.PARTISAN_ATTACK:
        return EmotionLabel.ANGER
    if actor.tone.value == "skeptical":
        return EmotionLabel.DISTRUST
    if actor.tone.value == "ironic":
        return EmotionLabel.MOCKERY
    if actor.tone.value == "emotional":
        return EmotionLabel.FEAR
    return EmotionLabel.NEUTRAL


def _distortion_for_actor(actor: MediaActor, echo_type: EchoType, jitter: float) -> int:
    if echo_type in {EchoType.EXPERT_CORRECTION, EchoType.OFFICIAL_CLARIFICATION}:
        return clamp(6 + jitter * 8)
    return clamp(actor.sensationalism * 0.58 + (100 - actor.credibility) * 0.24 + jitter * 12)


def _echo_text(
    event: NewsEvent, actor: MediaActor, echo_type: EchoType, emotion: EmotionLabel
) -> str:
    if echo_type == EchoType.TABLOID_HEADLINE:
        return f"{actor.name}: Anger grows as {event.title.lower()} could hit households hard"
    if echo_type == EchoType.EXPERT_CORRECTION:
        return f"{actor.name}: What the evidence does and does not show about {event.title.lower()}"
    if echo_type == EchoType.OFFICIAL_CLARIFICATION:
        return f"{actor.name}: Officials clarify scope and safeguards for {event.title.lower()}"
    if echo_type == EchoType.PARTISAN_ATTACK:
        return f"{actor.name}: Opponents say {event.title.lower()} reveals misplaced priorities"
    if echo_type == EchoType.INFLUENCER_POST:
        return f"{actor.name}: Here's why people are arguing about {event.title.lower()}"
    if echo_type == EchoType.VIRAL_COMMENT:
        return f"{actor.name}: Everyone seems to have a different story about {event.title.lower()}"
    return f"{actor.name}: A quick summary of the debate around {event.title.lower()} ({emotion.value})"


def _select_echo_item_for_bubble(
    agent: AgentProfile, bubble: SocialBubble, items: list[EchoItem], seed: int
) -> EchoItem:
    targeted = [item for item in items if bubble.id in item.target_bubbles] or items
    rng = seeded_rng(seed, agent.id, bubble.id, "echo-selection")
    return targeted[rng.randrange(len(targeted))]


def _updated_stance(previous: Stance, shift: int) -> Stance:
    base = {
        Stance.SUPPORT: 35,
        Stance.OPPOSE: -35,
        Stance.NEUTRAL: 0,
        Stance.CONFUSED: 0,
    }[previous]
    updated = base + shift
    if updated >= 22:
        return Stance.SUPPORT
    if updated <= -22:
        return Stance.OPPOSE
    return Stance.NEUTRAL


def _final_state(
    agent_id: str,
    original: AgentReaction,
    echo_reaction: EchoReaction,
    bubble_id: str,
) -> FinalAgentState:
    return FinalAgentState(
        agent_id=agent_id,
        initial_stance=original.stance,
        final_stance=echo_reaction.updated_stance,
        initial_stance_strength=original.stance_strength,
        final_stance_strength=clamp(
            original.stance_strength + abs(echo_reaction.stance_shift) * 0.5
        ),
        initial_trust=original.trust_in_source,
        final_trust=clamp(original.trust_in_source + echo_reaction.trust_shift),
        initial_share_likelihood=original.share_likelihood,
        final_share_likelihood=clamp(
            original.share_likelihood + echo_reaction.share_likelihood_shift
        ),
        social_bubble_id=bubble_id,
    )


def _echo_reaction_reason(
    item: EchoItem, correction: bool, outrage: bool
) -> str:
    if correction:
        return "The item provides a corrective or clarifying frame, so trust and anger shift depend on openness and correction resistance."
    if outrage:
        return "The item uses emotional amplification, so stance, distrust, and sharing shift with outrage sensitivity."
    return "The item adds another interpretation without strong emotional pressure."
