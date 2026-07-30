import { useEffect, useRef, useState, type FormEvent } from "react";
import Markdown from "@/components/Markdown";
import { askAI, fetchChatHistory } from "@/services/aiService";
import type { ChatMessage } from "@/types";

const SUGGESTIONS = [
  "Why is CPU usage high right now?",
  "Show all critical errors in the last hour.",
  "Which alerts are currently active?",
  "Summarize the current system health.",
];

export default function AIChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [aiAvailable, setAiAvailable] = useState(true);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fetchChatHistory().then(setMessages).catch(() => {});
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function send(question: string) {
    if (!question.trim() || sending) return;
    setInput("");
    setSending(true);
    setMessages((prev) => [
      ...prev,
      { role: "user", message: question, created_at: new Date().toISOString() },
    ]);
    try {
      const result = await askAI(question);
      setAiAvailable(result.available);
      setMessages((prev) => [
        ...prev,
        { role: "assistant", message: result.answer, created_at: new Date().toISOString() },
      ]);
    } finally {
      setSending(false);
    }
  }

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    send(input);
  }

  return (
    <div className="flex flex-col h-[calc(100vh-8rem)]">
      <div>
        <p className="label-eyebrow">AI Agent</p>
        <h1 className="text-xl font-semibold text-ink-primary mt-1">AI Chat</h1>
        <p className="text-sm text-ink-secondary mt-1">
          Ask about current metrics, cluster state, Jenkins, active alerts, open incidents, and
          recent logs.
        </p>
      </div>

      {!aiAvailable && (
        <div className="panel p-3 mt-4 text-xs text-ink-muted">
          AI isn't configured yet — set <code className="font-mono text-accent">LLM_PROVIDER</code>{" "}
          and <code className="font-mono text-accent">LLM_API_KEY</code> in your environment
          (groq / openai / ollama) to get real answers instead of this fallback message.
        </div>
      )}

      <div className="panel flex-1 mt-4 flex flex-col overflow-hidden">
        <div className="flex-1 overflow-y-auto p-4 space-y-3">
          {messages.length === 0 && (
            <div className="h-full flex flex-col items-center justify-center gap-3 text-center">
              <p className="text-sm text-ink-muted">Try asking:</p>
              <div className="flex flex-col gap-2">
                {SUGGESTIONS.map((s) => (
                  <button
                    key={s}
                    onClick={() => send(s)}
                    className="btn-ghost text-xs py-1.5 px-3"
                  >
                    {s}
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map((m, i) => (
            <div key={i} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
              <div
                className={`max-w-[75%] rounded-lg px-3 py-2 ${
                  m.role === "user"
                    ? "bg-accent text-base-950 font-medium text-sm"
                    : "bg-base-800 text-ink-primary border border-base-600"
                }`}
              >
                {m.role === "assistant" ? <Markdown>{m.message}</Markdown> : m.message}
              </div>
            </div>
          ))}
          {sending && (
            <div className="flex justify-start">
              <div className="rounded-lg px-3 py-2 text-sm bg-base-800 border border-base-600 text-ink-muted">
                Thinking…
              </div>
            </div>
          )}
          <div ref={bottomRef} />
        </div>

        <form onSubmit={handleSubmit} className="border-t border-base-700 p-3 flex gap-2">
          <input
            className="input-field flex-1"
            placeholder="Ask about your systems…"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={sending}
          />
          <button type="submit" className="btn-primary text-sm" disabled={sending || !input.trim()}>
            Send
          </button>
        </form>
      </div>
    </div>
  );
}
