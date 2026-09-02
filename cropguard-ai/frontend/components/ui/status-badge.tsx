import { cn } from "@/lib/utils";
import type { RiskLevel } from "@/types";

const CONFIG: Record<RiskLevel, { label: string; dot: string; className: string }> = {
  healthy: { label: "Healthy", dot: "bg-growth", className: "badge-healthy" },
  moderate: { label: "Moderate Risk", dot: "bg-marigold", className: "badge-moderate" },
  high: { label: "High Risk", dot: "bg-rust", className: "badge-high" },
};

export function StatusBadge({ level, className }: { level: RiskLevel; className?: string }) {
  const c = CONFIG[level];
  return (
    <span className={cn(c.className, className)}>
      <span className={cn("h-1.5 w-1.5 rounded-full", c.dot)} />
      {c.label}
    </span>
  );
}
