import { useEffect, useState } from "react";

interface PollResult<T> {
  data: T | null;
  error: Error | null;
  isLoading: boolean;
}

/**
 * Polls an async fetcher on an interval. Used across the monitoring pages
 * so widgets stay live without pulling in a heavier data-fetching library
 * for what is, here, just "refetch every N seconds".
 *
 * `deps` lets callers whose fetcher closes over changing state (e.g. search
 * filters) force an immediate refetch when that state changes - without it,
 * the effect only re-runs when `intervalMs` changes, so a fetcher built from
 * new params would sit unused until the component unmounts/remounts.
 */
export function usePolling<T>(
  fetcher: () => Promise<T>,
  intervalMs = 15000,
  deps: unknown[] = []
): PollResult<T> {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<Error | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;

    async function run() {
      try {
        console.log("Calling fetcher...");

        const result = await fetcher();

        console.log("Fetcher returned:", result);

        if (!cancelled) {
          setData(result);
          setError(null);
        }
      } catch (err) {
        console.error("Polling Error:", err);

        if (!cancelled) {
          setError(err as Error);
        }
      } finally {
        if (!cancelled) {
          setIsLoading(false);
        }
      }
    }

    run();
    const id = setInterval(run, intervalMs);
    return () => {
      cancelled = true;
      clearInterval(id);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [intervalMs, ...deps]);

  return { data, error, isLoading };
}
