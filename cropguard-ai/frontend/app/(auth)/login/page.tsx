"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Loader2 } from "lucide-react";
import { useAuth } from "@/context/auth-context";
import { isRequired } from "@/lib/validation";
import { ApiError, USE_MOCK_API } from "@/lib/api/client";
import { GoogleSignInButton } from "@/components/shared/google-button";

export default function LoginPage() {
  const router = useRouter();
  const { login } = useAuth();

  const [identifier, setIdentifier] = useState("");
  const [password, setPassword] = useState("");
  const [errors, setErrors] = useState<{ identifier?: string; password?: string }>({});
  const [formError, setFormError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const nextErrors = {
      identifier: isRequired(identifier) ?? undefined,
      password: isRequired(password) ?? undefined,
    };
    setErrors(nextErrors);
    if (nextErrors.identifier || nextErrors.password) return;

    setFormError(null);
    setSubmitting(true);
    try {
      await login(identifier, password);
      router.push("/dashboard");
    } catch (err) {
      setFormError(err instanceof ApiError ? err.message : "Something went wrong. Please try again.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div>
      <h1 className="font-display text-2xl text-forest-dark">Welcome back</h1>
      <p className="mt-1 text-sm text-ink-soft">Log in to check on your fields.</p>
      {USE_MOCK_API ? (
        <p className="mt-2 rounded-md bg-bg-alt px-3 py-2 text-xs text-ink-soft">
          Demo login: <span className="font-mono">9876543210</span> / <span className="font-mono">cropguard1</span>
        </p>
      ) : (
        <p className="mt-2 rounded-md bg-bg-alt px-3 py-2 text-xs text-ink-soft">
          Real backend mode is on. Use a Supabase account, or run the demo seed script first.
        </p>
      )}

      <form className="mt-6 space-y-4" onSubmit={handleSubmit} noValidate>
        <div>
          <label className="mb-1.5 block text-sm font-medium text-ink" htmlFor="identifier">
            Mobile number or email
          </label>
          <input
            id="identifier"
            type="text"
            placeholder="98765 43210"
            value={identifier}
            onChange={(e) => setIdentifier(e.target.value)}
            className="w-full rounded-md border border-line bg-paper px-3.5 py-2.5 text-sm outline-none focus:border-growth"
            aria-invalid={!!errors.identifier}
          />
          {errors.identifier && <p className="mt-1 text-xs text-rust">{errors.identifier}</p>}
        </div>
        <div>
          <div className="mb-1.5 flex items-center justify-between">
            <label className="block text-sm font-medium text-ink" htmlFor="password">
              Password
            </label>
            <Link href="/forgot-password" className="text-xs font-medium text-growth hover:text-growth-dark">
              Forgot password?
            </Link>
          </div>
          <input
            id="password"
            type="password"
            placeholder="••••••••"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full rounded-md border border-line bg-paper px-3.5 py-2.5 text-sm outline-none focus:border-growth"
            aria-invalid={!!errors.password}
          />
          {errors.password && <p className="mt-1 text-xs text-rust">{errors.password}</p>}
        </div>

        {formError && (
          <p className="rounded-md bg-rust-light/20 px-3 py-2 text-sm text-rust-dark">{formError}</p>
        )}

        <button type="submit" className="btn-primary w-full" disabled={submitting}>
          {submitting && <Loader2 className="h-4 w-4 animate-spin" />}
          {submitting ? "Logging in…" : "Log In"}
        </button>
      </form>

      <GoogleSignInButton next="/dashboard" />

      <p className="mt-6 text-center text-sm text-ink-soft">
        New to CropGuard?{" "}
        <Link href="/register" className="font-semibold text-growth hover:text-growth-dark">
          Create an account
        </Link>
      </p>
    </div>
  );
}
