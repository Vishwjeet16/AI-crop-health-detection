"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  ScanLine,
  Map,
  Bell,
  Settings,
  Sprout,
  LogOut,
  MessageCircle,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Logo } from "./logo";
import { useAuth } from "@/context/auth-context";
import { useLanguage } from "@/context/language-context";
import { useEffect, useState } from "react";
import { listAlerts } from "@/lib/api/alerts";
import { LANGUAGE_CODES, SUPPORTED_LANGUAGES, type TranslationKey } from "@/lib/i18n";

// `labelKey` rather than a literal string: the sidebar is where the language is
// switched, so it was the one place that had to visibly respond to it.
const NAV: { href: string; labelKey: TranslationKey; icon: typeof LayoutDashboard }[] = [
  { href: "/dashboard", labelKey: "nav.dashboard", icon: LayoutDashboard },
  { href: "/fields", labelKey: "nav.fields", icon: Sprout },
  { href: "/scan", labelKey: "nav.scan", icon: ScanLine },
  { href: "/assistant", labelKey: "nav.assistant", icon: MessageCircle },
  { href: "/map", labelKey: "nav.map", icon: Map },
  { href: "/alerts", labelKey: "nav.alerts", icon: Bell },
  { href: "/settings", labelKey: "nav.settings", icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();
  const { logout } = useAuth();
  const { language, setLanguage, t } = useLanguage();
  const [unread, setUnread] = useState(0);

  useEffect(() => {
    listAlerts().then((alerts) => setUnread(alerts.filter((a) => !a.read).length));
  }, [pathname]);

  return (
    <aside className="hidden w-64 shrink-0 flex-col border-r border-line bg-paper md:flex">
      <div className="border-b border-line px-5 py-5">
        <Logo href="/dashboard" />
      </div>
      <nav className="flex-1 space-y-1 px-3 py-4">
        {NAV.map((item) => {
          const active =
            pathname === item.href || pathname?.startsWith(item.href + "/");
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center justify-between rounded-md px-3 py-2.5 text-sm font-medium transition-colors",
                active
                  ? "bg-forest text-white"
                  : "text-ink-soft hover:bg-bg-alt"
              )}
            >
              <span className="flex items-center gap-3">
                <item.icon className="h-[18px] w-[18px]" strokeWidth={2} />
                {t(item.labelKey)}
              </span>
              {item.href === "/alerts" && unread > 0 && (
                <span
                  className={cn(
                    "rounded-full px-1.5 py-0.5 text-[11px] font-mono",
                    active ? "bg-white/20 text-white" : "bg-rust text-white"
                  )}
                >
                  {unread}
                </span>
              )}
            </Link>
          );
        })}
      </nav>
      <div className="space-y-3 border-t border-line px-5 py-4">
        <div>
          <span className="eyebrow block mb-1.5">{t("settings.language")}</span>
          {/* Wraps: five languages don't fit on one row in a 256px sidebar.
              Driven by the i18n registry, so a sixth needs no change here. */}
          <div className="flex flex-wrap gap-1.5">
            {LANGUAGE_CODES.map((code) => (
              <button
                key={code}
                onClick={() => setLanguage(code)}
                aria-pressed={language === code}
                title={SUPPORTED_LANGUAGES[code].label}
                className={cn(
                  "rounded-md px-2.5 py-1 text-xs font-medium transition-colors",
                  language === code
                    ? "bg-forest text-white"
                    : "bg-bg-alt text-ink-soft hover:bg-bg-alt/70"
                )}
              >
                {SUPPORTED_LANGUAGES[code].short}
              </button>
            ))}
          </div>
        </div>
        <button
          onClick={logout}
          className="flex w-full items-center gap-2 rounded-md px-2 py-2 text-sm font-medium text-ink-soft hover:bg-bg-alt hover:text-rust"
        >
          <LogOut className="h-4 w-4" /> Log out
        </button>
      </div>
    </aside>
  );
}
