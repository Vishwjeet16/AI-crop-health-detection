"use client";

import { useEffect, useState } from "react";
import { Topbar } from "@/components/shared/topbar";
import { StatusBadge } from "@/components/ui/status-badge";
import { ErrorState } from "@/components/shared/states";
import { WeatherCard } from "@/components/shared/weather-card";
import { listFields } from "@/lib/api/fields";
import { getWeatherByCoordinates } from "@/lib/api/weather";
import { getActiveLocation, type Coordinates } from "@/lib/location";
import { formatRelativeTime } from "@/lib/utils";
import { X, Loader2, LocateFixed, RefreshCw } from "lucide-react";
import type { Field, Weather } from "@/types";

const COLOR: Record<string, string> = {
  healthy: "#4C7A3F",
  moderate: "#DFA23C",
  high: "#B4432E",
};

export default function MapPage() {
  const [fields, setFields] = useState<Field[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [selected, setSelected] = useState<Field | null>(null);
  const [activeLocation, setActiveLocation] = useState<Coordinates | null>(null);
  const [activeWeather, setActiveWeather] = useState<Weather | null>(null);
  const [locationError, setLocationError] = useState<string | null>(null);
  const [locating, setLocating] = useState(false);

  function load() {
    setError(null);
    setFields(null);
    setSelected(null);
    listFields()
      .then(setFields)
      .catch(() => setError("We couldn't load your field map. Please try again."));
  }

  async function loadActiveLocation() {
    setLocating(true);
    setLocationError(null);
    try {
      const coords = await getActiveLocation();
      setActiveLocation(coords);
      setActiveWeather(await getWeatherByCoordinates(coords.latitude, coords.longitude));
    } catch (err) {
      setLocationError(err instanceof Error ? err.message : "We couldn't read your active location.");
      setActiveWeather(null);
    } finally {
      setLocating(false);
    }
  }

  useEffect(() => {
    load();
    loadActiveLocation();
  }, []);

  if (error) {
    return (
      <div>
        <Topbar title="Field Map" />
        <main className="px-5 py-8 md:px-8">
          <ErrorState message={error} actionLabel="Try Again" onAction={load} />
        </main>
      </div>
    );
  }

  if (!fields) {
    return (
      <div>
        <Topbar title="Field Map" />
        <main className="flex justify-center px-5 py-16">
          <Loader2 className="h-6 w-6 animate-spin text-growth" />
        </main>
      </div>
    );
  }

  const mapPoints = [
    ...fields.map((f) => ({ latitude: f.latitude, longitude: f.longitude })),
    ...(activeLocation ? [activeLocation] : []),
  ];
  const safePoints = mapPoints.length > 0 ? mapPoints : [{ latitude: 0, longitude: 0 }];
  const lats = safePoints.map((p) => p.latitude);
  const lngs = safePoints.map((p) => p.longitude);
  const minLat = Math.min(...lats), maxLat = Math.max(...lats);
  const minLng = Math.min(...lngs), maxLng = Math.max(...lngs);

  function pos(point: { latitude: number; longitude: number }) {
    const x = maxLng === minLng ? 50 : ((point.longitude - minLng) / (maxLng - minLng)) * 70 + 15;
    const y = maxLat === minLat ? 50 : (1 - (point.latitude - minLat) / (maxLat - minLat)) * 70 + 15;
    return { x, y };
  }

  return (
    <div>
      <Topbar title="Field Map" />
      <main className="px-5 py-8 md:px-8">
        <div className="grid gap-6 lg:grid-cols-3">
          <div className="scan-frame relative h-[440px] overflow-hidden rounded-lg border border-line bg-bg-alt lg:col-span-2">
            <span className="corner-tl" />
            <span className="corner-br" />
            <div
              className="absolute inset-0"
              style={{
                backgroundImage:
                  "linear-gradient(#DAE2CD 1px, transparent 1px), linear-gradient(90deg, #DAE2CD 1px, transparent 1px)",
                backgroundSize: "40px 40px",
              }}
            />
            {fields.map((f) => {
              const { x, y } = pos(f);
              return (
                <button
                  key={f.id}
                  onClick={() => setSelected(f)}
                  className="absolute flex -translate-x-1/2 -translate-y-1/2 flex-col items-center"
                  style={{ left: `${x}%`, top: `${y}%` }}
                >
                  <span
                    className="h-5 w-5 rounded-full border-2 border-white shadow-md"
                    style={{ backgroundColor: COLOR[f.healthStatus] }}
                  />
                  <span className="mt-1 rounded bg-paper px-2 py-0.5 text-xs font-medium shadow-sm">
                    {f.name}
                  </span>
                </button>
              );
            })}
            {activeLocation && (
              <div
                className="absolute flex -translate-x-1/2 -translate-y-1/2 flex-col items-center"
                style={{ left: `${pos(activeLocation).x}%`, top: `${pos(activeLocation).y}%` }}
              >
                <span className="flex h-8 w-8 items-center justify-center rounded-full border-2 border-white bg-sky-500 text-white shadow-md">
                  <LocateFixed className="h-4 w-4" />
                </span>
                <span className="mt-1 rounded bg-paper px-2 py-0.5 text-xs font-medium shadow-sm">
                  You
                </span>
              </div>
            )}
            <p className="hidden">
              Demo map — production build renders real boundaries via Leaflet/OpenStreetMap.
            </p>
          </div>
          <div className="space-y-4">
            <div className="card p-5">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <h3 className="font-display text-lg text-forest-dark">Active Location</h3>
                  <p className="mt-1 text-xs text-ink-soft">
                    {activeLocation
                      ? `${activeLocation.latitude.toFixed(5)}, ${activeLocation.longitude.toFixed(5)}`
                      : locationError ?? "Allow location access to show your live position."}
                  </p>
                </div>
                <button
                  type="button"
                  onClick={loadActiveLocation}
                  disabled={locating}
                  className="rounded-md border border-line p-2 text-ink-soft hover:border-growth hover:text-growth disabled:opacity-60"
                  title="Refresh location"
                >
                  {locating ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />}
                </button>
              </div>
            </div>
            {activeWeather && <WeatherCard weather={activeWeather} />}

            <div className="card p-5">
            {selected ? (
              <>
                <div className="flex items-start justify-between">
                  <h3 className="font-display text-lg text-forest-dark">{selected.name}</h3>
                  <button onClick={() => setSelected(null)} className="text-ink-soft hover:text-ink">
                    <X className="h-4 w-4" />
                  </button>
                </div>
                <StatusBadge level={selected.healthStatus} className="mt-2" />
                <dl className="mt-4 space-y-2 text-sm">
                  <Row label="Crop" value={selected.crop} />
                  <Row label="Health" value={selected.healthStatus} />
                  <Row label="Last scan" value={formatRelativeTime(selected.lastScanAt)} />
                  <Row label="Disease" value={selected.lastDisease ?? "None detected"} />
                  <Row label="Risk" value={selected.lastRisk ?? "—"} />
                </dl>
                <a href={`/fields/${selected.id}`} className="btn-primary mt-5 w-full">
                  Open Field
                </a>
              </>
            ) : fields.length > 0 ? (
              <p className="text-sm text-ink-soft">Tap a marker to see field details.</p>
            ) : (
              <p className="text-sm text-ink-soft">Add a field to see it here.</p>
            )}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between border-b border-line pb-2">
      <dt className="text-ink-soft">{label}</dt>
      <dd className="font-medium capitalize text-ink">{value}</dd>
    </div>
  );
}
