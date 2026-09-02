"use client";

import { Bell, Menu, User } from "lucide-react";
import Link from "next/link";
import { useAuth } from "@/context/auth-context";

export function Topbar({ title }: { title?: string }) {
  const { user } = useAuth();

  return (
    <header className="flex items-center justify-between border-b border-line bg-paper px-5 py-4 md:px-8">
      <div className="flex items-center gap-3">
        <button className="rounded-md p-2 hover:bg-bg-alt md:hidden" aria-label="Open menu">
          <Menu className="h-5 w-5" />
        </button>
        {title && <h1 className="font-display text-xl text-forest-dark">{title}</h1>}
      </div>
      <div className="flex items-center gap-4">
        <Link href="/alerts" className="rounded-md p-2 hover:bg-bg-alt" aria-label="Alerts">
          <Bell className="h-5 w-5 text-ink-soft" />
        </Link>
        <div className="flex items-center gap-2">
          <span className="flex h-8 w-8 items-center justify-center rounded-full bg-bg-alt">
            <User className="h-4 w-4 text-forest" />
          </span>
          <span className="hidden text-sm font-medium sm:inline">{user?.name ?? "Farmer"}</span>
        </div>
      </div>
    </header>
  );
}
