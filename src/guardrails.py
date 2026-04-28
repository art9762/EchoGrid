"""Central ethical guardrails for EchoGrid request handling."""

from __future__ import annotations

from dataclasses import dataclass


PROHIBITED_USE_TEXT = (
    "EchoGrid must not be used for manipulative targeting, election targeting, "
    "vulnerable-group targeting, harassment, radicalization, or persuasion "
    "optimization."
)

_DISALLOWED_PATTERNS = {
    "manipulative targeting": (
        "manipulate group",
        "manipulate voters",
        "best message to manipulate",
        "persuade vulnerable",
        "target vulnerable",
        "optimize persuasion",
        "psychographic targeting",
    ),
    "election targeting": (
        "election targeting",
        "target voters",
        "swing voters",
        "suppress turnout",
    ),
    "harassment or radicalization": (
        "harass",
        "radicalize",
        "incite",
        "intimidate",
    ),
}


@dataclass(frozen=True)
class GuardrailDecision:
    allowed: bool
    reason: str
    refusal_message: str | None = None


def classify_request(request_text: str) -> GuardrailDecision:
    normalized = " ".join(request_text.lower().split())
    for reason, patterns in _DISALLOWED_PATTERNS.items():
        if any(pattern in normalized for pattern in patterns):
            return GuardrailDecision(
                allowed=False,
                reason=reason,
                refusal_message=(
                    "I cannot help optimize persuasion, targeting, harassment, "
                    "radicalization, or manipulation. I can help reframe this as "
                    "synthetic risk analysis, safety evaluation, or educational "
                    "comparison instead."
                ),
            )
    return GuardrailDecision(allowed=True, reason="allowed research or analysis")


def is_disallowed_request(request_text: str) -> bool:
    return not classify_request(request_text).allowed
