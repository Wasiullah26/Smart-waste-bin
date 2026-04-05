"""Unit tests for ingestion payload validation (no AWS calls)."""

from __future__ import annotations

from validation import validate_payload


def test_valid_summary():
    sample = {
        "schema_version": "1.0",
        "message_type": "summary",
        "emitted_at": 1712345678.0,
        "records": [
            {
                "bin_id": "BIN-zone-A-01",
                "zone": "zone-A",
                "fill_level": 40.0,
                "weight_kg": 50.0,
                "temperature_c": 22.0,
                "usage_rate": 30.0,
                "priority": 35.0,
                "status": "normal",
                "fill_alert": "none",
                "fire_risk": False,
                "probable_fire_alert": False,
                "timestamp": 1712345678.0,
                "fog_node_id": "fog-1",
            }
        ],
    }
    ok, err = validate_payload(sample)
    assert ok and err is None


def test_valid_probable_fire_summary():
    sample = {
        "schema_version": "1.0",
        "message_type": "summary",
        "emitted_at": 1712345678.0,
        "records": [
            {
                "bin_id": "BIN-zone-A-01",
                "zone": "zone-A",
                "fill_level": 30.0,
                "weight_kg": 40.0,
                "temperature_c": 62.0,
                "usage_rate": 30.0,
                "priority": 40.0,
                "status": "probable_fire",
                "fill_alert": "none",
                "fire_risk": True,
                "probable_fire_alert": True,
                "timestamp": 1712345678.0,
                "fog_node_id": "fog-1",
            }
        ],
    }
    ok, err = validate_payload(sample)
    assert ok and err is None


def test_invalid_fill():
    sample = {
        "schema_version": "1.0",
        "message_type": "summary",
        "emitted_at": 1.0,
        "records": [
            {
                "bin_id": "BIN-zone-A-01",
                "zone": "zone-A",
                "fill_level": 101.0,
                "weight_kg": 50.0,
                "temperature_c": 22.0,
                "usage_rate": 30.0,
                "priority": 35.0,
                "status": "normal",
                "fill_alert": "none",
                "fire_risk": False,
                "probable_fire_alert": False,
                "timestamp": 1.0,
            }
        ],
    }
    ok, err = validate_payload(sample)
    assert not ok and err is not None
