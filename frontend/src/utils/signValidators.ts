import type { SignData } from "@/types";

export interface ValidationResult {
  valid: boolean;
  error?: string; // i18n key
}

/** Validate time format HH:MM */
export function validateTime(value: string): ValidationResult {
  if (!value) return { valid: false, error: "oracle.error_sign_required" };
  // Accepts HH:MM from native time input
  const match = /^([01]\d|2[0-3]):([0-5]\d)$/.exec(value);
  if (!match) return { valid: false, error: "oracle.error_time_format" };
  return { valid: true };
}

/** Validate numeric sign (1+ digits) */
export function validateNumber(value: string): ValidationResult {
  if (!value) return { valid: false, error: "oracle.error_sign_required" };
  if (!/^\d+$/.test(value))
    return { valid: false, error: "oracle.error_number_format" };
  return { valid: true };
}

/** Validate Iranian car plate format: 2digits + letter + 3digits + 2digits (e.g. 12A345-67) */
export function validateCarPlate(value: string): ValidationResult {
  if (!value) return { valid: false, error: "oracle.error_sign_required" };
  // Accepts formats like "12A345-67" or "12A34567" or Persian equivalents
  const normalized = value.replace(/[-\s]/g, "").toUpperCase();
  if (normalized.length < 7)
    return { valid: false, error: "oracle.error_carplate_format" };
  return { valid: true };
}

/** Validate custom sign (non-empty) */
function validateCustom(value: string): ValidationResult {
  if (!value.trim())
    return { valid: false, error: "oracle.error_sign_required" };
  return { valid: true };
}

/** Validate a SignData based on its type */
export function validateSign(sign: SignData): ValidationResult {
  switch (sign.type) {
    case "time":
      return validateTime(sign.value);
    case "number":
      return validateNumber(sign.value);
    case "carplate":
      return validateCarPlate(sign.value);
    case "custom":
      return validateCustom(sign.value);
  }
}
