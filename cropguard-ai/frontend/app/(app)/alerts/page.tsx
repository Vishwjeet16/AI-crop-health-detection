"use client";

import { useEffect, useState } from "react";
import { BellOff } from "lucide-react";
import { Topbar } from "@/components/shared/topbar";
import { AlertCard } from "@/components/shared/alert-card";
import { EmptyState, ErrorState } from "@/components/shared/states";
import { listAlerts, markAlertRead } from "@/lib/api/alerts";
import type { Alert } from "@/types";

export default function AlertsPage() {
  const [alerts, setAlerts] = useState<Alert[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  function load() {
    setError(null);
    setAlerts(null);
    listAlerts()
      .then(setAlerts)
      .catch(() => setError("We couldn't load your alerts. Please try again."));
  }

  useEffect(load, []);

  function markRead(id: string) {
    setAlerts((prev) => prev?.map((a) => (a.id === id ? { ...a, read: true } : a)) ?? null);
    markAlertRead(id).catch(() => load());
  }

  return (
    <div>
      <Topbar title="Alerts" />
      <main className="mx-auto max-w-2xl px-5 py-8 md:px-8">
        {error ? (
          <ErrorState message={error} actionLabel="Try Again" onAction={load} />
        ) : alerts ? (
          alerts.length > 0 ? (
            <div className="space-y-3">
              {alerts.map((a) => (
                <AlertCard key={a.id} alert={a} onMarkRead={markRead} />
              ))}
            </div>
          ) : (
            <EmptyState
              icon={BellOff}
              title="No alerts"
              message="You're all caught up. New alerts will appear here when a field's risk changes."
            />
          )
        ) : (
          <div className="space-y-3">
            {Array.from({ length: 3 }).map((_, i) => (
              <div key={i} className="card h-[68px] animate-pulse bg-bg-alt/60" />
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
