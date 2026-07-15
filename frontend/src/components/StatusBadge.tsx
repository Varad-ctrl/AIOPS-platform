interface StatusBadgeProps {
  status: string;
}

const STATUS_TONE: Record<string, string> = {
  Running: "text-signal-ok border-signal-ok/40 bg-signal-ok/10",
  Healthy: "text-signal-ok border-signal-ok/40 bg-signal-ok/10",
  SUCCESS: "text-signal-ok border-signal-ok/40 bg-signal-ok/10",
  Ready: "text-signal-ok border-signal-ok/40 bg-signal-ok/10",
  Pending: "text-signal-warn border-signal-warn/40 bg-signal-warn/10",
  UNSTABLE: "text-signal-warn border-signal-warn/40 bg-signal-warn/10",
  Degraded: "text-signal-warn border-signal-warn/40 bg-signal-warn/10",
  Failed: "text-signal-crit border-signal-crit/40 bg-signal-crit/10",
  FAILURE: "text-signal-crit border-signal-crit/40 bg-signal-crit/10",
  NotReady: "text-signal-crit border-signal-crit/40 bg-signal-crit/10",
  CrashLoopBackOff: "text-signal-crit border-signal-crit/40 bg-signal-crit/10",
  Disconnected: "text-ink-muted border-base-600 bg-base-800",
  Unknown: "text-ink-muted border-base-600 bg-base-800",
};

export default function StatusBadge({ status }: StatusBadgeProps) {
  const classes = STATUS_TONE[status] || "text-ink-secondary border-base-600 bg-base-800";
  return (
    <span
      className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-mono ${classes}`}
    >
      {status}
    </span>
  );
}
