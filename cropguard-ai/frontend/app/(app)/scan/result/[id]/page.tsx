"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Save, Bug, Loader2, Check } from "lucide-react";
import { Topbar } from "@/components/shared/topbar";
import { DetectionResult } from "@/components/shared/detection-result";
import { SeverityBadge } from "@/components/ui/severity-badge";
import { RiskGauge } from "@/components/ui/risk-gauge";
import { WeatherCard } from "@/components/shared/weather-card";
import { RecommendationCard } from "@/components/shared/recommendation-card";
import { ErrorState } from "@/components/shared/states";
import { getScan, saveScan } from "@/lib/api/scans";
import type { Scan } from "@/types";

export default function ScanResultPage({ params }: { params: { id: string } }) {
  const [scan, setScan] = useState<Scan | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  function load() {
    setError(null);
    setScan(null);
    getScan(params.id).catch(() => null).then((s) => {
      if (s) setScan(s);
      else setError("We couldn't find this scan. It may have expired.");
    });
  }

  useEffect(load, [params.id]);

  async function handleSave() {
    if (!scan) return;
    setSaving(true);
    try {
      await saveScan(scan);
      setSaved(true);
    } finally {
      setSaving(false);
    }
  }

  if (error) {
    return (
      <div>
        <Topbar title="Scan Result" />
        <main className="px-5 py-8 md:px-8">
          <ErrorState title="Scan not found" message={error} />
        </main>
      </div>
    );
  }

  if (!scan) {
    return (
      <div>
        <Topbar title="Scan Result" />
        <main className="flex justify-center px-5 py-16">
          <Loader2 className="h-6 w-6 animate-spin text-growth" />
        </main>
      </div>
    );
  }

  const topDetection = scan.detections[0];
  const lowConfidence = topDetection && topDetection.confidence < 0.6;

  return (
    <div>
      <Topbar title="Scan Result" />
      <main className="px-5 py-8 md:px-8">
        <div className="grid gap-6 lg:grid-cols-3">
          <div className="space-y-6 lg:col-span-2">
            <DetectionResult
              imageUrl={scan.imageUrl}
              detections={scan.detections}
              isDemo={scan.isDemo}
            />

            {topDetection ? (
              <div className="card p-5">
                <span className="eyebrow">Detection Result</span>
                <div className="mt-2 flex flex-wrap items-center justify-between gap-3">
                  <div className="flex items-center gap-3">
                    <span className="flex h-11 w-11 items-center justify-center rounded-md bg-rust-light/40 text-rust-dark">
                      <Bug className="h-5 w-5" />
                    </span>
                    <div>
                      <h2 className="font-display text-xl text-forest-dark">{topDetection.label}</h2>
                      <p className="text-sm text-ink-soft">{scan.crop} · {Math.round(topDetection.confidence * 100)}% confidence</p>
                    </div>
                  </div>
                  <SeverityBadge level={scan.severity.level} />
                </div>
                {lowConfidence && (
                  <p className="mt-4 rounded-md bg-marigold-light/30 px-4 py-3 text-sm text-marigold-dark">
                    The AI is not confident enough. Please capture a clearer image or consult an
                    agricultural expert.
                  </p>
                )}
                <p className="mt-4 text-sm text-ink-soft">
                  Estimated affected area:{" "}
                  <span className="font-mono font-semibold text-ink">{scan.severity.affectedAreaPercent}%</span>
                  {scan.severity.isDemo && (
                    <span className="ml-2 rounded-full bg-marigold-light/40 px-2 py-0.5 font-mono text-[11px] uppercase text-marigold-dark">
                      Demo estimate
                    </span>
                  )}
                </p>
              </div>
            ) : (
              <div className="card p-5 text-sm text-ink-soft">
                No crop, pest, or disease could be confidently identified in this image.
              </div>
            )}

            <RecommendationCard recommendation={scan.recommendation} />
          </div>

          <div className="space-y-6">
            <div className="card flex flex-col items-center p-5">
              <span className="eyebrow self-start">Crop Risk</span>
              <RiskGauge level={scan.risk.level} score={scan.risk.score} />
              <ul className="mt-3 w-full space-y-1 text-xs text-ink-soft">
                {scan.risk.factors.map((f) => (
                  <li key={f}>• {f}</li>
                ))}
              </ul>
            </div>

            <WeatherCard weather={scan.weather} />

            <div className="flex gap-3">
              <button className="btn-primary flex-1" onClick={handleSave} disabled={saving || saved}>
                {saving ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : saved ? (
                  <Check className="h-4 w-4" />
                ) : (
                  <Save className="h-4 w-4" />
                )}
                {saved ? "Saved to History" : saving ? "Saving…" : "Save to History"}
              </button>
              <Link href="/scan" className="btn-secondary flex-1">
                Scan Again
              </Link>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
