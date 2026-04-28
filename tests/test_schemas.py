import pytest
from pydantic import ValidationError

from src.schemas import (
    AgentProfile,
    AgentReaction,
    EchoItem,
    EchoReaction,
    EchoType,
    EmotionShift,
    EmotionLabel,
    Emotions,
    NewsEvent,
    NewsFrame,
    Stance,
)


def make_agent() -> AgentProfile:
    return AgentProfile(
        id="agent-001",
        age=42,
        gender="woman",
        country="United States",
        location_type="suburban",
        education_level="college",
        income_level="middle",
        occupation_category="education",
        family_status="parent",
        economic_position="stable",
        social_position="middle_class",
        institutional_trust=61,
        political_engagement="moderate",
        risk_aversion=52,
        openness_to_change=47,
        anger_proneness=31,
        empathy_level=70,
        need_for_stability=58,
        status_anxiety=35,
        media_diet=["public_broadcaster", "local_news"],
        preferred_content_style="explanatory",
        main_concerns=["cost_of_living", "education"],
        values=["fairness", "stability"],
    )


def test_agent_profile_accepts_valid_persona() -> None:
    agent = make_agent()

    assert agent.id == "agent-001"
    assert agent.institutional_trust == 61
    assert "stability" in agent.values


def test_agent_profile_rejects_out_of_range_scores() -> None:
    with pytest.raises(ValidationError):
        AgentProfile(**{**make_agent().model_dump(), "risk_aversion": 101})


def test_news_event_and_frame_validate() -> None:
    event = NewsEvent(
        title="City restricts short-term rentals",
        description="A city council proposes limits on short-term rental listings.",
        country="United States",
        topic="housing",
        source_type="official_statement",
        original_text="The council announced a proposed cap on short-term rentals.",
    )
    frame = NewsFrame(
        frame_id="neutral",
        label="Neutral",
        text="The proposal would limit short-term rentals while preserving some permits.",
        tone="neutral",
        implied_values=["stability", "fairness"],
        source_type="public_broadcaster",
    )

    assert event.topic == "housing"
    assert frame.frame_id == "neutral"


def test_agent_reaction_validates_nested_emotions_and_stance() -> None:
    reaction = AgentReaction(
        agent_id="agent-001",
        frame_id="neutral",
        stance=Stance.SUPPORT,
        stance_strength=66,
        emotions=Emotions(anger=15, fear=20, hope=45, distrust=22, indifference=12),
        trust_in_source=64,
        perceived_personal_impact=40,
        perceived_group_impact=62,
        share_likelihood=35,
        comment_likelihood=20,
        discussion_likelihood=45,
        triggered_values=["stability"],
        main_reason="The frame sounds measured and addresses housing availability.",
        likely_comment="This might help if it is implemented carefully.",
        what_could_change_mind="Evidence that renters would not benefit.",
    )

    assert reaction.stance == Stance.SUPPORT
    assert reaction.emotional_intensity == pytest.approx(22.8)


def test_echo_item_and_echo_reaction_validate() -> None:
    item = EchoItem(
        id="echo-001",
        round_number=1,
        echo_type=EchoType.TABLOID_HEADLINE,
        text="City plan sparks fierce debate over housing rules",
        origin_actor_id="tabloid-001",
        source_frame_id="neutral",
        target_bubbles=["low_trust_working_class"],
        emotion=EmotionLabel.ANGER,
        distortion_level=42,
        sensationalism_level=76,
        estimated_reach=80,
        created_from_reaction_ids=["reaction-001"],
    )
    reaction = EchoReaction(
        agent_id="agent-001",
        echo_item_id="echo-001",
        previous_stance=Stance.NEUTRAL,
        updated_stance=Stance.OPPOSE,
        stance_shift=-18,
        emotion_shift=EmotionShift(
            anger=20, fear=10, hope=-8, distrust=18, indifference=-5
        ),
        trust_shift=-12,
        share_likelihood_shift=16,
        reason="The headline increases concern and distrust.",
    )

    assert item.echo_type == EchoType.TABLOID_HEADLINE
    assert reaction.stance_shift == -18
