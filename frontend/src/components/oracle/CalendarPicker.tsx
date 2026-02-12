import { useState, useEffect, useRef } from "react";
import { useTranslation } from "react-i18next";
import {
  type CalendarMode,
  formatDate,
  buildCalendarGrid,
  isoToJalaali,
  todayIso,
  JALAALI_MONTHS,
  JALAALI_WEEKDAYS,
  GREGORIAN_MONTHS,
  GREGORIAN_WEEKDAYS,
} from "@/utils/dateFormatters";

interface CalendarPickerProps {
  value: string; // "YYYY-MM-DD" or ""
  onChange: (isoDate: string) => void;
  label?: string;
  error?: string;
}

export function CalendarPicker({
  value,
  onChange,
  label,
  error,
}: CalendarPickerProps) {
  const { t } = useTranslation();
  const [isOpen, setIsOpen] = useState(false);
  const [mode, setMode] = useState<CalendarMode>("gregorian");
  const containerRef = useRef<HTMLDivElement>(null);

  // Current view year/month — derived from value or today
  const today = todayIso();
  const initDate = value || today;

  const [viewYear, setViewYear] = useState(() => {
    if (mode === "jalaali") {
      return isoToJalaali(initDate).jy;
    }
    return parseInt(initDate.split("-")[0]);
  });
  const [viewMonth, setViewMonth] = useState(() => {
    if (mode === "jalaali") {
      return isoToJalaali(initDate).jm;
    }
    return parseInt(initDate.split("-")[1]);
  });

  // Reset view when mode changes
  useEffect(() => {
    const ref = value || today;
    if (mode === "jalaali") {
      const j = isoToJalaali(ref);
      setViewYear(j.jy);
      setViewMonth(j.jm);
    } else {
      setViewYear(parseInt(ref.split("-")[0]));
      setViewMonth(parseInt(ref.split("-")[1]));
    }
  }, [mode, value, today]);

  // Close on outside click
  useEffect(() => {
    if (!isOpen) return;
    function handleClick(e: MouseEvent) {
      if (
        containerRef.current &&
        !containerRef.current.contains(e.target as Node)
      ) {
        setIsOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, [isOpen]);

  function handlePrevMonth() {
    if (mode === "jalaali") {
      if (viewMonth === 1) {
        setViewYear((y) => y - 1);
        setViewMonth(12);
      } else {
        setViewMonth((m) => m - 1);
      }
    } else {
      if (viewMonth === 1) {
        setViewYear((y) => y - 1);
        setViewMonth(12);
      } else {
        setViewMonth((m) => m - 1);
      }
    }
  }

  function handleNextMonth() {
    if (mode === "jalaali") {
      if (viewMonth === 12) {
        setViewYear((y) => y + 1);
        setViewMonth(1);
      } else {
        setViewMonth((m) => m + 1);
      }
    } else {
      if (viewMonth === 12) {
        setViewYear((y) => y + 1);
        setViewMonth(1);
      } else {
        setViewMonth((m) => m + 1);
      }
    }
  }

  function handleDayClick(iso: string) {
    onChange(iso);
    setIsOpen(false);
  }

  const grid = buildCalendarGrid(viewYear, viewMonth, mode);
  const weekdays = mode === "jalaali" ? JALAALI_WEEKDAYS : GREGORIAN_WEEKDAYS;
  const monthName =
    mode === "jalaali"
      ? JALAALI_MONTHS[viewMonth - 1]
      : GREGORIAN_MONTHS[viewMonth - 1];

  return (
    <div ref={containerRef} className="relative">
      {label && (
        <label className="block text-sm text-nps-text-dim mb-1">{label}</label>
      )}

      {/* Display input */}
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className={`w-full text-start bg-nps-bg-input border rounded px-3 py-2 text-sm text-nps-text focus:outline-none focus:border-nps-oracle-accent ${
          error ? "border-nps-error" : "border-nps-border"
        }`}
      >
        {value ? formatDate(value, mode) : t("oracle.calendar_select_date")}
      </button>

      {error && <p className="text-nps-error text-xs mt-1">{error}</p>}

      {/* Dropdown calendar */}
      {isOpen && (
        <div className="fixed inset-x-0 bottom-0 sm:absolute sm:inset-x-auto sm:bottom-auto sm:start-0 sm:top-full sm:mt-1 z-50 bg-nps-bg-card border border-nps-oracle-border rounded-t-lg sm:rounded-lg p-3 shadow-lg w-full sm:w-72">
          {/* Calendar mode toggle */}
          <div className="flex gap-1 mb-3">
            <button
              type="button"
              onClick={() => setMode("gregorian")}
              className={`flex-1 text-xs py-1 min-h-[44px] sm:min-h-0 rounded transition-colors ${
                mode === "gregorian"
                  ? "bg-nps-oracle-accent text-nps-bg font-medium"
                  : "bg-nps-bg-input text-nps-text-dim hover:text-nps-text"
              }`}
            >
              {t("oracle.calendar_gregorian")}
            </button>
            <button
              type="button"
              onClick={() => setMode("jalaali")}
              className={`flex-1 text-xs py-1 min-h-[44px] sm:min-h-0 rounded transition-colors ${
                mode === "jalaali"
                  ? "bg-nps-oracle-accent text-nps-bg font-medium"
                  : "bg-nps-bg-input text-nps-text-dim hover:text-nps-text"
              }`}
            >
              {t("oracle.calendar_jalaali")}
            </button>
          </div>

          {/* Month/year navigation */}
          <div className="flex items-center justify-between mb-2">
            <button
              type="button"
              onClick={handlePrevMonth}
              className="w-10 h-10 sm:w-7 sm:h-7 flex items-center justify-center text-nps-text-dim hover:text-nps-text rounded transition-colors"
              aria-label="Previous month"
            >
              ‹
            </button>
            <span className="text-sm font-medium text-nps-text">
              {monthName} {viewYear}
            </span>
            <button
              type="button"
              onClick={handleNextMonth}
              className="w-10 h-10 sm:w-7 sm:h-7 flex items-center justify-center text-nps-text-dim hover:text-nps-text rounded transition-colors"
              aria-label="Next month"
            >
              ›
            </button>
          </div>

          {/* Weekday header */}
          <div
            className="grid grid-cols-7 gap-0.5 mb-1"
            dir={mode === "jalaali" ? "rtl" : "ltr"}
          >
            {weekdays.map((d) => (
              <div
                key={d}
                className="text-center text-xs text-nps-text-dim py-1"
              >
                {d}
              </div>
            ))}
          </div>

          {/* Day grid */}
          <div dir={mode === "jalaali" ? "rtl" : "ltr"}>
            {grid.map((week, wi) => (
              <div key={wi} className="grid grid-cols-7 gap-0.5">
                {week.map((cell, ci) => {
                  const isSelected = cell.iso === value;
                  const isToday = cell.iso === today;
                  return (
                    <button
                      key={ci}
                      type="button"
                      onClick={() => handleDayClick(cell.iso)}
                      className={`h-10 sm:h-8 text-xs rounded transition-colors ${
                        isSelected
                          ? "bg-nps-oracle-accent text-nps-bg font-bold"
                          : isToday
                            ? "bg-nps-oracle-accent/20 text-nps-oracle-accent font-medium"
                            : cell.isCurrentMonth
                              ? "text-nps-text hover:bg-nps-bg-hover"
                              : "text-nps-text-dim/40 hover:bg-nps-bg-hover"
                      }`}
                    >
                      {cell.day}
                    </button>
                  );
                })}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
