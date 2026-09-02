import { AlertOctagon, Inbox } from "lucide-react";
import type { LucideIcon } from "lucide-react";

export function ErrorState({
  title = "Something went wrong",
  message,
  actionLabel,
  onAction,
}: {
  title?: string;
  message: string;
  actionLabel?: string;
  onAction?: () => void;
}) {
  return (
    <div className="flex flex-col items-center gap-3 rounded-lg border border-rust-light bg-rust-light/10 px-6 py-10 text-center">
      <AlertOctagon className="h-8 w-8 text-rust" />
      <h3 className="font-display text-lg text-rust-dark">{title}</h3>
      <p className="max-w-sm text-sm text-ink-soft">{message}</p>
      {actionLabel && (
        <button onClick={onAction} className="btn-secondary mt-2">
          {actionLabel}
        </button>
      )}
    </div>
  );
}

export function EmptyState({
  icon: Icon = Inbox,
  title,
  message,
  actionLabel,
  onAction,
}: {
  icon?: LucideIcon;
  title: string;
  message: string;
  actionLabel?: string;
  onAction?: () => void;
}) {
  return (
    <div className="flex flex-col items-center gap-3 rounded-lg border border-dashed border-line px-6 py-14 text-center">
      <span className="flex h-12 w-12 items-center justify-center rounded-full bg-bg-alt text-forest">
        <Icon className="h-5 w-5" />
      </span>
      <h3 className="font-display text-lg text-forest-dark">{title}</h3>
      <p className="max-w-sm text-sm text-ink-soft">{message}</p>
      {actionLabel && (
        <button onClick={onAction} className="btn-primary mt-2">
          {actionLabel}
        </button>
      )}
    </div>
  );
}
