import { useState, type FormEvent } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { Button } from "../components/ui/Button";
import { Input } from "../components/ui/Input";
import { Card } from "../components/ui/Card";

export function Login() {
  const { login, isAuthenticated, isLoading } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
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
    if (!email || !password) { setError("Email and password are required"); return; }
    setSubmitting(true);
    try {
      const userData = await login(email, password);
      navigate(userData.role === "admin" ? "/admin" : "/");
    } catch (err: any) {
      setError(err.response?.data?.detail || "Login failed");
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
          <h1 className="text-2xl font-semibold tracking-tight">Welcome back</h1>
          <p className="mt-1.5 text-sm text-[var(--color-text-secondary)]">
            Sign in to manage your inventory
          </p>
        </div>

        <Card hover={false}>
          <form onSubmit={handleSubmit} className="flex flex-col gap-4">
            <Input label="Email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="you@example.com" autoComplete="email" />
            <Input label="Password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Enter your password" autoComplete="current-password" />
            {error && (
              <div className="rounded-lg bg-[var(--color-danger-light)] border border-[var(--color-danger)]/20 px-3 py-2.5 text-sm text-[var(--color-danger)]">
                {error}
              </div>
            )}
            <Button type="submit" loading={submitting} className="w-full">
              Sign In
            </Button>
          </form>
        </Card>

        <p className="mt-6 text-center text-sm text-[var(--color-text-secondary)]">
          Don't have an account?{" "}
          <Link to="/register" className="font-medium text-[var(--color-accent)] hover:underline">Create one</Link>
        </p>
      </div>
    </div>
  );
}
