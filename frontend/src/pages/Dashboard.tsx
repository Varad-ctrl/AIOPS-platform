import { useAuth } from "@/contexts/AuthContext";
import StatCard from "@/components/StatCard";

export default function Dashboard() {
  const { user } = useAuth();

  return (
    <div className="space-y-6">
      <div>
        <p className="label-eyebrow">Overview</p>
        <h1 className="text-xl font-semibold text-ink-primary mt-1">
          Welcome back, {user?.full_name || user?.email}
        </h1>
        <p className="text-sm text-ink-secondary mt-1">
          This foundation is live. Metrics, incidents, and AI analysis populate here starting in
          Phase 2.
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard label="Open incidents" value="0" tone="ok" hint="Phase 5 will populate this" />
        <StatCard label="Active alerts" value="0" tone="ok" hint="Phase 5 will populate this" />
        <StatCard label="Monitored nodes" value="—" tone="info" hint="Phase 2 will populate this" />
        <StatCard label="Your role" value={user?.role ?? "—"} tone="info" />
      </div>

      <div className="panel p-6">
        <p className="label-eyebrow mb-3">Roadmap status</p>
        <ul className="space-y-2 text-sm">
          <RoadmapRow label="Phase 1 — Project Foundation" status="done" />
          <RoadmapRow label="Phase 2 — Observability Layer" status="pending" />
          <RoadmapRow label="Phase 3 — Log Intelligence" status="pending" />
          <RoadmapRow label="Phase 4 — AI Agent" status="pending" />
          <RoadmapRow label="Phase 5 — Incident Detection Engine" status="pending" />
          <RoadmapRow label="Phase 6 — AI Root Cause Analysis" status="pending" />
          <RoadmapRow label="Phase 7 — Notification & Alerting" status="pending" />
        </ul>
      </div>
    </div>
  );
}

function RoadmapRow({ label, status }: { label: string; status: "done" | "pending" }) {
  return (
    <li className="flex items-center justify-between border-b border-base-700 last:border-0 py-2">
      <span className="text-ink-secondary">{label}</span>
      <span
        className={`text-xs font-mono uppercase tracking-wide ${
          status === "done" ? "text-signal-ok" : "text-ink-muted"
        }`}
      >
        {status === "done" ? "complete" : "not started"}
      </span>
    </li>
  );
}
