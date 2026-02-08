import { useState } from "react";
import { useTranslation } from "react-i18next";
import { translation } from "@/services/api";

interface TranslatedReadingProps {
  reading: string;
}

export function TranslatedReading({ reading }: TranslatedReadingProps) {
  const { t } = useTranslation();
  const [translatedText, setTranslatedText] = useState<string | null>(null);
  const [isTranslating, setIsTranslating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showTranslation, setShowTranslation] = useState(false);

  async function handleTranslate() {
    setIsTranslating(true);
    setError(null);
    try {
      const result = await translation.translate(reading, "en", "fa");
      setTranslatedText(result.translated_text);
      setShowTranslation(true);
    } catch {
      setError(t("oracle.translate_error"));
    } finally {
      setIsTranslating(false);
    }
  }

  return (
    <div className="space-y-2">
      {/* Original reading */}
      <div
        className={`text-sm text-nps-text ${translatedText && !showTranslation ? "opacity-60" : ""}`}
      >
        {showTranslation && translatedText ? (
          <p dir="rtl" className="font-[Vazirmatn]">
            {translatedText}
          </p>
        ) : (
          <p>{reading}</p>
        )}
      </div>

      {/* Controls */}
      <div className="flex items-center gap-2 flex-wrap">
        {!translatedText && (
          <button
            onClick={handleTranslate}
            disabled={isTranslating}
            className="px-3 py-1 text-xs bg-nps-oracle-accent/20 text-nps-oracle-accent border border-nps-oracle-border rounded hover:bg-nps-oracle-accent/30 transition-colors disabled:opacity-50"
          >
            {isTranslating ? t("oracle.translating") : t("oracle.translate")}
          </button>
        )}

        {translatedText && (
          <button
            onClick={() => setShowTranslation(!showTranslation)}
            className="px-3 py-1 text-xs text-nps-text-dim border border-nps-border rounded hover:text-nps-text transition-colors"
          >
            {showTranslation
              ? t("oracle.show_original")
              : t("oracle.show_translation")}
          </button>
        )}
      </div>

      {/* Error */}
      {error && <p className="text-xs text-nps-bg-danger">{error}</p>}
    </div>
  );
}
