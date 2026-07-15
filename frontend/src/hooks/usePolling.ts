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
 */
export function usePolling<T>(fetcher: () => Promise<T>, intervalMs = 15000): PollResult<T> {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<Error | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;

    async function run() {
      try {
        const result = await fetcher();
        if (!cancelled) {
          setData(result);
          setError(null);
        }
      } catch (err) {
        if (!cancelled) setError(err as Error);
      } finally {
        if (!cancelled) setIsLoading(false);
      }
    }

    run();
    const id = setInterval(run, intervalMs);
    return () => {
      cancelled = true;
      clearInterval(id);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [intervalMs]);

  return { data, error, isLoading };
}
