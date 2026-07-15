import StatusBadge from "@/components/StatusBadge";
import { usePolling } from "@/hooks/usePolling";
import { fetchJenkinsJobs } from "@/services/jenkinsService";

export default function Jenkins() {
  const { data: jobs } = usePolling(fetchJenkinsJobs, 20000);

  return (
    <div className="space-y-6">
      <div>
        <p className="label-eyebrow">CI/CD</p>
        <h1 className="text-xl font-semibold text-ink-primary mt-1">Jenkins</h1>
        <p className="text-sm text-ink-secondary mt-1">Job and build status.</p>
      </div>

      {jobs && !jobs.configured && (
        <div className="panel p-4 text-sm text-ink-secondary">
          Jenkins isn't configured yet. Set <code className="font-mono text-accent">JENKINS_URL</code>{" "}
          in your environment to connect it.
        </div>
      )}

      <div className="panel divide-y divide-base-700">
        {(jobs?.items ?? []).map((job) => (
          <div key={job.name} className="p-4 flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-ink-primary font-mono">{job.name}</p>
              <p className="text-xs text-ink-muted mt-0.5">{job.url}</p>
            </div>
            <StatusBadge status={job.status} />
          </div>
        ))}
        {(jobs?.items ?? []).length === 0 && jobs?.configured && (
          <div className="p-8 text-center text-sm text-ink-muted">No jobs found</div>
        )}
      </div>
    </div>
  );
}
