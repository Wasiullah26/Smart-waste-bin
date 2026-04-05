/** Fill and temperature bands used for on-screen hints (aligned with backend thresholds). */
export const FILL_WARNING_PCT = 80;
export const FILL_CRITICAL_PCT = 95;
export const FIRE_TEMP_THRESHOLD_C = 45;
export const PROBABLE_FIRE_TEMP_THRESHOLD_C = 60;

export type SignalTone = "ok" | "warn" | "crit" | "fire" | "warm" | "severe";

export function fillSignal(fill: number): { label: string; tone: SignalTone } {
  const f = Number(fill);
  if (f >= FILL_CRITICAL_PCT) return { label: "Near full", tone: "crit" };
  if (f >= FILL_WARNING_PCT) return { label: "High fill", tone: "warn" };
  return { label: "Fill OK", tone: "ok" };
}

export function tempSignal(tempC: number): { label: string; tone: SignalTone } {
  const t = Number(tempC);
  if (t >= PROBABLE_FIRE_TEMP_THRESHOLD_C) return { label: "Probable fire", tone: "severe" };
  if (t >= FIRE_TEMP_THRESHOLD_C) return { label: "Elevated heat", tone: "fire" };
  if (t >= 35) return { label: "Warm", tone: "warm" };
  return { label: "Temp OK", tone: "ok" };
}

export const PRIORITY_HELP =
  "Score from 0–100 combining fill, usage, and temperature to suggest which bins to handle first.";
