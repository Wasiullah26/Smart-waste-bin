import { useCallback, useEffect, useState } from "react";
import { useRefetchOnIngest } from "./useRefetchOnIngest";
import { useRefreshOnInterval } from "./useRefreshOnInterval";

/**
 * Load once (with spinner), then poll; also refetches when the app dispatches a refresh signal.
 */
export function useFetchedData<T>(
  cacheKey: string,
  fetcher: () => Promise<T>,
): {
  data: T | null;
  error: string | null;
  loading: boolean;
  lastUpdated: Date | null;
} {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  const load = useCallback(
    async (initial: boolean) => {
      if (initial) setLoading(true);
      try {
        const result = await fetcher();
        setData(result);
        setError(null);
        setLastUpdated(new Date());
      } catch (e: unknown) {
        setError(e instanceof Error ? e.message : String(e));
        if (initial) setData(null);
      } finally {
        setLoading(false);
      }
    },
    [fetcher],
  );

  useEffect(() => {
    void load(true);
  }, [cacheKey, load]);

  useRefreshOnInterval(() => {
    void load(false);
  }, [cacheKey, load]);

  useRefetchOnIngest(() => {
    void load(false);
  }, [load]);

  return { data, error, loading, lastUpdated };
}
