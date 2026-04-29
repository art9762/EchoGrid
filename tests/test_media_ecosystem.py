from src.media_ecosystem import default_media_actors
from src.schemas import ActorType


def test_media_actor_presets_adjust_environment_shape() -> None:
    balanced = default_media_actors()
    expert_heavy = default_media_actors(preset="expert_heavy")
    low_trust = default_media_actors(preset="low_trust")

    assert len(expert_heavy) >= len(balanced)
    assert sum(actor.credibility for actor in expert_heavy) > sum(
        actor.credibility for actor in low_trust
    )
    assert any(actor.actor_type == ActorType.EXPERT for actor in expert_heavy)


def test_media_actor_toggles_include_requested_types_only() -> None:
    actors = default_media_actors(
        include_actor_types={ActorType.EXPERT, ActorType.GOVERNMENT_SOURCE}
    )

    assert actors
    assert {actor.actor_type for actor in actors} <= {
        ActorType.EXPERT,
        ActorType.GOVERNMENT_SOURCE,
    }
