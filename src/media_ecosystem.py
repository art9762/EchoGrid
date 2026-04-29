"""Default media actors and media ecosystem helpers."""

from __future__ import annotations

from collections.abc import Iterable

from src.schemas import ActorType, MediaActor, MediaTone, PoliticalBias


def default_media_actors(
    preset: str = "balanced",
    include_actor_types: Iterable[ActorType] | None = None,
) -> list[MediaActor]:
    actors = [
        MediaActor(
            id="public-broadcaster",
            name="Civic Public Broadcaster",
            actor_type=ActorType.PUBLIC_BROADCASTER,
            political_bias=PoliticalBias.CENTER,
            tone=MediaTone.NEUTRAL,
            sensationalism=12,
            credibility=82,
            reach=76,
            audience_affinity=["high_trust_institutionalists", "expert_oriented_professionals"],
            typical_platforms=["tv", "radio", "website"],
        ),
        MediaActor(
            id="policy-brief",
            name="Policy Brief Daily",
            actor_type=ActorType.PARTISAN_OUTLET,
            political_bias=PoliticalBias.CENTER,
            tone=MediaTone.TECHNOCRATIC,
            sensationalism=18,
            credibility=74,
            reach=42,
            audience_affinity=["expert_oriented_professionals"],
            typical_platforms=["newsletter", "website"],
        ),
        MediaActor(
            id="progressive-outlet",
            name="Forward City",
            actor_type=ActorType.PARTISAN_OUTLET,
            political_bias=PoliticalBias.CENTER_LEFT,
            tone=MediaTone.EMOTIONAL,
            sensationalism=46,
            credibility=58,
            reach=59,
            audience_affinity=["young_urban_progressives"],
            typical_platforms=["website", "social"],
        ),
        MediaActor(
            id="conservative-outlet",
            name="Homefront Review",
            actor_type=ActorType.PARTISAN_OUTLET,
            political_bias=PoliticalBias.CENTER_RIGHT,
            tone=MediaTone.SKEPTICAL,
            sensationalism=44,
            credibility=57,
            reach=58,
            audience_affinity=["conservative_suburban_families"],
            typical_platforms=["website", "podcast"],
        ),
        MediaActor(
            id="right-populist-tabloid",
            name="The Daily Alarm",
            actor_type=ActorType.TABLOID,
            political_bias=PoliticalBias.POPULIST,
            tone=MediaTone.OUTRAGE,
            sensationalism=88,
            credibility=28,
            reach=72,
            audience_affinity=["low_trust_working_class", "highly_online_outrage_users"],
            typical_platforms=["social", "website"],
        ),
        MediaActor(
            id="left-activist-page",
            name="People First Network",
            actor_type=ActorType.GRASSROOTS_ACCOUNT,
            political_bias=PoliticalBias.LEFT,
            tone=MediaTone.EMOTIONAL,
            sensationalism=64,
            credibility=43,
            reach=51,
            audience_affinity=["young_urban_progressives", "highly_online_outrage_users"],
            typical_platforms=["social"],
        ),
        MediaActor(
            id="centrist-explainer",
            name="The Context Thread",
            actor_type=ActorType.INFLUENCER,
            political_bias=PoliticalBias.CENTER,
            tone=MediaTone.EXPLANATORY,
            sensationalism=22,
            credibility=68,
            reach=64,
            audience_affinity=["apolitical_cost_sensitive", "expert_oriented_professionals"],
            typical_platforms=["social", "newsletter"],
        ),
        MediaActor(
            id="outrage-influencer",
            name="No Filter Civic",
            actor_type=ActorType.INFLUENCER,
            political_bias=PoliticalBias.POPULIST,
            tone=MediaTone.OUTRAGE,
            sensationalism=91,
            credibility=24,
            reach=83,
            audience_affinity=["highly_online_outrage_users"],
            typical_platforms=["short_video", "social"],
        ),
        MediaActor(
            id="expert-fact-checker",
            name="Evidence Desk",
            actor_type=ActorType.EXPERT,
            political_bias=PoliticalBias.NONE,
            tone=MediaTone.EXPLANATORY,
            sensationalism=8,
            credibility=88,
            reach=45,
            audience_affinity=["high_trust_institutionalists", "expert_oriented_professionals"],
            typical_platforms=["website", "newsletter"],
        ),
        MediaActor(
            id="government-source",
            name="Official Information Office",
            actor_type=ActorType.GOVERNMENT_SOURCE,
            political_bias=PoliticalBias.NONE,
            tone=MediaTone.TECHNOCRATIC,
            sensationalism=5,
            credibility=62,
            reach=54,
            audience_affinity=["high_trust_institutionalists"],
            typical_platforms=["website", "press_release"],
        ),
        MediaActor(
            id="grassroots-viral-account",
            name="Neighborhood Pulse",
            actor_type=ActorType.GRASSROOTS_ACCOUNT,
            political_bias=PoliticalBias.NONE,
            tone=MediaTone.IRONIC,
            sensationalism=58,
            credibility=38,
            reach=67,
            audience_affinity=["apolitical_cost_sensitive", "highly_online_outrage_users"],
            typical_platforms=["social", "messaging_apps"],
        ),
    ]
    actors = _apply_preset(actors, preset)
    if include_actor_types is not None:
        allowed = set(include_actor_types)
        actors = [actor for actor in actors if actor.actor_type in allowed]
    return actors


def _apply_preset(actors: list[MediaActor], preset: str) -> list[MediaActor]:
    normalized = preset.strip().lower()
    if normalized in {"balanced", "default"}:
        return actors
    if normalized == "low_trust":
        return [
            actor.model_copy(
                update={
                    "credibility": max(10, actor.credibility - 18),
                    "sensationalism": min(100, actor.sensationalism + 14),
                    "reach": min(100, actor.reach + 5),
                }
            )
            for actor in actors
        ]
    if normalized == "high_institutional_trust":
        return [
            actor.model_copy(
                update={
                    "credibility": min(100, actor.credibility + 12),
                    "sensationalism": max(0, actor.sensationalism - 8),
                }
            )
            for actor in actors
        ]
    if normalized == "highly_partisan":
        return [
            actor.model_copy(
                update={
                    "sensationalism": min(100, actor.sensationalism + 18),
                    "reach": min(100, actor.reach + 8),
                }
            )
            for actor in actors
            if actor.actor_type
            in {ActorType.PARTISAN_OUTLET, ActorType.TABLOID, ActorType.INFLUENCER}
        ]
    if normalized == "expert_heavy":
        expert_boost = [
            actor.model_copy(
                update={
                    "credibility": min(100, actor.credibility + 10),
                    "reach": min(100, actor.reach + 7),
                }
            )
            for actor in actors
            if actor.actor_type
            in {
                ActorType.EXPERT,
                ActorType.GOVERNMENT_SOURCE,
                ActorType.PUBLIC_BROADCASTER,
            }
        ]
        return expert_boost + [
            actor
            for actor in actors
            if actor.actor_type
            not in {
                ActorType.EXPERT,
                ActorType.GOVERNMENT_SOURCE,
                ActorType.PUBLIC_BROADCASTER,
            }
        ]
    return actors
