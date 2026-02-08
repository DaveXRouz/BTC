import { useTranslation } from "react-i18next";
import { TranslatedReading } from "./TranslatedReading";
import type { ConsultationResult } from "@/types";

interface SummaryTabProps {
  result: ConsultationResult | null;
}

function getSummaryText(result: ConsultationResult): string {
  switch (result.type) {
    case "reading":
      return result.data.summary;
    case "question":
      return result.data.interpretation;
    case "name":
      return result.data.interpretation;
  }
}

function getTypeBadge(
  type: ConsultationResult["type"],
  t: (key: string) => string,
): { label: string; color: string } {
  switch (type) {
    case "reading":
      return {
        label: t("oracle.type_reading"),
        color: "bg-blue-600/20 text-blue-400",
      };
    case "question":
      return {
        label: t("oracle.type_question"),
        color: "bg-purple-600/20 text-purple-400",
      };
    case "name":
      return {
        label: t("oracle.type_name"),
        color: "bg-green-600/20 text-green-400",
      };
  }
}

export function SummaryTab({ result }: SummaryTabProps) {
  const { t } = useTranslation();

  if (!result) {
    return (
      <p className="text-nps-text-dim text-sm">
        {t("oracle.results_placeholder")}
      </p>
    );
  }

  const summary = getSummaryText(result);
  const badge = getTypeBadge(result.type, t);

  return (
    <div className="space-y-4">
      {/* Type badge + timestamp */}
      <div className="flex items-center gap-2">
        <span className={`px-2 py-0.5 text-xs rounded ${badge.color}`}>
          {badge.label}
        </span>
        {result.type === "reading" && result.data.generated_at && (
          <span className="text-xs text-nps-text-dim">
            {t("oracle.generated_at")}:{" "}
            {new Date(result.data.generated_at).toLocaleString()}
          </span>
        )}
      </div>

      {/* Quick stats for reading type */}
      {result.type === "reading" && result.data.fc60 && (
        <div className="flex gap-4 text-xs flex-wrap">
          <span className="text-nps-text-dim">
            {t("oracle.element")}:{" "}
            <span className="text-nps-text">{result.data.fc60.element}</span>
          </span>
          <span className="text-nps-text-dim">
            {t("oracle.energy")}:{" "}
            <span className="text-nps-text">
              {result.data.fc60.energy_level}
            </span>
          </span>
          {result.data.numerology && (
            <span className="text-nps-text-dim">
              {t("oracle.life_path")}:{" "}
              <span className="text-nps-text">
                {result.data.numerology.life_path}
              </span>
            </span>
          )}
          {result.data.moon && (
            <span className="text-nps-text-dim">
              Moon:{" "}
              <span className="text-nps-text">
                {result.data.moon.emoji} {result.data.moon.phase_name}
              </span>
            </span>
          )}
          {result.data.synchronicities &&
            result.data.synchronicities.length > 0 && (
              <span className="text-nps-text-dim">
                Syncs:{" "}
                <span className="text-nps-text">
                  {result.data.synchronicities.length}
                </span>
              </span>
            )}
        </div>
      )}

      {/* Quick stats for question type */}
      {result.type === "question" && (
        <div className="flex gap-4 text-xs">
          <span className="text-nps-text-dim">
            {t("oracle.answer")}:{" "}
            <span className="text-nps-text">{result.data.answer}</span>
          </span>
          <span className="text-nps-text-dim">
            {t("oracle.confidence")}:{" "}
            <span className="text-nps-text">
              {Math.round(result.data.confidence * 100)}%
            </span>
          </span>
        </div>
      )}

      {/* AI Interpretation (with translation support) */}
      {result.type === "reading" && result.data.ai_interpretation && (
        <div className="border border-nps-oracle-border rounded p-3 bg-nps-oracle-accent/5">
          <h4 className="text-xs font-medium text-nps-oracle-accent mb-2">
            AI Interpretation
          </h4>
          <TranslatedReading reading={result.data.ai_interpretation} />
        </div>
      )}

      {/* Summary text with translation support */}
      <TranslatedReading reading={summary} />
    </div>
  );
}
