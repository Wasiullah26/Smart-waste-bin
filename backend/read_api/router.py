"""HTTP API route dispatch (``routeKey`` + fallback for local tests)."""

from __future__ import annotations

from typing import Any

from handlers import (
    handle_bin_by_id,
    handle_bins,
    handle_critical,
    handle_history,
    handle_zone_bins,
)
from response import api_response


def dispatch_fallback(event: dict[str, Any]) -> dict[str, Any] | None:
    """Resolve routes when ``routeKey`` is missing (some local test payloads)."""
    raw = event.get("rawPath") or ""
    params = event.get("pathParameters") or {}
    if raw == "/bins":
        return handle_bins()
    if raw == "/critical":
        return handle_critical()
    if raw.startswith("/bins/") and len(raw) > len("/bins/"):
        rest = raw[len("/bins/") :]
        if "/" not in rest:
            return handle_bin_by_id(rest)
    if raw.startswith("/zones/") and raw.endswith("/bins"):
        inner = raw[len("/zones/") : -len("/bins")]
        if inner:
            return handle_zone_bins(inner)
    if raw.startswith("/history/"):
        rest = raw[len("/history/") :]
        if rest and "/" not in rest:
            return handle_history(rest, event)
    bid = params.get("bin_id")
    if bid and "/history" in raw:
        return handle_history(bid, event)
    if bid and "/bins/" in raw and "zones" not in raw:
        return handle_bin_by_id(bid)
    zone = params.get("zone")
    if zone:
        return handle_zone_bins(zone)
    return None


def dispatch(event: dict[str, Any]) -> dict[str, Any]:
    route_key = event.get("routeKey") or ""
    params = event.get("pathParameters") or {}

    if route_key == "GET /bins":
        return handle_bins()
    if route_key == "GET /critical":
        return handle_critical()
    if route_key == "GET /bins/{bin_id}":
        bid = params.get("bin_id")
        if bid:
            return handle_bin_by_id(bid)
    if route_key == "GET /zones/{zone}/bins":
        zone = params.get("zone")
        if zone:
            return handle_zone_bins(zone)
    if route_key == "GET /history/{bin_id}":
        bid = params.get("bin_id")
        if bid:
            return handle_history(bid, event)

    fb = dispatch_fallback(event)
    if fb is not None:
        return fb

    return api_response(404, {"error": "route not recognized", "routeKey": route_key})
