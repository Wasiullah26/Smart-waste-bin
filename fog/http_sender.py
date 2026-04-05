"""
HTTPS POST uplink for fog outbound messages (API Gateway ingestion).

Uses ``requests`` with retries and bounded timeouts. Intended for Learner Lab /
manual deploy workflows (no long-lived credentials in CI).
"""

from __future__ import annotations

import logging
from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


def _is_allowed_url(url: str) -> bool:
    u = url.lower().strip()
    if u.startswith("https://"):
        return True
    if u.startswith("http://127.0.0.1") or u.startswith("http://localhost"):
        return True
    return False


def build_session(
    *,
    retries: int = 3,
    backoff_factor: float = 0.5,
    status_forcelist: tuple[int, ...] = (502, 503, 504),
) -> requests.Session:
    session = requests.Session()
    retry = Retry(
        total=retries,
        connect=retries,
        read=retries,
        status=retries,
        backoff_factor=backoff_factor,
        status_forcelist=list(status_forcelist),
        allowed_methods=("POST",),
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


def post_fog_payload(
    session: requests.Session,
    url: str,
    payload: dict[str, Any],
    *,
    timeout_sec: float = 10.0,
) -> tuple[bool, int | None, str]:
    """
    POST JSON body to ingestion endpoint.

    Returns (success, http_status_or_none, detail_message).
    """
    if not _is_allowed_url(url):
        return (
            False,
            None,
            "URL must use https://, or http://localhost / http://127.0.0.1 for local SAM tests",
        )

    try:
        resp = session.post(
            url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=timeout_sec,
        )
    except requests.RequestException as e:
        logger.warning("[uplink] POST failed: %s", e)
        return False, None, str(e)

    if 200 <= resp.status_code < 300:
        logger.info(
            "[uplink] OK status=%s message_type=%s",
            resp.status_code,
            payload.get("message_type"),
        )
        return True, resp.status_code, (resp.text or "")[:500]

    logger.warning("[uplink] bad status=%s body=%s", resp.status_code, (resp.text or "")[:300])
    return False, resp.status_code, (resp.text or "")[:500]
