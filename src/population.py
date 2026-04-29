"""Synthetic population generation."""

from __future__ import annotations

import random

from src.schemas import AgentProfile, PopulationConfig
from src.utils import clamp, weighted_choice

AGE_GROUPS = [
    ((18, 24), 0.12),
    ((25, 34), 0.19),
    ((35, 49), 0.25),
    ((50, 64), 0.25),
    ((65, 85), 0.19),
]

GENDERS = [("woman", 0.49), ("man", 0.49), ("nonbinary", 0.02)]
LOCATIONS = [("urban", 0.39), ("suburban", 0.38), ("rural", 0.18), ("small_town", 0.05)]
EDUCATION = [
    ("secondary", 0.28),
    ("vocational", 0.19),
    ("college", 0.35),
    ("graduate", 0.18),
]
INCOME = [("low", 0.22), ("lower_middle", 0.25), ("middle", 0.3), ("upper_middle", 0.17), ("high", 0.06)]
POLITICAL_ENGAGEMENT = [("low", 0.36), ("moderate", 0.44), ("high", 0.2)]

MEDIA_OPTIONS = [
    "public_broadcaster",
    "local_news",
    "social_media",
    "tabloid",
    "partisan_outlet",
    "expert_analysis",
    "podcasts",
    "influencers",
    "community_groups",
]

OCCUPATIONS = [
    "student",
    "service",
    "manual_trade",
    "office_admin",
    "education",
    "healthcare",
    "technology",
    "public_sector",
    "small_business",
    "retired",
    "unemployed",
]

CONCERNS = [
    "cost_of_living",
    "jobs",
    "housing",
    "healthcare",
    "education",
    "public_safety",
    "civil_liberties",
    "environment",
    "taxes",
    "community_stability",
]

VALUES = [
    "fairness",
    "stability",
    "freedom",
    "security",
    "tradition",
    "opportunity",
    "care",
    "accountability",
    "innovation",
    "local_control",
]


def generate_population(config: PopulationConfig) -> list[AgentProfile]:
    rng = random.Random(config.seed)
    return [_generate_agent(index, config, rng) for index in range(config.population_size)]


def _generate_agent(index: int, config: PopulationConfig, rng: random.Random) -> AgentProfile:
    age_range = weighted_choice(rng, AGE_GROUPS)
    age = rng.randint(age_range[0], age_range[1])
    gender = weighted_choice(rng, GENDERS)
    location_type = weighted_choice(rng, LOCATIONS)
    education_level = weighted_choice(rng, EDUCATION)
    income_level = weighted_choice(rng, INCOME)
    political_engagement = weighted_choice(rng, POLITICAL_ENGAGEMENT)
    occupation_category = _occupation_for_age(age, education_level, rng)
    family_status = _family_status_for_age(age, rng)
    economic_position = _economic_position_for_income(income_level, rng)
    social_position = _social_position(income_level, education_level)
    media_diet = _media_diet(location_type, education_level, political_engagement, rng)
    values = _values_for_profile(age, location_type, income_level, rng)
    concerns = _concerns_for_profile(age, income_level, location_type, rng)

    trust_base = 52
    if education_level in {"college", "graduate"}:
        trust_base += 8
    if "public_broadcaster" in media_diet or "expert_analysis" in media_diet:
        trust_base += 10
    if "tabloid" in media_diet or "partisan_outlet" in media_diet:
        trust_base -= 12
    if income_level in {"low", "lower_middle"}:
        trust_base -= 8

    openness_base = 48 + (8 if age < 35 else 0) + (8 if education_level == "graduate" else 0)
    stability_base = 45 + (10 if age >= 50 else 0) + (8 if "stability" in values else 0)
    status_anxiety_base = 35 + (15 if income_level in {"low", "lower_middle"} else 0)
    anger_base = 30 + (12 if "tabloid" in media_diet or "partisan_outlet" in media_diet else 0)

    return AgentProfile(
        id=f"agent-{index + 1:05d}",
        age=age,
        gender=gender,
        country=config.country,
        location_type=location_type,
        education_level=education_level,
        income_level=income_level,
        occupation_category=occupation_category,
        family_status=family_status,
        economic_position=economic_position,
        social_position=social_position,
        institutional_trust=clamp(trust_base + rng.gauss(0, 13)),
        political_engagement=political_engagement,
        risk_aversion=clamp(stability_base + rng.gauss(0, 12)),
        openness_to_change=clamp(openness_base + rng.gauss(0, 14)),
        anger_proneness=clamp(anger_base + rng.gauss(0, 13)),
        empathy_level=clamp(55 + rng.gauss(0, 15)),
        need_for_stability=clamp(stability_base + rng.gauss(0, 12)),
        status_anxiety=clamp(status_anxiety_base + rng.gauss(0, 15)),
        media_diet=media_diet,
        preferred_content_style=_content_style(media_diet, rng),
        main_concerns=concerns,
        values=values,
    )


