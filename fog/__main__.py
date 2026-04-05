"""
Fog processing entrypoint.

- Default: read NDJSON sensor lines from stdin, write fog messages to stdout.
- ``--demo``: run an embedded sensor loop (no stdin) for quick local tests.

Example pipe::

    PYTHONPATH=. python -m sensors --interval 2 | PYTHONPATH=. python -m fog --summary-interval 5
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from typing import Any

from fog.http_sender import build_session, post_fog_payload
from fog.service import FogProcessingService
from shared.models import BinReading


def main() -> None:
    parser = argparse.ArgumentParser(description="Fog validation, smoothing, and uplink batching.")
    parser.add_argument(
        "--summary-interval",
        type=float,
        default=5.0,
        help="Seconds between periodic summary messages (all bins).",
    )
    parser.add_argument(
        "--fog-node-id",
        type=str,
        default="fog-1",
        help="Identifier stamped onto outbound records.",
    )
    parser.add_argument(
        "--smoothing-window",
        type=int,
        default=0,
        help="Moving-average window length (0 = use default from shared.constants).",
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run embedded sensor simulator (ignores stdin).",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=3.0,
        help="With --demo: seconds between sensor fleet ticks.",
    )
    parser.add_argument(
        "--no-thermal-demo",
        action="store_true",
        help="With --demo: disable hot-low-fill bins (default demo includes 2 bins with high temp, low fill).",
    )
    parser.add_argument(
        "--post-url",
        type=str,
        default="",
        help="If set, HTTPS POST each outbound message to this URL (e.g. .../ingest).",
    )
    parser.add_argument(
        "--post-timeout",
        type=float,
        default=10.0,
        help="Seconds for each POST request.",
    )
    parser.add_argument(
        "--post-retries",
        type=int,
        default=3,
        help="urllib3 retry count for transient HTTP failures.",
    )
    parser.add_argument(
        "--no-stdout",
        action="store_true",
        help="Do not print JSON lines to stdout (use with --post-url for silent uplink).",
    )
    args = parser.parse_args()

    if args.post_url:
        logging.basicConfig(level=logging.INFO, format="%(message)s")

    win = args.smoothing_window if args.smoothing_window > 0 else None
    svc = FogProcessingService(
        summary_interval_sec=args.summary_interval,
        fog_node_id=args.fog_node_id,
        smoothing_window=win,
    )
    http = (
        build_session(retries=max(0, args.post_retries))
        if args.post_url
        else None
    )

    def emit(msg_dict: dict[str, Any]) -> None:
        if not args.no_stdout:
            print(json.dumps(msg_dict), flush=True)
        if http and args.post_url:
            ok, code, detail = post_fog_payload(
                http,
                args.post_url.strip(),
                msg_dict,
                timeout_sec=args.post_timeout,
            )
            if not ok:
                print(
                    f"[fog] uplink failed ok={ok} status={code} detail={detail[:200]}",
                    file=sys.stderr,
                )

    if args.demo:
        from sensors.config import SensorSimulationConfig
        from sensors.simulator import MultiBinOrchestrator

        cfg = SensorSimulationConfig(
            interval_sec=args.interval,
            enable_thermal_demo=not args.no_thermal_demo,
        )
        orch = MultiBinOrchestrator(cfg)
        thermal = "on" if cfg.enable_thermal_demo else "off"
        print(
            f"[fog] demo mode bins={len(orch.bins)} thermal_demo={thermal} summary_interval={args.summary_interval}s",
            file=sys.stderr,
        )
        while True:
            for reading in orch.all_readings_tick():
                for msg in svc.process_reading(reading):
                    emit(msg.to_dict())
            time.sleep(args.interval)
    else:
        print(
            f"[fog] reading stdin NDJSON summary_interval={args.summary_interval}s",
            file=sys.stderr,
        )
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            try:
                payload = json.loads(line)
                reading = BinReading.from_dict(payload)
            except (json.JSONDecodeError, KeyError, TypeError, ValueError) as e:
                print(f"[fog] skip bad line: {e}", file=sys.stderr)
                continue
            for msg in svc.process_reading(reading):
                emit(msg.to_dict())


if __name__ == "__main__":
    main()
