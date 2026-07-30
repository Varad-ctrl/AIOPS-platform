import { useState } from "react";
import { usePolling } from "@/hooks/usePolling";
import { downloadLogsAsText, fetchRecentLogs, searchLogs } from "@/services/logsService";
import { analyzeLogs } from "@/services/aiService";
import type { LogAnalysisResult } from "@/types";

export default function Logs() {
  const [query, setQuery] = useState("");
  const [namespace, setNamespace] = useState("");
  const [pod, setPod] = useState("");
  const [severity, setSeverity] = useState("");
  const [hours, setHours] = useState(1);
  const [live, setLive] = useState(true);
  const [activeSearch, setActiveSearch] = useState<null | {
    query?: string;
    namespace?: string;
    pod?: string;
    severity?: string;
    hours: number;
  }>(null);

  const [analysis, setAnalysis] = useState<LogAnalysisResult | null>(null);
  const [aiLoading, setAiLoading] = useState(false);

  const pollInterval = live ? 10000 : 3600000;

  const { data: recent } = usePolling(
    () => fetchRecentLogs(hours, 100),
    activeSearch ? 3600000 : pollInterval,
    [hours, activeSearch === null]
  );
  const { data: searchResults, isLoading: searching } = usePolling(
    () =>
      activeSearch
        ? searchLogs({ ...activeSearch, limit: 200 })
        : Promise.resolve({ available: true, count: 0, items: [] }),
    activeSearch ? pollInterval : 3600000,
    [JSON.stringify(activeSearch), live]
  );

  const results = activeSearch ? searchResults : recent;

  function runSearch() {
    setActiveSearch({
      query: query || undefined,
      namespace: namespace || undefined,
      pod: pod || undefined,
      severity: severity || undefined,
      hours,
    });
  }

  function clearSearch() {
    setQuery("");
    setNamespace("");
    setPod("");
    setSeverity("");
    setActiveSearch(null);
  }

  async function runAnalysis() {
    setAiLoading(true);
    setAnalysis(null);
    try {
      const result = await analyzeLogs(namespace || undefined, pod || undefined, hours);
      setAnalysis(result);
    } finally {
      setAiLoading(false);
    }
  }

  function handleDownload() {
    if (!results) return;
    const filename = activeSearch
      ? `logs-search-${new Date().toISOString().slice(0, 19)}.txt`
      : `logs-recent-${new Date().toISOString().slice(0, 19)}.txt`;
    downloadLogsAsText(results.items, filename);
  }

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="label-eyebrow">Log Intelligence</p>
          <h1 className="text-xl font-semibold text-ink-primary mt-1">Logs</h1>
          <p className="text-sm text-ink-secondary mt-1">
            Search across every container Promtail is shipping to Loki, or ask the AI to analyze
            what it sees.
          </p>
        </div>
        <label className="flex items-center gap-2 text-xs text-ink-secondary shrink-0 pt-1">
          <input type="checkbox" checked={live} onChange={(e) => setLive(e.target.checked)} />
          Live (10s refresh)
        </label>
      </div>

      <div className="panel p-4 space-y-3">
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
          <input
            className="input-field col-span-2 sm:col-span-1"
            placeholder="Search text…"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
          <input
            className="input-field"
            placeholder="Namespace"
            value={namespace}
            onChange={(e) => setNamespace(e.target.value)}
          />
          <input
            className="input-field"
            placeholder="Pod / container"
            value={pod}
            onChange={(e) => setPod(e.target.value)}
          />
          <select className="input-field" value={severity} onChange={(e) => setSeverity(e.target.value)}>
            <option value="">Any severity</option>
            <option value="error">Error</option>
            <option value="warn">Warning</option>
            <option value="info">Info</option>
            <option value="debug">Debug</option>
          </select>
          <select
            className="input-field"
            value={hours}
            onChange={(e) => setHours(Number(e.target.value))}
          >
            <option value={1}>Last 1h</option>
            <option value={6}>Last 6h</option>
            <option value={24}>Last 24h</option>
            <option value={168}>Last 7d</option>
          </select>
        </div>
        <div className="flex gap-2 flex-wrap">
          <button onClick={runSearch} className="btn-primary text-xs py-1.5">
            Search
          </button>
          <button onClick={clearSearch} className="btn-ghost text-xs py-1.5">
            Clear (show recent)
          </button>
          <button onClick={handleDownload} className="btn-ghost text-xs py-1.5" disabled={!results?.items.length}>
            Download .txt
          </button>
          <div className="flex-1" />
          <button onClick={runAnalysis} disabled={aiLoading} className="btn-ghost text-xs py-1.5">
            {aiLoading ? "Analyzing…" : "AI: Analyze logs"}
          </button>
        </div>
      </div>

      {analysis && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <div className="panel p-4">
            <p className="label-eyebrow mb-2">
              AI summary {analysis.available ? `(${analysis.log_count} lines)` : ""}
            </p>
            <p className="text-sm text-ink-secondary whitespace-pre-wrap">{analysis.summary}</p>
          </div>
          <div className="panel p-4">
            <p className="label-eyebrow mb-2">AI anomaly findings</p>
            <p className="text-sm text-ink-secondary whitespace-pre-wrap">{analysis.findings}</p>
          </div>
        </div>
      )}

      <div className="panel">
        <div className="px-4 py-3 border-b border-base-700 flex items-center justify-between">
          <p className="label-eyebrow">
            {activeSearch ? "Search results" : "Recent logs"}
            {results && ` · ${results.count} lines`}
            {live && !activeSearch && (
              <span className="ml-2 text-signal-ok normal-case">● live</span>
            )}
          </p>
          {results && !results.available && (
            <span className="text-xs text-ink-muted">Loki not connected</span>
          )}
        </div>
        <div className="max-h-[480px] overflow-y-auto font-mono text-xs">
          {(results?.items ?? []).map((entry, i) => (
            <div
              key={i}
              className="px-4 py-2 border-b border-base-700 last:border-0 flex gap-3 hover:bg-base-800/50"
            >
              <span className="text-ink-muted whitespace-nowrap">
                {new Date(entry.timestamp).toLocaleTimeString()}
              </span>
              <span className="text-accent whitespace-nowrap">
                {entry.labels.container || entry.labels.service || entry.labels.pod || "—"}
              </span>
              <span className="text-ink-secondary break-all">{entry.message}</span>
            </div>
          ))}
          {!searching && (results?.items ?? []).length === 0 && (
            <div className="p-8 text-center text-sm text-ink-muted">
              {results?.available === false
                ? "Connect Loki + Promtail (see docker-compose.yml) to see logs here."
                : "No log lines found for this window."}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
