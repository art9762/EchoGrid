from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class EchoGridModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Stance(str, Enum):
    SUPPORT = "support"
    OPPOSE = "oppose"
    NEUTRAL = "neutral"
    CONFUSED = "confused"


class ActorType(str, Enum):
    PUBLIC_BROADCASTER = "public_broadcaster"
    TABLOID = "tabloid"
    PARTISAN_OUTLET = "partisan_outlet"
    INFLUENCER = "influencer"
    EXPERT = "expert"
    GOVERNMENT_SOURCE = "government_source"
    GRASSROOTS_ACCOUNT = "grassroots_account"


class PoliticalBias(str, Enum):
    LEFT = "left"
    CENTER_LEFT = "center_left"
    CENTER = "center"
    CENTER_RIGHT = "center_right"
    RIGHT = "right"
    POPULIST = "populist"
    NONE = "none"


class MediaTone(str, Enum):
    NEUTRAL = "neutral"
    TECHNOCRATIC = "technocratic"
    EMOTIONAL = "emotional"
    OUTRAGE = "outrage"
    SKEPTICAL = "skeptical"
    EXPLANATORY = "explanatory"
    IRONIC = "ironic"


class EchoType(str, Enum):
    VIRAL_COMMENT = "viral_comment"
    REPOST_SUMMARY = "repost_summary"
    TABLOID_HEADLINE = "tabloid_headline"
    INFLUENCER_POST = "influencer_post"
    EXPERT_CORRECTION = "expert_correction"
    MEME_CAPTION = "meme_caption"
    PARTISAN_ATTACK = "partisan_attack"
    OFFICIAL_CLARIFICATION = "official_clarification"


class EmotionLabel(str, Enum):
    ANGER = "anger"
    FEAR = "fear"
    HOPE = "hope"
    DISTRUST = "distrust"
    REASSURANCE = "reassurance"
    MOCKERY = "mockery"
    NEUTRAL = "neutral"


class LLMProvider(str, Enum):
    MOCK = "mock"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"
    OPENAI = "openai"


class Emotions(EchoGridModel):
    anger: int = Field(ge=0, le=100)
    fear: int = Field(ge=0, le=100)
    hope: int = Field(ge=0, le=100)
    distrust: int = Field(ge=0, le=100)
    indifference: int = Field(ge=0, le=100)

    @property
    def average(self) -> float:
        return (
            self.anger + self.fear + self.hope + self.distrust + self.indifference
        ) / 5


class EmotionShift(EchoGridModel):
    anger: int = Field(ge=-100, le=100)
    fear: int = Field(ge=-100, le=100)
    hope: int = Field(ge=-100, le=100)
    distrust: int = Field(ge=-100, le=100)
    indifference: int = Field(ge=-100, le=100)


class AgentProfile(EchoGridModel):
    id: str = Field(min_length=1)
    age: int = Field(ge=16, le=100)
    gender: str = Field(min_length=1)
    country: str = Field(min_length=1)
    location_type: str = Field(min_length=1)
    education_level: str = Field(min_length=1)
    income_level: str = Field(min_length=1)
    occupation_category: str = Field(min_length=1)
    family_status: str = Field(min_length=1)
    economic_position: str = Field(min_length=1)
    social_position: str = Field(min_length=1)
    institutional_trust: int = Field(ge=0, le=100)
    political_engagement: str = Field(min_length=1)
    risk_aversion: int = Field(ge=0, le=100)
    openness_to_change: int = Field(ge=0, le=100)
    anger_proneness: int = Field(ge=0, le=100)
    empathy_level: int = Field(ge=0, le=100)
    need_for_stability: int = Field(ge=0, le=100)
    status_anxiety: int = Field(ge=0, le=100)
    media_diet: list[str] = Field(default_factory=list)
    preferred_content_style: str = Field(min_length=1)
    main_concerns: list[str] = Field(default_factory=list)
    values: list[str] = Field(default_factory=list)


class PopulationConfig(EchoGridModel):
    country: str = Field(default="United States", min_length=1)
    population_size: int = Field(default=250, ge=1, le=100_000)
    seed: int = Field(default=42)
    preset_name: str | None = None
    age_distribution: dict[str, float] | None = None
    income_distribution: dict[str, float] | None = None
    politics_distribution: dict[str, float] | None = None
    education_distribution: dict[str, float] | None = None
    media_diet_distribution: dict[str, float] | None = None


class NewsEvent(EchoGridModel):
    title: str = Field(min_length=1)
    description: str = Field(min_length=1)
    country: str = Field(min_length=1)
    topic: str = Field(min_length=1)
    source_type: str = Field(min_length=1)
    original_text: str = Field(min_length=1)


class NewsFrame(EchoGridModel):
    frame_id: str = Field(min_length=1)
    label: str = Field(min_length=1)
    text: str = Field(min_length=1)
    tone: str = Field(min_length=1)
    implied_values: list[str] = Field(default_factory=list)
    source_type: str | None = None


