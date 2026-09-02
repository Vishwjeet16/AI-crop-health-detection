"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Plus } from "lucide-react";
import { Topbar } from "@/components/shared/topbar";
import { FieldCard } from "@/components/shared/field-card";
import { FieldCardSkeleton } from "@/components/shared/skeleton";
import { EmptyState, ErrorState } from "@/components/shared/states";
import { listFields } from "@/lib/api/fields";
import type { Field } from "@/types";

export default function FieldsPage() {
  const [fields, setFields] = useState<Field[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  function load() {
    setError(null);
    setFields(null);
    listFields()
      .then(setFields)
      .catch(() => setError("We couldn't load your fields. Please try again."));
  }

  useEffect(load, []);

  return (
    <div>
      <Topbar title="My Fields" />
      <main className="px-5 py-8 md:px-8">
        <div className="flex items-center justify-between">
          <p className="text-sm text-ink-soft">
            {fields ? `${fields.length} fields under monitoring` : "Loading your fields…"}
          </p>
          <Link href="/fields/new" className="btn-primary">
            <Plus className="h-4 w-4" /> Add Field
          </Link>
        </div>

        <div className="mt-6">
          {error ? (
            <ErrorState message={error} actionLabel="Try Again" onAction={load} />
          ) : fields ? (
            fields.length > 0 ? (
              <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
                {fields.map((f) => (
                  <FieldCard key={f.id} field={f} />
                ))}
              </div>
            ) : (
              <EmptyState
                title="No fields yet"
                message="Add your first field to start scanning crops and tracking health over time."
                actionLabel="Add Field"
              />
            )
          ) : (
            <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
              {Array.from({ length: 3 }).map((_, i) => (
                <FieldCardSkeleton key={i} />
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
