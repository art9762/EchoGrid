"""Shared deterministic randomness and data-normalization utilities."""

from __future__ import annotations

import hashlib
import random
from collections.abc import Sequence
from typing import TypeVar


T = TypeVar("T")


def clamp(value: int | float, minimum: int = 0, maximum: int = 100) -> int:
    return int(max(minimum, min(maximum, round(value))))


def stable_seed(*parts: object) -> int:
    raw = "::".join(str(part) for part in parts)
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    return int(digest[:16], 16)


def seeded_rng(*parts: object) -> random.Random:
    return random.Random(stable_seed(*parts))


def weighted_choice(rng: random.Random, choices: Sequence[tuple[T, float]]) -> T:
    total = sum(weight for _, weight in choices)
    if total <= 0:
        raise ValueError("weighted_choice requires positive total weight")

    threshold = rng.uniform(0, total)
    cumulative = 0.0
    for value, weight in choices:
        cumulative += weight
        if threshold <= cumulative:
            return value
    return choices[-1][0]
