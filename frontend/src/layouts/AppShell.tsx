import { NavLink, Outlet } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";

const NAV_ITEMS = [
  { to: "/dashboard", label: "Dashboard", glyph: "◆" },
  { to: "/monitoring", label: "Monitoring", glyph: "▲" },
  { to: "/incidents", label: "Incidents", glyph: "●" },
  { to: "/chat", label: "AI Chat", glyph: "◈" },
  { to: "/settings", label: "Settings", glyph: "◐" },
];

export default function AppShell() {
  const { user, signOut } = useAuth();

  return (
    <div className="min-h-screen flex bg-base-950">
      <aside className="w-60 shrink-0 border-r border-base-700 bg-base-900 flex flex-col">
        <div className="px-5 py-5 border-b border-base-700">
          <div className="flex items-center gap-2">
            <PulseMark />
            <span className="font-display font-semibold tracking-tight text-ink-primary">
              AIOPS
            </span>
          </div>
          <p className="label-eyebrow mt-1">Assistant Console</p>
        </div>

        <nav className="flex-1 px-3 py-4 space-y-1">
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `flex items-center gap-3 rounded px-3 py-2 text-sm font-medium transition ${
                  isActive
                    ? "bg-base-800 text-accent border border-base-600"
                    : "text-ink-secondary hover:bg-base-800 hover:text-ink-primary border border-transparent"
                }`
              }
            >
              <span className="font-mono text-xs">{item.glyph}</span>
              {item.label}
            </NavLink>
          ))}
        </nav>

        <div className="px-4 py-4 border-t border-base-700">
          <p className="text-sm text-ink-primary truncate">{user?.full_name || user?.email}</p>
          <p className="label-eyebrow mt-0.5">{user?.role}</p>
          <button onClick={() => signOut()} className="btn-ghost w-full mt-3 text-xs py-1.5">
            Sign out
          </button>
        </div>
      </aside>

      <div className="flex-1 flex flex-col min-w-0">
        <header className="h-14 border-b border-base-700 bg-base-900/60 backdrop-blur flex items-center px-6 justify-between">
          <SystemPulseStrip />
          <span className="label-eyebrow">Phase 1 · Foundation</span>
        </header>
        <main className="flex-1 overflow-y-auto p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}

function PulseMark() {
  return (
    <svg width="20" height="20" viewBox="0 0 32 32" fill="none">
      <rect width="32" height="32" rx="6" fill="#161C26" />
      <path
        d="M4 18 L11 18 L14 9 L18 24 L21 14 L23 18 L28 18"
        stroke="#5EEAD4"
        strokeWidth="2.2"
        fill="none"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

/**
 * Signature element: a live-looking oscilloscope trace that reads as the
 * platform's heartbeat. Subtle, on-brand for an ops-monitoring console,
 * and doubles as the "all systems nominal" status indicator.
 */
function SystemPulseStrip() {
  return (
    <div className="flex items-center gap-3">
      <span className="relative flex h-2 w-2">
        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-signal-ok opacity-75" />
        <span className="relative inline-flex rounded-full h-2 w-2 bg-signal-ok" />
      </span>
      <svg width="120" height="20" viewBox="0 0 120 20" className="text-signal-ok/70">
        <polyline
          points="0,10 20,10 26,3 32,17 38,10 60,10 66,4 72,16 78,10 120,10"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.5"
        />
      </svg>
      <span className="label-eyebrow">All systems nominal</span>
    </div>
  );
}
