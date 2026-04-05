import type { BinEvent, BinLatest } from "../types";

function baseUrl(): string {
  const raw = import.meta.env.VITE_API_BASE_URL ?? "";
  return raw.replace(/\/+$/, "");
}

async function getJson<T>(path: string): Promise<T> {
  const b = baseUrl();
  if (!b) {
    throw new Error(
      "VITE_API_BASE_URL is not set. Create frontend/.env with VITE_API_BASE_URL=https://your-api.execute-api.region.amazonaws.com",
    );
  }
  const res = await fetch(`${b}${path}`);
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`${res.status} ${res.statusText}: ${text.slice(0, 200)}`);
  }
  return res.json() as Promise<T>;
}

export async function fetchAllBins(): Promise<BinLatest[]> {
  const data = await getJson<{ bins: BinLatest[] }>("/bins");
  return data.bins;
}

export async function fetchBin(binId: string): Promise<BinLatest> {
  return getJson<BinLatest>(`/bins/${encodeURIComponent(binId)}`);
}

export async function fetchZoneBins(zone: string): Promise<BinLatest[]> {
  const data = await getJson<{ bins: BinLatest[] }>(
    `/zones/${encodeURIComponent(zone)}/bins`,
  );
  return data.bins;
}

export async function fetchCritical(): Promise<BinLatest[]> {
  const data = await getJson<{ critical: BinLatest[] }>("/critical");
  return data.critical;
}

export async function fetchHistory(
  binId: string,
  limit = 50,
): Promise<{ events: BinEvent[]; count: number }> {
  return getJson<{ events: BinEvent[]; count: number }>(
    `/history/${encodeURIComponent(binId)}?limit=${limit}`,
  );
}

export function getConfiguredApiBase(): string {
  return baseUrl();
}

/** Clear stored bin data (backend must expose the matching endpoint). */
export async function postAdminPurge(): Promise<{
  purged?: boolean;
  deleted_events?: number;
  deleted_latest?: number;
  sqs_purged?: boolean;
}> {
  const b = baseUrl();
  if (!b) {
    throw new Error("VITE_API_BASE_URL is not set.");
  }
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  const key = import.meta.env.VITE_ADMIN_API_KEY;
  if (typeof key === "string" && key.length > 0) {
    headers["X-Admin-Key"] = key;
  }
  const res = await fetch(`${b}/admin/purge`, {
    method: "POST",
    headers,
    body: "{}",
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`${res.status} ${res.statusText}: ${text.slice(0, 400)}`);
  }
  return res.json() as Promise<{
    purged?: boolean;
    deleted_events?: number;
    deleted_latest?: number;
    sqs_purged?: boolean;
  }>;
}

/** Optional: submit a device payload (requires API URL in env). */
export async function postIngest(
  body: unknown,
): Promise<{ accepted?: boolean; message_id?: string; records?: number }> {
  const b = baseUrl();
  if (!b) {
    throw new Error("VITE_API_BASE_URL is not set.");
  }
  const res = await fetch(`${b}/ingest`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`${res.status} ${res.statusText}: ${text.slice(0, 200)}`);
  }
  return res.json() as Promise<{
    accepted?: boolean;
    message_id?: string;
    records?: number;
  }>;
}
