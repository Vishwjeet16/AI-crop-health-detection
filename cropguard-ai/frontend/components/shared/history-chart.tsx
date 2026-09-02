"use client";

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import type { HistoryPoint, TrendType } from "@/types";
import { TrendingDown, TrendingUp, Minus, AlertTriangle } from "lucide-react";

const TREND_CONFIG: Record<TrendType, { label: string; icon: typeof Minus; className: string }> = {
  stable: { label: "Stable", icon: Minus, className: "text-ink-soft" },
  improving: { label: "Improving", icon: TrendingDown, className: "text-growth-dark" },
  slowly_spreading: { label: "Slowly Spreading", icon: TrendingUp, className: "text-marigold-dark" },
  rapidly_spreading: { label: "Rapidly Spreading", icon: AlertTriangle, className: "text-rust" },
};

function classifyTrend(points: HistoryPoint[]): TrendType {
  if (points.length < 2) return "stable";
  const first = points[0].affectedAreaPercent;
  const last = points[points.length - 1].affectedAreaPercent;
  const delta = last - first;
  const rate = delta / points.length;
  if (delta <= 0) return "improving";
  if (rate > 5) return "rapidly_spreading";
  if (rate > 1) return "slowly_spreading";
  return "stable";
}

export function HistoryChart({ points }: { points: HistoryPoint[] }) {
  const trend = classifyTrend(points);
  const T = TREND_CONFIG[trend];

  return (
    <div className="card p-5">
      <div className="mb-4 flex items-center justify-between">
        <div>
          <h3 className="font-display text-lg text-forest-dark">Disease Progression</h3>
          <p className="text-xs text-ink-soft">Estimated affected area over recent scans</p>
        </div>
        <span className={`flex items-center gap-1.5 text-sm font-semibold ${T.className}`}>
          <T.icon className="h-4 w-4" /> {T.label}
        </span>
      </div>
      <div className="h-56">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={points} margin={{ left: -20, right: 10 }}>
            <CartesianGrid stroke="#DAE2CD" strokeDasharray="3 3" />
            <XAxis dataKey="date" tick={{ fontSize: 12, fill: "#3D4F41" }} />
            <YAxis
              tick={{ fontSize: 12, fill: "#3D4F41" }}
              unit="%"
              domain={[0, "dataMax + 10"]}
            />
            <Tooltip
              formatter={(value: number) => [`${value}%`, "Affected area"]}
              contentStyle={{ borderRadius: 8, borderColor: "#DAE2CD" }}
            />
            <Line
              type="monotone"
              dataKey="affectedAreaPercent"
              stroke="#B4432E"
              strokeWidth={2.5}
              dot={{ r: 4, fill: "#B4432E" }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
      <p className="mt-3 text-xs text-ink-soft">
        Trend classification is an estimate based on recent scans, not a guaranteed forecast.
      </p>
    </div>
  );
}
