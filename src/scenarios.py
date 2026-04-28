from __future__ import annotations

from src.schemas import NewsEvent


def demo_scenarios() -> dict[str, NewsEvent]:
    events = [
        NewsEvent(
            title="Emissions-based car tax",
            description="A proposal would tax private cars based on estimated emissions.",
            country="United States",
            topic="taxes",
            source_type="policy_proposal",
            original_text="The government is considering an emissions-based car tax for private vehicles.",
        ),
        NewsEvent(
            title="AI surveillance in public spaces",
            description="A city considers AI-assisted cameras for transit hubs and major public squares.",
            country="United States",
            topic="civil_liberties",
            source_type="public_safety_plan",
            original_text="Officials proposed AI-assisted public-space monitoring to support safety operations.",
        ),
        NewsEvent(
            title="Four-day work week proposal",
            description="A proposal would encourage employers to test a four-day work week.",
            country="United States",
            topic="jobs",
            source_type="policy_proposal",
            original_text="The proposal creates incentives for employers piloting a four-day work week.",
        ),
        NewsEvent(
            title="Mandatory digital ID",
            description="A proposal would require a digital ID for some public services.",
            country="United States",
            topic="civil_liberties",
            source_type="policy_proposal",
            original_text="Officials proposed a mandatory digital ID for selected public services.",
        ),
        NewsEvent(
            title="Housing policy reform",
            description="A reform package would change zoning rules and rental protections.",
            country="United States",
            topic="housing",
            source_type="legislative_package",
            original_text="Lawmakers introduced housing reforms covering zoning, rentals, and affordability rules.",
        ),
        NewsEvent(
            title="University bans phones in classrooms",
            description="A university announces restrictions on phone use during classes.",
            country="United States",
            topic="education",
            source_type="institutional_policy",
            original_text="The university will restrict phone use in classrooms except for accessibility needs.",
        ),
        NewsEvent(
            title="City restricts short-term rentals",
            description="A city council proposes limits on short-term rental listings.",
            country="United States",
            topic="housing",
            source_type="official_statement",
            original_text="The council announced a proposed cap on short-term rentals and new permit rules.",
        ),
    ]
    return {event.title: event for event in events}