def _occupation_for_age(age: int, education_level: str, rng: random.Random) -> str:
    if age < 23 and rng.random() < 0.6:
        return "student"
    if age >= 67 and rng.random() < 0.72:
        return "retired"
    if education_level == "graduate":
        return weighted_choice(rng, [("technology", 0.22), ("education", 0.24), ("healthcare", 0.22), ("public_sector", 0.18), ("small_business", 0.14)])
    return weighted_choice(rng, [(occupation, 1.0) for occupation in OCCUPATIONS if occupation not in {"student", "retired"}])


def _family_status_for_age(age: int, rng: random.Random) -> str:
    if age < 28:
        return weighted_choice(rng, [("single", 0.62), ("partnered", 0.26), ("parent", 0.12)])
    if age < 55:
        return weighted_choice(rng, [("single", 0.24), ("partnered", 0.28), ("parent", 0.42), ("caregiver", 0.06)])
    return weighted_choice(rng, [("single", 0.22), ("partnered", 0.42), ("parent", 0.18), ("caregiver", 0.18)])


def _economic_position_for_income(income_level: str, rng: random.Random) -> str:
    mapping = {
        "low": [("precarious", 0.72), ("strained", 0.28)],
        "lower_middle": [("strained", 0.58), ("stable", 0.42)],
        "middle": [("stable", 0.72), ("strained", 0.2), ("comfortable", 0.08)],
        "upper_middle": [("comfortable", 0.68), ("stable", 0.32)],
        "high": [("secure", 0.7), ("comfortable", 0.3)],
    }
    return weighted_choice(rng, mapping[income_level])


def _social_position(income_level: str, education_level: str) -> str:
    if income_level == "high" or (income_level == "upper_middle" and education_level == "graduate"):
        return "upper_middle_class"
    if income_level in {"middle", "upper_middle"}:
        return "middle_class"
    if income_level == "lower_middle":
        return "working_middle"
    return "working_class"


def _media_diet(
    location_type: str, education_level: str, political_engagement: str, rng: random.Random
) -> list[str]:
    weights = [(option, 1.0) for option in MEDIA_OPTIONS]
    if education_level in {"college", "graduate"}:
        weights.extend([("expert_analysis", 1.8), ("public_broadcaster", 1.4)])
    if political_engagement == "high":
        weights.extend([("partisan_outlet", 1.6), ("podcasts", 1.2)])
    if location_type in {"rural", "small_town"}:
        weights.extend([("local_news", 1.5), ("community_groups", 1.2)])

    selected: list[str] = []
    while len(selected) < rng.randint(2, 4):
        item = weighted_choice(rng, weights)
        if item not in selected:
            selected.append(item)
    return selected


def _values_for_profile(
    age: int, location_type: str, income_level: str, rng: random.Random
) -> list[str]:
    weighted = [(value, 1.0) for value in VALUES]
    if age >= 50:
        weighted.extend([("stability", 1.7), ("security", 1.4), ("tradition", 1.2)])
    if age < 35:
        weighted.extend([("fairness", 1.4), ("innovation", 1.2), ("freedom", 1.2)])
    if location_type == "rural":
        weighted.extend([("local_control", 1.6), ("tradition", 1.2)])
    if income_level in {"low", "lower_middle"}:
        weighted.extend([("fairness", 1.6), ("security", 1.3)])
    return _unique_weighted_sample(rng, weighted, 3)


def _concerns_for_profile(
    age: int, income_level: str, location_type: str, rng: random.Random
) -> list[str]:
    weighted = [(concern, 1.0) for concern in CONCERNS]
    if income_level in {"low", "lower_middle", "middle"}:
        weighted.extend([("cost_of_living", 2.0), ("housing", 1.4), ("jobs", 1.3)])
    if age >= 55:
        weighted.extend([("healthcare", 1.8), ("taxes", 1.2)])
    if location_type in {"urban", "suburban"}:
        weighted.extend([("housing", 1.5), ("public_safety", 1.2)])
    return _unique_weighted_sample(rng, weighted, 3)


def _content_style(media_diet: list[str], rng: random.Random) -> str:
    if "expert_analysis" in media_diet:
        return weighted_choice(rng, [("explanatory", 0.55), ("data_driven", 0.45)])
    if "tabloid" in media_diet:
        return weighted_choice(rng, [("emotional", 0.55), ("short_form", 0.45)])
    if "social_media" in media_diet or "influencers" in media_diet:
        return weighted_choice(rng, [("short_form", 0.58), ("conversational", 0.42)])
    return weighted_choice(rng, [("neutral", 0.35), ("explanatory", 0.35), ("local", 0.3)])


def _unique_weighted_sample(
    rng: random.Random, weighted: list[tuple[str, float]], size: int
) -> list[str]:
    selected: list[str] = []
    while len(selected) < size:
        item = weighted_choice(rng, weighted)
        if item not in selected:
            selected.append(item)
    return selected
