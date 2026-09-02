"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Loader2, MapPin } from "lucide-react";
import { Topbar } from "@/components/shared/topbar";
import { createField } from "@/lib/api/fields";
import { ApiError } from "@/lib/api/client";
import { getActiveLocation, type Coordinates } from "@/lib/location";
import { isPositiveNumber, isRequired } from "@/lib/validation";

interface FormState {
  name: string;
  crop: string;
  area: string;
}

export default function NewFieldPage() {
  const router = useRouter();
  const [form, setForm] = useState<FormState>({ name: "", crop: "Tomato", area: "" });
  const [location, setLocation] = useState<Coordinates | null>(null);
  const [locating, setLocating] = useState(false);
  const [locationError, setLocationError] = useState<string | null>(null);
  const [errors, setErrors] = useState<Partial<Record<keyof FormState, string>>>({});
  const [formError, setFormError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  function update<K extends keyof FormState>(key: K, value: FormState[K]) {
    setForm((f) => ({ ...f, [key]: value }));
  }

  async function pinActiveLocation() {
    setLocating(true);
    setLocationError(null);
    try {
      setLocation(await getActiveLocation());
    } catch (err) {
      setLocationError(err instanceof Error ? err.message : "Could not read your active location.");
    } finally {
      setLocating(false);
    }
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const nextErrors = {
      name: isRequired(form.name) ?? undefined,
      area: isPositiveNumber(form.area) ?? undefined,
    };
    setErrors(nextErrors);
    if (Object.values(nextErrors).some(Boolean)) return;

    setFormError(null);
    setSubmitting(true);
    try {
      const activeLocation = location ?? (await getActiveLocation());
      await createField({
        name: form.name,
        crop: form.crop,
        areaAcres: Number(form.area),
        latitude: activeLocation.latitude,
        longitude: activeLocation.longitude,
      });
      router.push("/dashboard");
    } catch (err) {
      setFormError(err instanceof ApiError || err instanceof Error ? err.message : "Something went wrong. Please try again.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div>
      <Topbar title="Add Field" />
      <main className="px-5 py-8 md:px-8">
        <div className="mx-auto max-w-lg card p-6">
          <form className="space-y-4" onSubmit={handleSubmit} noValidate>
            <div>
              <label className="mb-1.5 block text-sm font-medium text-ink" htmlFor="name">
                Field name
              </label>
              <input
                id="name"
                placeholder="e.g. Field D"
                value={form.name}
                onChange={(e) => update("name", e.target.value)}
                className="w-full rounded-md border border-line bg-paper px-3.5 py-2.5 text-sm outline-none focus:border-growth"
                aria-invalid={!!errors.name}
              />
              {errors.name && <p className="mt-1 text-xs text-rust">{errors.name}</p>}
            </div>
            <div>
              <label className="mb-1.5 block text-sm font-medium text-ink" htmlFor="crop">
                Crop type
              </label>
              <select
                id="crop"
                value={form.crop}
                onChange={(e) => update("crop", e.target.value)}
                className="w-full rounded-md border border-line bg-paper px-3.5 py-2.5 text-sm outline-none focus:border-growth"
              >
                <option>Tomato</option>
                <option>Cotton</option>
                <option>Soybean</option>
                <option>Wheat</option>
                <option>Rice</option>
              </select>
            </div>
            <div>
              <label className="mb-1.5 block text-sm font-medium text-ink" htmlFor="area">
                Area (acres)
              </label>
              <input
                id="area"
                type="number"
                step="0.1"
                placeholder="2.0"
                value={form.area}
                onChange={(e) => update("area", e.target.value)}
                className="w-full rounded-md border border-line bg-paper px-3.5 py-2.5 text-sm outline-none focus:border-growth"
                aria-invalid={!!errors.area}
              />
              {errors.area && <p className="mt-1 text-xs text-rust">{errors.area}</p>}
            </div>
            <div>
              <label className="mb-1.5 block text-sm font-medium text-ink">Field location</label>
              <button
                type="button"
                onClick={pinActiveLocation}
                disabled={locating}
                className={`flex w-full items-center justify-center gap-2 rounded-md border border-dashed px-4 py-8 text-sm ${
                  location ? "border-growth bg-growth-light/20 text-growth-dark" : "border-line bg-bg-alt/60 text-ink-soft hover:border-growth"
                }`}
              >
                {locating ? <Loader2 className="h-4 w-4 animate-spin" /> : <MapPin className="h-4 w-4" />}
                {locating ? "Reading location..." : location ? "Active location pinned" : "Use active location"}
              </button>
              <p className="hidden">
                Real map picking (Leaflet) lands in Stage 3 — a nearby demo coordinate is used for now.
              </p>
              {location && (
                <p className="mt-1 text-xs text-ink-soft">
                  {location.latitude.toFixed(5)}, {location.longitude.toFixed(5)}
                </p>
              )}
              {locationError && <p className="mt-1 text-xs text-rust">{locationError}</p>}
            </div>

            {formError && (
              <p className="rounded-md bg-rust-light/20 px-3 py-2 text-sm text-rust-dark">{formError}</p>
            )}

            <button type="submit" className="btn-primary w-full" disabled={submitting}>
              {submitting && <Loader2 className="h-4 w-4 animate-spin" />}
              {submitting ? "Saving…" : "Save Field"}
            </button>
          </form>
        </div>
      </main>
    </div>
  );
}
