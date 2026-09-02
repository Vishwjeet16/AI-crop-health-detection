"use client";

import { useEffect, useState } from "react";
import { Sprout, ShieldCheck, AlertTriangle, BellRing } from "lucide-react";
import { Topbar } from "@/components/shared/topbar";
import { DashboardCard } from "@/components/shared/dashboard-card";
import { FieldCard } from "@/components/shared/field-card";
import { AlertCard } from "@/components/shared/alert-card";
import { FieldCardSkeleton } from "@/components/shared/skeleton";
import { ErrorState, EmptyState } from "@/components/shared/states";
import { useAuth } from "@/context/auth-context";
import { listFields } from "@/lib/api/fields";
import { listAlerts, markAlertRead } from "@/lib/api/alerts";
import type { Alert, Field } from "@/types";

export default function DashboardPage() {
  const { user } = useAuth();
  const [fields, setFields] = useState<Field[] | null>(null);
  const [alerts, setAlerts] = useState<Alert[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    setError(null);
    setFields(null);
    setAlerts(null);
    try {
      const [f, a] = await Promise.all([listFields(), listAlerts()]);
      setFields(f);
      setAlerts(a);
    } catch {
      setError("We couldn't load your dashboard. Check your connection and try again.");
    }
  }

  useEffect(() => {
    load();
  }, []);

  function handleMarkRead(id: string) {
    setAlerts((prev) => prev?.map((a) => (a.id === id ? { ...a, read: true } : a)) ?? null);
    markAlertRead(id).catch(() => load());
  }

  if (error) {
    return (
      <div>
        <Topbar />
        <main className="px-5 py-8 md:px-8">
          <ErrorState message={error} actionLabel="Try Again" onAction={load} />
        </main>
      </div>
    );
  }

  const stats = fields && alerts
    ? {
        totalFields: fields.length,
        healthyFields: fields.filter((f) => f.healthStatus === "healthy").length,
        atRiskFields: fields.filter((f) => f.healthStatus !== "healthy").length,
        activeAlerts: alerts.filter((a) => !a.read).length,
      }
    : null;

  return (
    <div>
      <Topbar />
      <main className="px-5 py-8 md:px-8">
        <h1 className="font-display text-2xl text-forest-dark">
          Good Morning, {user?.name.split(" ")[0] ?? "Farmer"} 👋
        </h1>
        <p className="mt-1 text-sm text-ink-soft">Here's what's happening across your farm today.</p>

        <div className="mt-6 grid grid-cols-2 gap-4 lg:grid-cols-4">
          {stats ? (
            <>
              <DashboardCard label="Total Fields" value={stats.totalFields} icon={Sprout} />
              <DashboardCard label="Healthy Fields" value={stats.healthyFields} icon={ShieldCheck} tone="growth" />
              <DashboardCard label="Fields at Risk" value={stats.atRiskFields} icon={AlertTriangle} tone="marigold" />
              <DashboardCard label="Active Alerts" value={stats.activeAlerts} icon={BellRing} tone="rust" />
            </>
          ) : (
            Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="card h-[76px] animate-pulse bg-bg-alt/60" />
            ))
          )}
        </div>

        <div className="mt-10 flex items-center justify-between">
          <h2 className="font-display text-xl text-forest-dark">Your Fields</h2>
          <a href="/fields/new" className="text-sm font-semibold text-growth hover:text-growth-dark">
            + Add Field
          </a>
        </div>
        <div className="mt-4 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {fields
            ? fields.length > 0
              ? fields.map((f) => <FieldCard key={f.id} field={f} />)
              : (
                <div className="sm:col-span-2 lg:col-span-3">
                  <EmptyState
                    title="No fields yet"
                    message="Add your first field to start scanning crops and tracking health over time."
                    actionLabel="Add Field"
                  />
                </div>
              )
            : Array.from({ length: 3 }).map((_, i) => <FieldCardSkeleton key={i} />)}
        </div>

        <div className="mt-10">
          <h2 className="font-display text-xl text-forest-dark">Recent Alerts</h2>
          <div className="mt-4 space-y-3">
            {alerts
              ? alerts.slice(0, 2).map((a) => (
                  <AlertCard key={a.id} alert={a} onMarkRead={handleMarkRead} />
                ))
              : Array.from({ length: 2 }).map((_, i) => (
                  <div key={i} className="card h-[68px] animate-pulse bg-bg-alt/60" />
                ))}
          </div>
        </div>
      </main>
    </div>
  );
}
