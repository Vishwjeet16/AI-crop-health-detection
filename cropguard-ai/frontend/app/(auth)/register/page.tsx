"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Loader2, MailCheck } from "lucide-react";
import { useAuth } from "@/context/auth-context";
import { isEmailOrPhone, isRequired, isStrongPassword } from "@/lib/validation";
import { ApiError } from "@/lib/api/client";
import { GoogleSignInButton } from "@/components/shared/google-button";
import { SUPPORTED_LANGUAGES, type LanguageCode } from "@/lib/i18n";

interface FormState {
  name: string;
  contact: string;
  password: string;
  location: string;
  language: LanguageCode;
}

type FieldErrors = Partial<Record<keyof FormState, string>>;

export default function RegisterPage() {
  const router = useRouter();
  const { register } = useAuth();

  const [form, setForm] = useState<FormState>({
    name: "",
    contact: "",
    password: "",
    location: "",
    language: "en",
  });
  const [errors, setErrors] = useState<FieldErrors>({});
  const [formError, setFormError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  // Set when the account was created but needs confirmation before it can be
  // used. This is a success state; it used to arrive as an HTTP 202 that the
  // client threw, so the page told the user their signup had failed.
  const [pendingMessage, setPendingMessage] = useState<string | null>(null);

  function update<K extends keyof FormState>(key: K, value: FormState[K]) {
    setForm((f) => ({ ...f, [key]: value }));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const nextErrors: FieldErrors = {
      name: isRequired(form.name) ?? undefined,
      contact: isEmailOrPhone(form.contact) ?? undefined,
      password: isStrongPassword(form.password) ?? undefined,
      location: isRequired(form.location) ?? undefined,
    };
    setErrors(nextErrors);
    if (Object.values(nextErrors).some(Boolean)) return;

    setFormError(null);
    setSubmitting(true);
    try {
      const result = await register(form);
      if (result.signedIn) {
        router.push("/dashboard");
      } else {
        setPendingMessage(
          result.message ?? "Account created. Please confirm your email, then log in."
        );
      }
    } catch (err) {
      setFormError(err instanceof ApiError ? err.message : "Something went wrong. Please try again.");
    } finally {
      setSubmitting(false);
    }
  }

  if (pendingMessage) {
    return (
      <div className="flex flex-col items-center gap-3 text-center">
        <span className="flex h-12 w-12 items-center justify-center rounded-full bg-growth-light/40 text-growth-dark">
          <MailCheck className="h-5 w-5" />
        </span>
        <h1 className="font-display text-2xl text-forest-dark">Almost there</h1>
        <p className="max-w-xs text-sm text-ink-soft">{pendingMessage}</p>
        <Link href="/login" className="btn-primary mt-2">
          Go to login
        </Link>
      </div>
    );
  }

  return (
    <div>
      <h1 className="font-display text-2xl text-forest-dark">Create your account</h1>
      <p className="mt-1 text-sm text-ink-soft">Start monitoring your fields with AI.</p>

      <form className="mt-6 space-y-4" onSubmit={handleSubmit} noValidate>
        <Field
          id="name"
          label="Full name"
          placeholder="Ramesh Patil"
          value={form.name}
          onChange={(v) => update("name", v)}
          error={errors.name}
        />
        <Field
          id="contact"
          label="Mobile number or email"
          placeholder="98765 43210"
          value={form.contact}
          onChange={(v) => update("contact", v)}
          error={errors.contact}
        />
        <Field
          id="password"
          label="Password"
          placeholder="At least 8 characters"
          type="password"
          value={form.password}
          onChange={(v) => update("password", v)}
          error={errors.password}
        />
        <Field
          id="location"
          label="Location"
          placeholder="Nashik, Maharashtra"
          value={form.location}
          onChange={(v) => update("location", v)}
          error={errors.location}
        />
        <div>
          <label className="mb-1.5 block text-sm font-medium text-ink" htmlFor="language">
            Preferred language
          </label>
          <select
            id="language"
            value={form.language}
            onChange={(e) => update("language", e.target.value as LanguageCode)}
            className="w-full rounded-md border border-line bg-paper px-3.5 py-2.5 text-sm outline-none focus:border-growth"
          >
            {/* Driven by the i18n registry — adding a language file is the
                only step needed to make it selectable here. */}
            {Object.entries(SUPPORTED_LANGUAGES).map(([code, { label }]) => (
              <option key={code} value={code}>
                {label}
              </option>
            ))}
          </select>
        </div>

        {formError && (
          <p className="rounded-md bg-rust-light/20 px-3 py-2 text-sm text-rust-dark">{formError}</p>
        )}

        <button type="submit" className="btn-primary w-full" disabled={submitting}>
          {submitting && <Loader2 className="h-4 w-4 animate-spin" />}
          {submitting ? "Creating account…" : "Create Account"}
        </button>
      </form>

      <GoogleSignInButton next="/dashboard" label="Sign up with Google" />

      <p className="mt-6 text-center text-sm text-ink-soft">
        Already have an account?{" "}
        <Link href="/login" className="font-semibold text-growth hover:text-growth-dark">
          Log in
        </Link>
      </p>
    </div>
  );
}

function Field({
  id,
  label,
  placeholder,
  type = "text",
  value,
  onChange,
  error,
}: {
  id: string;
  label: string;
  placeholder: string;
  type?: string;
  value: string;
  onChange: (v: string) => void;
  error?: string;
}) {
  return (
    <div>
      <label className="mb-1.5 block text-sm font-medium text-ink" htmlFor={id}>
        {label}
      </label>
      <input
        id={id}
        type={type}
        placeholder={placeholder}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full rounded-md border border-line bg-paper px-3.5 py-2.5 text-sm outline-none focus:border-growth"
        aria-invalid={!!error}
      />
      {error && <p className="mt-1 text-xs text-rust">{error}</p>}
    </div>
  );
}
