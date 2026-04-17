# AWS backend (SAM) — Smart waste bin

This stack implements:

- **API Gateway (HTTP API)** — `POST /ingest` (fog → SQS), read routes for the dashboard
- **SQS** — decouples ingestion from persistence
- **Lambda** — ingestion (enqueue) + processor (DynamoDB) + read API + optional admin purge + **IoTFogFunction** (MQTT fog → same SQS queue)
- **DynamoDB** — `waste-bin-events-v2` (history), `waste-bin-latest` (current state per bin), **`FogStateTable`** (serialized fog state for MQTT Lambda)

**Deployment model:** build and deploy **manually** from your laptop while **AWS Learner Lab** credentials are valid. GitHub Actions only validates/tests — it does **not** deploy (temporary keys rotate ~every 4 hours).

## Prerequisites

- [AWS SAM CLI](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html)
- [AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html)
- Python 3.12 (matches `template.yaml` `Runtime`)

## Learner Lab: Lambda execution role (required)

Student accounts **cannot create new IAM roles** (`iam:CreateRole` is denied). The template therefore **does not** auto-create Lambda execution roles. You must pass an **existing role ARN** (almost always **`LabRole`** in AWS Academy / Vocareum).

1. In the AWS console: **IAM → Roles**, search **`Lab`** or **`LabRole`**.
2. Open the role your lab documentation names (often **`LabRole`**) and copy its **ARN**, e.g.  
   `arn:aws:iam::478098186215:role/LabRole` (your account ID will match `aws sts get-caller-identity`).

Or from the CLI:

```bash
aws iam list-roles --query "Roles[?contains(RoleName, 'Lab')].[RoleName,Arn]" --output table
```

Deploy with that ARN (see below). **`LabRole`** is usually broad enough for SQS, DynamoDB, and CloudWatch Logs. If something still fails with “access denied” on a specific service, check with your instructor.

### If a previous deploy failed (`ROLLBACK_COMPLETE`)

Delete the failed stack, then deploy again:

```bash
aws cloudformation delete-stack --stack-name smart-waste-bin
aws cloudformation wait stack-delete-complete --stack-name smart-waste-bin
```

### Upgrading from an older stack (events sort key / GSI)

If you deployed **before** the `event_sk` (string) sort key and **ZoneBinIndex** GSI:

- CloudFormation may **replace** the `waste-bin-events` table when the key schema changes.
- Prefer **deleting the stack** (and retained tables if any) then redeploying, or create a new stack name so you start clean.

## Learner Lab credentials (temporary session)

When the lab session is active, export the **Access Key ID**, **Secret Access Key**, and **Session Token** from the lab panel (values change when the session refreshes):

```bash
export AWS_ACCESS_KEY_ID="AKIA..."
export AWS_SECRET_ACCESS_KEY="..."
export AWS_SESSION_TOKEN="..."
export AWS_DEFAULT_REGION="eu-west-1"   # use your lab region
```

Verify:

```bash
aws sts get-caller-identity
```

## Build and deploy (local)

From this `backend/` directory:

```bash
sam validate --lint
sam build
```

Deploy **with your Lab role ARN** (replace with your real ARN):

```bash
sam deploy --guided --parameter-overrides LambdaExecutionRoleArn=arn:aws:iam::YOUR_ACCOUNT_ID:role/LabRole
```

Or non-guided after the first successful deploy:

```bash
sam deploy --parameter-overrides LambdaExecutionRoleArn=arn:aws:iam::YOUR_ACCOUNT_ID:role/LabRole
```

You can store `parameter_overrides` in `samconfig.toml` under `[default.deploy.parameters]` (see `samconfig.toml.example`). This repo **gitignores** `samconfig.toml`.

Suggested first-time answers for `--guided`:

- **Stack name:** e.g. `smart-waste-bin`
- **Region:** your Learner Lab region (e.g. `us-east-1`)
- **Parameter `LambdaExecutionRoleArn`:** paste the **LabRole** ARN
- **Confirm changes:** Yes
- **Allow SAM IAM role creation:** can be **No** now (Lambdas use `LabRole`; CloudFormation still needs **CAPABILITY_IAM** for Lambda permission resources — say **Yes** if SAM asks for capabilities)
- **Disable rollback:** No
- **Save parameters:** Yes (optional; updates `samconfig.toml`)

