"use client";

import { Camera, UploadCloud, AlertCircle } from "lucide-react";
import { useRef, useState } from "react";
import Image from "next/image";
import { validateImageFile } from "@/lib/validation";

export function UploadBox({
  onFileSelected,
}: {
  onFileSelected?: (file: File) => void;
}) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  function handleFile(file: File | undefined) {
    if (!file) return;
    const validationError = validateImageFile(file);
    if (validationError) {
      setError(validationError);
      setPreview(null);
      return;
    }
    setError(null);
    setPreview(URL.createObjectURL(file));
    onFileSelected?.(file);
  }

  if (preview) {
    return (
      <div className="scan-frame overflow-hidden rounded-lg border border-line">
        <span className="corner-tl" />
        <span className="corner-br" />
        <Image
          src={preview}
          alt="Selected crop photo preview"
          width={800}
          height={500}
          className="h-72 w-full object-cover"
          unoptimized
        />
        <div className="flex items-center justify-between bg-paper px-4 py-3">
          <button
            className="text-sm font-medium text-ink-soft hover:text-rust"
            onClick={() => {
              setPreview(null);
              setError(null);
            }}
          >
            Remove photo
          </button>
          <button
            className="text-sm font-medium text-forest hover:text-growth"
            onClick={() => inputRef.current?.click()}
          >
            Choose different photo
          </button>
        </div>
        <input
          ref={inputRef}
          type="file"
          accept="image/*"
          className="hidden"
          onChange={(e) => handleFile(e.target.files?.[0])}
        />
      </div>
    );
  }

  return (
    <div>
      <div
        className="scan-frame flex flex-col items-center justify-center gap-4 rounded-lg border-2 border-dashed border-line bg-bg-alt/60 px-6 py-14 text-center"
        onDragOver={(e) => e.preventDefault()}
        onDrop={(e) => {
          e.preventDefault();
          handleFile(e.dataTransfer.files?.[0]);
        }}
      >
        <span className="corner-tl" />
        <span className="corner-br" />
        <span className="flex h-14 w-14 items-center justify-center rounded-full bg-forest text-white">
          <UploadCloud className="h-6 w-6" />
        </span>
        <div>
          <p className="font-medium text-ink">Drag a crop photo here, or choose an option</p>
          <p className="mt-1 text-sm text-ink-soft">Clear, well-lit photos give the most reliable results. JPG, PNG or WEBP, up to 8MB.</p>
        </div>
        <div className="flex flex-wrap justify-center gap-3">
          <button className="btn-primary" onClick={() => inputRef.current?.click()}>
            <Camera className="h-4 w-4" /> Take Photo
          </button>
          <button className="btn-secondary" onClick={() => inputRef.current?.click()}>
            <UploadCloud className="h-4 w-4" /> Upload Image
          </button>
        </div>
        <input
          ref={inputRef}
          type="file"
          accept="image/*"
          capture="environment"
          className="hidden"
          onChange={(e) => handleFile(e.target.files?.[0])}
        />
      </div>
      {error && (
        <p className="mt-2 flex items-center gap-1.5 text-sm text-rust">
          <AlertCircle className="h-4 w-4 shrink-0" /> {error}
        </p>
      )}
    </div>
  );
}
