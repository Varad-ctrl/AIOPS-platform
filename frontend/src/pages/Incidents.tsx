import EmptyState from "@/components/EmptyState";

export default function Incidents() {
  return (
    <EmptyState
      eyebrow="Incident management"
      title="Automatic incident timeline"
      description="Detected incidents - CrashLoopBackOff, OOMKilled, node failures, and build failures - will appear here with AI-generated root cause analysis."
      phase="Phase 5 & 6"
    />
  );
}
