import { describe, it, expect } from "vitest";
import {
  toPersianDigits,
  toPersianNumber,
  formatPersianDate,
} from "../persianFormatter";

describe("toPersianDigits", () => {
  it("converts Latin digits to Persian", () => {
    expect(toPersianDigits("123")).toBe("\u06F1\u06F2\u06F3");
  });

  it("converts all digits 0-9", () => {
    expect(toPersianDigits("0123456789")).toBe(
      "\u06F0\u06F1\u06F2\u06F3\u06F4\u06F5\u06F6\u06F7\u06F8\u06F9",
    );
  });

  it("returns empty string for empty input", () => {
    expect(toPersianDigits("")).toBe("");
  });

  it("preserves non-digit characters", () => {
    expect(toPersianDigits("abc")).toBe("abc");
    expect(toPersianDigits("12-34")).toBe("\u06F1\u06F2-\u06F3\u06F4");
  });

  it("handles mixed content", () => {
    expect(toPersianDigits("2024/01/15")).toBe(
      "\u06F2\u06F0\u06F2\u06F4/\u06F0\u06F1/\u06F1\u06F5",
    );
  });
});

describe("toPersianNumber", () => {
  it("converts 0", () => {
    expect(toPersianNumber(0)).toBe("\u06F0");
  });

  it("converts positive numbers", () => {
    expect(toPersianNumber(1234)).toBe("\u06F1\u06F2\u06F3\u06F4");
  });

  it("converts negative numbers", () => {
    expect(toPersianNumber(-5)).toBe("-\u06F5");
  });
});

describe("formatPersianDate", () => {
  it("returns empty string for empty input", () => {
    expect(formatPersianDate("")).toBe("");
  });

  it("formats an ISO date as Jalaali with Persian digits", () => {
    // 2024-03-20 is roughly 1403/01/01 (Nowruz)
    const result = formatPersianDate("2024-03-20");
    // Should contain Persian digits and slashes
    expect(result).toMatch(
      /[\u06F0-\u06F9]+\/[\u06F0-\u06F9]+\/[\u06F0-\u06F9]+/,
    );
  });

  it("produces consistent output for known date", () => {
    // 2024-01-01 is Jalaali 1402/10/11
    const result = formatPersianDate("2024-01-01");
    expect(result).toBe("\u06F1\u06F4\u06F0\u06F2/\u06F1\u06F0/\u06F1\u06F1");
  });
});
