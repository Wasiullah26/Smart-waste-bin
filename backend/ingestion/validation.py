"""JSON validation for fog outbound messages (shared with tests)."""

from __future__ import annotations

from typing import Any

REQUIRED_TOP = ("schema_version", "message_type", "emitted_at", "records")
RECORD_FIELDS = (
    "bin_id",
    "zone",
    "fill_level",
    "weight_kg",
    "temperature_c",
    "usage_rate",
    "priority",
    "status",
    "fill_alert",
    "fire_risk",
    "probable_fire_alert",
    "timestamp",
)


def _is_str(v: Any) -> bool:
    return isinstance(v, str) and len(v) > 0


def _is_num(v: Any) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def validate_payload(data: Any) -> tuple[bool, str | None]:
    """Return (ok, error_message)."""
    if not isinstance(data, dict):
        return False, "body must be a JSON object"

    for k in REQUIRED_TOP:
        if k not in data:
            return False, f"missing field: {k}"

    if data["schema_version"] != "1.0":
        return False, "unsupported schema_version"

    if data["message_type"] not in ("summary", "alert"):
        return False, "message_type must be summary or alert"

    if not _is_num(data["emitted_at"]):
        return False, "emitted_at must be a number"

    recs = data["records"]
    if not isinstance(recs, list) or len(recs) == 0:
        return False, "records must be a non-empty array"

    for i, rec in enumerate(recs):
        if not isinstance(rec, dict):
            return False, f"records[{i}] must be an object"
        for f in RECORD_FIELDS:
            if f not in rec:
                return False, f"records[{i}] missing {f}"
        if not _is_str(rec["bin_id"]) or not _is_str(rec["zone"]):
            return False, f"records[{i}] bin_id and zone must be non-empty strings"
        if not _is_num(rec["fill_level"]) or not (0 <= float(rec["fill_level"]) <= 100):
            return False, f"records[{i}] fill_level must be between 0 and 100"
        if not _is_num(rec["weight_kg"]):
            return False, f"records[{i}] weight_kg invalid"
        if not _is_num(rec["temperature_c"]):
            return False, f"records[{i}] temperature_c invalid"
        if not _is_num(rec["usage_rate"]):
            return False, f"records[{i}] usage_rate invalid"
        if not _is_num(rec["priority"]):
            return False, f"records[{i}] priority invalid"
        if rec["status"] not in (
            "normal",
            "warning",
            "critical",
            "fire_risk",
            "probable_fire",
        ):
            return False, f"records[{i}] status invalid"
        if rec["fill_alert"] not in ("none", "warning", "critical"):
            return False, f"records[{i}] fill_alert invalid"
        if not isinstance(rec["fire_risk"], bool):
            return False, f"records[{i}] fire_risk must be boolean"
        if not isinstance(rec["probable_fire_alert"], bool):
            return False, f"records[{i}] probable_fire_alert must be boolean"
        if not _is_num(rec["timestamp"]):
            return False, f"records[{i}] timestamp invalid"

    return True, None
