Smart Waste Bin — Fog & Edge (local run)
=========================================

Prerequisites
-------------
- Python 3.10 or newer
- Working directory: project root (folder containing `shared`, `sensors`, `fog`).

Set PYTHONPATH to the project root so packages resolve::

  export PYTHONPATH="/path/to/Fog&Edge"

(On Windows PowerShell: `$env:PYTHONPATH="C:\path\to\Fog&Edge"`)

Sensor simulation (NDJSON to stdout)
-------------------------------------
Emits one JSON object per line (one reading per bin per tick). Default: 3 zones × 3 bins = 9 bins.

  python -m sensors --interval 3 --bins-per-zone 3 --zones zone-A,zone-B,zone-C

Options:
  --interval       Seconds between full-fleet rounds (try 2–5).
  --bins-per-zone  Integer; total bins = (number of zones) × (bins-per-zone).
  --zones          Comma-separated zone names (at least 2).
  --seed           RNG seed (negative = nondeterministic).

Fog processing
--------------
From stdin (pipe from sensors)::

  python -m sensors --interval 2 | python -m fog --summary-interval 5

Fog options:
  --summary-interval  Seconds between periodic "summary" messages (all bins).
  --fog-node-id         ID stamped on records (default fog-1).
  --smoothing-window    Moving-average length (default from shared/constants.py).
  --post-url            HTTPS POST each outbound JSON message to API Gateway /ingest (needs: pip install -r requirements.txt).
  --no-stdout           With --post-url: do not print NDJSON lines.
  --post-timeout        POST timeout seconds (default 10).
  --post-retries        HTTP retry count (default 3).
  --no-thermal-demo     With --demo: disable the two simulated bins that emit high temperature with low fill (default: one bin exercises probable fire ≥60°C, one fire risk ~45–55°C).

Standalone fog demo (embedded sensors, no pipe)::

  python -m fog --demo --interval 2 --summary-interval 5

HTTPS uplink example (after SAM deploy — see backend/README.md)::

  python -m fog --demo --post-url "https://xxxx.execute-api.REGION.amazonaws.com/ingest"

MQTT uplink (edge laptop → AWS IoT Core → IoTFogFunction → same SQS as /ingest)::

  See backend/README.md section "MQTT (AWS IoT Core)". Requires Thing certs + IoT Rule on topic ``waste/edge/readings``.

  With certs under ``docs/`` (see ``scripts/run_edge_mqtt.sh`` for paths), from repo root::

    ./scripts/run_edge_mqtt.sh

  Or call ``python scripts/edge_mqtt_publish.py`` with ``--endpoint``, ``--ca``, ``--cert``, ``--key``, ``--topic waste/edge/readings``.

Sample payloads
---------------
- samples/sensor_reading.ndjson — raw lines the fog expects on stdin.
- samples/fog_to_aws_message.json — example outbound message shape for API Gateway / SQS.

AWS backend (SAM) — deploy from your machine (Learner Lab)
-----------------------------------------------------------
See **backend/README.md** for temporary credentials, `sam build`, `sam deploy --guided`, **curl** examples, verification checklist, and the **HttpApiUrl** output.

CI (GitHub Actions) runs tests + `sam validate` + `sam build` only — it does **not** deploy to AWS.

