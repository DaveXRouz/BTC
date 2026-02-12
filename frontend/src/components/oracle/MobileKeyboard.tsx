import { useState, useEffect } from "react";
import { useTranslation } from "react-i18next";
import {
  PERSIAN_ROWS,
  PERSIAN_SHIFT_ROWS,
} from "@/utils/persianKeyboardLayout";

interface MobileKeyboardProps {
  onCharacterClick: (char: string) => void;
  onBackspace: () => void;
  onClose: () => void;
}

export function MobileKeyboard({
  onCharacterClick,
  onBackspace,
  onClose,
}: MobileKeyboardProps) {
  const { t } = useTranslation();
  const [isShifted, setIsShifted] = useState(false);

  const rows = isShifted ? PERSIAN_SHIFT_ROWS : PERSIAN_ROWS;

  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape") onClose();
    }
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [onClose]);

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/30 z-40"
        onClick={onClose}
        data-testid="mobile-keyboard-backdrop"
        aria-hidden="true"
      />

      {/* Keyboard panel fixed to bottom */}
      <div
        role="dialog"
        aria-label={t("oracle.keyboard_persian")}
        dir="rtl"
        className="fixed bottom-0 inset-x-0 z-50 bg-[var(--nps-bg-card)] border-t border-[var(--nps-border)] p-3 shadow-lg animate-slide-up"
        data-testid="mobile-keyboard"
      >
        {/* Close button */}
        <div className="flex justify-end mb-2">
          <button
            type="button"
            onClick={onClose}
            className="min-w-[44px] min-h-[44px] flex items-center justify-center text-[var(--nps-text-dim)] hover:text-[var(--nps-text)] rounded"
            aria-label={t("oracle.keyboard_close")}
          >
            <svg
              width="18"
              height="18"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth={2}
            >
              <line x1="18" y1="6" x2="6" y2="18" />
              <line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
        </div>

        {/* Character rows */}
        <div className="space-y-1.5">
          {rows.map((row, rowIndex) => (
            <div key={rowIndex} className="flex gap-1 justify-center flex-wrap">
              {row.map((char) => (
                <button
                  key={`${isShifted ? "s" : "b"}-${char}`}
                  type="button"
                  onClick={() => onCharacterClick(char)}
                  onTouchStart={(e) => {
                    e.preventDefault();
                    onCharacterClick(char);
                  }}
                  aria-label={char}
                  className="min-w-[36px] min-h-[44px] text-sm bg-[var(--nps-bg-input)] hover:bg-[var(--nps-bg-hover)] active:bg-[var(--nps-accent)]/20 border border-[var(--nps-border)] rounded text-[var(--nps-text)] transition-colors select-none flex items-center justify-center"
                >
                  {char}
                </button>
              ))}
            </div>
          ))}

          {/* Bottom row: Shift + Space + Backspace */}
          <div className="flex gap-1 justify-center">
            <button
              type="button"
              onClick={() => setIsShifted(!isShifted)}
              aria-label={t("oracle.keyboard_shift")}
              className={`min-h-[44px] px-4 text-xs border rounded transition-colors select-none ${
                isShifted
                  ? "bg-[var(--nps-accent)]/30 text-[var(--nps-accent)] border-[var(--nps-accent)]"
                  : "bg-[var(--nps-bg-input)] text-[var(--nps-text-dim)] border-[var(--nps-border)] hover:bg-[var(--nps-bg-hover)]"
              }`}
            >
              {t("oracle.keyboard_shift")}
            </button>
            <button
              type="button"
              onClick={() => onCharacterClick(" ")}
              onTouchStart={(e) => {
                e.preventDefault();
                onCharacterClick(" ");
              }}
              aria-label={t("oracle.keyboard_space")}
              className="min-h-[44px] flex-1 text-xs bg-[var(--nps-bg-input)] hover:bg-[var(--nps-bg-hover)] border border-[var(--nps-border)] rounded text-[var(--nps-text-dim)] transition-colors select-none"
            >
              {t("oracle.keyboard_space")}
            </button>
            <button
              type="button"
              onClick={onBackspace}
              onTouchStart={(e) => {
                e.preventDefault();
                onBackspace();
              }}
              aria-label={t("oracle.keyboard_backspace")}
              className="min-h-[44px] px-6 text-xs bg-[var(--nps-bg-input)] hover:bg-[var(--nps-bg-hover)] border border-[var(--nps-border)] rounded text-[var(--nps-text-dim)] transition-colors select-none"
            >
              &#x232B;
            </button>
          </div>
        </div>
      </div>
    </>
  );
}
