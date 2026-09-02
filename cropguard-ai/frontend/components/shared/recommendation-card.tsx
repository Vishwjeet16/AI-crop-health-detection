import { CheckCircle2, ShieldAlert, CalendarClock } from "lucide-react";
import type { Recommendation } from "@/types";

export function RecommendationCard({ recommendation }: { recommendation: Recommendation }) {
  return (
    <div className="card overflow-hidden">
      <div className="border-b border-line bg-growth-light/20 px-5 py-4">
        <span className="eyebrow">Recommended Action</span>
        <h3 className="font-display text-xl text-forest-dark">{recommendation.title}</h3>
      </div>
      <div className="space-y-5 p-5">
        <ul className="space-y-2">
          {recommendation.actions.map((a, i) => (
            <li key={i} className="flex gap-2 text-sm text-ink">
              <CheckCircle2 className="h-4 w-4 shrink-0 text-growth" />
              {a}
            </li>
          ))}
        </ul>

        <div>
          <h4 className="mb-2 text-sm font-semibold text-ink">Prevention</h4>
          <ul className="grid gap-1.5 sm:grid-cols-2">
            {recommendation.prevention.map((p, i) => (
              <li key={i} className="text-sm text-ink-soft">• {p}</li>
            ))}
          </ul>
        </div>

        <div className="flex items-center gap-2 rounded-md bg-bg-alt px-4 py-3 text-sm text-ink-soft">
          <CalendarClock className="h-4 w-4 shrink-0 text-forest" />
          {recommendation.nextScan}
        </div>

        <div className="flex items-start gap-2 rounded-md border border-marigold-light bg-marigold-light/20 px-4 py-3 text-xs text-marigold-dark">
          <ShieldAlert className="h-4 w-4 shrink-0" />
          <span>
            This guidance is AI-generated decision support, not a replacement for expert advice.
            For chemical control, confirm doses and products with ICAR, your local Krishi Vigyan
            Kendra (KVK), or state agriculture department before acting.
          </span>
        </div>
      </div>
    </div>
  );
}
