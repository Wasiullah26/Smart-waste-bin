"""
API Gateway → SQS ingestion Lambda.

POST /ingest with JSON body matching the fog ``FogOutboundMessage`` shape.
Valid payloads are sent to SQS as the message body (stringified JSON).
"""

from __future__ import annotations

import json
import os
from typing import Any

import boto3

from validation import validate_payload

sqs = boto3.client("sqs")
QUEUE_URL = os.environ.get("QUEUE_URL", "")

MAX_BODY_BYTES = 240_000  # below SQS 256 KiB limit with headroom


def _response(status: int, body: dict[str, Any]) -> dict[str, Any]:
    headers = {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "Content-Type",
        "Access-Control-Allow-Methods": "POST,OPTIONS",
    }
    return {
        "statusCode": status,
        "headers": headers,
        "body": json.dumps(body),
    }


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    if not QUEUE_URL:
        return _response(500, {"error": "QUEUE_URL is not configured"})

    raw_body = event.get("body") or ""
    if event.get("isBase64Encoded"):
        import base64

        raw_body = base64.b64decode(raw_body).decode("utf-8")

    if len(raw_body.encode("utf-8")) > MAX_BODY_BYTES:
        return _response(413, {"error": "payload too large"})

    try:
        data = json.loads(raw_body) if raw_body else None
    except json.JSONDecodeError:
        return _response(400, {"error": "invalid JSON"})

    ok, err = validate_payload(data)
    if not ok or data is None:
        return _response(400, {"error": err or "invalid payload"})

    try:
        resp = sqs.send_message(QueueUrl=QUEUE_URL, MessageBody=json.dumps(data))
    except Exception as e:  # noqa: BLE001 — surface minimal message to client
        print(f"[ingest] SQS send failed: {e}")
        return _response(502, {"error": "failed to enqueue message"})

    mid = resp.get("MessageId", "")
    print(f"[ingest] accepted message_type={data.get('message_type')} sqs_message_id={mid}")
    return _response(
        202,
        {"accepted": True, "message_id": mid, "records": len(data["records"])},
    )


# Local smoke test helper (optional)
if __name__ == "__main__":
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
    print(validate_payload(sample))
