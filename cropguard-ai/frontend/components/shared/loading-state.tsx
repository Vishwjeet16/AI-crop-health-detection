"use client";

import { useEffect, useState } from "react";
import { Check } from "lucide-react";

const STEPS = [
  "Image preprocessing",
  "Crop detection",
  "Pest/disease detection",
  "Severity estimation",
  "Risk analysis",
  "Recommendation generation",
];

export function LoadingState({ onComplete }: { onComplete?: () => void }) {
  const [activeStep, setActiveStep] = useState(0);

  useEffect(() => {
    if (activeStep >= STEPS.length) {
      const t = setTimeout(() => onComplete?.(), 400);
      return () => clearTimeout(t);
    }
    const t = setTimeout(() => setActiveStep((s) => s + 1), 550);
    return () => clearTimeout(t);
  }, [activeStep, onComplete]);

  return (
    <div className="scan-frame mx-auto max-w-md rounded-lg border border-line bg-paper p-8 text-center">
      <span className="corner-tl" />
      <span className="corner-br" />
      <div className="relative mx-auto mb-6 h-32 w-32 overflow-hidden rounded-md bg-forest">
        <div className="absolute inset-x-0 h-1 animate-scan-sweep bg-marigold shadow-[0_0_12px_2px_rgba(223,162,60,0.6)]" />
      </div>
      <h3 className="font-display text-lg text-forest-dark">AI is analyzing your crop…</h3>
      <ul className="mt-5 space-y-2.5 text-left">
        {STEPS.map((step, i) => (
          <li key={step} className="flex items-center gap-3 text-sm">
            <span
              className={`flex h-5 w-5 shrink-0 items-center justify-center rounded-full border text-[10px] ${
                i < activeStep
                  ? "border-growth bg-growth text-white"
                  : i === activeStep
                  ? "border-marigold text-marigold-dark"
                  : "border-line text-ink-soft/40"
              }`}
            >
              {i < activeStep ? <Check className="h-3 w-3" /> : i + 1}
            </span>
            <span className={i <= activeStep ? "text-ink" : "text-ink-soft/50"}>{step}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
