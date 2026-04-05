#!/usr/bin/env bash
# Run the built-in fog demo and POST summaries to your deployed /ingest endpoint.
#
# This is a shell script — run it with bash, NOT with python3:
#   ./scripts/run_fog_demo.sh
#   bash scripts/run_fog_demo.sh
#
# Usage (from repo root):
#   export API_BASE_URL="https://YOUR_ID.execute-api.REGION.amazonaws.com"
#   chmod +x scripts/run_fog_demo.sh
#   ./scripts/run_fog_demo.sh
#
# Or: source .env   # if API_BASE_URL is set there

set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
export PYTHONPATH="$ROOT"

if [[ -f .venv/bin/activate ]]; then
  # shellcheck source=/dev/null
  source .venv/bin/activate
fi

API_ROOT="${API_BASE_URL:-}"
if [[ -z "$API_ROOT" ]]; then
  echo "Set API_BASE_URL to your HttpApiUrl (no trailing slash), e.g." >&2
  echo "  export API_BASE_URL=https://xxxx.execute-api.us-east-1.amazonaws.com" >&2
  exit 1
fi

URL="${API_ROOT%/}/ingest"
echo "Posting fog demo to: $URL"
exec python -m fog --demo --interval 3 --summary-interval 5 --post-url "$URL" --no-stdout "$@"
