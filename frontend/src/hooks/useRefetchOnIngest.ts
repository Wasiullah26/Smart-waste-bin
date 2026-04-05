import { useEffect } from "react";

const EVENT = "dashboard-refetch";

/** Call after actions that change cloud data (e.g. clear-all) so lists refresh sooner than the next poll. */
export function dispatchDashboardRefetch(): void {
  window.dispatchEvent(new CustomEvent(EVENT));
}

/**
 * Re-run `refetch` when something dispatches `dashboard-refetch` (e.g. after clearing data).
 */
export function useRefetchOnIngest(
  refetch: () => void | Promise<void>,
  deps: readonly unknown[],
): void {
  useEffect(() => {
    const handler = () => {
      void refetch();
    };
    window.addEventListener(EVENT, handler);
    return () => window.removeEventListener(EVENT, handler);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);
}
