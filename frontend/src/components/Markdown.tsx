import ReactMarkdown from "react-markdown";

interface MarkdownProps {
  children: string;
}

/**
 * Renders AI responses as markdown - headings, lists, and (importantly for
 * an SRE assistant) fenced code blocks for kubectl commands, log snippets,
 * etc. Kept intentionally minimal: no syntax highlighting library, just
 * monospace + a distinct background so commands are easy to copy visually.
 */
export default function Markdown({ children }: MarkdownProps) {
  return (
    <div className="text-sm leading-relaxed space-y-2 [&_p]:my-1 [&_ul]:list-disc [&_ul]:pl-5 [&_ol]:list-decimal [&_ol]:pl-5 [&_li]:my-0.5 [&_strong]:text-ink-primary [&_strong]:font-semibold [&_a]:text-accent [&_a]:underline [&_h1]:text-base [&_h1]:font-semibold [&_h2]:text-base [&_h2]:font-semibold [&_h3]:text-sm [&_h3]:font-semibold">
      <ReactMarkdown
        components={{
          code: ({ className, children, ...props }) => {
            const isBlock = className?.includes("language-");
            if (isBlock) {
              return (
                <pre className="bg-base-950 border border-base-600 rounded px-3 py-2 my-2 overflow-x-auto">
                  <code className="font-mono text-xs text-accent">{children}</code>
                </pre>
              );
            }
            return (
              <code
                className="font-mono text-xs bg-base-950 border border-base-600 rounded px-1 py-0.5 text-accent"
                {...props}
              >
                {children}
              </code>
            );
          },
        }}
      >
        {children}
      </ReactMarkdown>
    </div>
  );
}
