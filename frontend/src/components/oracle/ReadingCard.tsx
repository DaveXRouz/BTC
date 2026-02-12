import { useTranslation } from "react-i18next";
import type { StoredReading } from "@/types";

interface ReadingCardProps {
  reading: StoredReading;
  onSelect: (id: number) => void;
  onToggleFavorite: (id: number) => void;
  onDelete: (id: number) => void;
}

const TYPE_COLORS: Record<string, string> = {
  reading: "bg-blue-500/20 text-blue-300",
  time: "bg-blue-500/20 text-blue-300",
  question: "bg-purple-500/20 text-purple-300",
  name: "bg-emerald-500/20 text-emerald-300",
  daily: "bg-amber-500/20 text-amber-300",
  multi_user: "bg-rose-500/20 text-rose-300",
};

export function ReadingCard({
  reading,
  onSelect,
  onToggleFavorite,
  onDelete,
}: ReadingCardProps) {
  const { t } = useTranslation();

  const typeClass =
    TYPE_COLORS[reading.sign_type] ?? "bg-nps-bg-input text-nps-text-dim";
  const displayText =
    reading.question || reading.sign_value || reading.sign_type;
  const dateStr = new Date(reading.created_at).toLocaleDateString();

  return (
    <div className="group border border-nps-border rounded-lg p-3 hover:border-nps-oracle-accent/50 transition-colors">
      {/* Header row: type badge + date + actions */}
      <div className="flex items-center gap-2 mb-2">
        <span
          className={`px-1.5 py-0.5 text-[10px] rounded font-medium ${typeClass}`}
        >
          {reading.sign_type}
        </span>
        <span className="flex-1" />
        <span className="text-[10px] text-nps-text-dim">{dateStr}</span>
        <button
          type="button"
          onClick={(e) => {
            e.stopPropagation();
            onToggleFavorite(reading.id);
          }}
          className="text-xs opacity-60 hover:opacity-100 transition-opacity"
          title={t("oracle.toggle_favorite")}
        >
          {reading.is_favorite ? "\u2605" : "\u2606"}
        </button>
        <button
          type="button"
          onClick={(e) => {
            e.stopPropagation();
            onDelete(reading.id);
          }}
          className="text-xs text-nps-text-dim opacity-0 group-hover:opacity-60 hover:!opacity-100 hover:text-red-400 transition-all"
          title={t("oracle.delete_reading")}
        >
          &times;
        </button>
      </div>

      {/* Body — clickable */}
      <button
        type="button"
        onClick={() => onSelect(reading.id)}
        className="w-full text-left"
      >
        <p className="text-xs text-nps-text truncate">{displayText}</p>
        {reading.ai_interpretation && (
          <p className="mt-1 text-[10px] text-nps-text-dim line-clamp-2">
            {reading.ai_interpretation}
          </p>
        )}
      </button>
    </div>
  );
}
