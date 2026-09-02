// Central API client. Every function in lib/api/*.ts goes through here so
// switching between the mock layer and the FastAPI backend is an env change.

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export const USE_MOCK_API = process.env.NEXT_PUBLIC_USE_MOCK_API !== "false";

export class ApiError extends Error {
  status: number;

  constructor(message: string, status = 500) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

/** Simulates realistic network latency for the demo/mock layer. */
export function mockDelay(ms = 700) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

// --- Session storage --------------------------------------------------------
// One module owns these keys. auth-context.tsx and the multipart upload in
// scans.ts each used to read "cg_token" by hand, so the storage shape was
// duplicated in three places and only one of them knew about refresh tokens.

export const TOKEN_KEY = "cg_token";
export const REFRESH_TOKEN_KEY = "cg_refresh_token";
export const USER_KEY = "cg_user";

function readLocal(key: string): string | null {
  if (typeof window === "undefined") return null;
  try {
    return localStorage.getItem(key);
  } catch {
    // Safari private mode / storage disabled. Treated as "logged out" rather
    // than crashing the render.
    return null;
  }
}

function writeLocal(key: string, value: string | null) {
  if (typeof window === "undefined") return;
  try {
    if (value === null) localStorage.removeItem(key);
    else localStorage.setItem(key, value);
  } catch {
    /* storage unavailable — the session just won't survive a reload */
  }
}

export function readToken(): string | null {
  return readLocal(TOKEN_KEY);
}

export function readRefreshToken(): string | null {
  return readLocal(REFRESH_TOKEN_KEY);
}

export function storeTokens(token: string, refreshToken?: string | null) {
  writeLocal(TOKEN_KEY, token);
  if (refreshToken) writeLocal(REFRESH_TOKEN_KEY, refreshToken);
}

export function storeUser(user: unknown) {
  writeLocal(USER_KEY, JSON.stringify(user));
}

/**
 * Reads the cached user, tolerating a corrupt entry.
 *
 * The bug this fixes: auth-context called JSON.parse(localStorage) unguarded
 * inside its mount effect. A truncated or hand-edited "cg_user" threw, the
 * effect aborted before setLoading(false), and the app sat on its loading
 * spinner forever — unrecoverable without clearing site data by hand.
 */
export function readStoredUser<T>(): T | null {
  const raw = readLocal(USER_KEY);
  if (!raw) return null;
  try {
    const parsed = JSON.parse(raw);
    return parsed && typeof parsed === "object" ? (parsed as T) : null;
  } catch {
    writeLocal(USER_KEY, null);
    return null;
  }
}

export function clearSession() {
  writeLocal(TOKEN_KEY, null);
  writeLocal(REFRESH_TOKEN_KEY, null);
  writeLocal(USER_KEY, null);
}

/** Authorization header for requests that can't go through apiFetch (multipart). */
export function authHeaders(): Record<string, string> {
  const token = readToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

// --- Expired-session handling ----------------------------------------------

type UnauthorizedHandler = () => void;

let unauthorizedHandler: UnauthorizedHandler | null = null;

/**
 * Registered by AuthProvider. Called when the server rejects a token that
 * can't be refreshed, so one 401 on any screen logs the user out cleanly
 * instead of leaving a logged-in shell where every panel shows an error.
 */
export function setUnauthorizedHandler(handler: UnauthorizedHandler | null) {
  unauthorizedHandler = handler;
  return () => {
    if (unauthorizedHandler === handler) unauthorizedHandler = null;
  };
}

function sessionExpired() {
  clearSession();
  unauthorizedHandler?.();
}

// Single-flight: a dashboard render fires several requests at once, and all of
// them can 401 together. Without this they'd each burn the refresh token, and
// Supabase invalidates a refresh token once it's been used.
let refreshInFlight: Promise<string | null> | null = null;

async function refreshAccessToken(): Promise<string | null> {
  const refreshToken = readRefreshToken();
  if (!refreshToken) return null;

  if (!refreshInFlight) {
    refreshInFlight = (async () => {
      try {
        const res = await fetch(`${API_BASE_URL}/api/auth/refresh`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ refresh_token: refreshToken }),
        });
        if (!res.ok) return null;
        const body = await res.json().catch(() => null);
        if (!body?.token) return null;
        storeTokens(body.token, body.refresh_token ?? refreshToken);
        if (body.user) storeUser(body.user);
        return body.token as string;
      } catch {
        // Network failure — not proof the session is dead, so don't log out.
        return null;
      } finally {
        refreshInFlight = null;
      }
    })();
  }
  return refreshInFlight;
}

export interface ApiFetchOptions extends RequestInit {
  /**
   * True for /api/auth/login and /api/auth/register, where a 401 means "wrong
   * password" rather than "your session expired". Without this flag a failed
   * login attempt would trigger the global logout path.
   */
  isAuthAttempt?: boolean;
}

function buildHeaders(options: ApiFetchOptions, token: string | null): HeadersInit {
  const headers: Record<string, string> = {};
  // Let the browser set multipart/form-data itself — it has to append the
  // boundary, which we can't know here.
  if (!(options.body instanceof FormData)) {
    headers["Content-Type"] = "application/json";
  }
  if (token) headers.Authorization = `Bearer ${token}`;
  return { ...headers, ...(options.headers as Record<string, string>) };
}

/** Real fetch wrapper, used once USE_MOCK_API is false. */
export async function apiFetch<T>(
  path: string,
  options: ApiFetchOptions = {}
): Promise<T> {
  const { isAuthAttempt = false, ...init } = options;

  const send = (token: string | null) =>
    fetch(`${API_BASE_URL}${path}`, { ...init, headers: buildHeaders(options, token) });

  let res: Response;
  try {
    res = await send(readToken());
  } catch (e) {
    // fetch() only rejects on a transport failure, which is worth naming: the
    // usual cause here is the FastAPI process not running.
    throw new ApiError(
      `Could not reach the server at ${API_BASE_URL}. Check that the backend is running.`,
      0
    );
  }

  if (res.status === 401 && !isAuthAttempt) {
    const fresh = await refreshAccessToken();
    if (fresh) {
      try {
        res = await send(fresh);
      } catch {
        throw new ApiError(`Could not reach the server at ${API_BASE_URL}.`, 0);
      }
    }
    if (res.status === 401) sessionExpired();
  }

  const body = await res.json().catch(() => null);

  if (!res.ok || body?.status === "error") {
    const message =
      body?.error ?? body?.detail ?? body?.message ?? `Request failed (${res.status})`;
    throw new ApiError(
      typeof message === "string" ? message : `Request failed (${res.status})`,
      res.status
    );
  }

  return body as T;
}
