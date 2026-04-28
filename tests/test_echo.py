from src.echo_engine import generate_echo_items, run_echo_reaction, run_echo_simulation
from src.framing import generate_framings
from src.media_ecosystem import default_media_actors
from src.population import generate_population
from src.reaction_engine import run_initial_reactions
from src.schemas import (
    EchoItem,
    EchoReaction,
    EchoSimulationResult,
    EchoType,
    EmotionLabel,
    NewsEvent,
    PopulationConfig,
)
from src.social_bubbles import assign_agents_to_bubbles, default_social_bubbles


def sample_echo_context(population_size: int = 60):
    event = NewsEvent(
        title="Mandatory digital ID",
        description="A proposal would require a digital ID for some public services.",
        country="United States",
        topic="civil_liberties",
        source_type="policy_proposal",
        original_text="Officials proposed a mandatory digital ID for selected services.",
    )
    agents = generate_population(PopulationConfig(population_size=population_size, seed=31))
    frames = generate_framings(event, n=2)
    reactions = run_initial_reactions(agents, event, frames, mode="mock", seed=31)
    actors = default_media_actors()
    bubbles = default_social_bubbles()
    assignments = assign_agents_to_bubbles(agents, bubbles)
    return event, agents, frames, reactions, actors, bubbles, assignments


def test_generate_echo_items_returns_deterministic_valid_items() -> None:
    event, _, frames, reactions, actors, bubbles, _ = sample_echo_context()

    first = generate_echo_items(event, frames, reactions, actors, bubbles, mode="mock", seed=31)
    second = generate_echo_items(event, frames, reactions, actors, bubbles, mode="mock", seed=31)

    assert first
    assert [item.model_dump() for item in first] == [item.model_dump() for item in second]
    assert all(isinstance(item, EchoItem) for item in first)
    assert {"tabloid_headline", "expert_correction"} <= {
        item.echo_type.value for item in first
    }


def test_run_echo_reaction_validates_and_records_bubble() -> None:
    event, agents, frames, reactions, actors, bubbles, assignments = sample_echo_context(30)
    echo_item = generate_echo_items(event, frames, reactions, actors, bubbles, seed=31)[0]
    bubble = bubbles[0]
    agent_id = assignments[bubble.id][0]
    agent = next(agent for agent in agents if agent.id == agent_id)
    original = next(reaction for reaction in reactions if reaction.agent_id == agent.id)

    reaction = run_echo_reaction(agent, original, echo_item, bubble, mode="mock", seed=31)

    assert isinstance(reaction, EchoReaction)
    assert reaction.bubble_id == bubble.id
    assert -100 <= reaction.stance_shift <= 100
    assert -100 <= reaction.trust_shift <= 100


def test_run_echo_simulation_returns_result_with_metrics() -> None:
    event, agents, frames, reactions, actors, bubbles, assignments = sample_echo_context(40)

    result = run_echo_simulation(
        agents=agents,
        event=event,
        frames=frames,
        initial_reactions=reactions,
        media_actors=actors,
        bubbles=bubbles,
        bubble_assignments=assignments,
        mode="mock",
        seed=31,
    )

    assert isinstance(result, EchoSimulationResult)
    assert result.echo_items
    assert result.echo_reactions
    assert {
        "echo_amplification_index",
        "distortion_drift",
        "trust_delta",
        "anger_delta",
        "virality_growth",
    } <= set(result.amplification_metrics)


def test_run_echo_simulation_accepts_echo_items_override() -> None:
    event, agents, frames, reactions, actors, bubbles, assignments = sample_echo_context(40)
    custom_item = EchoItem(
        id="llm-echo-1",
        round_number=1,
        echo_type=EchoType.OFFICIAL_CLARIFICATION,
        text="Officials clarify the scope of the proposal.",
        origin_actor_id="official-source",
        source_frame_id=frames[0].frame_id,
        target_bubbles=[bubbles[0].id],
        emotion=EmotionLabel.REASSURANCE,
        distortion_level=3,
        sensationalism_level=5,
        estimated_reach=50,
        created_from_reaction_ids=[],
    )

    result = run_echo_simulation(
        agents=agents,
        event=event,
        frames=frames,
        initial_reactions=reactions,
        media_actors=actors,
        bubbles=bubbles,
        bubble_assignments=assignments,
        mode="mock",
        seed=31,
        echo_items_override=[custom_item],
    )

    assert result.echo_items == [custom_item]
    assert {reaction.echo_item_id for reaction in result.echo_reactions} == {"llm-echo-1"}
