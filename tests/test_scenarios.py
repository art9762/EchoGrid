from src.scenarios import demo_scenarios
from src.schemas import NewsEvent


def test_demo_scenarios_include_expected_events() -> None:
    scenarios = demo_scenarios()

    assert len(scenarios) == 7
    assert all(isinstance(event, NewsEvent) for event in scenarios.values())
    assert "Mandatory digital ID" in scenarios
    assert "City restricts short-term rentals" in scenarios