class AgentReaction(EchoGridModel):
    agent_id: str = Field(min_length=1)
    frame_id: str = Field(min_length=1)
    stance: Stance
    stance_strength: int = Field(ge=0, le=100)
    emotions: Emotions
    trust_in_source: int = Field(ge=0, le=100)
    perceived_personal_impact: int = Field(ge=0, le=100)
    perceived_group_impact: int = Field(ge=0, le=100)
    share_likelihood: int = Field(ge=0, le=100)
    comment_likelihood: int = Field(ge=0, le=100)
    discussion_likelihood: int = Field(ge=0, le=100)
    triggered_values: list[str] = Field(default_factory=list)
    main_reason: str = Field(min_length=1)
    likely_comment: str = Field(min_length=1)
    what_could_change_mind: str = Field(min_length=1)

    @property
    def emotional_intensity(self) -> float:
        return self.emotions.average


class MediaActor(EchoGridModel):
    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    actor_type: ActorType
    political_bias: PoliticalBias
    tone: MediaTone
    sensationalism: int = Field(ge=0, le=100)
    credibility: int = Field(ge=0, le=100)
    reach: int = Field(ge=0, le=100)
    audience_affinity: list[str] = Field(default_factory=list)
    typical_platforms: list[str] = Field(default_factory=list)


class SocialBubble(EchoGridModel):
    id: str = Field(min_length=1)
    label: str = Field(min_length=1)
    description: str = Field(min_length=1)
    selection_rules: dict[str, Any] = Field(default_factory=dict)
    dominant_values: list[str] = Field(default_factory=list)
    dominant_media: list[str] = Field(default_factory=list)
    internal_trust: int = Field(ge=0, le=100)
    external_trust: int = Field(ge=0, le=100)
    outrage_sensitivity: int = Field(ge=0, le=100)
    correction_resistance: int = Field(ge=0, le=100)


class EchoItem(EchoGridModel):
    id: str = Field(min_length=1)
    round_number: int = Field(ge=1)
    echo_type: EchoType
    text: str = Field(min_length=1)
    origin_actor_id: str | None = None
    source_frame_id: str | None = None
    target_bubbles: list[str] = Field(default_factory=list)
    emotion: EmotionLabel
    distortion_level: int = Field(ge=0, le=100)
    sensationalism_level: int = Field(ge=0, le=100)
    estimated_reach: int = Field(ge=0, le=100)
    created_from_reaction_ids: list[str] = Field(default_factory=list)


class EchoReaction(EchoGridModel):
    agent_id: str = Field(min_length=1)
    echo_item_id: str = Field(min_length=1)
    bubble_id: str | None = None
    previous_stance: Stance
    updated_stance: Stance
    stance_shift: int = Field(ge=-100, le=100)
    emotion_shift: EmotionShift
    trust_shift: int = Field(ge=-100, le=100)
    share_likelihood_shift: int = Field(ge=-100, le=100)
    reason: str = Field(min_length=1)


class SimulationConfig(EchoGridModel):
    provider: LLMProvider = LLMProvider.MOCK
    reaction_model: str = "claude-haiku-4-5-20251001"
    echo_model: str = "claude-sonnet-4-6"
    report_model: str = "claude-sonnet-4-6"
    gemini_reaction_model: str = "gemini-2.5-flash-lite"
    gemini_echo_model: str = "gemini-2.5-flash"
    openai_reaction_model: str = "gpt-5.4-nano"
    openai_echo_model: str = "gpt-5.4-mini"
    openai_report_model: str = "gpt-5.4-mini"
    echo_enabled: bool = True
    echo_rounds: int = Field(default=1, ge=0, le=5)
    selected_frame_ids: list[str] = Field(default_factory=list)
    max_workers: int = Field(default=8, ge=1, le=64)


class RoundSummary(EchoGridModel):
    simulation_id: str = Field(min_length=1)
    round_number: int = Field(ge=0)
    label: str = Field(min_length=1)
    metrics: dict[str, Any] = Field(default_factory=dict)


class FinalAgentState(EchoGridModel):
    agent_id: str = Field(min_length=1)
    initial_stance: Stance
    final_stance: Stance
    initial_stance_strength: int = Field(ge=0, le=100)
    final_stance_strength: int = Field(ge=0, le=100)
    initial_trust: int = Field(ge=0, le=100)
    final_trust: int = Field(ge=0, le=100)
    initial_share_likelihood: int = Field(ge=0, le=100)
    final_share_likelihood: int = Field(ge=0, le=100)
    social_bubble_id: str | None = None


class EchoSimulationResult(EchoGridModel):
    simulation_id: str = Field(min_length=1)
    echo_items: list[EchoItem] = Field(default_factory=list)
    echo_reactions: list[EchoReaction] = Field(default_factory=list)
    round_summaries: list[RoundSummary] = Field(default_factory=list)
    final_reaction_state_by_agent: dict[str, FinalAgentState] = Field(
        default_factory=dict
    )
    amplification_metrics: dict[str, float] = Field(default_factory=dict)
