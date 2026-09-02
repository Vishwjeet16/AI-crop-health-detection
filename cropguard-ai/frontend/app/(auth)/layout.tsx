import { Logo } from "@/components/shared/logo";
import { Sprout, ScanLine, Bug } from "lucide-react";

export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="grid min-h-screen md:grid-cols-2">
      <div className="flex flex-col justify-between bg-forest px-8 py-10 text-white md:px-14">
        <Logo />
        <div className="max-w-sm">
          <h2 className="font-display text-3xl leading-snug">
            Detect Early. Act Smart. Protect Every Crop.
          </h2>
          <ul className="mt-8 space-y-4 text-white/85">
            <li className="flex items-center gap-3">
              <Sprout className="h-5 w-5 text-marigold-light" /> Track every field in one place
            </li>
            <li className="flex items-center gap-3">
              <ScanLine className="h-5 w-5 text-marigold-light" /> Scan crops in seconds
            </li>
            <li className="flex items-center gap-3">
              <Bug className="h-5 w-5 text-marigold-light" /> Catch disease before it spreads
            </li>
          </ul>
        </div>
        <p className="text-xs text-white/50">Built for Smart India Hackathon</p>
      </div>
      <div className="flex items-center justify-center bg-bg px-6 py-14">
        <div className="w-full max-w-sm">{children}</div>
      </div>
    </div>
  );
}
