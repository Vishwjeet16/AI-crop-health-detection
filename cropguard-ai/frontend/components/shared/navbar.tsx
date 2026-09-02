import Link from "next/link";
import { Logo } from "./logo";

const LINKS = [
  { href: "#how-it-works", label: "How It Works" },
  { href: "#features", label: "AI Features" },
  { href: "#why", label: "Why CropGuard" },
];

export function Navbar() {
  return (
    <header className="sticky top-0 z-40 border-b border-line bg-bg/90 backdrop-blur">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
        <Logo />
        <nav className="hidden items-center gap-8 md:flex">
          {LINKS.map((l) => (
            <a
              key={l.href}
              href={l.href}
              className="text-sm font-medium text-ink-soft transition-colors hover:text-forest"
            >
              {l.label}
            </a>
          ))}
        </nav>
        <div className="flex items-center gap-3">
          <Link href="/login" className="btn-ghost hidden sm:inline-flex">
            Log in
          </Link>
          <Link href="/register" className="btn-primary">
            Get Started
          </Link>
        </div>
      </div>
    </header>
  );
}
