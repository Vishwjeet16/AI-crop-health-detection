"use client";

import { createContext, useContext, useEffect, useState } from "react";
import { SUPPORTED_LANGUAGES, t, type LanguageCode, type TranslationKey } from "@/lib/i18n";

interface LanguageContextValue {
  language: LanguageCode;
  setLanguage: (lang: LanguageCode) => void;
  t: (key: TranslationKey) => string;
}

const LanguageContext = createContext<LanguageContextValue | null>(null);
const STORAGE_KEY = "cg_language";

export function LanguageProvider({ children }: { children: React.ReactNode }) {
  const [language, setLanguageState] = useState<LanguageCode>("en");

  useEffect(() => {
    // Guarded: a throw here (Safari private mode, storage disabled) would abort
    // the mount effect of the provider that wraps the whole app.
    try {
      const stored = localStorage.getItem(STORAGE_KEY) as LanguageCode | null;
      if (stored && stored in SUPPORTED_LANGUAGES) setLanguageState(stored);
    } catch {
      /* keep the default */
    }
  }, []);

  function setLanguage(lang: LanguageCode) {
    try {
      localStorage.setItem(STORAGE_KEY, lang);
    } catch {
      /* preference just won't survive a reload */
    }
    setLanguageState(lang);
  }

  return (
    <LanguageContext.Provider
      value={{ language, setLanguage, t: (key) => t(language, key) }}
    >
      {children}
    </LanguageContext.Provider>
  );
}

export function useLanguage() {
  const ctx = useContext(LanguageContext);
  if (!ctx) throw new Error("useLanguage must be used within LanguageProvider");
  return ctx;
}
