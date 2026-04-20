"""JSON helpers and API Gateway response shaping."""

from __future__ import annotations

import json
from decimal import Decimal
from typing import Any


def json_safe(obj: Any) -> Any:
    if isinstance(obj, Decimal):
        if obj % 1 == 0:
            return int(obj)
        return float(obj)
    if isinstance(obj, dict):
        return {k: json_safe(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [json_safe(v) for v in obj]
    return obj


# Browsers calling the API from localhost need these on the Lambda response
# (API Gateway CORS also applies; duplicate headers are harmless for simple GET/POST).
_CORS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Allow-Methods": "GET,OPTIONS",
}


def api_response(status: int, body: Any) -> dict[str, Any]:
    headers = {
        "Content-Type": "application/json",
        # Prevent browsers / intermediaries from caching JSON reads (stale bins after purge).
        "Cache-Control": "no-store, max-age=0, must-revalidate",
        **_CORS,
    }
    return {
        "statusCode": status,
        "headers": headers,
        "body": json.dumps(body, default=str),
    }
