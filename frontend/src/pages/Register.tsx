import { useEffect, useState, type FormEvent } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { Button } from "../components/ui/Button";
import { Input } from "../components/ui/Input";
import { Card } from "../components/ui/Card";

export function Register() {
  const { register, isAuthenticated, isLoading } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [adminKey, setAdminKey] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  if (isLoading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-[var(--color-border)] border-t-[var(--color-accent)]" />
      </div>
    );
  }

  if (isAuthenticated) return <Navigate to="/" replace />;

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError("");
    if (!email || !username || !password) { setError("All fields are required"); return; }
    if (password.length < 8) { setError("Password must be at least 8 characters"); return; }
    setSubmitting(true);
    try {
      await register(email, username, password, adminKey || undefined);
      navigate("/login?registered=true");
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      if (Array.isArray(detail)) setError(detail[0]?.msg || "Validation failed");
      else if (typeof detail === "string") setError(detail);
      else setError("Registration failed");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="flex min-h-[calc(100vh-8rem)] items-center justify-center px-4">
      <div className="w-full max-w-sm animate-slide-up">
        <div className="text-center mb-8">
          <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-[var(--color-accent)] text-white text-lg font-bold shadow-lg shadow-[var(--color-accent)]/20">
            CD
          </div>
          <h1 className="text-2xl font-semibold tracking-tight">Create account</h1>
          <p className="mt-1.5 text-sm text-[var(--color-text-secondary)]">
            Get started with your dealership
          </p>
        </div>

        <Card hover={false}>
          <form onSubmit={handleSubmit} className="flex flex-col gap-4">
            <Input label="Email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="you@example.com" autoComplete="email" />
            <Input label="Username" value={username} onChange={(e) => setUsername(e.target.value)} placeholder="Choose a username" autoComplete="username" />
            <Input label="Password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="At least 8 characters" autoComplete="new-password" />
            <Input label="Admin Key (optional)" type="password" value={adminKey} onChange={(e) => setAdminKey(e.target.value)} placeholder="Leave blank for regular user" />
            {error && (
              <div className="rounded-lg bg-[var(--color-danger-light)] border border-[var(--color-danger)]/20 px-3 py-2.5 text-sm text-[var(--color-danger)]">{error}</div>
            )}
            <Button type="submit" loading={submitting} className="w-full">Create Account</Button>
          </form>
        </Card>

        <p className="mt-6 text-center text-sm text-[var(--color-text-secondary)]">
          Already have an account?{" "}
          <Link to="/login" className="font-medium text-[var(--color-accent)] hover:underline">Sign in</Link>
        </p>
      </div>
    </div>
  );
}
