"""Threshold-based event detection for fill and fire-risk heuristics."""

from __future__ import annotations

from shared.constants import (
    FILL_CRITICAL_PCT,
    FILL_WARNING_PCT,
    FIRE_TEMP_THRESHOLD_C,
    PROBABLE_FIRE_TEMP_THRESHOLD_C,
)
from shared.models import AlertLevel, BinStatus


def fill_alert_level(fill_level: float) -> AlertLevel:
    if fill_level > FILL_CRITICAL_PCT:
        return AlertLevel.CRITICAL
    if fill_level > FILL_WARNING_PCT:
        return AlertLevel.WARNING
    return AlertLevel.NONE


def fire_risk(temperature_c: float) -> bool:
    return temperature_c > FIRE_TEMP_THRESHOLD_C


def probable_fire_alert(temperature_c: float) -> bool:
    return temperature_c >= PROBABLE_FIRE_TEMP_THRESHOLD_C


def heat_escalation_tier(temperature_c: float) -> int:
    """0 = no heat alert, 1 = fire_risk band, 2 = probable fire — for edge detection."""
    if temperature_c >= PROBABLE_FIRE_TEMP_THRESHOLD_C:
        return 2
    if temperature_c > FIRE_TEMP_THRESHOLD_C:
        return 1
    return 0


def combine_status(
    fill_alert: AlertLevel,
    temperature_c: float,
) -> BinStatus:
    """
    Map to storage/dashboard status string (single worst-case label).
    """
    if temperature_c >= PROBABLE_FIRE_TEMP_THRESHOLD_C:
        return "probable_fire"
    if temperature_c > FIRE_TEMP_THRESHOLD_C:
        return "fire_risk"
    if fill_alert == AlertLevel.CRITICAL:
        return "critical"
    if fill_alert == AlertLevel.WARNING:
        return "warning"
    return "normal"
