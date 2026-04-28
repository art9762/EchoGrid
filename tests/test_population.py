from src.population import generate_population
from src.schemas import AgentProfile, PopulationConfig


def test_generate_population_returns_requested_size() -> None:
    agents = generate_population(PopulationConfig(population_size=50, seed=7))

    assert len(agents) == 50
    assert all(isinstance(agent, AgentProfile) for agent in agents)


def test_generate_population_is_deterministic_for_seed() -> None:
    config = PopulationConfig(population_size=25, seed=99)

    first = generate_population(config)
    second = generate_population(config)

    assert [agent.model_dump() for agent in first] == [
        agent.model_dump() for agent in second
    ]


def test_generate_population_has_diverse_coherent_agents() -> None:
    agents = generate_population(PopulationConfig(population_size=1000, seed=123))

    assert len({agent.income_level for agent in agents}) >= 4
    assert len({agent.location_type for agent in agents}) >= 3
    assert len({style for agent in agents for style in agent.media_diet}) >= 5
    assert all(16 <= agent.age <= 100 for agent in agents)
    assert all(agent.media_diet for agent in agents)
