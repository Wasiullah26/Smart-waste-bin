"""
Data models exchanged between sensors, fog, and (later) AWS backend.

All timestamps are Unix epoch seconds unless noted.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, cast, Literal


class AlertLevel(str, Enum):
    """Fill-level derived alert tier."""

    NONE = "none"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class BinReading:
    """Raw sensor reading from a simulated smart bin."""

    bin_id: str
    zone: str
    fill_level: float  # 0-100
    weight_kg: float
    temperature_c: float
    usage_count: int  # events in this sampling interval
    timestamp: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> BinReading:
        return cls(
            bin_id=str(d["bin_id"]),
            zone=str(d["zone"]),
            fill_level=float(d["fill_level"]),
            weight_kg=float(d["weight_kg"]),
            temperature_c=float(d["temperature_c"]),
            usage_count=int(d["usage_count"]),
            timestamp=float(d["timestamp"]),
        )


# Combined status for dashboard / storage (worst-case wins).
BinStatus = Literal["normal", "warning", "critical", "fire_risk", "probable_fire"]


@dataclass
class FogSummaryRecord:
    """
    Single bin snapshot after fog validation, smoothing, and scoring.
    This is what gets batched to the backend on a schedule or on alert.
    """

    bin_id: str
    zone: str
    fill_level: float
    weight_kg: float
    temperature_c: float
    usage_rate: float  # normalized 0-100 for priority formula
    priority: float  # 0-100 composite score
    status: BinStatus
    fill_alert: AlertLevel
    fire_risk: bool
    probable_fire_alert: bool
    timestamp: float
    fog_node_id: str = "fog-1"

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["fill_alert"] = self.fill_alert.value
        return d

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> FogSummaryRecord:
        return cls(
            bin_id=str(d["bin_id"]),
            zone=str(d["zone"]),
            fill_level=float(d["fill_level"]),
            weight_kg=float(d["weight_kg"]),
            temperature_c=float(d["temperature_c"]),
            usage_rate=float(d["usage_rate"]),
            priority=float(d["priority"]),
            status=cast(BinStatus, d["status"]),
            fill_alert=AlertLevel(str(d["fill_alert"])),
            fire_risk=bool(d["fire_risk"]),
            probable_fire_alert=bool(d["probable_fire_alert"]),
            timestamp=float(d["timestamp"]),
            fog_node_id=str(d.get("fog_node_id", "fog-1")),
        )


@dataclass
class FogOutboundMessage:
    """
    Wire payload from fog to API Gateway / queue.
    `message_type` distinguishes periodic summaries vs immediate alerts.
    """

    message_type: Literal["summary", "alert"]
    records: list[FogSummaryRecord]
    emitted_at: float
    schema_version: str = field(default="1.0")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "message_type": self.message_type,
            "emitted_at": self.emitted_at,
            "records": [r.to_dict() for r in self.records],
        }
