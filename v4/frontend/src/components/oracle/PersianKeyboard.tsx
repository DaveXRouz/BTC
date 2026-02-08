import { useEffect, useRef } from "react";
import { useTranslation } from "react-i18next";
import { PERSIAN_ROWS } from "@/utils/persianKeyboardLayout";

interface PersianKeyboardProps {
  onCharacterClick: (char: string) => void;
  onBackspace: () => void;
  onClose: () => void;
}

export function PersianKeyboard({
  onCharacterClick,
  onBackspace,
  onClose,
}: PersianKeyboardProps) {
  const { t } = useTranslation();
  const panelRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape") onClose();
    }
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [onClose]);

  return (
    <>
      {/* Transparent backdrop for outside click */}
      <div className="fixed inset-0 z-40" onClick={onClose} />

      <div
        ref={panelRef}
        role="dialog"
        aria-label={t("oracle.keyboard_persian")}
        dir="rtl"
        className="absolute left-0 right-0 top-full mt-1 z-50 bg-nps-bg-card border border-nps-oracle-border rounded-lg p-3 shadow-lg"
      >
        {/* Close button */}
        <button
          type="button"
          onClick={onClose}
          className="absolute top-1 left-1 w-6 h-6 flex items-center justify-center text-nps-text-dim hover:text-nps-text text-xs rounded"
          aria-label={t("oracle.keyboard_close")}
        >
          ✕
        </button>

        {/* Character rows */}
        <div className="space-y-1.5 mt-2">
          {PERSIAN_ROWS.map((row, rowIndex) => (
            <div key={rowIndex} className="flex gap-1 justify-center flex-wrap">
              {row.map((char) => (
                <button
                  key={char}
                  type="button"
                  onClick={() => onCharacterClick(char)}
                  aria-label={char}
                  className="w-8 h-8 text-sm bg-nps-bg-input hover:bg-nps-bg-hover border border-nps-border rounded text-nps-text transition-colors"
                >
                  {char}
                </button>
              ))}
            </div>
          ))}

          {/* Bottom row: Space + Backspace */}
          <div className="flex gap-1 justify-center">
            <button
              type="button"
              onClick={() => onCharacterClick(" ")}
              aria-label={t("oracle.keyboard_space")}
              className="h-8 px-8 text-xs bg-nps-bg-input hover:bg-nps-bg-hover border border-nps-border rounded text-nps-text-dim transition-colors"
            >
              {t("oracle.keyboard_space")}
            </button>
            <button
              type="button"
              onClick={onBackspace}
              aria-label={t("oracle.keyboard_backspace")}
              className="h-8 px-4 text-xs bg-nps-bg-input hover:bg-nps-bg-hover border border-nps-border rounded text-nps-text-dim transition-colors"
            >
              ⌫
            </button>
          </div>
        </div>
      </div>
    </>
  );
}
