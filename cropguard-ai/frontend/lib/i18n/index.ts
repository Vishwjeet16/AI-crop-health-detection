import en from "./en.json";
import hi from "./hi.json";
import mr from "./mr.json";
import ta from "./ta.json";
import te from "./te.json";

/**
 * The languages the app runs in. This is the single source of truth: the
 * register page, the sidebar picker, the settings page, the backend's
 * SUPPORTED_LANGUAGE_CODES and the assistant's LANGUAGES registry all track it.
 * Adding a language means adding a <code>.json file, one line here, and the
 * matching entry in backend/app/services/assistant_service.py — no component
 * code changes.
 *
 * `label` is for full-width selects and carries both the native and English
 * name, so a farmer can find their language and an English-reading judge or
 * evaluator can tell what it is. `short` is the native name alone, for the
 * cramped picker in the sidebar.
 */
export const SUPPORTED_LANGUAGES = {
  en: { label: "English", short: "English", english: "English", dict: en },
  hi: { label: "हिंदी (Hindi)", short: "हिंदी", english: "Hindi", dict: hi },
  mr: { label: "मराठी (Marathi)", short: "मराठी", english: "Marathi", dict: mr },
  ta: { label: "தமிழ் (Tamil)", short: "தமிழ்", english: "Tamil", dict: ta },
  te: { label: "తెలుగు (Telugu)", short: "తెలుగు", english: "Telugu", dict: te },
} as const;

export type LanguageCode = keyof typeof SUPPORTED_LANGUAGES;
export type TranslationKey = keyof typeof en;

/** Stable iteration order for pickers. */
export const LANGUAGE_CODES = Object.keys(SUPPORTED_LANGUAGES) as LanguageCode[];

export const DEFAULT_LANGUAGE: LanguageCode = "en";

/** Narrowing helper for values arriving from localStorage or an API response. */
export function isLanguageCode(value: unknown): value is LanguageCode {
  return typeof value === "string" && value in SUPPORTED_LANGUAGES;
}

/**
 * Look up a string. Falls back to English for a key a translation file hasn't
 * caught up on yet, and to the key itself if it exists nowhere — a visible
 * "assistant.send" in the UI is a better bug report than a blank button.
 */
export function t(lang: LanguageCode, key: TranslationKey): string {
  const dict = SUPPORTED_LANGUAGES[lang]?.dict as Record<string, string> | undefined;
  return dict?.[key] ?? (SUPPORTED_LANGUAGES.en.dict as Record<string, string>)[key] ?? key;
}
