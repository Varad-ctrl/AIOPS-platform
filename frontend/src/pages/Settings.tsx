import { useAuth } from "@/contexts/AuthContext";

export default function Settings() {
  const { user } = useAuth();

  return (
    <div className="space-y-6 max-w-2xl">
      <div>
        <p className="label-eyebrow">Settings</p>
        <h1 className="text-xl font-semibold text-ink-primary mt-1">Account & environment</h1>
      </div>

      <div className="panel p-6">
        <p className="label-eyebrow mb-4">Profile</p>
        <dl className="space-y-3 text-sm">
          <Row label="Full name" value={user?.full_name || "—"} />
          <Row label="Email" value={user?.email || "—"} />
          <Row label="Role" value={user?.role || "—"} />
          <Row label="Status" value={user?.is_active ? "Active" : "Inactive"} />
        </dl>
      </div>

      <div className="panel p-6">
        <p className="label-eyebrow mb-4">Connected integrations</p>
        <ul className="text-sm text-ink-secondary space-y-1.5">
          <li>Prometheus</li>
          <li>Loki</li>
          <li>Jenkins</li>
          <li>Kubernetes</li>
        </ul>
      </div>
    </div>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between border-b border-base-700 last:border-0 pb-3 last:pb-0">
      <dt className="text-ink-secondary">{label}</dt>
      <dd className="text-ink-primary font-medium">{value}</dd>
    </div>
  );
}
