import { useTranslation } from "react-i18next";
import type { ConfidenceData, ConfidenceBoost } from "@/types";

interface ConfidenceMeterProps {
  confidence: ConfidenceData | null;
  boosts: ConfidenceBoost[];
}

const LEVEL_COLORS: Record<string, string> = {
  very_high: "bg-green-600",
  high: "bg-blue-600",
  medium: "bg-amber-600",
  low: "bg-red-600",
};

const LEVEL_TEXT_COLORS: Record<string, string> = {
  very_high: "text-green-600",
  high: "text-blue-600",
  medium: "text-amber-600",
  low: "text-red-600",
};

export function ConfidenceMeter({ confidence, boosts }: ConfidenceMeterProps) {
  const { t } = useTranslation();

  if (!confidence) {
    return (
      <div
        className="h-6 bg-nps-bg-input rounded animate-pulse"
        data-testid="confidence-skeleton"
      />
    );
  }

  const barColor = LEVEL_COLORS[confidence.level] ?? "bg-gray-500";
  const textColor = LEVEL_TEXT_COLORS[confidence.level] ?? "text-gray-500";
  const levelLabel = t(`oracle.confidence_level_${confidence.level}`);

  return (
    <div className="space-y-2" data-testid="confidence-meter">
      {/* Score label */}
      <div className="flex items-center justify-between text-xs">
        <span className="text-nps-text-dim">
          {t("oracle.confidence_label")}
        </span>
        <span
          className={`font-medium ${textColor}`}
          data-testid="confidence-label"
        >
          {t("oracle.confidence_score", { score: confidence.score })} —{" "}
          {levelLabel}
        </span>
      </div>

      {/* Progress bar */}
      <div
        className="w-full h-2 bg-nps-bg-input rounded-full overflow-hidden"
        role="progressbar"
        aria-valuenow={confidence.score}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label={t("oracle.confidence_label")}
        title={t("oracle.confidence_factors", {
          count: boosts.filter((b) => b.filled).length,
        })}
        data-testid="confidence-bar"
      >
        <div
          className={`h-full rounded-full transition-all duration-500 ${barColor}`}
          style={{ width: `${confidence.score}%` }}
          data-testid="confidence-fill"
        />
      </div>

      {/* Completeness breakdown */}
      {boosts.length > 0 && (
        <div className="space-y-1 pt-1" data-testid="confidence-boosts">
          {boosts.map((boost) => (
            <div
              key={boost.field}
              className="flex items-center justify-between text-xs"
              data-testid={`boost-${boost.field}`}
            >
              <span className="flex items-center gap-1.5">
                <span
                  className={
                    boost.filled ? "text-green-500" : "text-nps-text-dim"
                  }
                  data-testid={`boost-icon-${boost.field}`}
                >
                  {boost.filled ? "✓" : "○"}
                </span>
                <span
                  className={
                    boost.filled ? "text-nps-text" : "text-nps-text-dim"
                  }
                >
                  {boost.label}
                </span>
              </span>
              <span className="text-nps-text-dim">
                {boost.filled ? (
                  `+${boost.boost}%`
                ) : (
                  <span className="text-nps-oracle-accent/60 cursor-pointer hover:text-nps-oracle-accent">
                    {t("oracle.confidence_boost_add")}
                  </span>
                )}
              </span>
            </div>
          ))}
        </div>
      )}

      {/* Priority hint */}
      <p className="text-[10px] text-nps-text-dim/50 pt-1">
        {t("oracle.confidence_priority_hint")}
      </p>
    </div>
  );
}
