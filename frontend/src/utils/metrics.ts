/**
 * API items may use `usage_rate` (current schema) or legacy `usage_count` (older rows).
 */
export function usageRate(
  row: { usage_rate?: unknown; usage_count?: unknown },
): number {
  const v = row.usage_rate ?? row.usage_count;
  const n = Number(v);
  return Number.isFinite(n) ? n : 0;
}
