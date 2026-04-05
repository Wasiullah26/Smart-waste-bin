"""
Run sensor simulation: prints one JSON object per line (NDJSON) to stdout.

Example::

    PYTHONPATH=. python -m sensors --interval 3 --bins-per-zone 3
"""

from __future__ import annotations

import argparse
import json
import sys
import time

from sensors.config import SensorSimulationConfig
from sensors.simulator import MultiBinOrchestrator


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Simulate 5–10 smart waste bins across 2–3 zones (NDJSON to stdout).",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=3.0,
        help="Seconds between full-fleet reading rounds (2–5 typical).",
    )
    parser.add_argument(
        "--bins-per-zone",
        type=int,
        default=3,
        help="Bins per zone; total bins = len(zones) * this value.",
    )
    parser.add_argument(
        "--zones",
        type=str,
        default="zone-A,zone-B,zone-C",
        help="Comma-separated logical zones.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="RNG seed for repeatable runs (use a negative value for nondeterministic).",
    )
    args = parser.parse_args()

    zones = [z.strip() for z in args.zones.split(",") if z.strip()]
    if len(zones) < 2:
        print("Need at least 2 zones (comma-separated).", file=sys.stderr)
        sys.exit(1)

    seed = None if args.seed < 0 else args.seed
    cfg = SensorSimulationConfig(
        zones=zones,
        bins_per_zone=args.bins_per_zone,
        interval_sec=args.interval,
        random_seed=seed,
    )
    orch = MultiBinOrchestrator(cfg)
    print(
        f"[sensors] bins={len(orch.bins)} zones={zones} interval={args.interval}s",
        file=sys.stderr,
    )

    while True:
        for reading in orch.all_readings_tick():
            print(json.dumps(reading.to_dict()), flush=True)
        time.sleep(args.interval)


if __name__ == "__main__":
    main()
