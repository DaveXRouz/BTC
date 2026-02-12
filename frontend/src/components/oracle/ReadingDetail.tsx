import { useTranslation } from "react-i18next";
import type { StoredReading } from "@/types";

interface ReadingDetailProps {
  reading: StoredReading;
  onClose: () => void;
  onToggleFavorite: (id: number) => void;
  onDelete: (id: number) => void;
}

export function ReadingDetail({
  reading,
  onClose,
  onToggleFavorite,
  onDelete,
}: ReadingDetailProps) {
  const { t } = useTranslation();

  return (
    <div className="border border-nps-border rounded-lg p-4 space-y-3">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="px-2 py-0.5 text-[10px] rounded bg-nps-bg-input text-nps-text-dim font-medium">
            {reading.sign_type}
          </span>
          <span className="text-xs text-nps-text-dim">
            {new Date(reading.created_at).toLocaleString()}
          </span>
        </div>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => onToggleFavorite(reading.id)}
            className="text-sm hover:scale-110 transition-transform"
            title={t("oracle.toggle_favorite")}
          >
            {reading.is_favorite ? "\u2605" : "\u2606"}
          </button>
          <button
            type="button"
            onClick={() => onDelete(reading.id)}
            className="text-xs text-nps-text-dim hover:text-red-400 transition-colors"
            title={t("oracle.delete_reading")}
          >
            {t("oracle.delete_reading")}
          </button>
          <button
            type="button"
            onClick={onClose}
            className="text-xs text-nps-text-dim hover:text-nps-text transition-colors"
          >
            {t("oracle.close_detail")}
          </button>
        </div>
      </div>

      {/* Question/Sign */}
      {reading.question && (
        <div>
          <h4 className="text-[10px] text-nps-text-dim uppercase tracking-wider mb-1">
            {t("oracle.question_label")}
          </h4>
          <p className="text-xs text-nps-text">{reading.question}</p>
        </div>
      )}
      {reading.sign_value && (
        <div>
          <h4 className="text-[10px] text-nps-text-dim uppercase tracking-wider mb-1">
            {t("oracle.sign_label")}
          </h4>
          <p className="text-xs text-nps-text">{reading.sign_value}</p>
        </div>
      )}

      {/* AI Interpretation */}
      {reading.ai_interpretation && (
        <div>
          <h4 className="text-[10px] text-nps-text-dim uppercase tracking-wider mb-1">
            {t("oracle.ai_interpretation")}
          </h4>
          <p className="text-xs text-nps-text whitespace-pre-line">
            {reading.ai_interpretation}
          </p>
        </div>
      )}

      {/* Raw reading result */}
      {reading.reading_result && (
        <div>
          <h4 className="text-[10px] text-nps-text-dim uppercase tracking-wider mb-1">
            {t("oracle.reading_data")}
          </h4>
          <pre className="text-[10px] text-nps-text-dim overflow-x-auto max-h-60 overflow-y-auto bg-nps-bg-input rounded p-2">
            {JSON.stringify(reading.reading_result, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
}
