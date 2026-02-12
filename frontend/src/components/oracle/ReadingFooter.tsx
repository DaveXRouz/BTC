import { useTranslation } from "react-i18next";

interface ReadingFooterProps {
  confidence: number;
  generatedAt?: string;
}

export function ReadingFooter({ confidence, generatedAt }: ReadingFooterProps) {
  const { t } = useTranslation();
  const pct = Math.round(confidence * 100);
  const barColor =
    confidence > 0.7
      ? "bg-nps-success"
      : confidence > 0.4
        ? "bg-nps-warning"
        : "bg-nps-error";

  return (
    <div className="space-y-3 pt-2">
      {/* Confidence bar */}
      <div>
        <div className="flex items-center justify-between text-xs text-nps-text-dim mb-1">
          <span>{t("oracle.confidence_label")}</span>
          <span>{pct}%</span>
        </div>
        <div className="w-full h-2 bg-nps-bg-input rounded-full overflow-hidden">
          <div
            className={`h-full ${barColor} rounded-full transition-all`}
            style={{ width: `${pct}%` }}
            role="progressbar"
            aria-valuenow={pct}
            aria-valuemin={0}
            aria-valuemax={100}
          />
        </div>
      </div>

      {/* Attribution and disclaimer */}
      <div className="text-xs text-nps-text-dim space-y-1">
        <p>{t("oracle.powered_by")}</p>
        <p className="italic">{t("oracle.disclaimer")}</p>
        {generatedAt && (
          <p>
            {t("oracle.generated_at")}: {new Date(generatedAt).toLocaleString()}
          </p>
        )}
      </div>
    </div>
  );
}
