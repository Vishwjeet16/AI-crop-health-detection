import { cn } from "@/lib/utils";
import type { SeverityLevel } from "@/types";

const CONFIG: Record<SeverityLevel, { label: string; className: string }> = {
  low: { label: "Low", className: "bg-growth-light/40 text-growth-dark" },
  moderate: { label: "Moderate", className: "bg-marigold-light/50 text-marigold-dark" },
  high: { label: "High", className: "bg-rust-light/50 text-rust-dark" },
  critical: { label: "Critical", className: "bg-rust text-white" },
};

export function SeverityBadge({ level }: { level: SeverityLevel }) {
  const c = CONFIG[level];
  return (
    <span className={cn("badge", c.className)}>
      {c.label} severity
    </span>
  );
}
