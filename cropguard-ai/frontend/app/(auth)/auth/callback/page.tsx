"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { AlertTriangle, Loader2 } from "lucide-react";
import { useAuth } from "@/context/auth-context";
import { exchangeCodeForSession } from "@/lib/supabase-browser";

/**
 * Landing point for the Google OAuth redirect.
 *
 * Supabase sends the browser back here with a one-time `code`. We exchange it
 * for a session, then hand the access token to the backend via
 * adoptSession(), which calls GET /api/auth/me — that request is what creates
 * the public.users profile row for a first-time Google user (ensure_profile in
 * backend/app/utils/auth.py), so the rest of the app has a profile to read.
 *
 * Query parameters are read from window.location rather than useSearchParams()
 * so this page doesn't need a Suspense boundary at build time.
 */
export default function OAuthCallbackPage() {
  const router = useRouter();
  const { adoptSession } = useAuth();
  const [error, setError] = useState<string | null>(null);

  // The code is single-use, and React's dev-mode double mount would spend it
  // on the first run and fail on the second.
  const started = useRef(false);

  useEffect(() => {
    if (started.current) return;
    started.current = true;

    const params = new URLSearchParams(window.location.search);
    const next = params.get("next") || "/dashboard";
    const oauthError = params.get("error_description") || params.get("error");
    const code = params.get("code");

    if (oauthError) {
      setError(oauthError);
      return;
    }
    if (!code) {
      setError(
        "This link is missing its sign-in code. Please start again from the login page."
      );
      return;
    }

    (async () => {
      try {
        const { accessToken, refreshToken } = await exchangeCodeForSession(code);
        await adoptSession(accessToken, refreshToken);
        // replace(), not push(), so Back doesn't return to a spent code.
        router.replace(next);
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "Google sign-in could not be completed."
        );
      }
    })();
    // adoptSession/router are stable enough for a run-once effect, and the ref
    // guard makes a re-run harmless anyway.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  if (error) {
    return (
      <div className="flex flex-col items-center gap-3 text-center">
        <span className="flex h-12 w-12 items-center justify-center rounded-full bg-rust-light/30 text-rust-dark">
          <AlertTriangle className="h-5 w-5" />
        </span>
        <h1 className="font-display text-2xl text-forest-dark">Sign-in didn't complete</h1>
        <p className="max-w-xs text-sm text-ink-soft">{error}</p>
        <Link href="/login" className="btn-primary mt-2">
          Back to login
        </Link>
      </div>
    );
  }

  return (
    <div className="flex flex-col items-center gap-3 text-center">
      <Loader2 className="h-6 w-6 animate-spin text-growth" />
      <h1 className="font-display text-2xl text-forest-dark">Signing you in…</h1>
      <p className="max-w-xs text-sm text-ink-soft">
        Finishing up with Google. This only takes a moment.
      </p>
    </div>
  );
}
