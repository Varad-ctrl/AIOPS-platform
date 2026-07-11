import EmptyState from "@/components/EmptyState";

export default function AIChat() {
  return (
    <EmptyState
      eyebrow="AI Agent"
      title="Natural language DevOps assistant"
      description="Ask things like “Why is CPU 95%?” or “Which pod restarted most today?” The agent will query Prometheus, Kubernetes, Jenkins, Loki, and Postgres to answer."
      phase="Phase 4"
    />
  );
}