After deploy, note the **Outputs**:

- `HttpApiUrl` — base URL, e.g. `https://abc123.execute-api.eu-west-1.amazonaws.com`

### Ingestion URL for fog

Append the stage path. For `$default` HTTP API stage, paths are typically:

```text
${HttpApiUrl}/ingest
```

Example:

```text
https://xxxxxxxx.execute-api.eu-west-1.amazonaws.com/ingest
```

### Read API (dashboard)

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/bins` | All latest bin states |
| GET | `/bins/{bin_id}` | One bin |
| GET | `/zones/{zone}/bins` | Bins in a zone (queries **ZoneBinIndex** GSI) |
| GET | `/critical` | Latest rows with `critical`, `fire_risk`, or `probable_fire` (scan + filter) |
| GET | `/history/{bin_id}?limit=50` | Recent events for a bin |

### Admin (lab reset)

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/admin/purge` | Purge ingestion **SQS** queue, then delete **all** items in `waste-bin-events-v2` and `waste-bin-latest` |

**Optional security:** template parameter **`AdminApiKey`** — if non-empty at deploy time, clients must send header **`X-Admin-Key: <same value>`**. The Vite dashboard can use **`VITE_ADMIN_API_KEY`** in `frontend/.env` to match.

**SQS:** `PurgeQueue` is limited to **once per 60 seconds** per queue; if purge fails, wait and retry.

**Frontend:** use the sidebar **Clear all data** button (or call **`POST /admin/purge`** with the same headers as the app).

## Example `curl` commands

Set `API` to your `HttpApiUrl` (no trailing slash):

```bash
export API="https://YOUR_API_ID.execute-api.REGION.amazonaws.com"
```

**POST /ingest** — minimal valid body (matches `samples/fog_to_aws_message.json`):

```bash
curl -sS -X POST "$API/ingest" \
  -H "Content-Type: application/json" \
  -d @../samples/fog_to_aws_message.json
```

**GET /bins**

```bash
curl -sS "$API/bins"
```

**GET /bins/{bin_id}**

```bash
curl -sS "$API/bins/BIN-zone-A-01"
```

**GET /zones/{zone}/bins**

```bash
curl -sS "$API/zones/zone-A/bins"
```

**GET /critical**

```bash
curl -sS "$API/critical"
```

**GET /history/{bin_id}**

```bash
curl -sS "$API/history/BIN-zone-A-01?limit=20"
```

**POST /admin/purge** (wipe tables + queue; add `-H "X-Admin-Key: YOUR_KEY"` if you set `AdminApiKey` on deploy)

```bash
curl -sS -X POST "$API/admin/purge" -H "Content-Type: application/json" -d "{}"
```

## Verification checklist

After deploy, work through this list:

- [ ] `sam validate --lint` and `sam build` succeed locally.
- [ ] Stack **Outputs** show `HttpApiUrl`.
- [ ] `POST /ingest` with `samples/fog_to_aws_message.json` returns **202** and `accepted: true`.
- [ ] Wait a few seconds, then `GET /bins` shows at least one bin with expected fields (`usage_rate`, `zone`, `status`).
- [ ] `GET /zones/zone-A/bins` returns bins for that zone only.
- [ ] `GET /history/BIN-zone-A-01` returns events with `event_sk` (not `event_ts`).
- [ ] Optional: run `python scripts/post_sample_ingest.py` (set `API_BASE_URL` or pass URL as argv).

## Optional: Python sample POST

From `backend/`:

```bash
export API_BASE_URL="https://YOUR_API_ID.execute-api.REGION.amazonaws.com"
python scripts/post_sample_ingest.py
```

## Plug the URL into fog

From the **repository root** (so `shared` / `fog` resolve):

```bash
export PYTHONPATH="/path/to/Fog&Edge"
python -m fog --demo --interval 3 --summary-interval 5 \
  --post-url "https://YOUR_API_ID.execute-api.REGION.amazonaws.com/ingest"
```

