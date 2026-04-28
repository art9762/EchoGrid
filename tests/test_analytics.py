from src.analytics import (
    emotion_averages,
    frame_comparison,
    polarization_score,
    segment_breakdown,
    share_likelihood_distribution,
    stance_distribution,
    trust_average,
    virality_risk_score,
)
from src.framing import generate_framings
from src.population import generate_population
from src.reaction_engine import run_initial_reactions
from src.schemas import NewsEvent, PopulationConfig


def sample_reactions():
    event = NewsEvent(
        title="Four-day work week proposal",
        description="A proposal would encourage employers to test a four-day week.",
        country="United States",
        topic="jobs",
        source_type="policy_proposal",
        original_text="The proposal creates incentives for four-day work week pilots.",
    )
    agents = generate_population(PopulationConfig(population_size=40, seed=17))
    frames = generate_framings(event, n=2)
    return agents, run_initial_reactions(agents, event, frames, mode="mock", seed=17)


def test_basic_reaction_metrics_return_expected_keys() -> None:
    _, reactions = sample_reactions()

    assert set(stance_distribution(reactions)) == {
        "support",
        "oppose",
        "neutral",
        "confused",
    }
    assert set(emotion_averages(reactions)) == {
        "anger",
        "fear",
        "hope",
        "distrust",
        "indifference",
        "emotional_intensity",
    }
    assert 0 <= trust_average(reactions) <= 100
    assert set(share_likelihood_distribution(reactions)) == {
        "average",
        "median",
        "p75",
        "high_share_percent",
    }


def test_polarization_and_virality_scores_are_bounded() -> None:
    _, reactions = sample_reactions()

    assert 0 <= polarization_score(reactions) <= 100
    assert 0 <= virality_risk_score(reactions) <= 100


def test_segment_breakdown_and_frame_comparison_return_rows() -> None:
    agents, reactions = sample_reactions()

    segments = segment_breakdown(reactions, agents, by_field="income_level")
    comparison = frame_comparison(reactions)

    assert segments
    assert {"segment", "count", "average_share_likelihood"} <= set(segments[0])
    assert set(comparison) == {"neutral", "technocratic"}


def test_segment_breakdown_supports_age_and_trust_buckets() -> None:
    agents, reactions = sample_reactions()

    age_segments = {
        row["segment"] for row in segment_breakdown(reactions, agents, by_field="age_group")
    }
    trust_segments = {
        row["segment"]
        for row in segment_breakdown(
            reactions, agents, by_field="institutional_trust_bucket"
        )
    }

    assert age_segments <= {"18-24", "25-34", "35-49", "50-64", "65+"}
    assert trust_segments <= {"low", "medium", "high"}
