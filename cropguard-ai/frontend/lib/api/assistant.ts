import { apiFetch, mockDelay, USE_MOCK_API } from "./client";
import { t, type LanguageCode } from "@/lib/i18n";

export interface AssistantTurn {
  role: "user" | "assistant";
  content: string;
}

export interface AssistantReply {
  reply: string;
  language: LanguageCode;
  /**
   * True when the backend's safety scan replaced the model's answer, or the
   * model declined. Not an error — the reply is the "contact your KVK" message
   * and the UI styles it as guidance.
   */
  filtered: boolean;
  model?: string | null;
}

export interface AskOptions {
  message: string;
  language: LanguageCode;
  /** Prior turns, oldest first. The backend trims this; sending it all is fine. */
  history?: AssistantTurn[];
  /** Scopes the context to one field when the chat is opened from a field page. */
  fieldId?: string;
}

/** Matches MAX_MESSAGE_CHARS in backend/app/schemas/assistant.py. */
export const MAX_MESSAGE_CHARS = 2000;

export async function ask({
  message,
  language,
  history = [],
  fieldId,
}: AskOptions): Promise<AssistantReply> {
  if (!USE_MOCK_API) {
    return apiFetch<AssistantReply>("/api/assistant/chat", {
      method: "POST",
      body: JSON.stringify({
        message,
        language,
        history,
        field_id: fieldId ?? null,
      }),
    });
  }

  // Mock mode has no model to call, so it demonstrates the one behaviour that
  // matters most: a question about spraying gets the safe redirect, in the
  // farmer's language, from the same dictionary the real filtered path uses.
  await mockDelay(900);
  const asksForChemical = /spray|pesticide|chemical|dose|दवा|औषध|மருந்து|మందు/i.test(message);
  return {
    reply: asksForChemical
      ? t(language, "assistant.disclaimer")
      : t(language, "assistant.empty"),
    language,
    filtered: asksForChemical,
    model: "mock",
  };
}

export interface AssistantLanguage {
  code: string;
  name: string;
  native: string;
}

/**
 * Whether the server has an API key configured, plus the languages it will
 * answer in. Used to show a clear "not set up" message instead of letting the
 * farmer type a question into a box that can only 503.
 */
export async function getAssistantStatus(): Promise<{
  languages: AssistantLanguage[];
  configured: boolean;
}> {
  if (!USE_MOCK_API) {
    return apiFetch<{ languages: AssistantLanguage[]; configured: boolean }>(
      "/api/assistant/languages"
    );
  }
  await mockDelay(200);
  return { languages: [], configured: true };
}
