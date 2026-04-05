"""Validate raw sensor readings before smoothing."""

from __future__ import annotations

from shared.models import BinReading


def validate_reading(r: BinReading) -> tuple[bool, str | None]:
    """
    Return (ok, error_reason). Invalid readings should be dropped at the fog edge.
    """
    if not r.bin_id or not r.zone:
        return False, "missing bin_id or zone"
    if r.fill_level < 0 or r.fill_level > 100:
        return False, f"fill_level out of range: {r.fill_level}"
    if r.weight_kg < 0 or r.weight_kg > 500:
        return False, f"weight_kg implausible: {r.weight_kg}"
    if r.temperature_c < -20 or r.temperature_c > 80:
        return False, f"temperature_c out of range: {r.temperature_c}"
    if r.usage_count < 0 or r.usage_count > 200:
        return False, f"usage_count implausible: {r.usage_count}"
    if r.timestamp <= 0:
        return False, "invalid timestamp"
    return True, None
