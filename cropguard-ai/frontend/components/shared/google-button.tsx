"use client";

import { useState } from "react";
import { Loader2 } from "lucide-react";
import { isSupabaseConfigured, signInWithGoogle } from "@/lib/supabase-browser";
import { USE_MOCK_API } from "@/lib/api/client";

/** Google's brand mark. lucide-react doesn't ship third-party logos. */
function GoogleMark({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 18 18" aria-hidden="true">
      <path
        fill="#4285F4"
        d="M17.64 9.2c0-.64-.06-1.25-.16-1.84H9v3.48h4.84a4.14 4.14 0 0 1-1.8 2.72v2.26h2.91c1.7-1.57 2.69-3.88 2.69-6.62Z"
      />
      <path
        fill="#34A853"
        d="M9 18c2.43 0 4.47-.8 5.96-2.18l-2.91-2.26c-.81.54-1.84.86-3.05.86-2.34 0-4.32-1.58-5.03-3.7H.96v2.34A9 9 0 0 0 9 18Z"
      />
      <path
        fill="#FBBC05"
        d="M3.97 10.72a5.4 5.4 0 0 1 0-3.44V4.94H.96a9 9 0 0 0 0 8.12l3.01-2.34Z"
      />
      <path
        fill="#EA4335"
        d="M9 3.58c1.32 0 2.5.45 3.44 1.35l2.58-2.58C13.46.89 11.43 0 9 0A9 9 0 0 0 .96 4.94l3.01 2.34C4.68 5.16 6.66 3.58 9 3.58Z"
      />
    </svg>
  );
}

/**
 * Google sign-in entry point for the login and register pages.
 *
 * Renders nothing when there's no Supabase project to talk to (mock mode, or
 * missing NEXT_PUBLIC_SUPABASE_* config) rather than showing a button that can
 * only fail.
 */
export function GoogleSignInButton({
  next = "/dashboard",
  label = "Continue with Google",
}: {
  next?: string;
  label?: string;
}) {
  const [redirecting, setRedirecting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (USE_MOCK_API || !isSupabaseConfigured()) return null;

  async function handleClick() {
    setError(null);
    setRedirecting(true);
    try {
      await signInWithGoogle(next);
      // On success the browser navigates away, so the spinner stays up until
      // it does. No setRedirecting(false) here on purpose.
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not start Google sign-in.");
      setRedirecting(false);
    }
  }

  return (
    <div className="mt-6">
      <div className="flex items-center gap-3">
        <span className="h-px flex-1 bg-line" />
        <span className="text-xs uppercase tracking-wide text-ink-soft">or</span>
        <span className="h-px flex-1 bg-line" />
      </div>

      <button
        type="button"
        onClick={handleClick}
        disabled={redirecting}
        className="mt-4 flex w-full items-center justify-center gap-2.5 rounded-md border border-line bg-paper px-3.5 py-2.5 text-sm font-medium text-ink transition-colors hover:bg-bg-alt disabled:opacity-60"
      >
        {redirecting ? (
          <Loader2 className="h-4 w-4 animate-spin" />
        ) : (
          <GoogleMark className="h-4 w-4" />
        )}
        {redirecting ? "Redirecting to Google…" : label}
      </button>

      {error && <p className="mt-2 text-xs text-rust">{error}</p>}
    </div>
  );
}
