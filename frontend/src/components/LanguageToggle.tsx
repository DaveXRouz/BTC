import { useTranslation } from "react-i18next";

export function LanguageToggle() {
  const { i18n } = useTranslation();
  const isFA = i18n.language === "fa";

  function toggle() {
    const next = isFA ? "en" : "fa";
    i18n.changeLanguage(next);
  }

  return (
    <button
      onClick={toggle}
      className="flex items-center gap-1 px-2 py-1 min-h-[44px] min-w-[44px] justify-center text-xs rounded border border-[var(--nps-border)] hover:border-[var(--nps-accent)] focus:outline-none focus:ring-2 focus:ring-[var(--nps-accent)] transition-colors lg:min-h-0 lg:min-w-0"
      aria-label={
        isFA
          ? "Switch to English"
          : "\u062a\u063a\u06cc\u06cc\u0631 \u0628\u0647 \u0641\u0627\u0631\u0633\u06cc"
      }
      title={isFA ? "English" : "\u0641\u0627\u0631\u0633\u06cc"}
    >
      <span
        className={
          isFA
            ? "text-[var(--nps-text-dim)]"
            : "text-[var(--nps-accent)] font-bold"
        }
      >
        EN
      </span>
      <span className="text-[var(--nps-text-dim)]">/</span>
      <span
        className={
          isFA
            ? "text-[var(--nps-accent)] font-bold"
            : "text-[var(--nps-text-dim)]"
        }
      >
        FA
      </span>
    </button>
  );
}
