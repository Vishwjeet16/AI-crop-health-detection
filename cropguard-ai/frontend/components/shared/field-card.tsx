import Link from "next/link";
import { ArrowRight, Bug, Ruler } from "lucide-react";
import type { Field } from "@/types";
import { StatusBadge } from "@/components/ui/status-badge";
import { formatRelativeTime } from "@/lib/utils";

export function FieldCard({ field }: { field: Field }) {
  return (
    <div className="card flex flex-col gap-4 p-5">
      <div className="flex items-start justify-between">
        <div>
          <h3 className="font-display text-lg text-forest-dark">{field.name}</h3>
          <p className="text-sm text-ink-soft">{field.crop}</p>
        </div>
        <StatusBadge level={field.healthStatus} />
      </div>

      <div className="flex flex-wrap gap-x-5 gap-y-1.5 text-sm text-ink-soft">
        <span className="flex items-center gap-1.5">
          <Ruler className="h-3.5 w-3.5" /> {field.areaAcres} acres
        </span>
        <span className="flex items-center gap-1.5">
          <Bug className="h-3.5 w-3.5" /> {field.lastDisease ?? "No issues detected"}
        </span>
      </div>

      <div className="flex items-center justify-between border-t border-line pt-3">
        <span className="text-xs text-ink-soft">
          Last scan: {formatRelativeTime(field.lastScanAt)}
        </span>
        <Link
          href={`/fields/${field.id}`}
          className="flex items-center gap-1 text-sm font-semibold text-growth hover:text-growth-dark"
        >
          View Field <ArrowRight className="h-3.5 w-3.5" />
        </Link>
      </div>
    </div>
  );
}
