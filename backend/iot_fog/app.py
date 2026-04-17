"""
AWS IoT Core (MQTT) → Lambda: restore fog state, process raw BinReading, persist state, enqueue FogOutboundMessage.
"""

from __future__ import annotations

import json
import os
import time
from typing import Any

import boto3

from fog.service import FogProcessingService
from shared.constants import SMOOTHING_WINDOW
from shared.models import BinReading

_sqs = boto3.client("sqs")
_ddb = boto3.resource("dynamodb")

QUEUE_URL = os.environ.get("QUEUE_URL", "")
STATE_TABLE_NAME = os.environ.get("STATE_TABLE_NAME", "")
FOG_NODE_ID = os.environ.get("FOG_NODE_ID", "fog-1")
SUMMARY_INTERVAL_SEC = float(os.environ.get("SUMMARY_INTERVAL_SEC", "5"))
SMOOTHING_WINDOW_ENV = int(os.environ.get("SMOOTHING_WINDOW", str(SMOOTHING_WINDOW)))


def _parse_bin_reading(event: dict[str, Any]) -> BinReading | None:
    """IoT Rule SQL ``SELECT * FROM 'topic'`` passes JSON fields at top level."""
    if not isinstance(event, dict):
        return None
    if "bin_id" in event:
        try:
            return BinReading.from_dict(event)
        except (KeyError, TypeError, ValueError):
            return None
    # Fallback: nested payload (some rule shapes)
    inner = event.get("reading") or event.get("data")
    if isinstance(inner, dict):
        try:
            return BinReading.from_dict(inner)
        except (KeyError, TypeError, ValueError):
            return None
    return None


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    if not QUEUE_URL or not STATE_TABLE_NAME:
        print("[iot_fog] missing QUEUE_URL or STATE_TABLE_NAME")
        return {"ok": False, "error": "misconfigured"}

    reading = _parse_bin_reading(event)
    if reading is None:
        print(f"[iot_fog] skip: could not parse BinReading keys={list(event)[:12]}")
        return {"ok": False, "skipped": True}

    table = _ddb.Table(STATE_TABLE_NAME)
    win = SMOOTHING_WINDOW_ENV if SMOOTHING_WINDOW_ENV > 0 else SMOOTHING_WINDOW
    svc = FogProcessingService(
        summary_interval_sec=SUMMARY_INTERVAL_SEC,
        fog_node_id=FOG_NODE_ID,
        smoothing_window=win,
    )

    resp = table.get_item(Key={"fog_node_id": FOG_NODE_ID})
    item = resp.get("Item") or {}
    raw_state = item.get("state")
    if isinstance(raw_state, str) and raw_state.strip():
        try:
            svc.apply_state_dict(json.loads(raw_state))
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            print(f"[iot_fog] reset state (bad snapshot): {e}")

    messages = svc.process_reading(reading)

    # Enqueue first so a cold retry does not advance state without delivery.
    mids: list[str] = []
    for msg in messages:
        body = json.dumps(msg.to_dict())
        r = _sqs.send_message(QueueUrl=QUEUE_URL, MessageBody=body)
        mid = r.get("MessageId", "")
        mids.append(mid)
        print(
            f"[iot_fog] sqs message_type={msg.message_type} id={mid} records={len(msg.records)}",
        )

    table.put_item(
        Item={
            "fog_node_id": FOG_NODE_ID,
            "state": json.dumps(svc.to_state_dict()),
            "updated_at": int(time.time()),
        }
    )

    return {
        "ok": True,
        "messages": len(messages),
        "sqs_message_ids": mids,
    }
