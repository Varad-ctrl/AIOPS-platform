interface GaugeProps {
  label: string;
  value: number | null;
  unit?: string;
  available?: boolean;
}

function toneFor(value: number | null): "ok" | "warn" | "crit" | "muted" {
  if (value === null) return "muted";
  if (value >= 90) return "crit";
  if (value >= 75) return "warn";
  return "ok";
}

const TONE_STROKE: Record<string, string> = {
  ok: "#3FB68B",
  warn: "#E0A526",
  crit: "#E2574C",
  muted: "#5B6778",
};

export default function Gauge({ label, value, unit = "%", available = true }: GaugeProps) {
  const pct = Math.max(0, Math.min(100, value ?? 0));
  const tone = available ? toneFor(value) : "muted";
  const radius = 46;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (pct / 100) * circumference;

  return (
    <div className="panel p-4 flex flex-col items-center">
      <p className="label-eyebrow self-start mb-2">{label}</p>
      <svg width="120" height="120" viewBox="0 0 120 120">
        <circle
          cx="60"
          cy="60"
          r={radius}
          fill="none"
          stroke="#1F2733"
          strokeWidth="10"
        />
        <circle
          cx="60"
          cy="60"
          r={radius}
          fill="none"
          stroke={TONE_STROKE[tone]}
          strokeWidth="10"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={available ? offset : circumference}
          transform="rotate(-90 60 60)"
          className="transition-all duration-700 ease-out"
        />
        <text
          x="60"
          y="56"
          textAnchor="middle"
          className="fill-ink-primary font-display font-semibold"
          fontSize="20"
        >
          {available && value !== null ? Math.round(value) : "—"}
        </text>
        <text x="60" y="74" textAnchor="middle" className="fill-ink-muted" fontSize="11">
          {available ? unit : "no data"}
        </text>
      </svg>
    </div>
  );
}
