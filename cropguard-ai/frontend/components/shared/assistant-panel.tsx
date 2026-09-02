"use client";

import { useEffect, useRef, useState } from "react";
import { Loader2, MessageCircle, RotateCcw, Send, ShieldAlert, Sprout } from "lucide-react";
import { cn } from "@/lib/utils";
import { useLanguage } from "@/context/language-context";
import { ApiError } from "@/lib/api/client";
import {
  MAX_MESSAGE_CHARS,
  ask,
  getAssistantStatus,
  type AssistantTurn,
} from "@/lib/api/assistant";

interface Message extends AssistantTurn {
  /** Set on assistant turns the backend's safety scan replaced. */
  filtered?: boolean;
}

/**
 * The chat panel.
 *
 * Two deliberate choices worth knowing about:
 *
 * - Conversation state lives here, not on the server, and is sent back with
 *   each question. That keeps the backend stateless; the tradeoff is that a
 *   reload starts a new conversation, which is the right default for a shared
 *   phone.
 * - A filtered reply is styled as guidance, not as an error. It is the correct
 *   answer to "what should I spray?" — the assistant genuinely cannot answer
 *   that, and a red error box would suggest something broke.
 */
export function AssistantPanel({ fieldId }: { fieldId?: string }) {
  const { language, t } = useLanguage();
  const [messages, setMessages] = useState<Message[]>([]);
  const [draft, setDraft] = useState("");
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [unavailable, setUnavailable] = useState<string | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  // Checked up front so a farmer isn't invited to type a question into a box
  // that can only fail. A failure here is ignored: if the check itself can't
  // run, let them try — the send path reports the real error.
  useEffect(() => {
    let active = true;
    getAssistantStatus()
      .then((status) => {
        if (active && !status.configured) setUnavailable(t("assistant.unavailable"));
      })
      .catch(() => {});
    return () => {
      active = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, pending]);

  async function send(text: string) {
    const message = text.trim();
    if (!message || pending) return;

    // Captured before the state update so the history sent to the server is the
    // conversation as it stood before this question.
    const history: AssistantTurn[] = messages.map(({ role, content }) => ({ role, content }));

    setMessages((prev) => [...prev, { role: "user", content: message }]);
    setDraft("");
    setError(null);
    setPending(true);

    try {
      const result = await ask({ message, language, history, fieldId });
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: result.reply, filtered: result.filtered },
      ]);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : t("assistant.error"));
      // The question stays on screen so it can be retried without retyping.
      setDraft(message);
      setMessages((prev) => prev.slice(0, -1));
    } finally {
      setPending(false);
      inputRef.current?.focus();
    }
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    // Enter sends; Shift+Enter is a newline. On a phone keyboard the send
    // button is the primary path either way.
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      send(draft);
    }
  }

  if (unavailable) {
    return (
      <div className="flex flex-col items-center gap-3 rounded-lg border border-dashed border-line px-6 py-14 text-center">
        <span className="flex h-12 w-12 items-center justify-center rounded-full bg-bg-alt text-forest">
          <MessageCircle className="h-5 w-5" />
        </span>
        <h3 className="font-display text-lg text-forest-dark">{t("assistant.title")}</h3>
        <p className="max-w-sm text-sm text-ink-soft">{unavailable}</p>
        <p className="max-w-sm font-mono text-xs text-ink-soft">
          Set ANTHROPIC_API_KEY in backend/.env and restart the API.
        </p>
      </div>
    );
  }

  const suggestions = [
    t("assistant.suggest1"),
    t("assistant.suggest2"),
    t("assistant.suggest3"),
  ];

  return (
    <div className="card flex h-[calc(100vh-13rem)] min-h-[26rem] flex-col overflow-hidden">
      <div className="flex items-center justify-between border-b border-line px-4 py-3">
        <div>
          <h3 className="font-display text-base text-forest-dark">{t("assistant.title")}</h3>
          <p className="text-xs text-ink-soft">{t("assistant.subtitle")}</p>
        </div>
        {messages.length > 0 && (
          <button
            onClick={() => {
              setMessages([]);
              setError(null);
            }}
            className="flex items-center gap-1.5 rounded-md px-2 py-1 text-xs font-medium text-ink-soft hover:bg-bg-alt"
          >
            <RotateCcw className="h-3.5 w-3.5" />
            {t("assistant.clear")}
          </button>
        )}
      </div>

      <div ref={scrollRef} className="flex-1 space-y-3 overflow-y-auto px-4 py-4">
        {messages.length === 0 && !pending && (
          <div className="flex flex-col items-center gap-4 py-8 text-center">
            <span className="flex h-11 w-11 items-center justify-center rounded-full bg-growth-light/40 text-growth-dark">
              <Sprout className="h-5 w-5" />
            </span>
            <p className="max-w-sm text-sm text-ink-soft">{t("assistant.empty")}</p>
            <div className="flex flex-wrap justify-center gap-2">
              {suggestions.map((s) => (
                <button
                  key={s}
                  onClick={() => send(s)}
                  className="rounded-full border border-line px-3 py-1.5 text-xs text-ink-soft transition-colors hover:border-growth hover:text-growth-dark"
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((m, i) => (
          <div
            key={i}
            className={cn("flex", m.role === "user" ? "justify-end" : "justify-start")}
          >
            <div
              className={cn(
                "max-w-[85%] whitespace-pre-wrap rounded-lg px-3.5 py-2.5 text-sm",
                m.role === "user"
                  ? "bg-forest text-white"
                  : m.filtered
                    ? // Guidance, not an error: this is the correct answer to a
                      // question about chemicals.
                      "border border-marigold-light bg-marigold-light/20 text-ink"
                    : "bg-bg-alt text-ink"
              )}
            >
              {m.role === "assistant" && m.filtered && (
                <span className="mb-1 flex items-center gap-1.5 text-xs font-medium text-marigold-dark">
                  <ShieldAlert className="h-3.5 w-3.5" />
                  {t("assistant.title")}
                </span>
              )}
              {m.content}
            </div>
          </div>
        ))}

        {pending && (
          <div className="flex justify-start">
            <div className="flex items-center gap-2 rounded-lg bg-bg-alt px-3.5 py-2.5 text-sm text-ink-soft">
              <Loader2 className="h-3.5 w-3.5 animate-spin" />
              {t("assistant.thinking")}
            </div>
          </div>
        )}

        {error && (
          <p className="rounded-md bg-rust-light/20 px-3 py-2 text-sm text-rust-dark">{error}</p>
        )}
      </div>

      <div className="border-t border-line px-4 py-3">
        <p className="mb-2 text-[11px] leading-snug text-ink-soft">{t("assistant.disclaimer")}</p>
        <div className="flex items-end gap-2">
          <textarea
            ref={inputRef}
            rows={1}
            value={draft}
            maxLength={MAX_MESSAGE_CHARS}
            onChange={(e) => setDraft(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={t("assistant.placeholder")}
            className="max-h-32 flex-1 resize-y rounded-md border border-line bg-paper px-3.5 py-2.5 text-sm outline-none focus:border-growth"
          />
          <button
            onClick={() => send(draft)}
            disabled={pending || !draft.trim()}
            className="btn-primary shrink-0"
            aria-label={t("assistant.send")}
          >
            {pending ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Send className="h-4 w-4" />
            )}
            <span className="hidden sm:inline">{t("assistant.send")}</span>
          </button>
        </div>
      </div>
    </div>
  );
}
