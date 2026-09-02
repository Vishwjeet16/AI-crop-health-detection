import Image from "next/image";
import type { Detection } from "@/types";

// bbox coords are treated as percentages of image width/height (0-100)
// so the overlay scales responsively regardless of source resolution.
export function DetectionResult({
  imageUrl,
  detections,
  isDemo,
}: {
  imageUrl: string;
  detections: Detection[];
  isDemo: boolean;
}) {
  return (
    <div className="scan-frame overflow-hidden rounded-lg border border-line bg-ink">
      <span className="corner-tl" />
      <span className="corner-br" />
      <div className="relative aspect-[4/3] w-full">
        <Image
          src={imageUrl}
          alt="Scanned crop with detected regions highlighted"
          fill
          className="object-cover opacity-90"
          unoptimized
        />
        {detections.map((d, i) => {
          const [x, y, w, h] = d.bbox;
          return (
            <div
              key={i}
              className="absolute border-2 border-marigold"
              style={{
                left: `${x}%`,
                top: `${y}%`,
                width: `${w}%`,
                height: `${h}%`,
              }}
            >
              <span className="absolute -top-7 left-0 whitespace-nowrap rounded-t-sm bg-marigold px-2 py-1 font-mono text-xs font-semibold text-forest-dark">
                {d.label} · {Math.round(d.confidence * 100)}%
              </span>
            </div>
          );
        })}
      </div>
      {isDemo && (
        <div className="bg-forest-dark px-4 py-2 text-center font-mono text-xs uppercase tracking-wide text-marigold-light">
          Demo Mode — results are simulated until a trained model is connected
        </div>
      )}
    </div>
  );
}
