from src.framing import generate_framings
from src.population import generate_population
from src.reaction_engine import run_agent_reaction, run_initial_reactions
from src.schemas import AgentReaction, NewsEvent, PopulationConfig, Stance


def make_event() -> NewsEvent:
    return NewsEvent(
        title="Emissions-based car tax",
        description="A proposal would tax cars based on estimated emissions.",
        country="United States",
        topic="taxes",
        source_type="policy_proposal",
        original_text="The government is considering an emissions-based car tax.",
    )


def test_mock_agent_reaction_validates_and_is_deterministic() -> None:
    event = make_event()
    frame = generate_framings(event, n=1)[0]
    agent = generate_population(PopulationConfig(population_size=1, seed=5))[0]

    first = run_agent_reaction(agent, event, frame, mode="mock", seed=5)
    second = run_agent_reaction(agent, event, frame, mode="mock", seed=5)

    assert isinstance(first, AgentReaction)
    assert first.model_dump() == second.model_dump()
    assert first.stance in set(Stance)
    assert 0 <= first.share_likelihood <= 100


def test_run_initial_reactions_covers_agents_and_frames() -> None:
    event = make_event()
    agents = generate_population(PopulationConfig(population_size=20, seed=3))
    frames = generate_framings(event, n=3)

    reactions = run_initial_reactions(agents, event, frames, mode="mock", seed=3)

    assert len(reactions) == 60
    assert {reaction.frame_id for reaction in reactions} == {
        "neutral",
        "technocratic",
        "progressive",
    }
    assert {reaction.agent_id for reaction in reactions} == {agent.id for agent in agents}
