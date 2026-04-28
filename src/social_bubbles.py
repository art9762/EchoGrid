"""Social bubble definitions and assignment helpers."""

from __future__ import annotations

from collections import defaultdict

from src.schemas import AgentProfile, SocialBubble


def default_social_bubbles() -> list[SocialBubble]:
    return [
        SocialBubble(
            id="high_trust_institutionalists",
            label="High-trust institutionalists",
            description="People who broadly trust institutions and mainstream sources.",
            selection_rules={"institutional_trust": ">=65"},
            dominant_values=["stability", "accountability", "evidence"],
            dominant_media=["public_broadcaster", "expert_analysis"],
            internal_trust=72,
            external_trust=58,
            outrage_sensitivity=28,
            correction_resistance=24,
        ),
        SocialBubble(
            id="low_trust_working_class",
            label="Low-trust working class",
            description="Cost-sensitive agents with lower institutional trust.",
            selection_rules={"institutional_trust": "<45", "income": "low_or_lower_middle"},
            dominant_values=["fairness", "security", "local_control"],
            dominant_media=["tabloid", "local_news", "community_groups"],
            internal_trust=66,
            external_trust=24,
            outrage_sensitivity=72,
            correction_resistance=68,
        ),
        SocialBubble(
            id="young_urban_progressives",
            label="Young urban progressives",
            description="Younger urban agents with fairness and change-oriented values.",
            selection_rules={"age": "<=34", "location_type": "urban"},
            dominant_values=["fairness", "care", "innovation"],
            dominant_media=["social_media", "influencers", "progressive_outlet"],
            internal_trust=69,
            external_trust=38,
            outrage_sensitivity=59,
            correction_resistance=45,
        ),
        SocialBubble(
            id="conservative_suburban_families",
            label="Conservative suburban families",
            description="Stability-oriented suburban agents with family concerns.",
            selection_rules={"location_type": "suburban", "family_status": "parent"},
            dominant_values=["stability", "security", "tradition"],
            dominant_media=["local_news", "conservative_outlet", "podcasts"],
            internal_trust=67,
            external_trust=36,
            outrage_sensitivity=55,
            correction_resistance=52,
        ),
        SocialBubble(
            id="apolitical_cost_sensitive",
            label="Apolitical cost-sensitive",
            description="Low-engagement agents focused on day-to-day costs.",
            selection_rules={"political_engagement": "low", "concern": "cost_of_living"},
            dominant_values=["security", "stability", "opportunity"],
            dominant_media=["local_news", "social_media", "centrist_explainer"],
            internal_trust=56,
            external_trust=42,
            outrage_sensitivity=45,
            correction_resistance=43,
        ),
        SocialBubble(
            id="highly_online_outrage_users",
            label="Highly online outrage users",
            description="Social-heavy agents more responsive to emotional amplification.",
            selection_rules={"media_diet": "social_or_tabloid", "anger_proneness": ">=55"},
            dominant_values=["freedom", "accountability", "status_protection"],
            dominant_media=["social_media", "tabloid", "influencers"],
            internal_trust=78,
            external_trust=20,
            outrage_sensitivity=88,
            correction_resistance=74,
        ),
        SocialBubble(
            id="expert_oriented_professionals",
            label="Expert-oriented professionals",
            description="Higher-education agents who prefer explanatory or expert sources.",
            selection_rules={"education_level": "college_or_graduate", "media": "expert_analysis"},
            dominant_values=["evidence", "competence", "accountability"],
            dominant_media=["expert_analysis", "public_broadcaster", "policy_brief"],
            internal_trust=70,
            external_trust=50,
            outrage_sensitivity=24,
            correction_resistance=21,
        ),
    ]


def assign_agents_to_bubbles(
    agents: list[AgentProfile], bubbles: list[SocialBubble] | None = None
) -> dict[str, list[str]]:
    selected_bubbles = bubbles or default_social_bubbles()
    assignments: dict[str, list[str]] = {bubble.id: [] for bubble in selected_bubbles}

    for agent in agents:
        bubble_id = _best_bubble(agent)
        if bubble_id not in assignments:
            bubble_id = "apolitical_cost_sensitive"
        assignments[bubble_id].append(agent.id)

    _ensure_nonempty_bubbles(assignments)
    return assignments


def _best_bubble(agent: AgentProfile) -> str:
    scores = defaultdict(int)
    media = set(agent.media_diet)
    values = set(agent.values)
    concerns = set(agent.main_concerns)

    if agent.institutional_trust >= 65:
        scores["high_trust_institutionalists"] += 4
    if media & {"public_broadcaster", "expert_analysis"}:
        scores["high_trust_institutionalists"] += 2

    if agent.institutional_trust < 45:
        scores["low_trust_working_class"] += 3
    if agent.income_level in {"low", "lower_middle"}:
        scores["low_trust_working_class"] += 3

    if agent.age <= 34:
        scores["young_urban_progressives"] += 2
    if agent.location_type == "urban":
        scores["young_urban_progressives"] += 2
    if values & {"fairness", "care", "innovation"}:
        scores["young_urban_progressives"] += 1

    if agent.location_type == "suburban":
        scores["conservative_suburban_families"] += 2
    if agent.family_status == "parent":
        scores["conservative_suburban_families"] += 2
    if values & {"stability", "security", "tradition"}:
        scores["conservative_suburban_families"] += 1

    if agent.political_engagement == "low":
        scores["apolitical_cost_sensitive"] += 3
    if "cost_of_living" in concerns:
        scores["apolitical_cost_sensitive"] += 3

    if media & {"social_media", "tabloid", "influencers"}:
        scores["highly_online_outrage_users"] += 2
    if agent.anger_proneness >= 55:
        scores["highly_online_outrage_users"] += 3
    if agent.status_anxiety >= 55:
        scores["highly_online_outrage_users"] += 1

    if agent.education_level in {"college", "graduate"}:
        scores["expert_oriented_professionals"] += 2
    if "expert_analysis" in media:
        scores["expert_oriented_professionals"] += 4
    if agent.preferred_content_style in {"explanatory", "data_driven"}:
        scores["expert_oriented_professionals"] += 1

    if not scores:
        return "apolitical_cost_sensitive"
    return max(scores.items(), key=lambda item: (item[1], item[0]))[0]


def _ensure_nonempty_bubbles(assignments: dict[str, list[str]]) -> None:
    empty_ids = [bubble_id for bubble_id, ids in assignments.items() if not ids]
    for empty_id in empty_ids:
        donor_id = max(assignments, key=lambda bubble_id: len(assignments[bubble_id]))
        if not assignments[donor_id]:
            continue
        assignments[empty_id].append(assignments[donor_id].pop())
