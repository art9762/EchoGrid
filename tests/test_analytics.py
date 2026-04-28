from src.analytics import (
    echo_amplification_breakdown,
    emotion_averages,
    final_state_metrics,
    frame_comparison,
    narrative_risk_summary,
    polarization_score,
    segment_breakdown,
    share_likelihood_distribution,
    stance_distribution,
    trust_average,
    virality_risk_score,
)
from src.echo_engine import run_echo_simulation
from src.framing import generate_framings
from src.media_ecosystem import default_media_actors
from src.population import generate_population
from src.reaction_engine import run_initial_reactions
from src.schemas import NewsEvent, PopulationConfig
from src.social_bubbles import assign_agents_to_bubbles, default_social_bubbles


def sample_context():
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
    reactions = run_initial_reactions(agents, event, frames, mode="mock", seed=17)
    return event, agents, frames, reactions


def sample_reactions():
    _, agents, _, reactions = sample_context()
    return agents, reactions


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


def test_final_state_metrics_and_narrative_risk_summary_describe_echo_layer() -> None:
    event, agents, frames, reactions = sample_context()
    actors = default_media_actors()
    bubbles = default_social_bubbles()
    assignments = assign_agents_to_bubbles(agents, bubbles)
    result = run_echo_simulation(
        agents=agents,
        event=event,
        frames=frames,
        initial_reactions=reactions,
        media_actors=actors,
        bubbles=bubbles,
        bubble_assignments=assignments,
        seed=17,
    )

    state_metrics = final_state_metrics(
        result.final_reaction_state_by_agent, result.echo_reactions
    )
    breakdown = echo_amplification_breakdown(
        reactions, result.echo_reactions, result.echo_items
    )
    risk = narrative_risk_summary(result.echo_items, result.echo_reactions, bubbles)

    assert set(state_metrics) == {
        "final_stance_distribution",
        "final_trust_average",
        "final_share_likelihood_average",
        "average_stance_shift",
        "average_anger_shift",
    }
    assert sum(state_metrics["final_stance_distribution"].values()) == 100.0
    assert {
        "anger_delta",
        "trust_loss",
        "share_growth",
        "stance_motion",
        "distortion",
    } <= set(breakdown)
    assert all({"raw_value", "weight", "weighted_contribution"} <= set(row) for row in breakdown.values())
    assert {"top_echo_type", "top_bubble", "highest_distortion_item"} <= set(risk)
