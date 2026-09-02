"use client";

import { useState } from "react";
import { Check, Loader2 } from "lucide-react";
import { Topbar } from "@/components/shared/topbar";
import { useAuth } from "@/context/auth-context";
import { useLanguage } from "@/context/language-context";
import { isRequired } from "@/lib/validation";
import { mockDelay } from "@/lib/api/client";
import { LANGUAGE_CODES, SUPPORTED_LANGUAGES, type LanguageCode } from "@/lib/i18n";

export default function SettingsPage() {
  const { user } = useAuth();
  const { language, setLanguage, t } = useLanguage();

  const [name, setName] = useState(user?.name ?? "");
  const [location, setLocation] = useState(user?.location ?? "");
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  async function handleSave(e: React.FormEvent) {
    e.preventDefault();
    const nameError = isRequired(name);
    if (nameError) {
      setError(nameError);
      return;
    }
    setError(null);
    setSaving(true);
    setSaved(false);
    await mockDelay(500); // Stage 3: PATCH /api/users/me
    setSaving(false);
    setSaved(true);
  }

  return (
    <div>
      <Topbar title="Settings" />
      <main className="mx-auto max-w-lg px-5 py-8 md:px-8">
        <div className="card p-6">
          <h3 className="font-display text-lg text-forest-dark">Profile</h3>
          <form className="mt-4 space-y-4" onSubmit={handleSave} noValidate>
            <div>
              <label className="mb-1.5 block text-sm font-medium text-ink">Full name</label>
              <input
                value={name}
                onChange={(e) => {
                  setName(e.target.value);
                  setSaved(false);
                }}
                className="w-full rounded-md border border-line bg-paper px-3.5 py-2.5 text-sm outline-none focus:border-growth"
                aria-invalid={!!error}
              />
              {error && <p className="mt-1 text-xs text-rust">{error}</p>}
            </div>
            <div>
              <label className="mb-1.5 block text-sm font-medium text-ink">Location</label>
              <input
                value={location}
                onChange={(e) => {
                  setLocation(e.target.value);
                  setSaved(false);
                }}
                className="w-full rounded-md border border-line bg-paper px-3.5 py-2.5 text-sm outline-none focus:border-growth"
              />
            </div>
            <div>
              <label className="mb-1.5 block text-sm font-medium text-ink" htmlFor="language">
                {t("settings.language")}
              </label>
              <select
                id="language"
                value={language}
                onChange={(e) => setLanguage(e.target.value as LanguageCode)}
                className="w-full rounded-md border border-line bg-paper px-3.5 py-2.5 text-sm outline-none focus:border-growth"
              >
                {/* From the i18n registry — this list used to be two hardcoded
                    options, so three of the five supported languages were
                    unreachable from here. */}
                {LANGUAGE_CODES.map((code) => (
                  <option key={code} value={code}>
                    {SUPPORTED_LANGUAGES[code].label}
                  </option>
                ))}
              </select>
              <p className="mt-1 text-xs text-ink-soft">{t("settings.languageHint")}</p>
            </div>
            <button type="submit" className="btn-primary w-full" disabled={saving}>
              {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : saved ? <Check className="h-4 w-4" /> : null}
              {saving ? "Saving…" : saved ? "Saved" : "Save Changes"}
            </button>
          </form>
        </div>

        <div className="card mt-6 p-6">
          <h3 className="font-display text-lg text-forest-dark">Notifications</h3>
          <label className="mt-4 flex items-center justify-between text-sm">
            High-risk field alerts
            <input type="checkbox" defaultChecked className="h-4 w-4 accent-growth" />
          </label>
          <label className="mt-3 flex items-center justify-between text-sm">
            Weekly field summary
            <input type="checkbox" defaultChecked className="h-4 w-4 accent-growth" />
          </label>
        </div>
      </main>
    </div>
  );
}
