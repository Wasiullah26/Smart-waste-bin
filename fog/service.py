"""
Fog orchestration: validate → smooth → score → periodic summaries + alert-on-edge.
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from fog.events import (
    combine_status,
    fill_alert_level,
    fire_risk,
    heat_escalation_tier,
    probable_fire_alert,
)
from fog.priority import compute_priority, normalize_usage
from fog.smoother import SmoothingRegistry, SmoothedReading
from fog.validator import validate_reading
from shared.constants import SMOOTHING_WINDOW
from shared.models import AlertLevel, BinReading, FogOutboundMessage, FogSummaryRecord


class FogProcessingService:
    """
    Stateful fog node processing pipeline.

    - Drops invalid samples.
    - Applies per-bin moving-average smoothing.
    - Computes priority and status flags.
    - Emits ``summary`` batches on a fixed wall-clock interval.
    - Emits ``alert`` immediately on escalation (fill tier or fire-risk edge).
    """

    def __init__(
        self,
        summary_interval_sec: float = 5.0,
        fog_node_id: str = "fog-1",
        smoothing_window: int | None = None,
    ) -> None:
        self.summary_interval_sec = summary_interval_sec
        self.fog_node_id = fog_node_id
        self._smoothing = SmoothingRegistry(window=smoothing_window or SMOOTHING_WINDOW)
        self._last_summary_emit = time.time()
        # Per-bin previous alert state for edge detection
        self._prev: dict[str, tuple[AlertLevel, int]] = {}
        # Latest summary record per bin (full fleet snapshot for periodic uplink)
        self._latest: dict[str, FogSummaryRecord] = {}

    def _to_record(self, s: SmoothedReading) -> FogSummaryRecord:
        fa = fill_alert_level(s.fill_level)
        fr = fire_risk(s.temperature_c)
        pf = probable_fire_alert(s.temperature_c)
        status = combine_status(fa, s.temperature_c)
        priority = compute_priority(s.fill_level, s.usage_count, s.temperature_c)
        return FogSummaryRecord(
            bin_id=s.bin_id,
            zone=s.zone,
            fill_level=round(s.fill_level, 2),
            weight_kg=round(s.weight_kg, 2),
            temperature_c=round(s.temperature_c, 2),
            usage_rate=round(normalize_usage(s.usage_count), 2),
            priority=priority,
            status=status,
            fill_alert=fa,
            fire_risk=fr,
            probable_fire_alert=pf,
            timestamp=s.timestamp,
            fog_node_id=self.fog_node_id,
        )

    @staticmethod
    def _is_escalation(
        prev: tuple[AlertLevel, int],
        rec: FogSummaryRecord,
    ) -> bool:
        prev_fill, prev_heat = prev
        curr_heat = heat_escalation_tier(rec.temperature_c)
        if curr_heat > prev_heat:
            return True
        order = {AlertLevel.NONE: 0, AlertLevel.WARNING: 1, AlertLevel.CRITICAL: 2}
        if order[rec.fill_alert] > order[prev_fill]:
            return True
        return False

    def process_reading(self, raw: BinReading) -> list[FogOutboundMessage]:
        messages: list[FogOutboundMessage] = []
        ok, _reason = validate_reading(raw)
        if not ok:
            return messages

        smoothed = self._smoothing.smooth(raw)
        record = self._to_record(smoothed)
        self._latest[record.bin_id] = record

        prev = self._prev.get(
            record.bin_id,
            (AlertLevel.NONE, 0),
        )
        if self._is_escalation(prev, record):
            messages.append(
                FogOutboundMessage(
                    message_type="alert",
                    records=[record],
                    emitted_at=time.time(),
                )
            )
        self._prev[record.bin_id] = (
            record.fill_alert,
            heat_escalation_tier(record.temperature_c),
        )

        now = time.time()
        if now - self._last_summary_emit >= self.summary_interval_sec:
            self._last_summary_emit = now
            if self._latest:
                messages.append(
                    FogOutboundMessage(
                        message_type="summary",
                        records=list(self._latest.values()),
                        emitted_at=now,
                    )
                )
        return messages
