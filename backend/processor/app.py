"""
SQS → DynamoDB processor.

Consumes fog JSON messages (same shape as ``FogOutboundMessage``) and:
- writes one row per record into ``waste-bin-events``
- upserts each bin into ``waste-bin-latest``
"""

from __future__ import annotations

import json
import os
import uuid
from decimal import Decimal
from typing import Any

import boto3

dynamodb = boto3.resource("dynamodb")

EVENTS_TABLE = os.environ.get("EVENTS_TABLE", "")
LATEST_TABLE = os.environ.get("LATEST_TABLE", "")


def _to_dec(x: Any) -> Decimal:
    return Decimal(str(float(x)))


def _event_sk(
    record_ts: float,
    emitted_at: float,
    record_index: int,
    message_type: str,
) -> str:
    """
    Unique, time-ordered sort key for ``waste-bin-events``.

    Format: ``{nanoseconds}#{idx}#{message_type}#{uuid}`` — avoids collisions when
    multiple records share the same coarse timestamp or appear in one SQS message.
    """
    ns = int(float(record_ts) * 1e9)
    return f"{ns:020d}#{record_index:04d}#{message_type}#{uuid.uuid4().hex}"


def _process_body(body_str: str) -> None:
    data = json.loads(body_str)
    message_type = data["message_type"]
    emitted_at = float(data["emitted_at"])
    records = data["records"]

    events_tbl = dynamodb.Table(EVENTS_TABLE)
    latest_tbl = dynamodb.Table(LATEST_TABLE)

    for idx, rec in enumerate(records):
        bin_id = rec["bin_id"]
        ts = float(rec["timestamp"])
        sk = _event_sk(ts, emitted_at, idx, message_type)

        event_item: dict[str, Any] = {
            "bin_id": bin_id,
            "event_sk": sk,
            "zone": rec["zone"],
            "timestamp": _to_dec(ts),
            "emitted_at": _to_dec(emitted_at),
            "fill_level": _to_dec(rec["fill_level"]),
            "weight": _to_dec(rec["weight_kg"]),
            "temperature": _to_dec(rec["temperature_c"]),
            "usage_rate": _to_dec(rec["usage_rate"]),
            "priority": _to_dec(rec["priority"]),
            "status": rec["status"],
            "message_type": message_type,
            "fill_alert": rec["fill_alert"],
            "fire_risk": rec["fire_risk"],
            "probable_fire_alert": rec.get("probable_fire_alert", False),
        }
        if rec.get("fog_node_id"):
            event_item["fog_node_id"] = rec["fog_node_id"]

        events_tbl.put_item(Item=event_item)

        latest_item = {
            "bin_id": bin_id,
            "zone": rec["zone"],
            "latest_timestamp": _to_dec(ts),
            "fill_level": _to_dec(rec["fill_level"]),
            "weight": _to_dec(rec["weight_kg"]),
            "temperature": _to_dec(rec["temperature_c"]),
            "usage_rate": _to_dec(rec["usage_rate"]),
            "priority": _to_dec(rec["priority"]),
            "status": rec["status"],
            "last_message_type": message_type,
            "probable_fire_alert": rec.get("probable_fire_alert", False),
        }
        if rec.get("fog_node_id"):
            latest_item["fog_node_id"] = rec["fog_node_id"]

        latest_tbl.put_item(Item=latest_item)


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    if not EVENTS_TABLE or not LATEST_TABLE:
        raise RuntimeError("EVENTS_TABLE / LATEST_TABLE not configured")

    failures: list[dict[str, str]] = []

    for record in event.get("Records", []):
        msg_id = record.get("messageId", "")
        try:
            body = record.get("body", "")
            if not isinstance(body, str):
                body = str(body)
            _process_body(body)
            print(f"[processor] ok messageId={msg_id}")
        except Exception as e:  # noqa: BLE001
            print(f"[processor] FAIL messageId={msg_id} err={e}")
            failures.append({"itemIdentifier": msg_id})

    # Partial batch failure (SQS triggers): failed messages return to queue
    return {"batchItemFailures": failures}
