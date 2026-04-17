#!/usr/bin/env bash
# Publish simulated bin readings to AWS IoT Core (MQTT TLS).
# Requires cert files under docs/ (see .gitignore — do not commit .pem).
#
# Usage (from repo root):
#   chmod +x scripts/run_edge_mqtt.sh
#   ./scripts/run_edge_mqtt.sh
#   ./scripts/run_edge_mqtt.sh --zones zone-A,zone-B --bins-per-zone 5
#   ./scripts/run_edge_mqtt.sh -- --zones ...   # leading "--" is optional
#
# Optional overrides:
#   export IOT_ENDPOINT="xxxx-ats.iot.us-east-1.amazonaws.com"

set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
export PYTHONPATH="$ROOT"

if [[ -f .venv/bin/activate ]]; then
  # shellcheck source=/dev/null
  source .venv/bin/activate
fi

ENDPOINT="${IOT_ENDPOINT:-a1mr4h9ipp5f1t-ats.iot.eu-west-1.amazonaws.com}"
CA="$ROOT/docs/AmazonRootCA1.pem"
CERT="$ROOT/docs/993e6cb7ce93fd5624fc800feeca16ebcc78a5c537d235af731edb196815e90d-certificate.pem.crt"
KEY="$ROOT/docs/993e6cb7ce93fd5624fc800feeca16ebcc78a5c537d235af731edb196815e90d-private.pem.key"

for f in "$CA" "$CERT" "$KEY"; do
  if [[ ! -f "$f" ]]; then
    echo "Missing file: $f" >&2
    exit 1
  fi
done

# Allow "./run_edge_mqtt.sh -- --zones ..." — do not pass a lone "--" through to Python.
if [[ "${1-}" == "--" ]]; then
  shift
fi

exec python3 "$ROOT/scripts/edge_mqtt_publish.py" \
  --endpoint "$ENDPOINT" \
  --ca "$CA" \
  --cert "$CERT" \
  --key "$KEY" \
  --topic waste/edge/readings \
  --interval 2 \
  "$@"
