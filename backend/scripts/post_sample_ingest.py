#!/usr/bin/env python3
"""
POST a sample fog outbound JSON payload to a deployed API Gateway /ingest endpoint.

Usage:
  export API_BASE_URL="https://xxxx.execute-api.region.amazonaws.com"
  python post_sample_ingest.py

Or pass the URL as the first argument:
  python post_sample_ingest.py "https://xxxx.execute-api.region.amazonaws.com"
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request

SAMPLE = {
    "schema_version": "1.0",
    "message_type": "summary",
    "emitted_at": 1712345690.0,
    "records": [
        {
            "bin_id": "BIN-zone-A-01",
            "zone": "zone-A",
            "fill_level": 41.2,
            "weight_kg": 50.1,
            "temperature_c": 22.1,
            "usage_rate": 23.33,
            "priority": 35.12,
            "status": "normal",
            "fill_alert": "none",
            "fire_risk": False,
            "probable_fire_alert": False,
            "timestamp": 1712345688.9,
            "fog_node_id": "fog-1",
        }
    ],
}


def main() -> int:
    base = (sys.argv[1] if len(sys.argv) > 1 else os.environ.get("API_BASE_URL", "")).rstrip("/")
    if not base:
        print("Set API_BASE_URL or pass base URL as argv[1]", file=sys.stderr)
        return 1
    url = f"{base}/ingest"
    body = json.dumps(SAMPLE).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            out = resp.read().decode("utf-8")
            print(resp.status, out)
    except urllib.error.HTTPError as e:
        print(e.code, e.read().decode("utf-8", errors="replace"), file=sys.stderr)
        return 1
    except urllib.error.URLError as e:
        print(str(e), file=sys.stderr)
        err_text = str(e.reason) if getattr(e, "reason", None) is not None else str(e)
        if any(
            s in err_text.lower()
            for s in ("nodename", "name or service not known", "failed to resolve")
        ):
            print(
                "\nDNS could not resolve the host. Common fixes:\n"
                "  • Use the real HttpApiUrl from `sam deploy` or CloudFormation Outputs — "
                "not a placeholder like abc123 or abc123xyz.\n"
                "  • The region in the URL must be a valid AWS region code "
                "(e.g. us-east-1, eu-west-1, eu-central-1). Note: there is no eu-east-1.\n"
                "  • Example: aws cloudformation describe-stacks --stack-name YOUR_STACK "
                "--query \"Stacks[0].Outputs[?OutputKey=='HttpApiUrl'].OutputValue\" --output text\n",
                file=sys.stderr,
            )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
