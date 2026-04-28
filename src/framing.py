"""News framing generation and deterministic built-in frames."""

from __future__ import annotations

from src.schemas import NewsEvent, NewsFrame


def generate_framings(event: NewsEvent, n: int = 5) -> list[NewsFrame]:
    frames = _builtin_frames(event)
    if n <= len(frames):
        return frames[:n]
    return frames


def _builtin_frames(event: NewsEvent) -> list[NewsFrame]:
    subject = event.title.rstrip(".")
    topic = event.topic.replace("_", " ")
    return [
        NewsFrame(
            frame_id="neutral",
            label="Neutral",
            text=(
                f"{subject}: officials describe the proposal as a policy change "
                f"with possible effects on {topic} and local households."
            ),
            tone="neutral",
            implied_values=["balance", "public_information"],
            source_type="public_broadcaster",
        ),
        NewsFrame(
            frame_id="technocratic",
            label="Technocratic",
            text=(
                f"{subject}: analysts focus on implementation details, budget "
                "tradeoffs, compliance timelines, and measurable outcomes."
            ),
            tone="technocratic",
            implied_values=["competence", "evidence", "stability"],
            source_type="policy_outlet",
        ),
        NewsFrame(
            frame_id="progressive",
            label="Progressive",
            text=(
                f"{subject}: supporters argue the measure could improve fairness, "
                "protect vulnerable residents, and correct structural imbalances."
            ),
            tone="values_oriented",
            implied_values=["fairness", "care", "accountability"],
            source_type="progressive_outlet",
        ),
        NewsFrame(
            frame_id="populist",
            label="Populist",
            text=(
                f"{subject}: critics frame the move as another decision made by "
                "elites without enough respect for ordinary people's daily costs."
            ),
            tone="populist",
            implied_values=["local_control", "freedom", "accountability"],
            source_type="populist_outlet",
        ),
        NewsFrame(
            frame_id="skeptical",
            label="Skeptical",
            text=(
                f"{subject}: skeptics question whether the policy will work as "
                "promised or create unintended consequences."
            ),
            tone="skeptical",
            implied_values=["caution", "accountability", "stability"],
            source_type="independent_commentary",
        ),
        NewsFrame(
            frame_id="tabloid_outrage",
            label="Tabloid / Outrage",
            text=(
                f"{subject}: a heated backlash grows as commentators warn the "
                "proposal could hit families, wallets, and local freedoms."
            ),
            tone="outrage",
            implied_values=["security", "freedom", "status_protection"],
            source_type="tabloid",
        ),
    ]
