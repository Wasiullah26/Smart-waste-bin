#!/usr/bin/env python3
"""
Edge (laptop): publish simulated smart-bin readings to AWS IoT Core over MQTT (TLS).

Prerequisites
-------------
- Thing + X.509 certs from IoT Core (certificate + private key + Amazon Root CA 1).
- IoT policy allowing ``iot:Connect``, ``iot:Publish`` on your topic (e.g. ``waste/edge/readings``).
- ``pip install 'paho-mqtt>=1.6.1,<2'``

Example::

  export PYTHONPATH="/path/to/Fog&Edge"
  python scripts/edge_mqtt_publish.py \\
    --endpoint xxxxx-ats.iot.REGION.amazonaws.com \\
    --ca AmazonRootCA1.pem --cert device.pem.crt --key private.pem.key \\
    --topic waste/edge/readings --interval 2

  # Print each BinReading JSON line to stdout (demo / supervisor review):
  # ... same flags ... --print-payload
"""

from __future__ import annotations

import argparse
import json
import ssl
import sys
import time
from pathlib import Path

try:
    import paho.mqtt.client as mqtt
except ImportError:
    print("Install: pip install 'paho-mqtt>=1.6.1,<2'", file=sys.stderr)
    sys.exit(1)

from sensors.config import SensorSimulationConfig
from sensors.simulator import MultiBinOrchestrator


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Publish simulated BinReading JSON to AWS IoT Core (MQTT).",
    )
    parser.add_argument(
        "--endpoint",
        required=True,
        help="IoT data endpoint (e.g. xxxxxx-ats.iot.region.amazonaws.com).",
    )
    parser.add_argument("--ca", required=True, type=Path, help="Path to AmazonRootCA1.pem")
    parser.add_argument("--cert", required=True, type=Path, help="Path to device certificate (.pem.crt)")
    parser.add_argument("--key", required=True, type=Path, help="Path to private key (.pem.key)")
    parser.add_argument(
        "--topic",
        default="waste/edge/readings",
        help="MQTT topic (must match IoT Rule SQL).",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=3.0,
        help="Seconds between full fleet rounds.",
    )
    parser.add_argument(
        "--bins-per-zone",
        type=int,
        default=3,
        help="Bins per zone; total bins = (number of zones) × this (default 3).",
    )
    parser.add_argument(
        "--zones",
        type=str,
        default="zone-A,zone-B,zone-C",
        help=(
            "Comma-separated zone names (at least 2). Default only when this flag is omitted; "
            "if you pass --zones, only those names are used (not merged with A/B/C)."
        ),
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="RNG seed for simulation; use negative for nondeterministic runs.",
    )
    parser.add_argument(
        "--no-thermal-demo",
        action="store_true",
        help="Disable simulated hot bins.",
    )
    parser.add_argument(
        "--client-id",
        default="edge-laptop",
        help="MQTT client id (unique per connection).",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Do not print a line after each publish round (errors still print).",
    )
    parser.add_argument(
        "--print-payload",
        action="store_true",
        dest="print_payload",
        help="Print each MQTT payload (BinReading JSON, one line per publish) to stdout.",
    )
    args = parser.parse_args()

    for p, label in (
        (args.ca, "ca"),
        (args.cert, "cert"),
        (args.key, "key"),
    ):
        if not p.is_file():
            print(f"Missing {label} file: {p}", file=sys.stderr)
            sys.exit(1)

    zones = [z.strip() for z in args.zones.split(",") if z.strip()]
    if len(zones) < 2:
        print("Need at least 2 zones (comma-separated), e.g. --zones zone-A,zone-B", file=sys.stderr)
        sys.exit(1)
    if args.bins_per_zone < 1:
        print("--bins-per-zone must be >= 1", file=sys.stderr)
        sys.exit(1)

    seed: int | None = None if args.seed < 0 else args.seed
    cfg = SensorSimulationConfig(
        zones=zones,
        bins_per_zone=args.bins_per_zone,
        interval_sec=args.interval,
        random_seed=seed,
        enable_thermal_demo=not args.no_thermal_demo,
    )
    orch = MultiBinOrchestrator(cfg)

    client = mqtt.Client(client_id=args.client_id, protocol=mqtt.MQTTv311)
    client.tls_set(
        ca_certs=str(args.ca),
        certfile=str(args.cert),
        keyfile=str(args.key),
        tls_version=ssl.PROTOCOL_TLSv1_2,
    )

    rc_holder: list[int] = [-1]

    def on_connect(_c: mqtt.Client, _u: object, _f: object, rc: int) -> None:
        rc_holder[0] = rc
        if rc != 0:
            print(f"[edge] MQTT connect failed rc={rc}", file=sys.stderr)

    client.on_connect = on_connect
    client.connect(args.endpoint, 8883, keepalive=60)
    client.loop_start()

    # Wait for CONNACK
    for _ in range(50):
        if rc_holder[0] != -1:
            break
        time.sleep(0.1)
    if rc_holder[0] != 0:
        sys.exit(1)

    print(
        f"[edge] publishing to topic={args.topic!r} endpoint={args.endpoint!r} "
        f"zones={zones!r} bins_per_zone={args.bins_per_zone} total_bins={len(orch.bins)}",
        file=sys.stderr,
    )

    round_no = 0
    try:
        while True:
            round_no += 1
            n_pub = 0
            for reading in orch.all_readings_tick():
                payload = json.dumps(reading.to_dict())
                if args.print_payload:
                    print(payload, flush=True)
                info = client.publish(args.topic, payload, qos=1)
                n_pub += 1
                if info.rc != mqtt.MQTT_ERR_SUCCESS:
                    print(f"[edge] publish rc={info.rc}", file=sys.stderr)
            if not args.quiet:
                print(
                    f"[edge] round {round_no}: published {n_pub} message(s) -> {args.topic!r}",
                    file=sys.stderr,
                    flush=True,
                )
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\n[edge] stopped", file=sys.stderr)
    finally:
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    main()
