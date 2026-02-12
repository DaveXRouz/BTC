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

export function toPersianDigits(n: number): string {
  return String(n)
    .split("")
    .map((ch) => {
      const digit = parseInt(ch, 10);
      return isNaN(digit) ? ch : PERSIAN_DIGITS[digit];
    })
    .join("");
}
