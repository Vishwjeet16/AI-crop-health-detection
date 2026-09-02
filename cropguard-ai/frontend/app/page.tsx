import Link from "next/link";
import {
  ScanLine,
  Bug,
  Leaf,
  Gauge,
  BellRing,
  ShieldCheck,
  Camera,
  Cpu,
  ClipboardCheck,
  Sprout,
  CloudSun,
  Map,
  BarChart3,
} from "lucide-react";
import { Navbar } from "@/components/shared/navbar";
import { LANGUAGE_CODES } from "@/lib/i18n";

const STEPS = [
  { icon: Camera, title: "Capture", copy: "Photograph a crop leaf or affected area with your phone." },
  { icon: Cpu, title: "Analyze", copy: "The AI pipeline preprocesses and scans the image." },
  { icon: Bug, title: "Detect", copy: "Pests, disease and damage are identified with a confidence score." },
  { icon: Gauge, title: "Assess", copy: "Severity and field risk are calculated from detection and weather." },
  { icon: ClipboardCheck, title: "Act", copy: "You get clear, evidence-aligned next steps for the field." },
];

const FEATURES = [
  { icon: Bug, title: "Disease Detection", copy: "Identify common crop diseases from a single photo." },
  { icon: Leaf, title: "Pest Detection", copy: "Spot pest damage patterns before they spread." },
  { icon: ScanLine, title: "Damage Detection", copy: "Localize affected regions with bounding boxes." },
  { icon: Gauge, title: "Severity Estimation", copy: "Get a severity level and estimated affected area." },
  { icon: BarChart3, title: "Risk Prediction", copy: "Combine detection with weather and history for a risk score." },
  { icon: BellRing, title: "Smart Alerts", copy: "Get notified when a field's risk crosses a threshold." },
];

const WHY = [
  "Catch problems days before they're visible to the eye.",
  "Move from photo to guidance in minutes, not a field visit later.",
  "Track every field's health from one dashboard.",
  "Decisions grounded in detection data, not guesswork.",
  "Built for farmers first — simple, clear, no jargon.",
];

