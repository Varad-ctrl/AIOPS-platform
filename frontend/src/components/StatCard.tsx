interface StatCardProps {
  label: string;
  value: string;
  tone?: "ok" | "warn" | "crit" | "info";
  hint?: string;
}

const TONE_CLASSES: Record<NonNullable<StatCardProps["tone"]>, string> = {
  ok: "text-signal-ok",
  warn: "text-signal-warn",
  crit: "text-signal-crit",
  info: "text-signal-info",
};

export default function StatCard({ label, value, tone = "info", hint }: StatCardProps) {
  return (
    <div className="panel p-4">
      <p className="label-eyebrow">{label}</p>
      <p className={`font-display text-2xl font-semibold mt-2 ${TONE_CLASSES[tone]}`}>{value}</p>
      {hint && <p className="text-xs text-ink-muted mt-1">{hint}</p>}
    </div>
  );
}
