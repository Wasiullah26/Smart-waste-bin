"""Fog threshold helpers (no AWS)."""

from __future__ import annotations

from fog.events import combine_status, heat_escalation_tier
from shared.models import AlertLevel


def test_combine_status_probable_fire_above_60():
    assert combine_status(AlertLevel.NONE, 61.0) == "probable_fire"


def test_combine_status_fire_risk_between_thresholds():
    assert combine_status(AlertLevel.NONE, 50.0) == "fire_risk"


def test_heat_escalation_tier():
    assert heat_escalation_tier(20.0) == 0
    assert heat_escalation_tier(46.0) == 1
    assert heat_escalation_tier(60.0) == 2
