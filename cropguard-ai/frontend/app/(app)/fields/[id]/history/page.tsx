"use client";

import { useEffect, useState } from "react";
import { Loader2 } from "lucide-react";
import { Topbar } from "@/components/shared/topbar";
import { HistoryChart } from "@/components/shared/history-chart";
import { SeverityBadge } from "@/components/ui/severity-badge";
import { StatusBadge } from "@/components/ui/status-badge";
import { ErrorState } from "@/components/shared/states";
import { getField } from "@/lib/api/fields";
import { getFieldHistory } from "@/lib/api/scans";
import type { Field, HistoryPoint } from "@/types";

export default function FieldHistoryPage({ params }: { params: { id: string } }) {
  const [field, setField] = useState<Field | null>(null);
  const [history, setHistory] = useState<HistoryPoint[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  function load() {
    setError(null);
    setField(null);
    setHistory(null);
    Promise.all([getField(params.id), getFieldHistory(params.id)])
      .then(([f, h]) => {
        setField(f);
        setHistory(h);
      })
      .catch(() => setError("We couldn't load this field's history."));
  }

  useEffect(load, [params.id]);

  if (error) {
    return (
      <div>
        <Topbar title="Field History" />
        <main className="px-5 py-8 md:px-8">
          <ErrorState message={error} actionLabel="Try Again" onAction={load} />
        </main>
      </div>
    );
  }

  if (!field || !history) {
    return (
      <div>
        <Topbar title="Field History" />
        <main className="flex justify-center px-5 py-16">
          <Loader2 className="h-6 w-6 animate-spin text-growth" />
        </main>
      </div>
    );
  }

  return (
    <div>
      <Topbar title={`${field.name} — History`} />
      <main className="px-5 py-8 md:px-8">
        <HistoryChart points={history} />

        <div className="card mt-6 overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-line text-left text-ink-soft">
                <th className="px-5 py-3 font-medium">Date</th>
                <th className="px-5 py-3 font-medium">Disease</th>
                <th className="px-5 py-3 font-medium">Severity</th>
                <th className="px-5 py-3 font-medium">Affected Area</th>
                <th className="px-5 py-3 font-medium">Risk</th>
              </tr>
            </thead>
            <tbody>
              {history.map((h) => (
                <tr key={h.date} className="border-b border-line last:border-0">
                  <td className="px-5 py-3 font-mono text-ink-soft">{h.date}</td>
                  <td className="px-5 py-3">{field.lastDisease ?? "—"}</td>
                  <td className="px-5 py-3"><SeverityBadge level={h.severity} /></td>
                  <td className="px-5 py-3 font-mono">{h.affectedAreaPercent}%</td>
                  <td className="px-5 py-3"><StatusBadge level={h.risk} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </main>
    </div>
  );
}