const TECH = [
  { icon: Cpu, label: "Computer Vision AI" },
  { icon: CloudSun, label: "Weather Data" },
  { icon: Map, label: "Field Monitoring" },
  { icon: BarChart3, label: "Risk Analytics" },
];

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-bg">
      <Navbar />

      {/* HERO */}
      <section className="mx-auto grid max-w-6xl items-center gap-12 px-6 py-16 md:grid-cols-2 md:py-24">
        <div>
          <span className="eyebrow">Smart India Hackathon · AgriTech</span>
          <h1 className="mt-3 font-display text-4xl leading-tight text-forest-dark md:text-5xl">
            Detect Crop Problems Before They Become{" "}
            <span className="italic text-growth">Crop Loss</span>.
          </h1>
          <p className="mt-5 max-w-md text-lg text-ink-soft">
            AI-powered early detection of crop diseases, pests and damage for
            smarter and faster farm management.
          </p>
          <div className="mt-8 flex flex-wrap gap-3">
            <Link href="/scan" className="btn-primary">
              <ScanLine className="h-4 w-4" /> Scan Your Crop
            </Link>
            <Link href="/dashboard" className="btn-secondary">
              Explore Dashboard
            </Link>
          </div>
        </div>

        {/* Signature scan-bracket visual: Farmer -> Crop -> AI Scan -> Detection -> Recommendation */}
        <div className="scan-frame rounded-lg border border-line bg-forest p-8 text-white">
          <span className="corner-tl" />
          <span className="corner-br" />
          <div className="flex flex-col gap-5">
            {[
              { icon: Sprout, label: "Farmer photographs the crop" },
              { icon: ScanLine, label: "AI scans the image" },
              { icon: Bug, label: "Disease / pest is detected" },
              { icon: ClipboardCheck, label: "Guidance is generated" },
            ].map((step, i, arr) => (
              <div key={step.label} className="flex items-center gap-4">
                <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-white/10">
                  <step.icon className="h-5 w-5 text-marigold-light" />
                </span>
                <span className="text-sm text-white/90">{step.label}</span>
                {i < arr.length - 1 && (
                  <span className="ml-auto hidden h-px flex-1 bg-white/15 sm:block" />
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* HOW IT WORKS */}
      <section id="how-it-works" className="border-y border-line bg-paper py-20">
        <div className="mx-auto max-w-6xl px-6">
          <h2 className="font-display text-3xl text-forest-dark">How It Works</h2>
          <div className="mt-10 grid gap-6 sm:grid-cols-2 lg:grid-cols-5">
            {STEPS.map((s, i) => (
              <div key={s.title} className="relative">
                <span className="font-mono text-xs text-marigold-dark">0{i + 1}</span>
                <span className="mt-2 flex h-11 w-11 items-center justify-center rounded-md bg-bg-alt text-forest">
                  <s.icon className="h-5 w-5" />
                </span>
                <h3 className="mt-3 font-semibold text-ink">{s.title}</h3>
                <p className="mt-1 text-sm text-ink-soft">{s.copy}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* AI FEATURES */}
      <section id="features" className="py-20">
        <div className="mx-auto max-w-6xl px-6">
          <h2 className="font-display text-3xl text-forest-dark">AI Features</h2>
          <div className="mt-10 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
            {FEATURES.map((f) => (
              <div key={f.title} className="card p-5">
                <span className="flex h-10 w-10 items-center justify-center rounded-md bg-growth-light/40 text-growth-dark">
                  <f.icon className="h-5 w-5" />
                </span>
                <h3 className="mt-3 font-semibold text-ink">{f.title}</h3>
                <p className="mt-1 text-sm text-ink-soft">{f.copy}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* WHY CROPGUARD */}
      <section id="why" className="border-y border-line bg-forest-dark py-20 text-white">
        <div className="mx-auto max-w-6xl px-6">
          <h2 className="font-display text-3xl">Why CropGuard?</h2>
          <ul className="mt-8 grid gap-4 sm:grid-cols-2">
            {WHY.map((w) => (
              <li key={w} className="flex items-start gap-3 text-white/90">
                <ShieldCheck className="mt-0.5 h-[18px] w-[18px] shrink-0 text-marigold-light" />
                {w}
              </li>
            ))}
          </ul>
        </div>
      </section>

      {/* TECHNOLOGY */}
      <section className="py-16">
        <div className="mx-auto max-w-6xl px-6">
          <span className="eyebrow">Under the hood</span>
          <div className="mt-6 flex flex-wrap gap-6">
            {TECH.map((t) => (
              <span key={t.label} className="flex items-center gap-2 text-ink-soft">
                <t.icon className="h-[18px] w-[18px] text-growth" /> {t.label}
              </span>
            ))}
          </div>
        </div>
      </section>

      {/* IMPACT (demo values, clearly labeled) */}
      <section className="border-t border-line bg-paper py-16">
        <div className="mx-auto max-w-6xl px-6">
          <div className="flex items-center justify-between">
            <h2 className="font-display text-2xl text-forest-dark">Prototype Impact</h2>
            <span className="rounded-full bg-marigold-light/40 px-3 py-1 font-mono text-xs uppercase text-marigold-dark">
              Demo values
            </span>
          </div>
          <div className="mt-8 grid gap-6 sm:grid-cols-3">
            {[
              ["14", "crop diseases the detector is trained on"],
              ["<3 min", "target time from photo to recommendation"],
              // Read from the registry so this can't go stale the way "2" did.
              [String(LANGUAGE_CODES.length), "languages, including the AI assistant"],
            ].map(([num, label]) => (
              <div key={label} className="card p-6 text-center">
                <div className="font-mono text-3xl font-semibold text-forest">{num}</div>
                <div className="mt-1 text-sm text-ink-soft">{label}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="bg-growth py-16 text-center text-white">
        <h2 className="font-display text-3xl">Start Protecting Your Crops Today.</h2>
        <Link href="/register" className="btn-secondary mt-6 inline-flex border-white text-white hover:bg-white hover:text-growth-dark">
          Create Free Account
        </Link>
      </section>

      <footer className="bg-forest-dark py-8 text-center text-sm text-white/60">
        CropGuard AI · Built for Smart India Hackathon — Early Detection and Management of Crop Damage and Pest Infestation
      </footer>
    </div>
  );
}
