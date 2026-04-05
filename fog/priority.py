"""Priority scoring for collection / attention routing."""

from __future__ import annotations

from shared.constants import (
    TEMP_MAX_C,
    TEMP_MIN_C,
    USAGE_COUNT_CAP,
    WEIGHT_FILL,
    WEIGHT_TEMP,
    WEIGHT_USAGE,
)


def normalize_usage(usage_count: float) -> float:
    """Map usage count to 0-100."""
    return max(0.0, min(100.0, (usage_count / USAGE_COUNT_CAP) * 100.0))


def normalize_temperature(temperature_c: float) -> float:
    """Map temperature band to 0-100 for weighting (linear clamp)."""
    span = TEMP_MAX_C - TEMP_MIN_C
    if span <= 0:
        return 0.0
    t = (temperature_c - TEMP_MIN_C) / span
    return max(0.0, min(100.0, t * 100.0))


def compute_priority(fill_level: float, usage_count: float, temperature_c: float) -> float:
    """
    Composite priority score 0-100:
    priority = fill*0.6 + usage_norm*0.3 + temp_norm*0.1
    """
    u = normalize_usage(usage_count)
    t = normalize_temperature(temperature_c)
    score = (
        fill_level * WEIGHT_FILL
        + u * WEIGHT_USAGE
        + t * WEIGHT_TEMP
    )
    return max(0.0, min(100.0, round(score, 2)))
