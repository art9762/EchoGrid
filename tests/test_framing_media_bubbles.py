from src.framing import generate_framings
from src.media_ecosystem import default_media_actors
from src.population import generate_population
from src.schemas import MediaActor, NewsEvent, NewsFrame, PopulationConfig, SocialBubble
from src.social_bubbles import assign_agents_to_bubbles, default_social_bubbles


def make_event() -> NewsEvent:
    return NewsEvent(
        title="City restricts short-term rentals",
        description="A city council proposes limits on short-term rental listings.",
        country="United States",
        topic="housing",
        source_type="official_statement",
        original_text="The council announced a proposed cap on short-term rentals.",
    )


def test_generate_framings_returns_expected_builtin_frames() -> None:
    frames = generate_framings(make_event(), n=6)

    assert len(frames) == 6
    assert all(isinstance(frame, NewsFrame) for frame in frames)
    assert {frame.frame_id for frame in frames} == {
        "neutral",
        "technocratic",
        "progressive",
        "populist",
        "skeptical",
        "tabloid_outrage",
    }


def test_default_media_actors_cover_expected_ecosystem() -> None:
    actors = default_media_actors()

    assert len(actors) >= 11
    assert all(isinstance(actor, MediaActor) for actor in actors)
    assert {actor.actor_type.value for actor in actors} >= {
        "public_broadcaster",
        "tabloid",
        "partisan_outlet",
        "influencer",
        "expert",
        "government_source",
        "grassroots_account",
    }


def test_default_social_bubbles_and_assignment_cover_agents() -> None:
    agents = generate_population(PopulationConfig(population_size=200, seed=11))
    bubbles = default_social_bubbles()
    assignments = assign_agents_to_bubbles(agents, bubbles)

    assert len(bubbles) >= 7
    assert all(isinstance(bubble, SocialBubble) for bubble in bubbles)
    assigned_ids = {agent_id for ids in assignments.values() for agent_id in ids}
    assert assigned_ids == {agent.id for agent in agents}
    assert all(assignments[bubble.id] for bubble in bubbles)
