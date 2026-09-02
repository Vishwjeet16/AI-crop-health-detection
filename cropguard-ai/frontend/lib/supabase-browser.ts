"use client";

/**
 * Browser-side Supabase client, used only for Google sign-in.
 *
 * Everything else in the app talks to the FastAPI backend, which holds the
 * service_role key and enforces per-user scoping. OAuth is the exception: the
 * redirect dance has to happen in the browser, so this client exists to start
 * it and to exchange the returned code for a session. The resulting access
 * token is then handed to the backend like any other token — see
 * app/(auth)/auth/callback/page.tsx.
 */

import { createClient, type SupabaseClient } from "@supabase/supabase-js";

const SUPABASE_URL = process.env.NEXT_PUBLIC_SUPABASE_URL ?? "";
const SUPABASE_ANON_KEY = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY ?? "";

/** Where Supabase sends the browser back after Google accepts. */
export const OAUTH_CALLBACK_PATH = "/auth/callback";

export function isSupabaseConfigured(): boolean {
  return Boolean(SUPABASE_URL && SUPABASE_ANON_KEY);
}

let cached: SupabaseClient | null = null;

export function getSupabaseBrowserClient(): SupabaseClient | null {
  if (!isSupabaseConfigured()) return null;
  if (!cached) {
    cached = createClient(SUPABASE_URL, SUPABASE_ANON_KEY, {
      auth: {
        // PKCE keeps the code verifier in localStorage across the redirect;
        // the implicit flow would put the access token in the URL fragment.
        flowType: "pkce",
        persistSession: true,
        // The app's own token lives in cg_token and is refreshed through
        // POST /api/auth/refresh. Letting this client also run a refresh timer
        // would give the session two owners racing each other.
        autoRefreshToken: false,
        // The callback page calls exchangeCodeForSession explicitly, so it can
        // report a failure instead of it happening silently on mount.
        detectSessionInUrl: false,
      },
    });
  }
  return cached;
}

export class OAuthNotConfiguredError extends Error {
  constructor() {
    super(
      "Google sign-in isn't configured. Set NEXT_PUBLIC_SUPABASE_URL and " +
        "NEXT_PUBLIC_SUPABASE_ANON_KEY in frontend/.env.local, and enable the " +
        "Google provider in the Supabase dashboard."
    );
    this.name = "OAuthNotConfiguredError";
  }
}

/**
 * Redirects to Google. On success the browser lands back on
 * OAUTH_CALLBACK_PATH with a `code` query parameter.
 *
 * `next` is where to go once the session is established, so a user who was
 * bounced to /login from a protected page returns there.
 */
export async function signInWithGoogle(next = "/dashboard"): Promise<void> {
  const supabase = getSupabaseBrowserClient();
  if (!supabase) throw new OAuthNotConfiguredError();

  const redirectTo = `${window.location.origin}${OAUTH_CALLBACK_PATH}?next=${encodeURIComponent(next)}`;

  const { error } = await supabase.auth.signInWithOAuth({
    provider: "google",
    options: {
      redirectTo,
      queryParams: {
        // Ask for a refresh token and let the user pick an account rather than
        // silently reusing whichever one the browser is already signed into.
        access_type: "offline",
        prompt: "select_account",
      },
    },
  });

  if (error) throw new Error(error.message);
}

/** Exchanges the ?code= from the callback URL for a Supabase session. */
export async function exchangeCodeForSession(code: string) {
  const supabase = getSupabaseBrowserClient();
  if (!supabase) throw new OAuthNotConfiguredError();

  const { data, error } = await supabase.auth.exchangeCodeForSession(code);
  if (error) throw new Error(error.message);
  if (!data.session?.access_token) {
    throw new Error("Google sign-in returned no session. Please try again.");
  }
  return {
    accessToken: data.session.access_token,
    refreshToken: data.session.refresh_token ?? null,
  };
}
