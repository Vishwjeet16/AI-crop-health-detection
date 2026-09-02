import {
  apiFetch,
  ApiError,
  mockDelay,
  USE_MOCK_API,
} from "./client";
import { currentUser } from "@/lib/mock-data";
import type { LanguageCode } from "@/lib/i18n";

export interface AuthUser {
  id?: string;
  name: string;
  location: string;
  language: LanguageCode;
  contact: string;
}

export interface LoginPayload {
  identifier: string;
  password: string;
}

export interface RegisterPayload {
  name: string;
  contact: string;
  password: string;
  location: string;
  language: LanguageCode;
}

/**
 * Mirrors backend/app/schemas/auth.py AuthResponse.
 *
 * `token` and `user` are nullable because a successful registration against a
 * Supabase project that requires email confirmation has no session yet. That
 * case used to come back as HTTP 202, which this client threw as an ApiError
 * and the register page rendered as a red failure box — telling the user their
 * signup failed when in fact the account had been created.
 */
export interface AuthApiResponse {
  token: string | null;
  refresh_token?: string | null;
  user: AuthUser | null;
  pending_confirmation?: boolean;
  message?: string | null;
}

export interface PasswordResetResult {
  sent: boolean;
  message?: string;
}

const MOCK_TOKEN = "demo-token";
// Demo credential so the login flow has a real success/failure path to
// exercise without a backend yet.
const MOCK_ACCOUNT = { identifier: "9876543210", password: "cropguard1" };

export async function login(payload: LoginPayload): Promise<AuthApiResponse> {
  if (!USE_MOCK_API) {
    return apiFetch<AuthApiResponse>("/api/auth/login", {
      method: "POST",
      body: JSON.stringify(payload),
      // A 401 here is a wrong password, not an expired session.
      isAuthAttempt: true,
    });
  }
  await mockDelay();
  const identifier = payload.identifier.replace(/[\s-]/g, "");
  if (identifier !== MOCK_ACCOUNT.identifier || payload.password !== MOCK_ACCOUNT.password) {
    throw new ApiError(
      "We couldn't find an account with those details. For this demo, use mobile 9876543210 / password cropguard1.",
      401
    );
  }
  return {
    token: MOCK_TOKEN,
    refresh_token: `${MOCK_TOKEN}-refresh`,
    user: {
      name: currentUser.name,
      location: currentUser.location,
      language: currentUser.language,
      contact: identifier,
    },
  };
}

export async function register(payload: RegisterPayload): Promise<AuthApiResponse> {
  if (!USE_MOCK_API) {
    return apiFetch<AuthApiResponse>("/api/auth/register", {
      method: "POST",
      body: JSON.stringify(payload),
      isAuthAttempt: true,
    });
  }
  await mockDelay(900);
  return {
    token: MOCK_TOKEN,
    refresh_token: `${MOCK_TOKEN}-refresh`,
    user: {
      name: payload.name,
      location: payload.location,
      language: payload.language,
      contact: payload.contact,
    },
  };
}

/**
 * Validates the stored token and returns the server's copy of the profile.
 *
 * Called on mount. Without it, a token that expired while the tab was closed
 * still rendered the full logged-in shell, and the user met the failure one
 * panel at a time instead of at the login screen.
 */
export async function me(): Promise<AuthUser> {
  if (!USE_MOCK_API) {
    return apiFetch<AuthUser>("/api/auth/me");
  }
  await mockDelay(200);
  return {
    name: currentUser.name,
    location: currentUser.location,
    language: currentUser.language,
    contact: MOCK_ACCOUNT.identifier,
  };
}

export async function requestPasswordReset(
  identifier: string
): Promise<PasswordResetResult> {
  if (!USE_MOCK_API) {
    return apiFetch<PasswordResetResult>("/api/auth/forgot-password", {
      method: "POST",
      body: JSON.stringify({ identifier }),
      isAuthAttempt: true,
    });
  }
  await mockDelay(600);
  if (!identifier.trim()) {
    throw new ApiError("Enter your mobile number or email first.", 400);
  }
  if (!identifier.includes("@")) {
    return {
      sent: false,
      message:
        "Password reset by mobile number isn't available yet. If you registered with an email address, enter that instead.",
    };
  }
  return {
    sent: true,
    message: `If an account exists for ${identifier.trim()}, a reset link is on its way.`,
  };
}
