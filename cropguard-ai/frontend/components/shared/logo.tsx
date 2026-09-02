import { ScanLine } from "lucide-react";
import Link from "next/link";

export function Logo({ href = "/" }: { href?: string }) {
  return (
    <Link href={href} className="flex items-center gap-2 shrink-0">
      <span className="flex h-8 w-8 items-center justify-center rounded-md bg-forest text-white">
        <ScanLine className="h-[18px] w-[18px]" strokeWidth={2.25} />
      </span>
      <span className="font-display text-lg font-semibold tracking-tight text-forest-dark">
        CropGuard <span className="text-growth">AI</span>
      </span>
    </Link>
  );
}
