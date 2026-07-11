import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import type { Role } from "@/types";

export default function Register() {
  const { signUp } = useAuth();
  const navigate = useNavigate();
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState<Role>("viewer");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      await signUp({ full_name: fullName, email, password, role });
      navigate("/dashboard");
    } catch {
      setError("Could not create account. That email may already be registered.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-base-950 px-4">
      <div className="w-full max-w-sm">
        <div className="panel p-6">
          <p className="label-eyebrow mb-1">Create account</p>
          <h1 className="text-lg font-semibold text-ink-primary mb-6">Join the console</h1>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="label-eyebrow block mb-1.5">Full name</label>
              <input
                required
                className="input-field"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
              />
            </div>
            <div>
              <label className="label-eyebrow block mb-1.5">Email</label>
              <input
                type="email"
                required
                className="input-field"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </div>
            <div>
              <label className="label-eyebrow block mb-1.5">Password</label>
              <input
                type="password"
                required
                minLength={8}
                className="input-field"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </div>
            <div>
              <label className="label-eyebrow block mb-1.5">Role</label>
              <select
                className="input-field"
                value={role}
                onChange={(e) => setRole(e.target.value as Role)}
              >
                <option value="viewer">Viewer</option>
                <option value="devops_engineer">DevOps Engineer</option>
                <option value="admin">Admin</option>
              </select>
            </div>

            {error && <p className="text-sm text-signal-crit">{error}</p>}

            <button type="submit" className="btn-primary w-full" disabled={isSubmitting}>
              {isSubmitting ? "Creating account…" : "Create account"}
            </button>
          </form>
        </div>

        <p className="text-center text-sm text-ink-secondary mt-4">
          Already have an account?{" "}
          <Link to="/login" className="text-accent hover:underline">
            Sign in
          </Link>
        </p>
      </div>
    </div>
  );
}
