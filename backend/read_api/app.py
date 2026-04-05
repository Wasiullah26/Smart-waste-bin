"""
Dashboard read API — DynamoDB queries behind API Gateway GET routes.

Endpoints:
  GET /bins
  GET /bins/{bin_id}
  GET /zones/{zone}/bins
  GET /critical
  GET /history/{bin_id}
"""

from __future__ import annotations

import os
from typing import Any

from response import api_response
from router import dispatch

EVENTS_TABLE = os.environ.get("EVENTS_TABLE", "")
LATEST_TABLE = os.environ.get("LATEST_TABLE", "")


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    if not EVENTS_TABLE or not LATEST_TABLE:
        return api_response(500, {"error": "table environment variables missing"})
    return dispatch(event)
