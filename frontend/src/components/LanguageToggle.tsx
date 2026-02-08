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
      className="flex items-center gap-1 px-2 py-1 text-xs rounded border border-nps-border hover:border-nps-oracle-accent transition-colors"
      aria-label={
        isFA
          ? "Switch to English"
          : "\u062a\u063a\u06cc\u06cc\u0631 \u0628\u0647 \u0641\u0627\u0631\u0633\u06cc"
      }
    >
      <span
        className={
          isFA ? "text-nps-text-dim" : "text-nps-oracle-accent font-bold"
        }
      >
        EN
      </span>
      <span className="text-nps-text-dim">/</span>
      <span
        className={
          isFA ? "text-nps-oracle-accent font-bold" : "text-nps-text-dim"
        }
      >
        FA
      </span>
    </button>
  );
}
