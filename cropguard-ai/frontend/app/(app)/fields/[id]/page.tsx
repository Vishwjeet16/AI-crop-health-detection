"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ScanLine, History, Ruler, MapPin, Loader2 } from "lucide-react";
import { Topbar } from "@/components/shared/topbar";
import { StatusBadge } from "@/components/ui/status-badge";
import { WeatherCard } from "@/components/shared/weather-card";
import { ErrorState } from "@/components/shared/states";
import { getField } from "@/lib/api/fields";
import { getScan } from "@/lib/api/scans";
import { ApiError } from "@/lib/api/client";
import { formatRelativeTime } from "@/lib/utils";
import type { Field, Scan } from "@/types";

export default function FieldDetailPage({ params }: { params: { id: string } }) {
  const [field, setField] = useState<Field | null>(null);
  const [scan, setScan] = useState<Scan | null>(null);
  const [error, setError] = useState<string | null>(null);

  function load() {
    setError(null);
    setField(null);
    getField(params.id)
      .then((f) => {
        setField(f);
        return getScan("scan-001").catch(() => null); // latest demo scan for weather context
      })
      .then(setScan)
      .catch((err) => {
        setError(err instanceof ApiError ? err.message : "We couldn't load this field.");
      });
  }

  useEffect(load, [params.id]);

  if (error) {
    return (
      <div>
        <Topbar title="Field" />
        <main className="px-5 py-8 md:px-8">
          <ErrorState title="Field not found" message={error} actionLabel="Try Again" onAction={load} />
        </main>
      </div>
    );
  }

  if (!field) {
    return (
      <div>
        <Topbar title="Field" />
        <main className="flex justify-center px-5 py-16">
          <Loader2 className="h-6 w-6 animate-spin text-growth" />
        </main>
      </div>
    );
  }

  return (
    <div>
      <Topbar title={field.name} />
      <main className="px-5 py-8 md:px-8">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <div className="flex items-center gap-3">
              <h2 className="font-display text-2xl text-forest-dark">{field.name}</h2>
              <StatusBadge level={field.healthStatus} />
            </div>
            <div className="mt-2 flex flex-wrap gap-x-5 gap-y-1 text-sm text-ink-soft">
              <span>{field.crop}</span>
              <span className="flex items-center gap-1"><Ruler className="h-3.5 w-3.5" /> {field.areaAcres} acres</span>
              <span className="flex items-center gap-1"><MapPin className="h-3.5 w-3.5" /> {field.latitude.toFixed(4)}, {field.longitude.toFixed(4)}</span>
            </div>
          </div>
          <div className="flex gap-3">
            <Link href={`/fields/${field.id}/history`} className="btn-secondary">
              <History className="h-4 w-4" /> View History
            </Link>
            <Link href="/scan" className="btn-primary">
              <ScanLine className="h-4 w-4" /> Scan This Field
            </Link>
          </div>
        </div>

        <div className="mt-8 grid gap-6 lg:grid-cols-3">
          <div className="lg:col-span-2 space-y-6">
            <div className="card p-5">
              <h3 className="font-display text-lg text-forest-dark">Latest Scan</h3>
              <p className="mt-1 text-sm text-ink-soft">{formatRelativeTime(field.lastScanAt)}</p>
              {field.lastDisease ? (
                <div className="mt-4 flex items-center justify-between rounded-md bg-bg-alt px-4 py-3">
                  <div>
                    <div className="font-semibold text-ink">{field.lastDisease}</div>
                    <div className="text-xs text-ink-soft">Detected in most recent scan</div>
                  </div>
                  {scan && (
                    <Link href={`/scan/result/${scan.id}`} className="text-sm font-semibold text-growth hover:text-growth-dark">
                      View Details
                    </Link>
                  )}
                </div>
              ) : (
                <p className="mt-4 text-sm text-ink-soft">No issues detected in the most recent scan.</p>
              )}
            </div>
            {scan && <WeatherCard weather={scan.weather} />}
          </div>

          <div className="card p-5">
            <h3 className="font-display text-lg text-forest-dark">Field Notes</h3>
            <p className="mt-2 text-sm text-ink-soft">
              Keep scanning regularly to build a reliable health history for this field. More
              scans improve the accuracy of trend classification over time.
            </p>
          </div>
        </div>
      </main>
    </div>
  );
}
