"use client";

import { Topbar } from "@/components/shared/topbar";
import { AssistantPanel } from "@/components/shared/assistant-panel";
import { useLanguage } from "@/context/language-context";

export default function AssistantPage() {
  const { t } = useLanguage();
  return (
    <div>
      <Topbar title={t("assistant.title")} />
      <main className="mx-auto max-w-2xl px-5 py-6 md:px-8">
        <AssistantPanel />
      </main>
    </div>
  );
}
