import { useEffect, useRef } from "react";

/** Min 2s; default 4s. Set `VITE_POLL_INTERVAL_MS` in `.env`. */
export function getPollIntervalMs(): number {
  const n = Number(import.meta.env.VITE_POLL_INTERVAL_MS);
  return Number.isFinite(n) && n >= 2000 ? n : 4000;
}

/** Re-runs `effect` on an interval while the browser tab is visible. */
export function useRefreshOnInterval(
  effect: () => void | Promise<void>,
  deps: readonly unknown[],
): void {
  const ref = useRef(effect);
  ref.current = effect;

  useEffect(() => {
    const ms = getPollIntervalMs();
    const id = setInterval(() => {
      if (document.visibilityState === "visible") {
        void ref.current();
      }
    }, ms);
    return () => clearInterval(id);
    // eslint-disable-next-line react-hooks/exhaustive-deps -- caller controls deps
  }, deps);
}
