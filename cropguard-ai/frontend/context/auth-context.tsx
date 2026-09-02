"use client";

import { createContext, useCallback, useContext, useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import type { AuthUser } from "@/lib/api/auth";
import * as authApi from "@/lib/api/auth";
import {
  ApiError,
  clearSession,
  readStoredUser,
  readToken,
  setUnauthorizedHandler,
  storeTokens,
  storeUser,
} from "@/lib/api/client";
import { useLanguage } from "@/context/language-context";
import { SUPPORTED_LANGUAGES, type LanguageCode } from "@/lib/i18n";

export interface RegisterResult {
  /** True when the response carried a session and the user is now logged in. */
  signedIn: boolean;
  /** True when the account was created but needs email/phone confirmation. */
  pendingConfirmation: boolean;
  message?: string;
}

interface AuthContextValue {
  user: AuthUser | null;
  loading: boolean;
  login: (identifier: string, password: string) => Promise<void>;
  register: (payload: authApi.RegisterPayload) => Promise<RegisterResult>;
  /** Applies a session obtained outside the password flow (e.g. Google OAuth). */
  adoptSession: (token: string, refreshToken: string | null) => Promise<AuthUser>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const { setLanguage } = useLanguage();
  const [user, setUser] = useState<AuthUser | null>(null);
  const [loading, setLoading] = useState(true);

  // Read in the 401 handler without making it a dependency, so the handler is
  // registered once instead of on every user change.
  const userRef = useRef<AuthUser | null>(null);
  userRef.current = user;

  const applyLanguage = useCallback(
    (lang: string | undefined) => {
      if (lang && lang in SUPPORTED_LANGUAGES) setLanguage(lang as LanguageCode);
    },
    [setLanguage]
  );

  const clear = useCallback(() => {
    clearSession();
    setUser(null);
  }, []);

  const logout = useCallback(() => {
    clear();
    router.push("/login");
  }, [clear, router]);

  // A 401 that survived a refresh attempt means the session is genuinely gone.
  // Previously nothing handled this: the shell stayed rendered and every panel
  // showed its own error, so the user had no way to tell they'd been logged out.
  useEffect(() => {
    return setUnauthorizedHandler(() => {
      if (!userRef.current) return; // nothing to tear down (e.g. public page)
      setUser(null);
      router.push("/login");
    });
  }, [router]);

  // Restore the session on load. The cached user paints the shell immediately;
  // GET /api/auth/me then confirms the token is still valid. Without that call
  // a token which expired while the tab was closed produced a logged-in UI
  // where every request failed.
  useEffect(() => {
    let cancelled = false;

    async function restore() {
      const token = readToken();
      const cached = readStoredUser<AuthUser>();

      if (!token) {
        if (!cancelled) {
          // A user blob with no token is a half-cleared session, not a login.
          if (cached) clearSession();
          setLoading(false);
        }
        return;
      }

      if (cached && !cancelled) {
        setUser(cached);
        applyLanguage(cached.language);
      }

      try {
        const fresh = await authApi.me();
        if (cancelled) return;
        setUser(fresh);
        storeUser(fresh);
        applyLanguage(fresh.language);
      } catch (err) {
        if (cancelled) return;
        // 401/403: the token is dead — the apiFetch layer already cleared it.
        // Anything else (backend down, 502) is not proof the session is
        // invalid, so keep the cached user rather than logging the user out
        // because the API happened to be restarting.
        const status = err instanceof ApiError ? err.status : 0;
        if (status === 401 || status === 403) {
          clearSession();
          setUser(null);
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    restore();
    return () => {
      cancelled = true;
    };
  }, [applyLanguage]);

  function persist(token: string, refreshToken: string | null | undefined, nextUser: AuthUser) {
    storeTokens(token, refreshToken ?? null);
    storeUser(nextUser);
    setUser(nextUser);
    applyLanguage(nextUser.language);
  }

  async function login(identifier: string, password: string) {
    const res = await authApi.login({ identifier, password });
    if (!res.token || !res.user) {
      // Registration can legitimately return no session; login cannot.
      throw new ApiError(
        res.message ?? "Login did not return a session. Please try again.",
        502
      );
    }
    persist(res.token, res.refresh_token, res.user);
  }

  async function register(payload: authApi.RegisterPayload): Promise<RegisterResult> {
    const res = await authApi.register(payload);

    if (res.token && res.user) {
      persist(res.token, res.refresh_token, res.user);
      return { signedIn: true, pendingConfirmation: false, message: res.message ?? undefined };
    }

    // Account created, confirmation pending. Not an error — the caller shows a
    // "check your inbox" state instead of pushing to the dashboard.
    return {
      signedIn: false,
      pendingConfirmation: res.pending_confirmation ?? true,
      message:
        res.message ??
        "Account created. Please confirm your email address, then log in.",
    };
  }

  /**
   * Used by the OAuth callback: Supabase hands the browser a session directly,
   * so there's no password round-trip. The token still has to be validated and
   * turned into a profile, which /api/auth/me does server-side.
   */
  async function adoptSession(token: string, refreshToken: string | null) {
    storeTokens(token, refreshToken);
    const profile = await authApi.me();
    storeUser(profile);
    setUser(profile);
    applyLanguage(profile.language);
    return profile;
  }

  return (
    <AuthContext.Provider
      value={{ user, loading, login, register, adoptSession, logout }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
