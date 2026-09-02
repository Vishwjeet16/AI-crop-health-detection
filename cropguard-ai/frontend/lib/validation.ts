export type ValidationErrors<T extends string> = Partial<Record<T, string>>;

export function isRequired(value: string): string | null {
  return value.trim().length === 0 ? "This field is required." : null;
}

export function isEmailOrPhone(value: string): string | null {
  const trimmed = value.trim();
  if (!trimmed) return "This field is required.";
  const isEmail = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(trimmed);
  const isPhone = /^[6-9]\d{9}$/.test(trimmed.replace(/[\s-]/g, ""));
  if (!isEmail && !isPhone) {
    return "Enter a valid email or 10-digit Indian mobile number.";
  }
  return null;
}

export function isStrongPassword(value: string): string | null {
  if (value.length < 8) return "Password must be at least 8 characters.";
  if (!/[A-Za-z]/.test(value) || !/[0-9]/.test(value)) {
    return "Password must include at least one letter and one number.";
  }
  return null;
}

export function isPositiveNumber(value: string): string | null {
  if (!value) return "This field is required.";
  const n = Number(value);
  if (Number.isNaN(n) || n <= 0) return "Enter a number greater than 0.";
  return null;
}

/** File validation for crop photo uploads. */
export function validateImageFile(file: File): string | null {
  const MAX_SIZE_MB = 8;
  const ALLOWED_TYPES = ["image/jpeg", "image/png", "image/webp"];
  if (!ALLOWED_TYPES.includes(file.type)) {
    return "Please upload a JPG, PNG, or WEBP image.";
  }
  if (file.size > MAX_SIZE_MB * 1024 * 1024) {
    return `Image is too large. Please upload a photo under ${MAX_SIZE_MB}MB.`;
  }
  return null;
}
