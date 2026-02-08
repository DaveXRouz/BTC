import { toJalaali, toGregorian, jalaaliMonthLength } from "jalaali-js";

export type CalendarMode = "gregorian" | "jalaali";

export const JALAALI_MONTHS = [
  "فروردین",
  "اردیبهشت",
  "خرداد",
  "تیر",
  "مرداد",
  "شهریور",
  "مهر",
  "آبان",
  "آذر",
  "دی",
  "بهمن",
  "اسفند",
];

export const JALAALI_WEEKDAYS = ["ش", "ی", "د", "س", "چ", "پ", "ج"];

export const GREGORIAN_MONTHS = [
  "January",
  "February",
  "March",
  "April",
  "May",
  "June",
  "July",
  "August",
  "September",
  "October",
  "November",
  "December",
];

export const GREGORIAN_WEEKDAYS = ["Su", "Mo", "Tu", "We", "Th", "Fr", "Sa"];

/** Convert ISO "YYYY-MM-DD" to Jalaali {jy, jm, jd} */
export function isoToJalaali(iso: string) {
  const [gy, gm, gd] = iso.split("-").map(Number);
  return toJalaali(gy, gm, gd);
}

/** Convert Jalaali {jy, jm, jd} to ISO "YYYY-MM-DD" */
export function jalaaliToIso(jy: number, jm: number, jd: number) {
  const { gy, gm, gd } = toGregorian(jy, jm, jd);
  return `${gy}-${String(gm).padStart(2, "0")}-${String(gd).padStart(2, "0")}`;
}

/** Format ISO date for display in given calendar mode */
export function formatDate(iso: string, mode: CalendarMode): string {
  if (!iso) return "";
  if (mode === "jalaali") {
    const { jy, jm, jd } = isoToJalaali(iso);
    return `${jy}/${String(jm).padStart(2, "0")}/${String(jd).padStart(2, "0")}`;
  }
  return iso; // Already "YYYY-MM-DD"
}

export interface CalendarDay {
  day: number;
  iso: string;
  isCurrentMonth: boolean;
}

/** Build a 6x7 grid of days for the given month */
export function buildCalendarGrid(
  year: number,
  month: number,
  mode: CalendarMode,
): CalendarDay[][] {
  const grid: CalendarDay[][] = [];

  if (mode === "jalaali") {
    // Jalaali calendar: Saturday-first week
    const monthLength = jalaaliMonthLength(year, month);
    const firstDayIso = jalaaliToIso(year, month, 1);
    const firstDate = new Date(firstDayIso);
    // Saturday = 0 in our grid (JS getDay: Sat=6, Sun=0, Mon=1...)
    const jsDay = firstDate.getDay(); // 0=Sun
    const startOffset = jsDay === 6 ? 0 : jsDay + 1; // Sat-first

    // Previous month info
    const prevMonth = month === 1 ? 12 : month - 1;
    const prevYear = month === 1 ? year - 1 : year;
    const prevMonthLength = jalaaliMonthLength(prevYear, prevMonth);

    // Next month
    const nextMonth = month === 12 ? 1 : month + 1;
    const nextYear = month === 12 ? year + 1 : year;

    let dayCounter = 1;
    let nextDayCounter = 1;

    for (let row = 0; row < 6; row++) {
      const week: CalendarDay[] = [];
      for (let col = 0; col < 7; col++) {
        const cellIndex = row * 7 + col;
        if (cellIndex < startOffset) {
          const d = prevMonthLength - startOffset + cellIndex + 1;
          week.push({
            day: d,
            iso: jalaaliToIso(prevYear, prevMonth, d),
            isCurrentMonth: false,
          });
        } else if (dayCounter <= monthLength) {
          week.push({
            day: dayCounter,
            iso: jalaaliToIso(year, month, dayCounter),
            isCurrentMonth: true,
          });
          dayCounter++;
        } else {
          week.push({
            day: nextDayCounter,
            iso: jalaaliToIso(nextYear, nextMonth, nextDayCounter),
            isCurrentMonth: false,
          });
          nextDayCounter++;
        }
      }
      grid.push(week);
    }
  } else {
    // Gregorian calendar: Sunday-first week
    const firstDay = new Date(year, month - 1, 1);
    const startOffset = firstDay.getDay(); // 0=Sun
    const monthLength = new Date(year, month, 0).getDate();

    const prevMonthLength = new Date(year, month - 1, 0).getDate();
    const prevMonth = month === 1 ? 12 : month - 1;
    const prevYear = month === 1 ? year - 1 : year;
    const nextMonth = month === 12 ? 1 : month + 1;
    const nextYear = month === 12 ? year + 1 : year;

    let dayCounter = 1;
    let nextDayCounter = 1;

    for (let row = 0; row < 6; row++) {
      const week: CalendarDay[] = [];
      for (let col = 0; col < 7; col++) {
        const cellIndex = row * 7 + col;
        if (cellIndex < startOffset) {
          const d = prevMonthLength - startOffset + cellIndex + 1;
          const m = String(prevMonth).padStart(2, "0");
          week.push({
            day: d,
            iso: `${prevYear}-${m}-${String(d).padStart(2, "0")}`,
            isCurrentMonth: false,
          });
        } else if (dayCounter <= monthLength) {
          const m = String(month).padStart(2, "0");
          week.push({
            day: dayCounter,
            iso: `${year}-${m}-${String(dayCounter).padStart(2, "0")}`,
            isCurrentMonth: true,
          });
          dayCounter++;
        } else {
          const m = String(nextMonth).padStart(2, "0");
          week.push({
            day: nextDayCounter,
            iso: `${nextYear}-${m}-${String(nextDayCounter).padStart(2, "0")}`,
            isCurrentMonth: false,
          });
          nextDayCounter++;
        }
      }
      grid.push(week);
    }
  }

  return grid;
}

/** Get today's date as ISO string */
export function todayIso(): string {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
}