- `--no-stdout` — only POST (no NDJSON on stdout)
- `--post-timeout` / `--post-retries` — tune resilience

## MQTT (AWS IoT Core) — edge laptop → fog in AWS

Deploy the stack so **`IoTFogFunction`** and **`FogStateTable`** exist. Stack **Outputs** include **`IoTFogFunctionArn`**.

1. **IoT Core → Rule** (console): SQL **`SELECT * FROM 'waste/edge/readings'`** (topic must match what the edge publishes). Action: **Lambda** → select **IoTFogFunction**. The console adds **Invoke permission** from IoT to Lambda.
2. **Thing + certificates**: Create a Thing, download the device cert, private key, and [Amazon Root CA 1](https://www.amazontrust.com/repository/AmazonRootCA1.pem). Attach an **IoT policy** that allows `iot:Connect`, `iot:Publish`, and (if needed) `iot:Subscribe` on the ARNs for your account/region.
3. **Edge (laptop)** from repo root (`PYTHONPATH` set as usual):

```bash
pip install -r requirements.txt   # includes paho-mqtt for the edge script
export PYTHONPATH="/path/to/Fog&Edge"
python scripts/edge_mqtt_publish.py \
  --endpoint YOUR_ENDPOINT-ats.iot.REGION.amazonaws.com \
  --ca AmazonRootCA1.pem --cert device.pem.crt --key private.pem.key \
  --topic waste/edge/readings --interval 2
```

Each MQTT payload is one **`BinReading`** JSON object (same fields as the NDJSON lines from `python -m sensors`). **IoTFogFunction** runs the same fog logic as `python -m fog`, stores state in **FogStateTable**, and enqueues **`FogOutboundMessage`** JSON to the **same SQS queue** as `POST /ingest`, so the rest of the pipeline is unchanged.

**Learner Lab:** If you cannot create **IoT Rules** or **IAM** roles from CloudFormation, use the console steps above after deploy. Ensure **LabRole** allows **DynamoDB** read/write on **FogStateTable** and **SQS** `SendMessage` on the ingestion queue (it usually does).

**Repo layout:** `backend/iot_fog/fog` and `backend/iot_fog/shared` are **symlinks** to the top-level packages so `sam build` bundles them into **IoTFogFunction** without duplicating code.

## Data mapping (DynamoDB)

- **waste-bin-events-v2** — one item per **record** in each fog message; sort key **`event_sk`** is a unique string (`nanoseconds#idx#message_type#uuid`) so rows never collide for the same `bin_id`. (Physical name **`waste-bin-events-v2`** avoids CloudFormation replace issues when upgrading from older `event_ts` tables.)
- **waste-bin-latest** — one item per `bin_id`; overwritten on each message. **GSI `ZoneBinIndex`** — partition key `zone`, sort key `bin_id` — powers `GET /zones/{zone}/bins` without scanning the whole table.
- **`usage_rate`** attribute stores the fog **normalized usage rate** (0–100) from each record’s `usage_rate` field.

## Troubleshooting

- **`POST .../admin/purge` returns 404 from API Gateway** (small JSON body like `Not Found`): the deployed HTTP API does not include the admin route yet. From `backend/`, run **`sam build`** then **`sam deploy`** with the current `template.yaml` so **AdminFunction** and the **`POST /admin/purge`** route are created. Confirm in **API Gateway → APIs → Routes** that `/admin/purge` exists, or check the CloudFormation stack for **AdminFunction**.
- **`sam deploy` fails on IAM:** Learner Lab roles sometimes restrict IAM; use the smallest permissions SAM suggests or create roles in the lab console if allowed.
- **Table already exists:** Events table is **`waste-bin-events-v2`**; latest is **`waste-bin-latest`**. Orphan **`waste-bin-events`** (old schema) can be deleted manually in DynamoDB after a successful migrate deploy.
- **403 on POST:** Ensure you are using **HTTPS** and the correct `/ingest` path.

## CI vs deploy

- **GitHub Actions** runs `pytest`, `sam validate --lint`, and `sam build` only.
- **Never** store long-lived AWS keys in GitHub for this project; Learner Lab keys are short-lived by design.
