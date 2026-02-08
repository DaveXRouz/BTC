import { isoToJalaali } from "./dateFormatters";

const PERSIAN_DIGITS = [
  "\u06F0",
  "\u06F1",
  "\u06F2",
  "\u06F3",
  "\u06F4",
  "\u06F5",
  "\u06F6",
  "\u06F7",
  "\u06F8",
  "\u06F9",
];

/** Convert Latin digits (0-9) in a string to Persian digits (\u06F0-\u06F9). */
export function toPersianDigits(str: string): string {
  if (!str) return "";
  return str.replace(/[0-9]/g, (d) => PERSIAN_DIGITS[Number(d)]);
}

/** Convert a number to a string with Persian digits. */
export function toPersianNumber(n: number): string {
  return toPersianDigits(String(n));
}

/** Format an ISO date (YYYY-MM-DD) as a Jalaali date string with Persian digits. */
export function formatPersianDate(iso: string): string {
  if (!iso) return "";
  const { jy, jm, jd } = isoToJalaali(iso);
  const formatted = `${jy}/${String(jm).padStart(2, "0")}/${String(jd).padStart(2, "0")}`;
  return toPersianDigits(formatted);
}
