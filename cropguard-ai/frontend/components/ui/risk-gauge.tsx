import type { RiskLevel } from "@/types";
import { cn } from "@/lib/utils";

const COLORS: Record<RiskLevel, string> = {
  healthy: "#4C7A3F",
  moderate: "#DFA23C",
  high: "#B4432E",
};

const LABELS: Record<RiskLevel, string> = {
  healthy: "LOW",
  moderate: "MEDIUM",
  high: "HIGH",
};

export function RiskGauge({ level, score }: { level: RiskLevel; score: number }) {
  const radius = 54;
  const circumference = Math.PI * radius; // half circle
  const offset = circumference * (1 - score / 100);
  const color = COLORS[level];

  return (
    <div className="flex flex-col items-center">
      <svg width="140" height="80" viewBox="0 0 140 80">
        <path
          d="M 10 74 A 60 60 0 0 1 130 74"
          fill="none"
          stroke="#DAE2CD"
          strokeWidth="12"
          strokeLinecap="round"
        />
        <path
          d="M 10 74 A 60 60 0 0 1 130 74"
          fill="none"
          stroke={color}
          strokeWidth="12"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          style={{ transition: "stroke-dashoffset 0.6s ease" }}
        />
      </svg>
      <div className="-mt-6 text-center">
        <div className="font-mono text-2xl font-semibold" style={{ color }}>
          {score}
        </div>
        <div
          className={cn("eyebrow")}
          style={{ color }}
        >
          {LABELS[level]}
        </div>
      </div>
    </div>
  );
}
