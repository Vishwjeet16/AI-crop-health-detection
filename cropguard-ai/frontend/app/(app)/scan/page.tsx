"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Loader2 } from "lucide-react";
import { Topbar } from "@/components/shared/topbar";
import { UploadBox } from "@/components/shared/upload-box";
import { LoadingState } from "@/components/shared/loading-state";
import { ErrorState } from "@/components/shared/states";
import { listFields } from "@/lib/api/fields";
import { analyzeImage } from "@/lib/api/scans";
import { ApiError } from "@/lib/api/client";
import type { Field, Scan } from "@/types";

export default function ScanPage() {
  const router = useRouter();
  const [fields, setFields] = useState<Field[] | null>(null);
  const [fieldId, setFieldId] = useState<string>("");
  const [file, setFile] = useState<File | null>(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [pendingScan, setPendingScan] = useState<Scan | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [fieldsError, setFieldsError] = useState<string | null>(null);

  useEffect(() => {
    // Without the catch, a failed request (API down, expired session) left
    // `fields` null forever, so the page sat on "Loading your fields…" and the
    // rejection only showed up in the console.
    listFields()
      .then((f) => {
        setFields(f);
        if (f.length > 0) setFieldId(f[0].id);
      })
      .catch((err) => {
        setFields([]);
        setFieldsError(
          err instanceof ApiError
            ? err.message
            : "Could not reach the server to load your fields.",
        );
      });
  }, []);

  async function handleAnalyze() {
    if (!file || !fieldId) return;
    setError(null);
    setAnalyzing(true);
    try {
      const scan = await analyzeImage(fieldId, file);
      setPendingScan(scan);
    } catch (err) {
      setAnalyzing(false);
      setError(err instanceof ApiError ? err.message : "The AI service is unavailable right now. Please try again.");
    }
  }

  if (error) {
    return (
      <div>
        <Topbar title="Scan Crop" />
        <main className="mx-auto max-w-2xl px-5 py-8 md:px-8">
          <ErrorState
            title="Analysis failed"
            message={error}
            actionLabel="Try Again"
            onAction={() => setError(null)}
          />
        </main>
      </div>
    );
  }

  return (
    <div>
      <Topbar title="Scan Crop" />
      <main className="mx-auto max-w-2xl px-5 py-8 md:px-8">
        {analyzing ? (
          <LoadingState
            onComplete={() => {
              if (pendingScan) router.push(`/scan/result/${pendingScan.id}`);
            }}
          />
        ) : (
          <>
            <div className="card mb-6 p-5">
              <label className="mb-1.5 block text-sm font-medium text-ink" htmlFor="field">
                Which field is this?
              </label>
              {!fields ? (
                <div className="flex items-center gap-2 text-sm text-ink-soft">
                  <Loader2 className="h-4 w-4 animate-spin" /> Loading your fields…
                </div>
              ) : fields.length === 0 ? (
                // A scan is stored against a field, so there is nothing useful to
                // show here until one exists. Previously this rendered an empty
                // dropdown and left Analyze Crop permanently disabled with no
                // explanation.
                <div className="text-sm text-ink-soft">
                  {fieldsError ? (
                    <>
                      {fieldsError}{" "}
                      <button
                        className="font-medium text-growth underline"
                        onClick={() => window.location.reload()}
                      >
                        Retry
                      </button>
                    </>
                  ) : (
                    <>
                      You have not added a field yet, and every scan is saved
                      against one.{" "}
                      <Link
                        href="/fields/new"
                        className="font-medium text-growth underline"
                      >
                        Add your first field
                      </Link>{" "}
                      to start scanning.
                    </>
                  )}
                </div>
              ) : (
                <select
                  id="field"
                  value={fieldId}
                  onChange={(e) => setFieldId(e.target.value)}
                  className="w-full rounded-md border border-line bg-paper px-3.5 py-2.5 text-sm outline-none focus:border-growth"
                >
                  {fields.map((f) => (
                    <option key={f.id} value={f.id}>
                      {f.name} — {f.crop}
                    </option>
                  ))}
                </select>
              )}
            </div>

            <UploadBox onFileSelected={setFile} />

            <button
              className="btn-primary mt-6 w-full"
              disabled={!file || !fieldId}
              onClick={handleAnalyze}
            >
              Analyze Crop
            </button>
            {/* The button greys out for two different reasons and looked broken
                when neither was stated. */}
            {(!file || !fieldId) && (
              <p className="mt-2 text-center text-xs text-ink-soft">
                {!fieldId
                  ? "Add a field first — a scan has to be saved against one."
                  : "Choose or take a photo of the crop to enable analysis."}
              </p>
            )}
            <p className="mt-3 text-center text-xs text-ink-soft">
              AI_MODE=demo — results shown next are simulated for this prototype.
            </p>
          </>
        )}
      </main>
    </div>
  );
}
