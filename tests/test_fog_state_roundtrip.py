"""FogProcessingService state (de)serialization for MQTT Lambda."""

from __future__ import annotations

from fog.service import FogProcessingService
from shared.models import BinReading


def test_fog_state_roundtrip_preserves_smoothing_window():
    svc = FogProcessingService(summary_interval_sec=5.0, fog_node_id="fog-test", smoothing_window=3)
    r1 = BinReading(
        bin_id="BIN-zone-A-01",
        zone="zone-A",
        fill_level=10.0,
        weight_kg=1.0,
        temperature_c=20.0,
        usage_count=1,
        timestamp=1000.0,
    )
    svc.process_reading(r1)
    blob = svc.to_state_dict()
    svc2 = FogProcessingService(summary_interval_sec=5.0, fog_node_id="fog-test", smoothing_window=3)
    svc2.apply_state_dict(blob)
    blob2 = svc2.to_state_dict()
    assert blob2 == blob
