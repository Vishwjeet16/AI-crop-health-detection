"use client";

import { useState } from "react";
import Link from "next/link";
import { ArrowLeft, Loader2, MailCheck } from "lucide-react";
import { requestPasswordReset } from "@/lib/api/auth";
import { ApiError } from "@/lib/api/client";
import { isRequired } from "@/lib/validation";

export default function ForgotPasswordPage() {
  const [identifier, setIdentifier] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [sent, setSent] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const fieldError = isRequired(identifier);
    if (fieldError) {
      setError(fieldError);
      return;
    }
    setError(null);
    setSubmitting(true);
    try {
      const result = await requestPasswordReset(identifier);
      // The server answers sent:false for a mobile number, because Supabase's
      // recover endpoint is email-only. This page used to show "Check your
      // inbox" either way, leaving the user waiting for an SMS that was never
      // going to arrive.
      if (result.sent) {
        setNotice(result.message ?? null);
        setSent(true);
      } else {
        setError(
          result.message ??
            "We can't send a reset link to that. Enter the email address you registered with."
        );
      }
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong. Please try again.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div>
      <Link href="/login" className="mb-6 flex items-center gap-1.5 text-sm text-ink-soft hover:text-forest">
        <ArrowLeft className="h-4 w-4" /> Back to login
      </Link>

      {sent ? (
        <div className="flex flex-col items-center gap-3 text-center">
          <span className="flex h-12 w-12 items-center justify-center rounded-full bg-growth-light/40 text-growth-dark">
            <MailCheck className="h-5 w-5" />
          </span>
          <h1 className="font-display text-2xl text-forest-dark">Check your inbox</h1>
          <p className="max-w-xs text-sm text-ink-soft">
            {notice ?? (
              <>
                If an account exists for <span className="font-medium text-ink">{identifier}</span>, a reset link is on its way.
              </>
            )}
          </p>
        </div>
      ) : (
        <>
          <h1 className="font-display text-2xl text-forest-dark">Reset your password</h1>
          <p className="mt-1 text-sm text-ink-soft">
            Enter the email address you registered with and we'll send you a reset link.
          </p>
          <form className="mt-8 space-y-4" onSubmit={handleSubmit} noValidate>
            <div>
              <label className="mb-1.5 block text-sm font-medium text-ink" htmlFor="identifier">
                Email address
              </label>
              <input
                id="identifier"
                type="email"
                placeholder="ramesh@example.com"
                value={identifier}
                onChange={(e) => setIdentifier(e.target.value)}
                className="w-full rounded-md border border-line bg-paper px-3.5 py-2.5 text-sm outline-none focus:border-growth"
                aria-invalid={!!error}
              />
              {error && <p className="mt-1 text-xs text-rust">{error}</p>}
            </div>
            <button type="submit" className="btn-primary w-full" disabled={submitting}>
              {submitting && <Loader2 className="h-4 w-4 animate-spin" />}
              {submitting ? "Sending…" : "Send Reset Link"}
            </button>
          </form>
        </>
      )}
    </div>
  );
}
