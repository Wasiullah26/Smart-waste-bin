"""Route handlers: DynamoDB access for dashboard read API."""

from __future__ import annotations

import os
from typing import Any

import boto3

from response import api_response, json_safe

_dynamodb = None


def _dynamodb_resource():
    global _dynamodb
    if _dynamodb is None:
        _dynamodb = boto3.resource("dynamodb")
    return _dynamodb


EVENTS_TABLE = os.environ.get("EVENTS_TABLE", "")
LATEST_TABLE = os.environ.get("LATEST_TABLE", "")
ZONE_GSI_NAME = os.environ.get("ZONE_GSI_NAME", "ZoneBinIndex")


def _query_limit(event: dict[str, Any], default: int = 50, max_limit: int = 200) -> int:
    qs = event.get("queryStringParameters") or {}
    if isinstance(qs, dict) and "limit" in qs and qs["limit"] is not None:
        try:
            return min(max_limit, max(1, int(qs["limit"])))
        except (TypeError, ValueError):
            return default
    return default


def _scan_all(table_name: str, **scan_kwargs: Any) -> list[dict[str, Any]]:
    table = _dynamodb_resource().Table(table_name)
    items: list[dict[str, Any]] = []
    kwargs = dict(scan_kwargs)
    while True:
        resp = table.scan(**kwargs)
        items.extend(resp.get("Items", []))
        lek = resp.get("LastEvaluatedKey")
        if not lek:
            break
        kwargs["ExclusiveStartKey"] = lek
    return items


def handle_bins() -> dict[str, Any]:
    items = _scan_all(LATEST_TABLE)
    return api_response(200, {"bins": json_safe(items)})


def handle_bin_by_id(bin_id: str) -> dict[str, Any]:
    table = _dynamodb_resource().Table(LATEST_TABLE)
    resp = table.get_item(Key={"bin_id": bin_id})
    item = resp.get("Item")
    if not item:
        return api_response(404, {"error": "bin not found"})
    return api_response(200, json_safe(item))


def handle_zone_bins(zone: str) -> dict[str, Any]:
    table = _dynamodb_resource().Table(LATEST_TABLE)
    items: list[dict[str, Any]] = []
    q_kwargs: dict[str, Any] = {
        "IndexName": ZONE_GSI_NAME,
        "KeyConditionExpression": "#z = :zone",
        "ExpressionAttributeNames": {"#z": "zone"},
        "ExpressionAttributeValues": {":zone": zone},
    }
    while True:
        resp = table.query(**q_kwargs)
        items.extend(resp.get("Items", []))
        lek = resp.get("LastEvaluatedKey")
        if not lek:
            break
        q_kwargs["ExclusiveStartKey"] = lek
    return api_response(200, {"zone": zone, "bins": json_safe(items)})


def handle_critical() -> dict[str, Any]:
    table = _dynamodb_resource().Table(LATEST_TABLE)
    items: list[dict[str, Any]] = []
    scan_kwargs: dict[str, Any] = {
        "FilterExpression": "#s IN (:c, :f, :p)",
        "ExpressionAttributeNames": {"#s": "status"},
        "ExpressionAttributeValues": {
            ":c": "critical",
            ":f": "fire_risk",
            ":p": "probable_fire",
        },
    }
    while True:
        resp = table.scan(**scan_kwargs)
        items.extend(resp.get("Items", []))
        lek = resp.get("LastEvaluatedKey")
        if not lek:
            break
        scan_kwargs["ExclusiveStartKey"] = lek
    return api_response(200, {"critical": json_safe(items)})


def handle_history(bin_id: str, event: dict[str, Any]) -> dict[str, Any]:
    limit = _query_limit(event)
    table = _dynamodb_resource().Table(EVENTS_TABLE)
    resp = table.query(
        KeyConditionExpression="bin_id = :b",
        ExpressionAttributeValues={":b": bin_id},
        ScanIndexForward=False,
        Limit=limit,
    )
    items = resp.get("Items", [])
    return api_response(
        200,
        {"bin_id": bin_id, "events": json_safe(items), "count": len(items)},
    )
