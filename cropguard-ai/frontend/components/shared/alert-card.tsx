"use client";

import { AlertTriangle, CheckCircle2, Info } from "lucide-react";
import type { Alert, RiskLevel } from "@/types";
import { formatRelativeTime } from "@/lib/utils";

const ICON: Record<RiskLevel, typeof AlertTriangle> = {
  high: AlertTriangle,
  moderate: Info,
  healthy: CheckCircle2,
};

const COLOR: Record<RiskLevel, string> = {
  high: "text-rust bg-rust-light/30",
  moderate: "text-marigold-dark bg-marigold-light/30",
  healthy: "text-growth-dark bg-growth-light/30",
};

export function AlertCard({
  alert,
  onMarkRead,
}: {
  alert: Alert;
  onMarkRead?: (id: string) => void;
}) {
  const Icon = ICON[alert.severity];
  return (
    <div className={`card flex items-start gap-4 p-4 ${alert.read ? "opacity-60" : ""}`}>
      <span className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-full ${COLOR[alert.severity]}`}>
        <Icon className="h-[18px] w-[18px]" />
      </span>
      <div className="flex-1">
        <p className="text-sm font-medium text-ink">{alert.message}</p>
        <p className="mt-0.5 text-xs text-ink-soft">
          {alert.fieldName} · {formatRelativeTime(alert.createdAt)}
        </p>
      </div>
      {!alert.read && (
        <button
          className="whitespace-nowrap text-xs font-semibold text-forest hover:text-growth"
          onClick={() => onMarkRead?.(alert.id)}
        >
          Mark as Read
        </button>
      )}
    </div>
  );
}
