import type { LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";

export function DashboardCard({
  label,
  value,
  icon: Icon,
  tone = "default",
}: {
  label: string;
  value: string | number;
  icon: LucideIcon;
  tone?: "default" | "growth" | "marigold" | "rust";
}) {
  const toneClasses = {
    default: "bg-bg-alt text-forest",
    growth: "bg-growth-light/40 text-growth-dark",
    marigold: "bg-marigold-light/50 text-marigold-dark",
    rust: "bg-rust-light/50 text-rust-dark",
  }[tone];

  return (
    <div className="card flex items-center gap-4 p-5">
      <span className={cn("flex h-11 w-11 shrink-0 items-center justify-center rounded-md", toneClasses)}>
        <Icon className="h-5 w-5" strokeWidth={2} />
      </span>
      <div>
        <div className="font-mono text-2xl font-semibold text-ink">{value}</div>
        <div className="text-sm text-ink-soft">{label}</div>
      </div>
    </div>
  );
}
