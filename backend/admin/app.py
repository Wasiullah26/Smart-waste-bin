"""
Admin API — destructive operations for lab demos (optional X-Admin-Key).
POST /admin/purge — purge SQS (in-flight messages), then wipe events + latest tables.

Also wipes FogStateTable when STATE_TABLE is set: IoTFogFunction keeps a per-fleet
snapshot in that table; if only events/latest are cleared, the next MQTT summary
would re-upsert every old bin_id/zone from restored fog state.
"""

from __future__ import annotations

import json
import os
from typing import Any

import boto3

dynamodb = boto3.resource("dynamodb")
sqs_client = boto3.client("sqs")

EVENTS_TABLE = os.environ.get("EVENTS_TABLE", "")
LATEST_TABLE = os.environ.get("LATEST_TABLE", "")
STATE_TABLE = os.environ.get("STATE_TABLE", "").strip()
QUEUE_URL = os.environ.get("QUEUE_URL", "")
ADMIN_API_KEY = os.environ.get("ADMIN_API_KEY", "").strip()

_CORS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type,X-Admin-Key",
    "Access-Control-Allow-Methods": "POST,OPTIONS",
}


def _response(status: int, body: dict[str, Any]) -> dict[str, Any]:
    return {
        "statusCode": status,
        "headers": {"Content-Type": "application/json", **_CORS},
        "body": json.dumps(body),
    }


def _http_method(event: dict[str, Any]) -> str:
    ctx = event.get("requestContext") or {}
    http = ctx.get("http") or {}
    return (http.get("method") or event.get("httpMethod") or "").upper()


def _http_path(event: dict[str, Any]) -> str:
    raw = event.get("rawPath") or event.get("path") or ""
    http = (event.get("requestContext") or {}).get("http") or {}
    return raw or str(http.get("path") or "")


def _is_purge_post(event: dict[str, Any]) -> bool:
    rk = event.get("routeKey") or ""
    if rk == "POST /admin/purge":
        return True
    if _http_method(event) != "POST":
        return False
    path = _http_path(event).rstrip("/") or "/"
    return path == "/admin/purge" or path.endswith("/admin/purge")


def _check_key(event: dict[str, Any]) -> bool:
    if not ADMIN_API_KEY:
        return True
    headers = event.get("headers") or {}
    low = {k.lower(): v for k, v in headers.items()}
    return low.get("x-admin-key") == ADMIN_API_KEY


def _purge_table(table_name: str, key_names: tuple[str, ...]) -> int:
    table = dynamodb.Table(table_name)
    total = 0
    scan_kwargs: dict[str, Any] = {}
    while True:
        resp = table.scan(**scan_kwargs)
        items = resp.get("Items", [])
        if items:
            with table.batch_writer() as batch:
                for item in items:
                    key = {k: item[k] for k in key_names}
                    batch.delete_item(Key=key)
                    total += 1
        lek = resp.get("LastEvaluatedKey")
        if not lek:
            break
        scan_kwargs["ExclusiveStartKey"] = lek
    return total


def _purge_sqs() -> bool:
    if not QUEUE_URL:
        return False
    sqs_client.purge_queue(QueueUrl=QUEUE_URL)
    return True


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    if not EVENTS_TABLE or not LATEST_TABLE:
        return _response(500, {"error": "EVENTS_TABLE / LATEST_TABLE not configured"})

    if not _is_purge_post(event):
        return _response(404, {"error": "not found", "expected": "POST /admin/purge"})

    if not _check_key(event):
        return _response(403, {"error": "invalid or missing X-Admin-Key"})

    try:
        sqs_purged = _purge_sqs()
        n_events = _purge_table(EVENTS_TABLE, ("bin_id", "event_sk"))
        n_latest = _purge_table(LATEST_TABLE, ("bin_id",))
        n_fog_state = _purge_table(STATE_TABLE, ("fog_node_id",)) if STATE_TABLE else 0
    except Exception as e:  # noqa: BLE001
        return _response(500, {"error": str(e)})

    body: dict[str, Any] = {
        "purged": True,
        "deleted_events": n_events,
        "deleted_latest": n_latest,
        "sqs_purged": sqs_purged,
    }
    if STATE_TABLE:
        body["deleted_fog_state"] = n_fog_state
    return _response(200, body)