Dashboard frontend (React + Vite)
----------------------------------
The UI lives in **frontend/**. It reads the deployed read API (GET /bins, /critical, etc.).

Requirements: Node.js 20+ recommended.

1. Install dependencies::

     cd frontend
     npm install

2. Configure the API base URL (no trailing slash). Copy the example env file::

     cp .env.example .env

   Edit **frontend/.env** and set::

     VITE_API_BASE_URL=https://YOUR_API_ID.execute-api.REGION.amazonaws.com

3. Run the dev server::

     npm run dev

   Open the printed local URL (usually http://127.0.0.1:5173).

4. Production build (optional, still local)::

     npm run build
     npm run preview

The dashboard **auto-refreshes** every few seconds (tab visible). Optional: set **VITE_POLL_INTERVAL_MS** in **frontend/.env** (minimum 2000, default 4000).

The sidebar includes **Clear all data** (calls the backend purge endpoint when configured). If you deploy with **AdminApiKey**, set **VITE_ADMIN_API_KEY** in **frontend/.env** to match.

Pointing the frontend at the deployed backend
---------------------------------------------
Set **VITE_API_BASE_URL** to the **HttpApiUrl** value from the SAM stack Outputs (same host you use for `/ingest`). The UI uses **GET** routes for the dashboard.

AWS Amplify Hosting (production UI)
-----------------------------------
Use **Amplify Hosting** to build and serve the dashboard from this repo (build spec: **amplify.yml** at the repo root).

1. In the **Amplify console** → *Host web app* → connect your Git provider and select this repository.
2. Amplify should detect **amplify.yml**. Build output is **frontend/dist** (Vite).
3. Under **App settings** → **Environment variables**, set at least:
   
     VITE_API_BASE_URL=https://YOUR_API_ID.execute-api.REGION.amazonaws.com
   
   (No trailing slash.) Optional: **VITE_POLL_INTERVAL_MS**, **VITE_ADMIN_API_KEY** (if you use the sidebar clear-data action with **AdminApiKey** on the API).
   
   Vite reads these at **build** time; redeploy the Amplify branch after changing them.
4. **Single-page app routes** (e.g. ``/bins/...``, ``/zones/...``): in Amplify → **Hosting** → **Rewrites and redirects** → add a rule so client-side routes work:
   
   - **Source address:** ``/<*>``
   - **Target address:** ``/index.html``
   - **Type:** **404 (Rewrite)** — or use Amplify’s “SPA redirect” preset if shown.
   
   Alternatively the common regex rewrite for SPAs (200 rewrite to ``index.html`` for non-file paths) is documented in `AWS Amplify` → *Support for single-page apps*.
5. **CORS:** API Gateway must allow your Amplify app origin (e.g. ``https://main.xxxxx.amplifyapp.com``) on **GET** (and **POST** if you call ingest/purge from the browser). Adjust the SAM/API **Access-Control-Allow-Origin** (or use a wildcard only if acceptable for your class demo).
6. **Node.js:** If the build fails on an old Node image, set **Node 20** in Amplify (e.g. *Build settings* → *Build image* / live updates, or add ``nvm install 20 && nvm use 20`` before ``npm ci`` in **amplify.yml**).

Where to change “data” / behaviour
----------------------------------
- **Sensor simulation (raw readings):** **sensors/simulator.py**, **shared/constants.py**
- **Fog thresholds & status (normal / warning / critical / fire_risk / probable_fire):** **fog/events.py**, **shared/constants.py** (e.g. FILL_WARNING_PCT, FILL_CRITICAL_PCT, FIRE_TEMP_THRESHOLD_C, PROBABLE_FIRE_TEMP_THRESHOLD_C)
- **Outbound JSON shape (CLI / fog):** **samples/fog_to_aws_message.json**
- **DynamoDB field names / persistence:** **backend/processor/app.py**
- **Full fog demo to AWS (script):** from repo root, **API_BASE_URL** set::

     chmod +x scripts/run_fog_demo.sh
     ./scripts/run_fog_demo.sh
     # (Shell script — use ./ or bash; do not run with python3.)

End-to-end verification (happy path)
------------------------------------
1. **Deploy the backend** — from `backend/`: `sam build` then `sam deploy` with your Lab role ARN (see backend/README.md).
2. **Post a sample payload** — `curl` POST to `/ingest` using `samples/fog_to_aws_message.json`, or `python backend/scripts/post_sample_ingest.py` with `API_BASE_URL` set.
3. **Run the fog demo** — from repo root with `PYTHONPATH` set, `python -m fog --demo --interval 3 --summary-interval 5 --post-url "https://.../ingest"` (optionally `--no-stdout`).
4. **Open the frontend locally** — `cd frontend && npm install && npm run dev`, with `VITE_API_BASE_URL` pointing at the same API host.
5. **Verify live data** — confirm **All bins** shows rows; open a bin for **history**; use **Critical** and **By zone** to match the API.
