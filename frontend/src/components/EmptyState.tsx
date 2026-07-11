interface EmptyStateProps {
  eyebrow: string;
  title: string;
  description: string;
  phase: string;
}

export default function EmptyState({ eyebrow, title, description, phase }: EmptyStateProps) {
  return (
    <div className="panel flex flex-col items-center justify-center text-center py-20 px-6">
      <p className="label-eyebrow">{eyebrow}</p>
      <h2 className="text-lg font-semibold text-ink-primary mt-2">{title}</h2>
      <p className="text-sm text-ink-secondary mt-2 max-w-md">{description}</p>
      <span className="mt-4 text-xs font-mono uppercase tracking-wide text-accent border border-base-600 rounded px-2 py-1">
        Ships in {phase}
      </span>
    </div>
  );
}
